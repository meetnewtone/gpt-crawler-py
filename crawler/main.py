import json
import click
import asyncio
import fnmatch
from itertools import islice

from config import *

# Brower used
from playwright.async_api import async_playwright


# Function to get page HTML
async def get_page_html(page, selector):
    await page.wait_for_selector(selector)
    element = await page.query_selector(selector)
    return await element.inner_text() if element else ""

class log_ongoing():
    def __init__(self, msg, ident=2):
        self.message = msg
        self.ident = ident

    def __enter__(self):
        print(" " * self.ident + f"  - {self.message}", end='', flush=True)

    def __exit__(*args, **kwargs):
        print(" [DONE]")

# Crawl function
async def crawl(config: CrawlerConfig):
    json_seperator = None
    queue = config.sources
    n_results_left = config.max_results \
        if config.max_results is not None else -1

    # Empty file before starting, json starts as ARRAY
    with open(config.output, 'w+') as f:
        json_seperator = "["

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            while queue and n_results_left != 0:
                current_src = queue.pop(0)
                print(f"Crawler: Crawling {current_src.url}")
                # Add cookies to context if needed
                if current_src.cookies:
                    with log_ongoing('Adding cookies'):
                        await page.context.add_cookies([
                            {
                                'name': cookie.name,
                                'value': cookie.value,
                                'url': current_src.url
                            } for cookie in current_src.cookies
                        ])

                # TODO: Add support for multi-type of pages, bellow is only HTML format (a, href, selector)

                with log_ongoing('Fetching HTML'):
                    await page.goto(current_src.url)
                    html = await get_page_html(page, current_src.selector)

                # TODO: Send HTML to some LLM to extract relevant content

                # Append data to output in minimal format (no spaces, lines)
                #   First iteration - [{"ref":"<url>","data":"<html>"}
                #   Later iteration - ,{"ref":"<url>","data":"<html>"}
                with open(config.output, 'a') as f:
                    f.write(json_seperator) 
                    json.dump(
                        { 'ref': current_src.url, 'data': html },
                        f, separators=(',', ':')
                    )
                json_seperator = ","
                n_results_left -= 1

                # Extract and enqueue links (<a href="{url}">) after fnmatch-ing
                links = await page.query_selector_all("a")
                for link in islice(links, current_src.max_n_ref):
                    href = await link.get_attribute("href")
                    if href and fnmatch.fnmatch(href, config.match):
                        queue.append(href)

                # Implement on_visit_page logic if needed

            # Done with loop - close JSON-ARRAY properly (only if results exist)
            if n_results_left != config.max_results:
                with open(config.output, 'a') as f:
                    f.write(']')
        finally:
            await browser.close()


########################################
#          CONFIG STRUCTURE            #
########################################
# ARRAY of the following DICT:
#   url: str { location to crawl }
#   match: str { fnmatch pattern for references }
#   selector: str { Filter for HTML document }
#   max_references: int { Maximum references we should follow }
#   cookies: ARRAY of the following DICT:
#       name: str { name of the cookie }
#       value: str { value related to cookie }
#
# EXAMPLE:
#   [
#       {
#           'url': 'https://www.laplace-ai.com/vision',
#           'match': 'https://www.laplace-ai.com/intro/vision/**',
#           'selector': '#SITE_PAGES',
#           'max_references': 100,
#           'cookies': [
#               {
#                   'name': 'test',
#                   'value': 'AXSCDFDSFDSDSSDSEE'
#               }
#           ]
#       }
#   ]
#
########################################

@click.command()
@click.option('-c', '--config-file', required=False, type=click.File('r'), help='File containing configuration for the crawl')
@click.option('-n', '--max-results', default=100, type=click.INT, help='Maximum # of pages in total we can crawl (URLs + references)')
@click.option('-o', '--output', type=click.Path(dir_okay=False), default='output.json', help='Output file name (for results json)')
@click.argument('urls', type=str, nargs=-1, required=False)
@click.option('-m', '--match', default='*', type=str, help='GLOBAL Pattern match for referenced URLs in FNMATCH format')
@click.option('-s', '--selector', default='.', type=str, help='GLOBAL Filter for HTML document (like which DIV to take)')
@click.option('-r', '--max-references', default=5, type=click.INT, help='GLOBAL Maximum # of references to follow per page (when recursing)')
def click_cli_main(match, selector, max_results, max_references, output, config_file, urls):
    # Check invalid usage
    if not config_file and not urls:
        raise click.ClickException('Must either specify --config-file or arguments for URLs')

    # Start with config from arguments of the CLI
    config = CrawlerConfig(
        sources=[(
            CrawlPoint(
                url=url,
                match=match,
                selector=selector,
                max_n_ref=max_references
            )
        ) for url in urls],
        max_results=max_results,
        output=output
    )

    if config_file:
        # Avoid cases where URLs and Config can collide
        if urls:
            raise click.ClickException(
                'Config-File and URLs are mutually exclusive, pass just one option'
            )
        # Read config data from file
        config_data = json.load(config_file)
        config.sources = [(
            CrawlPoint(
                url=cfg['url'],
                match=cfg.get('match', match),
                selector=cfg.get('selector', selector),
                max_n_ref=cfg.get('max_references', max_references),
                cookies=[(
                    CookieData(**cookie.values())
                ) for cookie in cfg.get('cookies', [])]
            )
        ) for cfg in config_data]

    asyncio.run(crawl(config))

# Running the main function
if __name__ == "__main__":
    click_cli_main()