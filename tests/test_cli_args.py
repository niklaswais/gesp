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
