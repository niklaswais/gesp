from gesp.src.create_file import save_as_html, save_as_pdf


def test_save_as_html_none_item_returns_none(tmp_path):
    assert save_as_html(None, "nw", str(tmp_path), False) is None
    assert list(tmp_path.iterdir()) == []


def test_save_as_pdf_none_item_returns_none(tmp_path):
    assert save_as_pdf(None, "hb", str(tmp_path)) is None
    assert list(tmp_path.iterdir()) == []


def test_save_as_html_missing_link_no_crash(tmp_path):
    """An item with metadata but no 'link' or 'text' should log + return without raising."""
    item = {"court": "lg-koeln", "date": "20090813", "az": "37-O-143-09"}
    # No link, no text — falls to the else branch that used to KeyError on item["link"].
    save_as_html(item, "nw", str(tmp_path), False)


def test_save_as_pdf_missing_link_no_crash(tmp_path):
    item = {"court": "ovg", "date": "20200101", "az": "1-A-1-20"}
    # No link, no body — falls to the else branch that used to KeyError on item["link"].
    save_as_pdf(item, "hb", str(tmp_path))
