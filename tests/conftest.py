import warnings

from scrapy.exceptions import ScrapyDeprecationWarning


def pytest_configure(config):
    # Treat Scrapy's deprecation warnings as errors during tests. The pipeline
    # `spider`-arg deprecation in particular fires once per process at import
    # time; promoting it to an error stops regressions silently slipping in.
    warnings.filterwarnings("error", category=ScrapyDeprecationWarning)
