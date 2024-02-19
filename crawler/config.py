from typing import List, Callable
from dataclasses import dataclass

@dataclass
class CookieData:
    name: str
    value: str

@dataclass
class CrawlPoint:
    url: str                    # The URL to start current crawl cycle
    match: str                  # Pattern matching for referenced URLs
    selector: str               # Selector inside the URL page (filter for HTML, like DIV)
    max_n_ref: int              # Max references allowed for this crawl point (references inherit this)
    cookies: List[CookieData]   # List of cookies to be added to this URL (browser keeps them available)


@dataclass
class CrawlerConfig:
    sources: List[CrawlPoint]       # List of crawl points to probe
    max_results : int               # Maximum # of pages in total we can crawl (sources + references)
    output: str = 'output.json'     # Output file name (for results json)
    on_visit_page: Callable = None  # Lambda function invoked every page we are visiting