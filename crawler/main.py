import json
import click
import asyncio
import fnmatch
from pathlib import Path
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
    n_results_left = config.max_results \
        if config.max_results is not None else -1
    queue = config.sources[:n_results_left]
    n_results_left -= len(queue)
    outpath = Path(config.output)

    # Empty file before starting, json starts as ARRAY
    if not outpath.is_dir():
        with outpath.open('w+') as f:
            json_seperator = "["

    already_crawled = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            while queue:
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
                already_crawled.add(current_src.url)

                chunks = [html]
                filename_format = "{basename}"
                if (config.source_split_size > 0):
                    import tiktoken
                    with log_ongoing('Splitting HTML to chunks', ident=4):
                        limit = config.source_split_size
                        tk_enc = tiktoken.get_encoding('cl100k_base')
                        tokens = tk_enc.encode(html)
                        chunks = [tokens[i : i + limit] for i in range(0, len(tokens), limit)]
                        chunks = [tk_enc.decode(chunk) for chunk in chunks]
                    # Allow partial names suffix: @<id>
                    if len(chunks) > 1:
                        filename_format = "{basename}@{chunkid}"

                # Save PDF under page-name
                #   example: https://a.com/omer.html?params.moshe -> 'omer.pdf'
                nampos = -2 if current_src.url.endswith('/') else -1
                basename = current_src.url.split('/')[nampos].split('.')[0]
                pdf_path = Path(config.output_dir) / f'{basename}.pdf'
                with log_ongoing(f'Saving PDF @ {pdf_path}'):
                    await page.pdf(path=pdf_path)

                for chunkid, chunk in enumerate(chunks):
                    # Default values -> single output file, adapt to chunk format
                    namebase = filename_format.format_map(
                        {"basename": basename, "chunkid": chunkid}
                    )
                    outfile = outpath
                    outfile_flags = 'a'
                    srcfile = namebase + '.pdf'

                    # Directory, split outputs
                    if outpath.is_dir():
                        outfile = outpath / f'{namebase}.json'
                        srcfile = f'{basename}.pdf'
                        outfile_flags = 'w+'
                        json_seperator = ''

                    # Append data to output in minimal format (no spaces, lines)
                    #   First iteration - [{"file":"<file>","data":"<html>"}
                    #   Later iteration - ,{"file":"<file>","data":"<html>"}
                    # in-case we deal with 'directory', no seperator is applied
                    chunk_data = { 'file': srcfile, 'data': chunk }
                    with outfile.open(outfile_flags) as cfile:
                        cfile.write(json_seperator)
                        json.dump(chunk_data, cfile, separators=(',', ':'))
                    json_seperator = ","

                # Extract and enqueue links (<a href="{url}">) after fnmatch-ing
                links = await page.query_selector_all("a")
                for link in islice(links, current_src.max_n_ref):
                    if n_results_left == 0:
                        break
                    href = await link.get_attribute("href")
                    if href and href not in already_crawled and fnmatch.fnmatch(href, current_src.match):
                        queue.append(
                            CrawlPoint(
                                url=href,
                                match=current_src.match,
                                selector=current_src.selector,
                                max_n_ref=current_src.max_n_ref,
                                cookies=current_src.cookies
                            )
                        )
                        already_crawled.add(href)
                        n_results_left -= 1

                # Implement on_visit_page logic if needed

            # Done with loop - close JSON-ARRAY properly (only if results exist)
            if n_results_left != config.max_results and not outpath.is_dir():
                with outpath.open('a') as f:
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
@click.option('-n', '--max-results', required=False, type=click.INT, help='Maximum # of pages in total we can crawl (URLs + references)')
@click.option('-o', '--output', type=click.Path(), default='output.json', help='Output file name or directory for multiple (for results json)')
@click.option('-d', '--out-dir', type=click.Path(dir_okay=True, file_okay=False), default='.', help='Directory path to output PDF files crawled')
@click.option('-S', '--split-size', type=click.INT, default=0, help='Size of text-chunks to be extracted per crawled page, 0 = no split')
@click.argument('urls', type=str, nargs=-1, required=False)
@click.option('-m', '--match', default='*', type=str, help='GLOBAL Pattern match for referenced URLs in FNMATCH format')
@click.option('-s', '--selector', default='.', type=str, help='GLOBAL Filter for HTML document (like which DIV to take)')
@click.option('-r', '--max-references', default=5, type=click.INT, help='GLOBAL Maximum # of references to follow per page (when recursing)')
def click_cli_main(config_file, max_results, output, out_dir, split_size, urls, match, selector, max_references):
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
        source_split_size=split_size,
        max_results=max_results,
        output=output,
        output_dir=out_dir
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

    # Create output directory if needed
    if len(config.sources) > 0:
        Path(out_dir).mkdir(exist_ok=True)

    config.pretty_print(click.echo)
    asyncio.run(crawl(config))

# Running the main function
if __name__ == "__main__":
    click_cli_main()
