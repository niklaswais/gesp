import pytest

from gesp.__main__ import _validate, build_parser


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


def _parse_and_validate(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    return _validate(parser, args)


def test_validate_accepts_known_states_courts_domains():
    courts, states, domains = _parse_and_validate(["-s", "bund,by", "-c", "bgh", "-d", "zivil"])
    assert states == ["bund", "by"]
    assert courts == ["bgh"]
    assert domains == ["zivil"]


def test_validate_returns_empty_lists_when_flags_omitted():
    courts, states, domains = _parse_and_validate([])
    assert (courts, states, domains) == ([], [], [])


@pytest.mark.parametrize("argv", [["-s", "xx"], ["-s", "bund,xx"], ["-s", "XX"]])
def test_unknown_state_exits(argv):
    with pytest.raises(SystemExit):
        _parse_and_validate(argv)


@pytest.mark.parametrize("argv", [["-c", "notacourt"], ["-c", "bgh,wat"]])
def test_unknown_court_exits(argv):
    with pytest.raises(SystemExit):
        _parse_and_validate(argv)


def test_unknown_domain_exits():
    with pytest.raises(SystemExit):
        _parse_and_validate(["-d", "garbage"])


@pytest.mark.parametrize("argv", [["-s", "bund,"], ["-s", ",bund"], ["-s", "bund,,by"], ["-c", " "]])
def test_empty_token_rejected(argv):
    with pytest.raises(SystemExit):
        _parse_and_validate(argv)


def test_alias_substitution_with_warning(capsys):
    courts, _, _ = _parse_and_validate(["-c", "larbg,vgh"])
    assert courts == ["lag", "ovg"]
    out = capsys.readouterr().out
    assert "larbg" in out and "lag" in out
    assert "vgh" in out and "ovg" in out


def test_validate_runs_before_makedirs(tmp_path, monkeypatch):
    """Invalid -s with -p NEWDIR must not create NEWDIR."""
    import sys

    from gesp import __main__ as gmain

    target = tmp_path / "should_not_exist"
    monkeypatch.setattr(sys, "argv", ["gesp", "-y", "-p", str(target), "-s", "xx"])
    with pytest.raises(SystemExit):
        gmain.main()
    assert not target.exists()
