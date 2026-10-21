r"""
decrypt_all.py — descriptografa em lote os arquivos .pgp de uma pasta de data.

Uso:
    # Linux/macOS (a passphrase não fica no histórico do shell)
    read -rs BIFROST_GPG_PASSPHRASE && export BIFROST_GPG_PASSPHRASE
    python decrypters/decrypt_all.py --input-dir <OUTPUT_ROOT>/20260603 --key chave.asc

    # Windows PowerShell
    $env:BIFROST_GPG_PASSPHRASE = Read-Host -MaskInput
    python decrypters\decrypt_all.py --input-dir D:\malwares-virus-sign\20260603 --key chave.asc

Saída: <input-dir>/decrypted/<arquivo sem .pgp>

Segurança: a passphrase é entregue ao gpg pelo stdin (--passphrase-fd 0) e nunca
aparece na linha de comando. O argumento --passphrase ainda funciona, mas é obsoleto.
"""

import subprocess
import argparse
import os
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# 1. Detecção do binário GPG conforme o SO
# ──────────────────────────────────────────────
def detect_gpg() -> str:
    """Retorna o nome do binário GPG disponível no sistema."""
    for binary in ["gpg", "gpg.exe"]:
        try:
            subprocess.run(
                [binary, "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            print(f"[INFO] Binário GPG encontrado: '{binary}'")
            return binary
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue

    print("[ERRO] Nenhum binário GPG encontrado ('gpg' ou 'gpg.exe'). Verifique se o GnuPG está instalado.")
    sys.exit(1)



# ──────────────────────────────────────────────
# 2. Importação da chave .asc
# ──────────────────────────────────────────────
def import_key(gpg: str, key_file: Path) -> None:
    """Importa a chave .asc para o keyring local do GPG."""
    if not key_file.exists():
        print(f"[ERRO] Arquivo de chave não encontrado: {key_file}")
        sys.exit(1)

    print(f"[INFO] Importando chave: {key_file}")
    result = subprocess.run(
        [gpg, "--batch", "--yes", "--import", str(key_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stderr_output = result.stderr.decode("utf-8").strip()

    if result.returncode == 0:
        print("[INFO] Chave importada com sucesso.")
    elif result.returncode == 2:
        # Código 2 indica aviso (ex: UID sem auto-assinatura), não falha fatal
        print(f"[AVISO] Chave importada com avisos (não críticos):\n{stderr_output}")
    else:
        print(f"[ERRO] Falha ao importar a chave (código {result.returncode}):\n{stderr_output}")
        sys.exit(1)


# ──────────────────────────────────────────────
# 3. Descriptografia de um único arquivo .pgp
# ──────────────────────────────────────────────
def decrypt_file(gpg: str, encrypted_file: Path, output_file: Path, passphrase: str) -> bool:
    """
    Descriptografa um arquivo .pgp e salva o resultado em output_file.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    command = [
        gpg,
        "--batch",
        "--yes",
        "--ignore-mdc-error",
        "--pinentry-mode", "loopback",
        "--passphrase-fd", "0",       # lê a passphrase do stdin: nunca aparece em argv/ps
        "--output", str(output_file),
        "--decrypt", str(encrypted_file),
    ]

    try:
        subprocess.run(
            command,
            input=(passphrase + "\n").encode("utf-8"),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"  [OK]     {encrypted_file.name} → {output_file.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FALHOU] {encrypted_file.name}")
        print(f"           {e.stderr.decode('utf-8').strip()}")
        return False


# ──────────────────────────────────────────────
# 4. Varredura do diretório e processamento em lote
# ──────────────────────────────────────────────
def process_directory(gpg: str, input_dir: Path, passphrase: str) -> None:
    """
    Varre input_dir em busca de arquivos .pgp,
    descriptografa cada um e salva em input_dir/decrypted/.
    """
    # Cria o subdiretório de saída
    output_dir = input_dir / "decrypted"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Diretório de saída: {output_dir}")

    # Lista apenas arquivos .pgp (não recursivo)
    pgp_files = sorted(input_dir.glob("*.pgp"))

    if not pgp_files:
        print("[AVISO] Nenhum arquivo .pgp encontrado no diretório informado.")
        return

    print(f"[INFO] {len(pgp_files)} arquivo(s) .pgp encontrado(s). Iniciando descriptografia...\n")

    ok = 0
    failed = 0

    for pgp_file in pgp_files:
        # Remove a extensão .pgp para obter o nome de saída
        # Ex: Android_260603_metadata.zip.pgp → Android_260603_metadata.zip
        output_file = output_dir / pgp_file.stem

        success = decrypt_file(gpg, pgp_file, output_file, passphrase)
        if success:
            ok += 1
        else:
            failed += 1

    # ── Relatório final ──
    print(f"\n{'─' * 45}")
    print(f"  Relatório final")
    print(f"{'─' * 45}")
    print(f"  Arquivos processados : {ok + failed}")
    print(f"  Sucesso              : {ok}")
    print(f"  Falhas               : {failed}")
    print(f"  Saída                : {output_dir}")
    print(f"{'─' * 45}")


# ──────────────────────────────────────────────
# 5. Obtenção da passphrase
# ──────────────────────────────────────────────
PASSPHRASE_ENV = "BIFROST_GPG_PASSPHRASE"


def resolve_passphrase(cli_value: str | None) -> str:
    """
    Fonte oficial: variável de ambiente BIFROST_GPG_PASSPHRASE.
    O argumento --passphrase ainda é aceito por compatibilidade, mas expõe a
    passphrase em ps e no histórico do shell, por isso gera aviso.
    """
    if cli_value:
        print(
            f"[AVISO] --passphrase está obsoleto: a passphrase fica visível na lista de processos "
            f"e no histórico do shell. Use a variável de ambiente {PASSPHRASE_ENV}.",
            file=sys.stderr,
        )
        return cli_value

    value = os.environ.get(PASSPHRASE_ENV)
    if not value:
        print(
            f"[ERRO] Passphrase não informada. Defina a variável de ambiente {PASSPHRASE_ENV}.\n"
            f"       Linux/macOS : read -rs {PASSPHRASE_ENV} && export {PASSPHRASE_ENV}\n"
            f"       PowerShell  : $env:{PASSPHRASE_ENV} = Read-Host -MaskInput",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


# ──────────────────────────────────────────────
# 6. Ponto de entrada
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Descriptografa em lote arquivos .pgp usando GnuPG."
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Diretório contendo os arquivos .pgp a serem descriptografados.",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="Caminho para o arquivo de chave .asc usado na descriptografia.",
    )
    parser.add_argument(
        "--passphrase",
        help=f"OBSOLETO (inseguro). Use a variável de ambiente {PASSPHRASE_ENV}.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    key_file  = Path(args.key).resolve()

    if not input_dir.is_dir():
        print(f"[ERRO] Diretório não encontrado: {input_dir}")
        sys.exit(1)

    passphrase = resolve_passphrase(args.passphrase)

    gpg = detect_gpg()
    import_key(gpg, key_file)
    process_directory(gpg, input_dir, passphrase)


if __name__ == "__main__":
    main()