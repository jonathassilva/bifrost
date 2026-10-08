"""Bugs 8 e 9 — detecção APK/DEX e ZIPs com senha 'infected'."""
import shutil
import subprocess
import zipfile

import pytest

APK_BYTES = b"PK\x03\x04" + b"\x00" * 60
DEX_BYTES = b"dex\n035\x00" + b"\x00" * 60

needs_zip_cli = pytest.mark.skipif(shutil.which("zip") is None, reason="binário 'zip' indisponível")


def make_zip(base_dir, zip_name, entries, password=None):
    """Cria um ZIP com entradas {caminho_interno: bytes}. Com senha, usa o CLI 'zip -P'."""
    zip_path = base_dir / zip_name
    if password is None:
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, data in entries.items():
                zf.writestr(name, data)
        return zip_path
    staging = base_dir / "_staging"
    for name, data in entries.items():
        (staging / name).parent.mkdir(parents=True, exist_ok=True)
        (staging / name).write_bytes(data)
    subprocess.run(["zip", "-q", "-r", "-P", password, str(zip_path), "."], cwd=staging, check=True)
    shutil.rmtree(staging)
    return zip_path


@pytest.mark.parametrize("data, expected", [(APK_BYTES, "apk"), (DEX_BYTES, "dex"), (b"MZ\x90\x00", "unknown")], ids=["apk", "dex", "pe-desconhecido"])
def test_detect_sample_type(installer, tmp_path, data, expected):
    f = tmp_path / "x.vir"
    f.write_bytes(data)
    assert installer.detect_sample_type(str(f)) == expected


@needs_zip_cli
def test_extract_vir_zip_com_senha(installer, tmp_path):
    zip_path = make_zip(tmp_path, "Android_260603_01.zip", {"ST22/apk/aaa.vir": APK_BYTES}, password="infected")
    vir = installer.extract_vir(str(zip_path), "ST22/apk/aaa.vir")
    assert open(vir, "rb").read() == APK_BYTES


def test_extract_vir_zip_sem_senha(installer, tmp_path):
    zip_path = make_zip(tmp_path, "Android_260603_02.zip", {"ST22/apk/bbb.vir": APK_BYTES})
    vir = installer.extract_vir(str(zip_path), "ST22/apk/bbb.vir")
    assert open(vir, "rb").read() == APK_BYTES


def test_run_install_ignora_dex_sem_chamar_adb(installer, tmp_path, monkeypatch):
    make_zip(tmp_path, "Android_260603_B_18.zip", {"ST27/dex/ccc.vir": DEX_BYTES})
    monkeypatch.setattr(installer, "check_adb_device", lambda: pytest.fail("adb não deveria ser chamado"))
    monkeypatch.setattr(installer, "install_apk", lambda p: pytest.fail("install não deveria ser chamado"))

    assert installer.run_install(r"Android_260603_B_18.zip::ST27\dex\ccc.vir", str(tmp_path)) is False
    assert not (tmp_path / "ST27").exists()   # nada de amostra solta no disco


def test_run_install_limpa_mesmo_se_adb_falhar(installer, tmp_path, monkeypatch):
    make_zip(tmp_path, "Android_260603_12.zip", {"ST22/apk/ddd.vir": APK_BYTES})
    monkeypatch.setattr(installer, "check_adb_device", lambda: None)

    def boom(_):
        raise RuntimeError("adb falhou")
    monkeypatch.setattr(installer, "install_apk", boom)

    with pytest.raises(RuntimeError):
        installer.run_install(r"Android_260603_12.zip::ST22\apk\ddd.vir", str(tmp_path))
    assert not (tmp_path / "ST22").exists()


def test_run_extract_preserva_extensao_real(installer, tmp_path, monkeypatch):
    zips = tmp_path / "zips"
    zips.mkdir()
    make_zip(zips, "Android_260603_12.zip", {"ST22/apk/eee.vir": APK_BYTES})
    make_zip(zips, "Android_260603_B_18.zip", {"ST27/dex/fff.vir": DEX_BYTES})

    script_dir = tmp_path / "installers"
    script_dir.mkdir()
    (script_dir / "list.txt").write_text(
        "Android_260603_12.zip::ST22\\apk\\eee.vir\nAndroid_260603_B_18.zip::ST27\\dex\\fff.vir\n"
    )
    monkeypatch.setattr(installer, "__file__", str(script_dir / "virussign_installer.py"))

    installer.run_extract("list.txt", str(zips))

    assert sorted(p.name for p in (script_dir / "samples").iterdir()) == ["eee.apk", "fff.dex"]
