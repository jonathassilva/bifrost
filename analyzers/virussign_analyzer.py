#!/usr/bin/env python3
"""
Bistrof — Módulo de Análise e Categorização
Entrada : diretório contendo ZIPs de binários + ZIP de metadata
Saída   : arquivo CSV com informações sumarizadas e categorizadas
"""

import argparse
import csv
import json
import logging
import os
import re
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bistrof")

# ---------------------------------------------------------------------------
# Hierarquia de engines para eleição do best_label
# Engines no início da lista têm maior prioridade
# ---------------------------------------------------------------------------
ENGINE_HIERARCHY = [
    "Kaspersky",
    "ESET-NOD32",
    "DrWeb",
    "AhnLab-V3",
    "BitDefenderFalx",
    "F-Secure",
    "SymantecMobileInsight",
    "Fortinet",
    "Ikarus",
]

# Engines cujos labels são genéricos/inúteis para categorização
GENERIC_ENGINES = {"Google", "Cynet", "K7GW", "K7AntiVirus"}

# Labels genéricos que devem ser ignorados na eleição
GENERIC_LABEL_PATTERNS = re.compile(
    r"^(Detected|Malicious.*|Trojan\s*\(\s*[0-9a-f]+\s*\)|"
    r"Virus\s*\(\s*[0-9a-f]+\s*\)|[0-9a-f]{8,})$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Mapeamento de category a partir do best_label
# A ordem importa: regras mais específicas primeiro
# ---------------------------------------------------------------------------

def _token(word: str) -> str:
    """
    Casa `word` apenas como token isolado, delimitado por qualquer coisa que não
    seja letra (início/fim, '.', '/', ':', '-', '_', dígitos...).
    Necessário para siglas curtas: sem isso, 'RAT' casaria com 'Operator',
    'Pirate', 'Corporate' e 'PUP' com 'Pupil'.
    Obs.: \\b não serve aqui porque trata '_' e dígitos como parte da palavra.
    """
    return rf"(?<![a-z]){word}(?![a-z])"


# RAT isolado (Android.Rat.X) OU sufixo em CamelCase (AsyncRAT, SpyRAT, AndroidRAT_x).
# O sufixo exige 'RAT' maiúsculo após minúscula para não casar 'Separate', 'Ratings'.
_RAT = rf"{_token('rat')}|(?-i:[a-z]RAT)(?![a-z])"

CATEGORY_RULES = [
    (re.compile(r"Trojan-Banker|Banker", re.I),                       "Trojan-Banker"),
    (re.compile(r"Trojan-Spy|SpyNote|Spyware", re.I),                 "Trojan-Spy"),
    (re.compile(r"Trojan-Dropper|Dropper", re.I),                     "Trojan-Dropper"),
    (re.compile(r"Trojan-Downloader|Downloader", re.I),               "Trojan-Downloader"),
    (re.compile(rf"Backdoor|{_RAT}", re.I),                           "Backdoor"),
    (re.compile(r"Mirai|Gafgyt|XorDDoS|Botnet", re.I),                "Botnet"),
    (re.compile(r"HackTool|Metasploit|Masplot", re.I),                "HackTool"),
    (re.compile(r"AdWare|(?<![a-z])Adlo|MobiDash", re.I),             "Adware"),
    (re.compile(rf"{_token('PUA')}|{_token('PUP')}|Riskware|Unwanted", re.I), "PUA"),
    (re.compile(r"Trojan", re.I),                                     "Trojan"),
]

CSV_COLUMNS = [
    "date_dir",
    "location",
    "local_location",
    "md5",
    "sha1",
    "sha256",
    "type",
    "positives",
    "scandate(GMT)",
    "best_engine",
    "best_label",
    "category",
    "engines_json",
]

# ---------------------------------------------------------------------------
# Parsing de um arquivo .log
# ---------------------------------------------------------------------------

def parse_log(content: str) -> dict:
    """
    Parseia o conteúdo de um arquivo .log do VirusSign.
    Retorna um dicionário com campos de cabeçalho e detecções por engine.
    """
    lines = content.splitlines()

    header = {}
    detections = {}       # engine -> label
    in_detections = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            in_detections = True
            continue

        if in_detections:
            parts = line.split("\t")
            if len(parts) >= 2:
                engine = parts[0].strip()
                label  = parts[1].strip()
                detections[engine] = label
        else:
            if ": " in line:
                key, _, value = line.partition(": ")
                header[key.strip()] = value.strip()

    return {"header": header, "detections": detections}


# ---------------------------------------------------------------------------
# Eleição de best_engine / best_label
# ---------------------------------------------------------------------------

def is_generic_label(label: str) -> bool:
    return bool(GENERIC_LABEL_PATTERNS.match(label))


def elect_best(detections: dict) -> tuple[str, str]:
    """
    Percorre a hierarquia de engines e retorna (best_engine, best_label).
    Engines genéricas e labels genéricos são ignorados na eleição.
    Fallback: primeiro engine disponível com label não genérico fora da lista negra.
    """
    # Tentativa 1: hierarquia definida
    for engine in ENGINE_HIERARCHY:
        label = detections.get(engine, "")
        if label and not is_generic_label(label):
            return engine, label

    # Tentativa 2: qualquer engine com label semântico
    for engine, label in detections.items():
        if engine not in GENERIC_ENGINES and label and not is_generic_label(label):
            return engine, label

    return "", ""


# ---------------------------------------------------------------------------
# Normalização de category
# ---------------------------------------------------------------------------

def normalize_category(best_label: str) -> str:
    if not best_label:
        return "Unknown"
    for pattern, category in CATEGORY_RULES:
        if pattern.search(best_label):
            return category
    return "Unknown"


# ---------------------------------------------------------------------------
# Construção do engines_json
# ---------------------------------------------------------------------------

def build_engines_json(detections: dict) -> str:
    """
    Retorna JSON apenas com engines da hierarquia que estiverem presentes,
    incluindo engines com labels genéricos (para fins de auditoria).
    """
    result = {
        engine: detections[engine]
        for engine in ENGINE_HIERARCHY
        if engine in detections
    }
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Etapa 1 — Localizar e extrair metadata
# ---------------------------------------------------------------------------

def extract_metadata(input_dir: Path) -> Path:
    candidates = list(input_dir.glob("*_metadata.zip"))
    if not candidates:
        raise FileNotFoundError(f"Nenhum arquivo *_metadata.zip encontrado em {input_dir}")
    if len(candidates) > 1:
        log.warning("Múltiplos *_metadata.zip encontrados; usando o primeiro: %s", candidates[0])

    metadata_zip = candidates[0]
    metadata_dir = input_dir / "metadata"
    metadata_dir.mkdir(exist_ok=True)

    log.info("Extraindo metadata de %s → %s", metadata_zip.name, metadata_dir)
    with zipfile.ZipFile(metadata_zip, "r") as zf:
        zf.extractall(metadata_dir)

    log.info("Logs extraídos: %d arquivos", len(list(metadata_dir.glob("*.log"))))
    return metadata_dir


# ---------------------------------------------------------------------------
# Etapa 2 — Pré-processar engines únicas (auditoria)
# ---------------------------------------------------------------------------

def collect_unique_engines(metadata_dir: Path) -> list[str]:
    engines = set()

    for log_file in metadata_dir.glob("*.log"):
        content = log_file.read_text(encoding="utf-8", errors="replace")
        in_detections = False
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                in_detections = True
                continue
            if in_detections:
                parts = line.split("\t")
                if parts:
                    engines.add(parts[0].strip())

    unique_sorted = sorted(engines)
    log.info("Engines únicas encontradas (%d): %s", len(unique_sorted), ", ".join(unique_sorted))
    return unique_sorted


# ---------------------------------------------------------------------------
# Etapa 3 — Construir índice MD5 → ZIP
# ---------------------------------------------------------------------------

def build_md5_index(input_dir: Path) -> dict[str, str]:
    """
    Varre todos os ZIPs de binários (exceto *_metadata.zip) e mapeia
    cada nome de arquivo interno (sem extensão = md5) ao nome do ZIP.
    """
    index: dict[str, str] = {}
    zip_files = [
        f for f in input_dir.glob("*.zip")
        if not f.name.endswith("_metadata.zip")
    ]

    log.info("Construindo índice MD5 → ZIP (%d arquivos ZIP)...", len(zip_files))
    for zip_path in sorted(zip_files):
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for name in zf.namelist():
                    # O nome interno é o MD5 com extensão .vir (ou similar)
                    md5 = Path(name).stem.lower()
                    if md5 and md5 not in index:
                        index[md5] = zip_path.name
        except zipfile.BadZipFile:
            log.warning("ZIP corrompido ou inválido, ignorado: %s", zip_path.name)

    log.info("Índice construído: %d entradas", len(index))
    return index


# ---------------------------------------------------------------------------
# Etapa 4+5 — Processar logs e gerar CSV
# ---------------------------------------------------------------------------

def process_logs(
    input_dir: Path,
    metadata_dir: Path,
    md5_index: dict[str, str],
    output_csv: Path,
) -> None:
    date_dir = input_dir.name
    log_files = sorted(metadata_dir.glob("*.log"))
    log.info("Processando %d arquivos de log...", len(log_files))

    not_found_count = 0

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for log_file in log_files:
            content = log_file.read_text(encoding="utf-8", errors="replace")
            parsed = parse_log(content)

            header     = parsed["header"]
            detections = parsed["detections"]

            location   = header.get("location", "")
            md5        = header.get("md5", log_file.stem).lower()

            # Monta local_location
            zip_origin = md5_index.get(md5)
            if zip_origin:
                local_location = f"{zip_origin}::{location}"
            else:
                local_location = "NOT_FOUND"
                not_found_count += 1

            best_engine, best_label = elect_best(detections)
            category    = normalize_category(best_label)
            engines_json = build_engines_json(detections)

            writer.writerow({
                "date_dir":      date_dir,
                "location":      location,
                "local_location": local_location,
                "md5":           md5,
                "sha1":          header.get("sha1", ""),
                "sha256":        header.get("sha256", ""),
                "type":          header.get("type", ""),
                "positives":     header.get("positives", ""),
                "scandate(GMT)": header.get("scandate(GMT)", ""),
                "best_engine":   best_engine,
                "best_label":    best_label,
                "category":      category,
                "engines_json":  engines_json,
            })

    log.info("CSV gerado: %s", output_csv)
    if not_found_count:
        log.warning("Samples não encontrados em nenhum ZIP: %d", not_found_count)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bistrof — Módulo de Análise e Categorização de Malwares"
    )
    parser.add_argument(
        "input_dir",
        help="Diretório contendo os ZIPs de binários e o ZIP de metadata",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Caminho do CSV de saída (padrão: <input_dir>/<date_dir>.csv)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Diretório não encontrado: {input_dir}")

    output_csv = Path(args.output) if args.output else input_dir / f"{input_dir.name}.csv"

    log.info("=== Bistrof Analyzer ===")
    log.info("Diretório de entrada : %s", input_dir)
    log.info("CSV de saída         : %s", output_csv)

    # Etapa 1 — Extrair metadata
    metadata_dir = extract_metadata(input_dir)

    # Etapa 2 — Pré-processar engines únicas (auditoria)
    collect_unique_engines(metadata_dir)

    # Etapa 3 — Construir índice MD5 → ZIP
    md5_index = build_md5_index(input_dir)

    # Etapas 4+5 — Processar logs e gerar CSV
    process_logs(input_dir, metadata_dir, md5_index, output_csv)

    log.info("=== Concluído ===")


if __name__ == "__main__":
    main()
