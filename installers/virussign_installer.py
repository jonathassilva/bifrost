import subprocess
import argparse
import os
import shutil
import zipfile


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

        zf.extract(match, extract_dir)
        vir_path = os.path.join(extract_dir, match.replace('/', os.sep))
        print(f"[OK] Arquivo extraído    : {vir_path}")
        return vir_path


def rename_vir_to_apk(vir_path):
    base     = os.path.splitext(vir_path)[0]
    apk_path = base + '.apk'
    shutil.copy2(vir_path, apk_path)
    print(f"[OK] Convertido para APK : {apk_path}")
    return apk_path


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


def cleanup(vir_path, apk_path):
    """Remove o .vir, o .apk e os diretórios intermediários criados pela extração."""
    for path in [vir_path, apk_path]:
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
    apk_path = rename_vir_to_apk(vir_path)
    check_adb_device()
    install_apk(apk_path)
    cleanup(vir_path, apk_path)

    print("\n=== Instalação concluída ===\n")


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
            apk_path = rename_vir_to_apk(vir_path)

            # Move o .apk para samples/ e remove o .vir
            apk_filename = os.path.basename(apk_path)
            dest_path    = os.path.join(samples_dir, apk_filename)
            shutil.move(apk_path, dest_path)
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
    parser = argparse.ArgumentParser(description="Instala ou extrai APKs a partir de entradas do módulo de análise.")
    parser.add_argument('--mode', choices=['install', 'extract'], default='install',
                        help="'install' (default): instala no device via ADB. 'extract': extrai APKs para ./samples/")
    parser.add_argument('entry',    help="Modo install: string CSV. Modo extract: nome do arquivo .txt.")
    parser.add_argument('base_dir', help="Diretório onde estão os ZIPs. Ex: C:\\analise\\260603\\")

    args = parser.parse_args()

    if args.mode == 'install':
        run_install(args.entry, args.base_dir)
    elif args.mode == 'extract':
        run_extract(args.entry, args.base_dir)
