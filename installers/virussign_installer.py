import subprocess
import argparse
import os
import shutil
import sys
import zipfile


# Senha padrão da indústria para arquivos de amostras (ZipCrypto)
ZIP_PASSWORD = b"infected"

# Assinaturas (magic bytes) usadas para identificar o tipo real da amostra
MAGIC_APK = b"PK\x03\x04"   # APK é um ZIP
MAGIC_DEX = b"dex\n"         # Dalvik Executable: "dex\n035\0", "dex\n039\0"...

EXTENSION_BY_TYPE = {"apk": ".apk", "dex": ".dex", "unknown": ".bin"}


# ── Funções compartilhadas ────────────────────────────────────────────────────

def parse_csv_entry(csv_entry):
    parts = csv_entry.strip().split('::')
    if len(parts) != 2:
        raise ValueError(f"[ERRO] Formato inválido: '{csv_entry}'\n"
                         f"       Esperado: 'arquivo.zip::caminho\\arquivo.vir'")

    zip_name      = parts[0]
    internal_path = parts[1].replace('\\', '/')

    print(f"[OK] ZIP identificado    : {zip_name}")
    print(f"[OK] Arquivo interno     : {internal_path}")
    return zip_name, internal_path


def locate_zip(base_dir, zip_name):
    zip_path = os.path.join(base_dir, zip_name)
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(f"[ERRO] ZIP não encontrado: {zip_path}")
    print(f"[OK] ZIP localizado      : {zip_path}")
    return zip_path


