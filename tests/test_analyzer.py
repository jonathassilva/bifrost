"""Bug 5 — categorização sem falsos positivos de siglas curtas."""
import pytest


@pytest.mark.parametrize("label, expected", [
    # verdadeiros positivos que DEVEM continuar funcionando
    ("HEUR:Trojan-Banker.AndroidOS.Anubis.t", "Trojan-Banker"),
    ("HEUR:Trojan-Spy.AndroidOS.SpyNote.a", "Trojan-Spy"),
    ("HEUR:Backdoor.AndroidOS.Ahmyth.f", "Backdoor"),
    ("Android.Rat.Generic", "Backdoor"),
    ("Trojan.AndroidOS.SpyRAT.a", "Backdoor"),
    ("MSIL/AsyncRAT.A", "Backdoor"),
    ("Win32/AndroidRAT_variant", "Backdoor"),
    ("Adware.Adload.B", "Adware"),
    ("not-a-virus:HEUR:AdWare.AndroidOS.MobiDash.b", "Adware"),
    ("Android/PUA.Generic", "PUA"),
    ("Application.PUP.Toolbar", "PUA"),
    ("Linux.Gafgyt.Botnet", "Botnet"),
    ("HackTool.Metasploit", "HackTool"),
    ("HEUR:Trojan.AndroidOS.Boogr.gsh", "Trojan"),
    # falsos positivos corrigidos
    ("Riskware.Operator", "PUA"),
    ("Android.Riskware.Separate", "PUA"),
    ("Trojan.Generic.Pirate", "Trojan"),
    ("Trojan.Headloader.X", "Trojan"),
    ("Win32.Pupil.Something", "Unknown"),
    ("Corporate.Tool", "Unknown"),
    ("Android.Hiddad.Ratings", "Unknown"),
    ("", "Unknown"),
    # Fase 2: novas regras
    ("not-a-virus:HEUR:RiskTool.AndroidOS.Pirater.a", "PUA"),
    ("not-a-virus:Monitor.AndroidOS.Cerberus.a", "PUA"),
    ("Android.RiskTool.Agent", "PUA"),
    ("HEUR:Backdoor.Linux.Mirai.ad", "Botnet"),
    ("HEUR:Trojan-Downloader.Shell.Mirai.a", "Botnet"),
    # Fase 2: o que NÃO pode mudar
    ("not-a-virus:HEUR:AdWare.AndroidOS.MobiDash.b", "Adware"),         # not-a-virus não engole Adware
    ("not-a-virus:HEUR:Downloader.AndroidOS.Agent.b", "Trojan-Downloader"),
    ("Trojan.Mirage.Generic", "Trojan"),                               # Mirage != Mirai
])
def test_normalize_category(analyzer, label, expected):
    assert analyzer.normalize_category(label) == expected


def test_elect_best_respeita_hierarquia_e_ignora_genericos(analyzer):
    detections = {
        "Google": "Detected",
        "Kaspersky": "Trojan (0040f0c11)",          # genérico -> ignorado
        "ESET-NOD32": "Android/Spy.SpyNote.A",
        "Fortinet": "Android/SpyNote.A!tr",
    }
    assert analyzer.elect_best(detections) == ("ESET-NOD32", "Android/Spy.SpyNote.A")
