from playwright.sync_api import sync_playwright
import pdfkit
import click
from bs4 import BeautifulSoup
import json
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
import os
import nest_asyncio
nest_asyncio.apply()

# CATO_SELECTOR = "#b-product-page-content-boxes-1 > section > div.b-product-page-content-boxes__list.container > article"
EXECUTABLE_PATH="/opt/homebrew/bin/chromium"
LLAMA_INDEX_API_KEY = "llx-LfEhUzGZDtDfnWnZMibUyUq69CRf6XURjre6ARUDBh32FTm8"


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

COMPANY = {
    'rad': {
        'default_css': 'rad.css',
        'default_url': RAD_URL
    },
    'qwak': {
        'default_css': 'qwak.css',
        'default_url': QWAK_URL
    },
    'cato': {
        'default_css': 'cato_blog.css',
        'default_url': CATO_BLOG
    },
}

SELECTOR = [
    '#b-product-page-content-boxes-1',
    '#vendor-consolidation'
    ]
USE_SELECTOR = False


def convert_url_to_pdf(url, 
                       output='new-fuck.pdf', 
                       output_dir=None, 
                       skip_browser=False, 
                       css=None, 
                       no_css=False,
                       playwright=False):
    # import pudb; pudb.set_trace()
# Launch Playwright with Chromium
    # if not skip_browser:

    if not skip_browser:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True, executable_path=EXECUTABLE_PATH)
            page = browser.new_page()

            # for url in urls:
            print(f"Goint to {url}")
            page.goto(url)
            body_dimensions = page.evaluate("document.body.getBoundingClientRect()")
            height = body_dimensions['height']
            width = body_dimensions['width']

            print("Received body dimensions")
            print(body_dimensions)

            html = page.content()
            if playwright:
                page.pdf(path="playwright-pdf.pdf")

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

    file_name = output
    if not file_name:
        file_name = url.split('/')[-1] + ".pdf"

    if output_dir:
        file_name = f"{output_dir}/{file_name}"

    try:
        if no_css:
            print("Generating PDF without CSS modification")
            pdfkit.from_file('page.html', file_name, options=options, verbose=True)
        else:
            print(f"Generating PDF with CSS modification from {css}")
            pdfkit.from_file('page.html', file_name, options=options, css=css, verbose=True)
    except OSError as e:
        print(f"Error while generating PDF: {e}, we will continue! Good luck!")


        
# This function is mainly used for extracting the HTML content from the page,
# that's not the recommendation, it's better to remove parts...
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


def prase_pdf_with_llama_index(pdf_path):
    parser = LlamaParse(
        api_key=LLAMA_INDEX_API_KEY,  # can also be set in your env as LLAMA_CLOUD_API_KEY
        result_type="markdown",  # "markdown" and "text" are available
        num_workers=4, # if multiple files passed, split in `num_workers` API calls
        verbose=True,
        language="en" # Optionaly you can define a language, default=en
    )

    if not(os.path.isdir(pdf_path)):
        documents = parser.load_data(pdf_path)

    else:
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(pdf_path, file_extractor=file_extractor).load_data()


    import pudb; pudb.set_trace()

    

    
    # for d in documents:
    #     file_name = d.metadata['file_name']
    #     with open(f"{company}/{file_name}.md", 'w') as file:
    #             file.write(d.to_json())


def prepare_folder_for_summarization(path):
    summary_dict = {}

    for file in os.listdir(path):
        if file.endswith(".md"): # This is a file from llama parse, in json
            with open(os.path.join(path, file), 'r') as f:
                content = json.load(f)
                summary_dict[file] = content["text"]

        if file.endswith(".json"): # This is what we got from the crawler
            with open(os.path.join(path, file), 'r') as f:
                content = json.load(f)
            for document in content:
                summary_dict[document['title']] = document['html']

    with open(os.path.join(path, "summary.json"), 'w') as f:
        json.dump(summary_dict, f, indent=4)


