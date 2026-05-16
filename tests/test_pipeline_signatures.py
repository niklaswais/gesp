"""Mirror of Scrapy's `_check_mw_method_spider_arg`: any pipeline hook whose
`spider` parameter is required triggers a ScrapyDeprecationWarning and will
break entirely when Scrapy drops the compatibility shim.
"""

import inspect

import pytest

from gesp.pipelines.exporters import (
    ExportAsHtmlPipeline,
    ExportAsPdfPipeline,
    ExportPipeline,
    FingerprintExportPipeline,
    RawExporter,
)
from gesp.pipelines.formatters import AZsPipeline, CourtsPipeline, DatesPipeline
from gesp.pipelines.texts import TextsPipeline

_PIPELINES = [
    AZsPipeline,
    DatesPipeline,
    CourtsPipeline,
    TextsPipeline,
    ExportPipeline,
    ExportAsHtmlPipeline,
    ExportAsPdfPipeline,
    FingerprintExportPipeline,
    RawExporter,
]

_HOOKS = ("open_spider", "close_spider", "process_item")


def _hooks_with_required_spider(cls):
    out = []
    for name in _HOOKS:
        if name not in cls.__dict__:
            continue
        sig = inspect.signature(getattr(cls, name))
        p = sig.parameters.get("spider")
        if p is not None and p.default is inspect.Parameter.empty:
            out.append(name)
    return out


@pytest.mark.parametrize("cls", _PIPELINES)
def test_no_pipeline_hook_requires_spider(cls):
    bad = _hooks_with_required_spider(cls)
    assert not bad, (
        f"{cls.__name__} hooks require `spider`: {bad}. "
        "Make it optional (spider=None) and use self.crawler.spider via from_crawler()."
    )
