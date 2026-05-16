"""Integrity checks across config, spider registry, and jportal extractor mappings.

These would have caught issue #14's class of bug (an attribute the dispatch path
referenced but didn't actually exist).
"""

import importlib

import scrapy

from gesp.__main__ import STATE_SPIDERS
from gesp.src import config
from gesp.src.fingerprint import _JPORTAL_EXTRACTORS, _JPORTAL_INIT, _SIMPLE_EXTRACTORS

_ALL_STATES = ["bund", "bw", "by", "be", "bb", "hb", "hh", "he", "mv", "ni", "nw", "rp", "sh", "sl", "sn", "st", "th"]


def test_state_spiders_covers_all_states():
    assert set(STATE_SPIDERS.keys()) == set(_ALL_STATES)


def test_every_spider_is_a_scrapy_spider_subclass():
    for state, cls in STATE_SPIDERS.items():
        assert issubclass(cls, scrapy.Spider), f"{state}: {cls!r} is not a scrapy.Spider"


def test_every_spider_module_imports():
    for state in _ALL_STATES:
        importlib.import_module(f"gesp.spiders.{state}")


def test_states_constant_includes_every_known_state():
    for state in _ALL_STATES:
        assert state in config.STATES, f"{state} missing from config.STATES"


def test_jportal_init_has_required_config_entries():
    """Each jportal state must have matching headers/cookies/body in config."""
    for state in _JPORTAL_INIT:
        assert hasattr(config, f"{state}_headers"), f"config.{state}_headers missing"
        assert hasattr(config, f"{state}_cookies"), f"config.{state}_cookies missing"
        assert hasattr(config, f"{state}_body"), f"config.{state}_body missing"


def test_jportal_extractors_match_init_map():
    """Every state with a CSRF init endpoint must also have an extractor."""
    assert set(_JPORTAL_EXTRACTORS.keys()) == set(_JPORTAL_INIT.keys())


def test_extractor_state_sets_disjoint():
    """A state is either jportal-style or simple-HTML-style, never both."""
    assert not (set(_JPORTAL_EXTRACTORS) & set(_SIMPLE_EXTRACTORS))


def test_extractor_states_subset_of_state_spiders():
    """Any state in the fingerprint dispatch must have a registered spider."""
    # bund/by/hb/sn are dispatched directly (zip-xml or PDF), not via extractors.
    dispatch_states = set(_JPORTAL_EXTRACTORS) | set(_SIMPLE_EXTRACTORS) | {"bund", "by", "hb", "sn"}
    assert dispatch_states <= set(STATE_SPIDERS.keys())


def test_by_not_in_simple_extractors():
    """by's fingerprint link is a ZIP URL — the by() extractor would treat
    it as HTML and fail. Reconstruction must dispatch by directly to
    save_as_html, which knows how to unpack the zip."""
    assert "by" not in _SIMPLE_EXTRACTORS


def test_sh_uses_jportal_dispatch():
    """sh()'s signature is (item, headers, cookies) — it must be in the jportal
    map. Calling _SIMPLE_EXTRACTORS[state](item) on a jportal extractor raises
    TypeError at reconstruction time."""
    assert "sh" in _JPORTAL_EXTRACTORS
    assert "sh" not in _SIMPLE_EXTRACTORS


def test_jportal_body_carries_its_own_client_id():
    """Each *_body JSON must reference its own state's portal id, not a neighbour's.

    Several past bugs were copy-paste survivors (e.g. sh_body with bssl, rp/mv
    pagination bodies with bshe). The portal id convention is bs<state>, with
    Hamburg as the one historical exception (bsha, not bshh).
    """
    overrides = {"hh": "bsha"}
    for state in _JPORTAL_INIT:
        expected = overrides.get(state, f"bs{state}")
        body = getattr(config, f"{state}_body")
        assert f'"clientID":"{expected}"' in body, (
            f"{state}_body has wrong clientID — expected {expected!r}, body is {body!r}"
        )