def write_to_chroma(path):
    pass
    



def parse_js_crwaler_json(document):
    with open(document, 'r') as file:
        document_list = json.load(file)

    url_list = [d['url'] for d in document_list]
    return url_list



def convert_with_pdfratpr():
    import requests
    from requests.auth import HTTPBasicAuth

    # Your DocRaptor API key
    api_key = '8pW2GxYpK3_rzeIxIW-B'

    # The URL of the DocRaptor API endpoint
    url = 'https://api.docraptor.com/docs'

    # Your HTML content or the URL of the web page you want to convert to PDF
    html_content = '<html><body>Hello World!</body></html>'
    # For URL, you would use "document_url": "http://example.com"

    # Prepare the JSON payload for the API request
    data = {
        "type": "pdf",
        "test": True,
        "document_url": "https://www.qwak.com/platform/model-registry",
        "prince_options": {
            "media": "print"  # Use "print" for print-optimized PDFs
        }
    }

    # data = {
    #     "type": "pdf",
    #     "test": True,  # Set to True for test documents; they will be watermarked
    #     "document_url": "https://www.qwak.com/platform/model-registry",
    #     "prince_options": {
    #         "media": "screen",
    #         # "page_size": "Letter",
    #         # "landscape": True,
    #         # "margins": {
    #         #     "top": "10mm",
    #         #     "bottom": "10mm",
    #         #     "left": "10mm",
    #         #     "right": "10mm"
    #         # }
    #     }
    # }

    # Headers for the API request
    headers = {
        'Content-Type': 'application/json'
    }

    # Send the request to DocRaptor
    response = requests.post(url, json=data, headers=headers, auth=HTTPBasicAuth(api_key, ''))

    # Check for successful response
    if response.status_code == 200:
        # Write the PDF to a file
        with open('output3.pdf', 'wb') as f:
            f.write(response.content)
        print('PDF generated successfully.')
    else:
        # Output error message
        print(f'Error generating PDF: {response.text}')


  
# 
@click.command()
@click.argument('urls', type=str, nargs=-1, required=False)
@click.option('-c', '--company', type=click.STRING, required=False,
              help='Company to genereate PDF for')
@click.option('-o', '--output', type=click.STRING, required=False,
              help='Company to genereate PDF for')
@click.option('-s', '--skip-browser', type=click.BOOL, is_flag=True, default=False,
              help='Skipping the browser')
@click.option('-d', '--debug', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
@click.option('--no-css', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
@click.option('--playwright', type=click.BOOL, is_flag=True, default=False,
              help='Generate PDF with Playwright')
@click.option('-l', '--llama-parse', type=click.STRING, required=False,
              help='Generating PDF with llama parse, just a checking')
@click.option('-s', '--summarize', type=click.STRING, required=False,
              help='Generating PDF with llama parse, just a checking')
def click_cli_main(urls, company, output, skip_browser, debug, no_css, playwright, llama_parse, summarize):
    if debug:
        import pudb; pudb.set_trace()

    if summarize:
        prepare_folder_for_summarization(summarize)
        return

    if llama_parse:
        prase_pdf_with_llama_index(llama_parse)
        return

    if company:
        company_dict = COMPANY[company]
        company_css = company_dict['default_css']
        css = f'css/{company_css}'
        # This url is mainly for tries while working, and should
        url_list = [company_dict['default_url'] ]
        # output = f"{company}/{output}.pdf"
    
    if urls:
        url_list = urls


    if not(url_list[0].startswith("http")):
        # It's a local file
        url_list = parse_js_crwaler_json(url_list[0])
        
    

    for url in url_list:
        convert_url_to_pdf(url, 
                            skip_browser=skip_browser, 
                            output_dir=company, 
                            output=output, 
                            css=css,
                            no_css=no_css,
                            playwright=playwright)
    # print(f"PDF generated at {output}")



if __name__ == "__main__":
    # convert_with_pdfratpr()
    click_cli_main()
