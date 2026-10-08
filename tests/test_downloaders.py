"""Bugs 6, 7 e 10 — URLs, deduplicação e nome de pasta do downloader Android."""
import pytest

LISTING_RELATIVE = """
<a href="?C=N;O=D">Name</a> <a href="/">[To Parent Directory]</a>
<a href="Android_260603_01.zip.pgp">Android_260603_01.zip.pgp</a>
<a href="Android_260603_B_02.zip.pgp">Android_260603_B_02.zip.pgp</a>
<a href="Android_260603_metadata.zip.pgp">Android_260603_metadata.zip.pgp</a>
<a href="Android_260604_01.zip.pgp">outra data</a>
"""
LISTING_ABSOLUTE = LISTING_RELATIVE.replace('href="Android', 'href="/android/Android')


@pytest.mark.parametrize("raw", ["2026/06/03", "2026-06-03", "20260603", " 2026/06/03 "])
def test_parse_date_retorna_yyyymmdd_nos_dois_downloaders(android_dl, malware_dl, raw):
    assert android_dl.parse_date(raw) == "20260603"
    assert malware_dl.parse_date(raw) == "20260603"


@pytest.mark.parametrize("raw", ["2026/02/30", "260603", "abc"])
def test_parse_date_invalida(android_dl, raw):
    with pytest.raises(ValueError):
        android_dl.parse_date(raw)


def test_android_file_token(android_dl):
    assert android_dl.android_file_token("20260603") == "260603"


@pytest.mark.parametrize("listing", [LISTING_RELATIVE, LISTING_ABSOLUTE], ids=["href-relativo", "href-absoluto"])
def test_parse_links_mantem_segmento_android(android_dl, listing):
    urls = android_dl.parse_links(listing, android_dl.BASE_URL, "260603")
    assert len(urls) == 3
    assert all(u.startswith("https://premium2.virussign.com/android/Android_260603") for u in urls)


def test_download_for_date_pasta_e_urls_unicas(android_dl, monkeypatch, tmp_path):
    calls = {"listings": 0, "urls": None}

    def fake_listing(wget_bin, url, auth):
        calls["listings"] += 1
        # listagem com o metadata repetido, para provar a deduplicação
        return LISTING_RELATIVE + '<a href="Android_260603_metadata.zip.pgp">dup</a>'

    def fake_download(wget_bin, url_file, dest_dir, auth):
        calls["urls"] = url_file.read_text().split()
        calls["dest"] = dest_dir
        return 0

    monkeypatch.setattr(android_dl, "OUTPUT_ROOT", tmp_path)
    monkeypatch.setattr(android_dl, "check_wget", lambda: "wget")
    monkeypatch.setattr(android_dl, "load_credentials", lambda: ("u", "p"))
    monkeypatch.setattr(android_dl, "fetch_listing", fake_listing)
    monkeypatch.setattr(android_dl, "run_wget_download", fake_download)

    android_dl.download_for_date("2026/06/03")

    assert calls["dest"] == tmp_path / "20260603"          # bug 10
    assert calls["listings"] == 1                           # bug 7: sem segunda requisição
    assert len(calls["urls"]) == len(set(calls["urls"])) == 3  # bug 7: sem duplicatas
    assert sum("_metadata" in u for u in calls["urls"]) == 1
