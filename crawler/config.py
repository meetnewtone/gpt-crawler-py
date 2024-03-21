from typing import List, Callable, Optional
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
    cookies: Optional[List[CookieData]] = None   # List of cookies to be added to this URL (browser keeps them available)

    def pretty_print(self, cout: Callable):
        cout(f"- {self.url} | {self.selector}")
        cout(f"    REF-MATCHER: {self.match}")
        cout(f"    MAX-REFERS : {self.max_n_ref}")
        if self.cookies:
            cout(f"    COOKIES [{len(self.cookies)}]: {self.cookies}")


@dataclass
class CrawlerConfig:
    sources: List[CrawlPoint]       # List of crawl points to probe
    source_split_size: int          # Maximum # of tokens to split each source into (0 = no split)
    max_results : int               # Maximum # of pages in total we can crawl (sources + references)
    output: str                     # Output file or directory name (for results json)
    output_dir: str                 # Output directory to handle all PDFs extracted
    on_visit_page: Callable = None  # Lambda function invoked every page we are visiting

    def pretty_print(self, cout: Callable):
        from pathlib import Path
        output_p = Path(self.output)
        assets_p = Path(self.output_dir)
        cout(f"--------------------------------------------------------------")
        cout(f"-                      Crawl Configuration                   -")
        cout(f"--------------------------------------------------------------")
        cout(f"Output    : {output_p.resolve()} {'[DIRECTORY, MultiOutput]' if output_p.is_dir() else '[JSON format]'}")
        cout(f"Asset-Dir : {assets_p.resolve()} [PDF output directory]")
        if self.max_results is not None:
            cout(f"Max-Pages : {self.max_results}")
        if self.source_split_size:
            cout(f"Split-Size: {self.source_split_size} [TOKENS]")
        cout(f"Crawl URIs:")
        for cp in self.sources:
            cp.pretty_print(cout)
        cout(f"--------------------------------------------------------------")