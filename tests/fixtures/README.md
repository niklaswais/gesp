# Spider parse fixtures

Snapshots of the responses each spider's parse path reads in production.
`tests/test_spider_parse.py` loads these and asserts each spider still extracts
well-formed items.

Two kinds:

* `<state>_search.{html,xml,json}` — the discovery / results-list response
  (every state). Auto-refreshed weekly; see [Refreshing](#refreshing).
* `<state>_detail.html` — one decision's detail page (only `bb`, `ni`, whose
  `parse()` makes a synchronous `requests.get()` per result row).
  Refreshed manually; see [Detail-page fixtures](#detail-page-fixtures-bb_detailhtml-ni_detailhtml).

Search fixtures come in three formats:

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

## Detail-page fixtures (`bb_detail.html`, `ni_detail.html`)

`bb` and `ni` make a synchronous `requests.get()` per result row inside
`parse()` to pull metadata off the decision's detail page. The drift test
stubs that call with one of these captured detail pages so CI stays offline.

Unlike the `_search.*` fixtures, these are **not** auto-refreshed by the
weekly cron — the detail URL depends on which decision is picked, and a
specific decision can disappear from the portal. Refresh them by hand if a
detail-page XPath starts failing:

```bash
# Pick any href from the corresponding _search fixture, then:
curl -sS -A "Mozilla/5.0" "https://gerichtsentscheidungen.brandenburg.de/gerichtsentscheidung/27692" -o bb_detail.html
curl -sS -A "Mozilla/5.0" "https://voris.wolterskluwer-online.de/browse/document/<uuid>" -o ni_detail.html
```

Missing detail fixtures cause the corresponding state's drift test to skip,
not fail.
