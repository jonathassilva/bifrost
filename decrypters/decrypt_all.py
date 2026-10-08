import subprocess
import argparse
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
        "--passphrase", passphrase,
        "--output", str(output_file),
        "--decrypt", str(encrypted_file),
    ]

    try:
        subprocess.run(
            command,
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
# 5. Ponto de entrada
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
        required=True,
        help="Passphrase para a chave privada.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    key_file  = Path(args.key).resolve()

    if not input_dir.is_dir():
        print(f"[ERRO] Diretório não encontrado: {input_dir}")
        sys.exit(1)

    gpg = detect_gpg()
    import_key(gpg, key_file)
    process_directory(gpg, input_dir, args.passphrase)


if __name__ == "__main__":
    main()