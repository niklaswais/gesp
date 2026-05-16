from datetime import datetime

from gesp.src.filenames import safe_filename
from gesp.src.htmlparser import DecisionHTMLParser, _format_ddmm_unpadded_year


def _parser_for_ecli(tmp_path, ecli="ECLI:DE:LGK:2023:1222.3O135.21.00"):
    parser = DecisionHTMLParser()
    parser.output_path = str(tmp_path)
    parser.gerichts_code_land = {"LGK": "nw"}
    parser.ecli = ecli
    parser.text = "body"
    return parser


def test_format_ddmm_unpadded_year_is_portable_replacement_for_dash_y():
    assert _format_ddmm_unpadded_year(datetime(2005, 1, 2)) == "02015"
    assert _format_ddmm_unpadded_year(datetime(2026, 5, 16)) == "160526"


def test_postprocess_writes_windows_safe_ecli_filename(tmp_path):
    ecli = "ECLI:DE:LGK:2023:1222.3O135.21.00"
    parser = _parser_for_ecli(tmp_path, ecli)

    parser.save_to_file()

    file_path = tmp_path / "nw" / "LGK" / safe_filename(ecli + ".txt")
    assert file_path.exists()
    assert f"ECLI: {ecli}" in file_path.read_text(encoding="utf-8")


def test_postprocess_duplicate_check_uses_windows_safe_ecli_filename(tmp_path):
    ecli = "ECLI:DE:LGK:2023:1222.3O135.21.00"
    file_dir = tmp_path / "nw" / "LGK"
    file_dir.mkdir(parents=True)
    (file_dir / safe_filename(ecli + ".txt")).write_text("", encoding="utf-8")
    parser = _parser_for_ecli(tmp_path, ecli)

    assert parser.teste_ecli_datei() is True
