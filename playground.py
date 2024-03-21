from playwright.sync_api import sync_playwright
import pdfkit
import click
from bs4 import BeautifulSoup

# CATO_SELECTOR = "#b-product-page-content-boxes-1 > section > div.b-product-page-content-boxes__list.container > article"
EXECUTABLE_PATH="/opt/homebrew/bin/chromium"

### Some commands related to PDF converstion
# options = {
#     'page-size': 'Letter',
#     'margin-top': '0.75in',
#     'margin-right': '0.75in',
#     'margin-bottom': '0.75in',
#     'margin-left': '0.75in',
#     'encoding': "UTF-8",
#     'custom-header': [
#         ('Accept-Encoding', 'gzip')
#     ],
#     'cookie': [
#         ('cookie-empty-value', '""')
#         ('cookie-name1', 'cookie-value1'),
#         ('cookie-name2', 'cookie-value2'),
#     ],
#     'no-outline': None
# }

options = {
    'page-width': '2000px',
    'page-height': '2000px'
}

RAD_URL = "https://www.rad.com/products/radinsight-ti"
QWAK_URL = "https://www.qwak.com/post/utilizing-llms-with-embedding-stores"
CATO_URL = "https://www.catonetworks.com/use-cases/#mpls-migration-to-sd-wan"
CATO_BLOG = "https://www.catonetworks.com/blog/evasive-phishing-kits-exposed-cato-networks-in-depth-analysis-and-real-time-defense/"

DOCUMENT_MAPPING = {
    'rad': RAD_URL,
    'qwak': QWAK_URL,
    'cato': CATO_URL,
    'cato_blog': CATO_BLOG
}

SELECTOR = [
    '#b-product-page-content-boxes-1',
    '#vendor-consolidation'
    ]
USE_SELECTOR = False


def convert_url_to_pdf(url=RAD_URL, output='new-fuck.pdf', skip_browser=False, css=None, no_css=False):
    # import pudb; pudb.set_trace()
# Launch Playwright with Chromium
    if not skip_browser:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True, executable_path=EXECUTABLE_PATH)
            page = browser.new_page()

            page.goto(url)
            body_dimensions = page.evaluate("document.body.getBoundingClientRect()")
            height = body_dimensions['height']
            width = body_dimensions['width']

            print("Received body dimensions")
            print(body_dimensions)

            html = page.content()

            if USE_SELECTOR:
                html = soup_extractor(html, SELECTOR)


            #### Try without soup
            # if SELECTOR:
            #     print("Doing wait for selector")
            #     page.wait_for_selector(SELECTOR)

            # if not SELECTOR:
            #     print("Extracting HTML without selector")
            #     html = page.content()
            # else:
            #     print("Extracting HTML after selector")
            #     content = page.inner_html(SELECTOR)
            #     content = STYLE_CSS + content

            with open('page.html', 'w', encoding='utf-8') as file:
                file.write(html)

            browser.close()

        # print(html)

    options = {
        # 'page-width': f'{width}px',
        # 'page-width': '2000px',
        # 'page-height': f'{height}px',
        # 'no-header-line': None,
        # 'no-footer-line': None,
        # 'header-right': '',
        # 'footer-right': '',
        'enable-local-file-access': ""
        }
    
    print('Option passed to pdfkit')
    print(options)

    print('CSS provided to pdfkit')
    print(css)

    if no_css:
        print("Generating PDF without CSS modification")
        pdfkit.from_file('page.html', output, options=options, verbose=True)
    else:
        print(f"Generating PDF with CSS modification from {css}")
        pdfkit.from_file('page.html', output, options=options, css=css, verbose=True)


        

def soup_extractor(html, selectors):
    soup = BeautifulSoup(html, 'html.parser')
    style_tags = soup.find_all('style')


    soup_selectpr = ", ".join(selectors)
    print("Soup selectors")
    print(soup_selectpr)

    elements_to_include = soup.select(soup_selectpr)

    new_html = '<html><head>'
    for style_tag in style_tags:
        new_html += str(style_tag)
    new_html += '</head><body>'
    for element in elements_to_include:
        new_html += str(element)
    new_html += '</body></html>'

    return new_html



        # import IPython; IPython.embed() 

    

@click.command()
@click.argument('urls', type=str, nargs=-1, required=False)
@click.option('-c', '--company', type=click.STRING, required=False,
              help='Company to genereate PDF for')
@click.option('-o', '--output', type=click.STRING, required=False,
              help='Company to genereate PDF for', default='generated.pdf')
@click.option('-s', '--skip-browser', type=click.BOOL, is_flag=True, default=False,
              help='Skipping the browser')
@click.option('-d', '--debug', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
@click.option('--no-css', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
def click_cli_main(urls, company, output, skip_browser, debug, no_css):
    if debug:
        import pudb; pudb.set_trace()
    
    if urls:
        url = urls[0]
    elif company:
        url = DOCUMENT_MAPPING[company]
    else:
        raise Exception('Need to provide either a URL or a company name')
    
    if company:
        css = f"css/{company}.css"
    else:
        css = None

    convert_url_to_pdf(url, skip_browser=skip_browser, output=output, css=css, no_css=no_css)
    print(f"PDF generated at {output}")


if __name__ == "__main__":
    click_cli_main()
