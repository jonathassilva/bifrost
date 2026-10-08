"""
Carrega os scripts do Bifrost como módulos a partir do caminho do arquivo.
Os scripts vivem em pastas sem __init__.py e não são instaláveis (ainda),
então importlib é a forma menos invasiva de testá-los.
"""
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_module(relative_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def analyzer():
    return load_module("analyzers/virussign_analyzer.py", "virussign_analyzer")


@pytest.fixture(scope="session")
def android_dl():
    return load_module("downloaders/android_downloader.py", "android_downloader")


@pytest.fixture(scope="session")
def malware_dl():
    return load_module("downloaders/malwares_downloader.py", "malwares_downloader")


@pytest.fixture
def installer():
    # escopo por teste: alguns testes fazem monkeypatch em __file__
    return load_module("installers/virussign_installer.py", "virussign_installer")
