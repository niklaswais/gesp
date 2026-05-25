"""Shared helpers for tests that need to drive async-converted spider callbacks.

The threading patch made bb.parse, ni.parse, and sn.parse_results_ovg async
generators that await deferToThread + deferred_to_future. Unit tests run
outside the reactor, so these helpers (a) replace those primitives with
synchronous stand-ins and (b) drain async generators via asyncio.run.
"""

from twisted.internet.defer import succeed

# Spiders whose modules import deferToThread / deferred_to_future and therefore
# have async machinery that unit tests must replace with synchronous stand-ins.
# Distinct from "spiders whose top-level parse() is async" — sn.parse stays
# sync, but sn.parse_results_ovg becomes async. The set covers both.
ASYNC_STUB_STATES = {"bb", "ni", "sn"}


def stub_async_machinery(state, monkeypatch):
    if state not in ASYNC_STUB_STATES:
        return

    def fake_defer(fn, *args, **kwargs):
        return succeed(fn(*args, **kwargs))

    async def fake_future(d):
        out = {}
        d.addBoth(lambda r: out.setdefault("v", r))
        return out["v"]

    monkeypatch.setattr(f"gesp.spiders.{state}.deferToThread", fake_defer)
    monkeypatch.setattr(f"gesp.spiders.{state}.deferred_to_future", fake_future)


async def adrain(agen):
    out = []
    async for x in agen:
        out.append(x)
    return out
