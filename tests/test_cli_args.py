import pytest

from gesp.__main__ import build_parser


def test_docId_flag_sets_attr_true():
    args = build_parser().parse_args(["--docId"])
    assert args.docId is True


def test_docId_default_false():
    args = build_parser().parse_args([])
    assert args.docId is False


def test_fingerprint_flag_no_arg_is_true():
    args = build_parser().parse_args(["-fp"])
    assert args.fingerprint is True


def test_fingerprint_with_path_argument():
    args = build_parser().parse_args(["-fp", "/tmp/some/path.xz"])
    assert args.fingerprint == "/tmp/some/path.xz"


def test_fingerprint_absent_is_none():
    args = build_parser().parse_args([])
    assert args.fingerprint is None


def test_states_and_courts_lowercased():
    args = build_parser().parse_args(["-s", "BUND,BY", "-c", "BGH"])
    assert args.states == "bund,by"
    assert args.courts == "bgh"


def test_yes_flag_default_false():
    args = build_parser().parse_args([])
    assert args.yes is False


def test_yes_flag_set():
    args = build_parser().parse_args(["-y"])
    assert args.yes is True


def test_wait_default_is_zero():
    args = build_parser().parse_args([])
    assert args.wait == 0.0


def test_wait_bare_uses_juris_safe_default():
    args = build_parser().parse_args(["-w"])
    assert args.wait == 1.75


def test_wait_accepts_explicit_seconds():
    args = build_parser().parse_args(["-w", "3.5"])
    assert args.wait == 3.5


def test_wait_accepts_explicit_zero():
    args = build_parser().parse_args(["-w", "0"])
    assert args.wait == 0.0


@pytest.mark.parametrize("bad", ["-1", "-0.5", "nan", "inf", "-inf"])
def test_wait_rejects_invalid_values(bad):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["-w", bad])