def extract_vir(zip_path, internal_path):
    extract_dir = os.path.dirname(zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zip_entries = zf.namelist()
        match = next((e for e in zip_entries if e.replace('\\', '/') == internal_path), None)

        if not match:
            raise FileNotFoundError(f"[ERRO] '{internal_path}' não encontrado dentro do ZIP.\n"
                                    f"       Arquivos disponíveis: {zip_entries[:5]}...")

        try:
            # pwd é ignorado em entradas sem criptografia, então serve para ambos os casos
            zf.extract(match, extract_dir, pwd=ZIP_PASSWORD)
        except RuntimeError as e:
            raise RuntimeError(f"[ERRO] Falha ao descompactar '{match}' com a senha padrão: {e}") from e
        except NotImplementedError as e:
            # zipfile só suporta ZipCrypto; ZIPs com AES precisam de pyzipper ou 7-Zip
            raise RuntimeError(f"[ERRO] Criptografia do ZIP não suportada pelo zipfile (AES?): {e}") from e
        vir_path = os.path.join(extract_dir, match.replace('/', os.sep))
        print(f"[OK] Arquivo extraído    : {vir_path}")
        return vir_path


def detect_sample_type(path):
    """Identifica o tipo real da amostra pelos primeiros bytes: 'apk', 'dex' ou 'unknown'."""
    with open(path, 'rb') as f:
        head = f.read(4)
    if head == MAGIC_APK:
        return 'apk'
    if head == MAGIC_DEX:
        return 'dex'
    return 'unknown'


def convert_vir(vir_path):
    """
    Copia o .vir para a extensão correspondente ao seu tipo real
    (.apk, .dex ou .bin). Retorna (caminho_convertido, tipo).
    """
    sample_type = detect_sample_type(vir_path)
    out_path    = os.path.splitext(vir_path)[0] + EXTENSION_BY_TYPE[sample_type]
    shutil.copy2(vir_path, out_path)
    print(f"[OK] Tipo detectado      : {sample_type}")
    print(f"[OK] Convertido para     : {out_path}")
    return out_path, sample_type


def cleanup_vir(vir_path):
    """Remove apenas o .vir e os diretórios intermediários vazios."""
    try:
        if os.path.exists(vir_path):
            os.remove(vir_path)
            print(f"[OK] Removido: {vir_path}")
    except OSError as e:
        print(f"[AVISO] Não foi possível remover {vir_path}: {e}")

    parent = os.path.dirname(vir_path)
    while parent and os.path.isdir(parent):
        try:
            os.rmdir(parent)
            print(f"[OK] Diretório removido: {parent}")
            parent = os.path.dirname(parent)
        except OSError:
            break


def cleanup(vir_path, out_path):
    """Remove o .vir, o arquivo convertido e os diretórios intermediários criados pela extração."""
    for path in [vir_path, out_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[OK] Removido: {path}")
        except OSError as e:
            print(f"[AVISO] Não foi possível remover {path}: {e}")

    parent = os.path.dirname(vir_path)
    while parent and os.path.isdir(parent):
        try:
            os.rmdir(parent)
            print(f"[OK] Diretório removido: {parent}")
            parent = os.path.dirname(parent)
        except OSError:
            break


def check_adb_device():
    try:
        result  = subprocess.run(['adb', 'devices'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output  = result.stdout.decode('utf-8').strip().splitlines()
        devices = [line for line in output[1:] if line.strip() and 'device' in line]

        if not devices:
            raise RuntimeError("[ERRO] Nenhum dispositivo ADB conectado.")

        print(f"[OK] Dispositivo(s) ADB  : {len(devices)} conectado(s)")
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha ao executar adb devices: {e.stderr.decode('utf-8')}")
        raise


def install_apk(apk_path):
    try:
        result = subprocess.run(['adb', 'install', '-r', apk_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[OK] Instalação concluída: {result.stdout.decode('utf-8').strip()}")
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha na instalação: {e.stderr.decode('utf-8')}")
        raise


# ── Modo install ──────────────────────────────────────────────────────────────

def run_install(csv_entry, base_dir):
    print("\n=== Iniciando instalação ===\n")

    zip_name, internal_path = parse_csv_entry(csv_entry)
    zip_path = locate_zip(base_dir, zip_name)
    vir_path = extract_vir(zip_path, internal_path)
    out_path, sample_type = convert_vir(vir_path)

    if sample_type != 'apk':
        print(f"[AVISO] Amostra do tipo '{sample_type}' não é instalável via ADB; instalação ignorada.")
        print("        Use --mode extract para obter o arquivo para análise.")
        cleanup(vir_path, out_path)
        print("\n=== Instalação ignorada ===\n")
        return False

    try:
        check_adb_device()
        install_apk(out_path)
    finally:
        cleanup(vir_path, out_path)   # nunca deixa a amostra solta no disco, mesmo em falha

    print("\n=== Instalação concluída ===\n")
    return True


# ── Modo extract ──────────────────────────────────────────────────────────────

def run_extract(txt_file, base_dir):
    print("\n=== Iniciando extração em lote ===\n")

    # Localiza o .txt no mesmo diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    txt_path   = os.path.join(script_dir, txt_file)

    if not os.path.isfile(txt_path):
        raise FileNotFoundError(f"[ERRO] Arquivo .txt não encontrado: {txt_path}")

    # Cria o diretório samples/
    samples_dir = os.path.join(script_dir, 'samples')
    os.makedirs(samples_dir, exist_ok=True)
    print(f"[OK] Diretório de saída  : {samples_dir}\n")

    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    total   = len(lines)
    success = 0
    errors  = []

    for i, line in enumerate(lines, 1):
        print(f"--- [{i}/{total}] {line}")
        try:
            zip_name, internal_path = parse_csv_entry(line)
            zip_path = locate_zip(base_dir, zip_name)
            vir_path = extract_vir(zip_path, internal_path)
            out_path, sample_type = convert_vir(vir_path)
            if sample_type == 'unknown':
                print("[AVISO] Tipo não reconhecido; salvo como .bin para análise manual.")

            # Move o arquivo convertido para samples/ e remove o .vir
            dest_path = os.path.join(samples_dir, os.path.basename(out_path))
            shutil.move(out_path, dest_path)
            print(f"[OK] Movido para samples : {dest_path}")

            cleanup_vir(vir_path)
            success += 1

        except Exception as e:
            print(f"[ERRO] Falha ao processar linha {i}: {e}")
            errors.append((i, line, str(e)))

        print()

    # Resumo
    print("=== Resumo da extração ===")
    print(f"    Total     : {total}")
    print(f"    Sucesso   : {success}")
    print(f"    Erros     : {len(errors)}")
    if errors:
        print("\n    Linhas com erro:")
        for idx, entry, msg in errors:
            print(f"      [{idx}] {entry}\n           {msg}")

    print("\n=== Extração concluída ===\n")


# ── Entrada via CLI ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Instala ou extrai amostras (APK/DEX) a partir de entradas do módulo de análise.")
    parser.add_argument('--mode', choices=['install', 'extract'], default='install',
                        help="'install' (default): instala APKs no device via ADB (DEX e desconhecidos são ignorados). "
                             "'extract': extrai as amostras (.apk/.dex/.bin) para ./samples/")
    parser.add_argument('entry',    help="Modo install: string CSV. Modo extract: nome do arquivo .txt.")
    parser.add_argument('base_dir', help="Diretório onde estão os ZIPs. Ex: C:\\analise\\260603\\")

    args = parser.parse_args()

    if args.mode == 'install':
        installed = run_install(args.entry, args.base_dir)
        sys.exit(0 if installed else 2)   # 2 = amostra não instalável (ex.: DEX)
    elif args.mode == 'extract':
        run_extract(args.entry, args.base_dir)
