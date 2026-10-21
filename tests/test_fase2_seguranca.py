"""Fase 2 — regressão dos itens de segurança e das correções do analyzer."""
import os
import subprocess
import types
import zipfile
from pathlib import Path

import pytest

SENHA = "S3nh@#Forte!"
posix_only = pytest.mark.skipif(os.name != "posix", reason="permissões POSIX")


def _fake_run(calls, returncode=0, stdout="<html></html>"):
    def run(cmd, *args, **kwargs):
        calls.append({"cmd": list(cmd), "kwargs": kwargs})
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")
    return run


# ── S1: credenciais do wget ────────────────────────────────────────────────────
@pytest.mark.parametrize("modulo", ["android_dl", "malware_dl"])
def test_s1_senha_nunca_vai_para_argv(request, monkeypatch, modulo):
    dl = request.getfixturevalue(modulo)
    calls = []
    monkeypatch.setattr(dl.subprocess, "run", _fake_run(calls))
    with dl.wget_auth("analista", SENHA) as flags:
        cfg = Path(flags[0].split("=", 1)[1])
        assert SENHA in cfg.read_text()                     # credencial está no arquivo...
        dl.fetch_listing("wget", "https://x/", flags)
    assert not any(SENHA in arg for c in calls for arg in c["cmd"])   # ...e não no comando
    assert not cfg.exists()                                 # arquivo removido ao sair


@posix_only
def test_s1_arquivo_de_credenciais_so_do_usuario(android_dl):
    with android_dl.wget_auth("u", SENHA) as flags:
        assert os.stat(flags[0].split("=", 1)[1]).st_mode & 0o077 == 0


def test_s1_arquivo_removido_mesmo_com_erro(android_dl):
    with pytest.raises(RuntimeError):
        with android_dl.wget_auth("u", SENHA) as flags:
            cfg = Path(flags[0].split("=", 1)[1])
            raise RuntimeError("falha no meio do download")
    assert not cfg.exists()


# ── S3: permissão do virussign.auth ────────────────────────────────────────────
@posix_only
@pytest.mark.parametrize("mode, avisa", [(0o600, False), (0o640, True), (0o644, True)], ids=["0600", "0640", "0644"])
def test_s3_aviso_de_permissao(android_dl, tmp_path, mode, avisa):
    f = tmp_path / "virussign.auth"
    f.write_text("u\np\n")
    f.chmod(mode)
    assert android_dl.warn_if_insecure_permissions(f) is avisa


# ── S5: diretório de saída ─────────────────────────────────────────────────────
def test_s5_precedencia_output_root(android_dl, monkeypatch):
    monkeypatch.delenv("BIFROST_OUTPUT_ROOT", raising=False)
    assert android_dl.resolve_output_root(None) == Path(android_dl.OUTPUT_ROOT)
    monkeypatch.setenv("BIFROST_OUTPUT_ROOT", "/env")
    assert android_dl.resolve_output_root(None) == Path("/env")
    assert android_dl.resolve_output_root("/cli") == Path("/cli")


# ── S2: passphrase do GPG ──────────────────────────────────────────────────────
def test_s2_passphrase_pelo_stdin(decrypter, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(decrypter.subprocess, "run", _fake_run(calls))
    decrypter.decrypt_file("gpg", tmp_path / "a.zip.pgp", tmp_path / "a.zip", SENHA)
    (call,) = calls
    assert not any(SENHA in arg for arg in call["cmd"])
    assert "--passphrase-fd" in call["cmd"]
    assert SENHA.encode() in call["kwargs"]["input"]


def test_s2_resolve_passphrase(decrypter, monkeypatch, capsys):
    monkeypatch.setenv("BIFROST_GPG_PASSPHRASE", "da-env")
    assert decrypter.resolve_passphrase(None) == "da-env"
    assert decrypter.resolve_passphrase("da-cli") == "da-cli"
    assert "obsoleto" in capsys.readouterr().err
    monkeypatch.delenv("BIFROST_GPG_PASSPHRASE")
    with pytest.raises(SystemExit):
        decrypter.resolve_passphrase(None)


# ── S7: extração do metadata ───────────────────────────────────────────────────
def _metadata_zip(pasta, entradas):
    with zipfile.ZipFile(pasta / "X_260919_metadata.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in entradas.items():
            z.writestr(nome, conteudo)


def test_s7_extrai_so_logs_legitimos(analyzer, tmp_path):
    _metadata_zip(tmp_path, {
        "aaa.log": "ok", "sub/bbb.log": "ok",
        "../escapou.log": "x", "/abs/x.log": "x", "sub/../../y.log": "x",
        "payload.exe": "MZ", "script.sh": "rm",
    })
    meta = analyzer.extract_metadata(tmp_path)
    criados = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file() and p.suffix != ".zip")
    assert criados == ["metadata/aaa.log", "metadata/sub/bbb.log"]
    assert meta == tmp_path / "metadata"


def test_s7_rejeita_log_grande_demais(analyzer, tmp_path, monkeypatch):
    monkeypatch.setattr(analyzer, "MAX_LOG_BYTES", 1000)
    _metadata_zip(tmp_path, {"bomba.log": b"\0" * 5000, "ok.log": "ok"})
    analyzer.extract_metadata(tmp_path)
    assert sorted(p.name for p in (tmp_path / "metadata").iterdir()) == ["ok.log"]


def test_s7_aborta_no_limite_total(analyzer, tmp_path, monkeypatch):
    monkeypatch.setattr(analyzer, "MAX_LOG_BYTES", 10_000)
    monkeypatch.setattr(analyzer, "MAX_TOTAL_BYTES", 25_000)
    _metadata_zip(tmp_path, {f"{i}.log": b"x" * 9_000 for i in range(5)})
    with pytest.raises(RuntimeError, match="zip bomb"):
        analyzer.extract_metadata(tmp_path)
    tamanhos = {p.stat().st_size for p in (tmp_path / "metadata").iterdir()}
    assert tamanhos == {9_000}                              # nenhum arquivo parcial


# ── date_dir ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("caminho, esperado", [
    ("dados/20260919/decrypted", "20260919"),
    ("dados/20260919/Decrypted", "20260919"),               # Windows não diferencia caixa
    ("dados/20260919", "20260919"),
    ("dados/decrypted_old", "decrypted_old"),
])
def test_date_dir(analyzer, tmp_path, caminho, esperado):
    assert analyzer.resolve_date_dir(tmp_path / caminho) == esperado
