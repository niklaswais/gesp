import pytest

from gesp.src.filenames import safe_filename, safe_filename_part


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('lg:koeln/az\\one|"two"?*', "lg-koeln-az-one-two"),
        ("  name.  ", "name"),
        ("a\x00b\x1fc", "a-b-c"),
        ("<>", "_"),
        ("CON", "_CON"),
    ],
)
def test_safe_filename_part_replaces_windows_unsafe_values(value, expected):
    assert safe_filename_part(value) == expected


def test_safe_filename_preserves_final_extension():
    assert safe_filename("ECLI:DE:LGK:2023:1222.3O135.21.00.txt") == "ECLI-DE-LGK-2023-1222.3O135.21.00.txt"


def test_safe_filename_treats_slashes_as_invalid_filename_chars():
    assert safe_filename("court_20200101_az_/raw/doc.html") == "court_20200101_az_-raw-doc.html"
