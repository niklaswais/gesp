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


def test_fingerprint_missing_path_exits(tmp_path):
    missing = tmp_path / "nope.xz"
    with pytest.raises(SystemExit):
        _parse_and_validate(["-fp", str(missing)])


def test_fingerprint_directory_path_exits(tmp_path):
    with pytest.raises(SystemExit):
        _parse_and_validate(["-fp", str(tmp_path)])


@pytest.mark.parametrize(
    "extra",
    [["-s", "bund"], ["-c", "bgh"], ["-d", "zivil"]],
)
def test_fingerprint_rejects_filter_flags(tmp_path, extra):
    fp = tmp_path / "fp.xz"
    fp.write_bytes(b"")  # exists, validation should still exit on the mutual-exclusion check
    with pytest.raises(SystemExit):
        _parse_and_validate(["-fp", str(fp), *extra])


def test_fingerprint_missing_path_no_makedirs(tmp_path, monkeypatch):
    """Bad -fp must exit before creating the -p folder."""
    import sys

    from gesp import __main__ as gmain

    target = tmp_path / "out"
    missing = tmp_path / "nope.xz"
    monkeypatch.setattr(sys, "argv", ["gesp", "-y", "-p", str(target), "-fp", str(missing)])
    with pytest.raises(SystemExit):
        gmain.main()
    assert not target.exists()


def test_fingerprint_corrupted_file_exits(tmp_path, monkeypatch):
    """A non-lzma .xz must exit non-zero with a readable error."""
    import sys

    from gesp import __main__ as gmain

    fp = tmp_path / "fp.xz"
    fp.write_bytes(b"not actually lzma compressed data")
    out_dir = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["gesp", "-y", "-p", str(out_dir), "-fp", str(fp)])
    with pytest.raises(SystemExit) as exc:
        gmain.main()
    assert exc.value.code == 1


def _build_fp(tmp_path, body_bytes):
    """Compress `body_bytes` with a flushed LZMA stream and return the file path."""
    import lzma

    c = lzma.LZMACompressor()
    out = c.compress(body_bytes) + c.flush()
    fp = tmp_path / "fp.xz"
    fp.write_bytes(out)
    return fp


def test_load_file_rejects_truncated_lzma(tmp_path):
    """A .xz without the LZMA end marker must raise even when earlier records decode."""
    import lzma

    from gesp.src.fingerprint import Fingerprint

    fp = _build_fp(tmp_path, b'{"a":1}|{"b":2}|')
    # Drop the end-of-stream marker without corrupting the readable prefix.
    fp.write_bytes(fp.read_bytes()[:-5])
    with pytest.raises(lzma.LZMAError):
        list(Fingerprint.load_file(str(fp)))


def test_load_file_rejects_unterminated_trailing_record(tmp_path):
    """An unflushed final record after the last '|' must raise, not silently drop."""
    from gesp.src.fingerprint import Fingerprint

    fp = _build_fp(tmp_path, b'{"a":1}|{"partial":')
    with pytest.raises(ValueError):
        list(Fingerprint.load_file(str(fp)))


def test_fingerprint_truncated_file_exits_via_main(tmp_path, monkeypatch):
    """End-to-end: -fp on a truncated fingerprint exits 1, no folder left dangling."""
    import sys

    from gesp import __main__ as gmain

    fp = _build_fp(tmp_path, b'{"version":"0","date":"0","args":{}}|{"s":"nw","c":"ag","d":"20200101","az":"1"}|')
    fp.write_bytes(fp.read_bytes()[:-5])  # truncate end marker
    out_dir = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["gesp", "-y", "-p", str(out_dir), "-fp", str(fp)])
    with pytest.raises(SystemExit) as exc:
        gmain.main()
    assert exc.value.code == 1
