# Spider parse fixtures

Each `<state>_search.{html,xml,json}` here is a snapshot of the response that the
corresponding spider's parse path reads in production. `tests/test_spider_parse.py`
loads these and asserts each spider still extracts well-formed items.

Three formats appear:

| Extension | States | Captured response |
| --- | --- | --- |
| `.xml` | `bund` | rechtsprechung-im-internet.de XML feed |
| `.html` | `bb`, `by`, `hb`, `ni`, `nw`, `sn` | search-results HTML page |
| `.json` | `be`, `bw`, `he`, `hh`, `mv`, `rp`, `sh`, `sl`, `st`, `th` | jportal `/search` response (after CSRF init) |

## Refreshing

```bash
python tests/refresh_fixtures.py            # all 17 states
python tests/refresh_fixtures.py be bw      # selected states
```

The script shells out to `gesp --probe-only`. The probe shapes live in
`gesp/probe.py` — that's where to add or adjust per-state request details.

After refreshing, `git diff tests/fixtures/` shows which portals changed their
output. If `pytest tests/test_spider_parse.py` then fails for state X, the
spider's XPath / extractor needs to be updated to match the new markup.

A weekly cron (`.github/workflows/refresh-fixtures.yml`) automates this and
opens a PR when fixtures change.

## Notes

- The `bund` feed returns the entire federal catalogue (~20 MB). `gesp/probe.py`
  trims it to the first 20 `<item>` blocks before saving.
- The probe automatically sends each spider's `config.<state>_headers` so it
  presents the same identity as the real scraper.
