from playwright.sync_api import sync_playwright
import pdfkit
import click
from bs4 import BeautifulSoup
import json
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
import os
import yaml
import convertapi
import nest_asyncio
nest_asyncio.apply()

# CATO_SELECTOR = "#b-product-page-content-boxes-1 > section > div.b-product-page-content-boxes__list.container > article"
EXECUTABLE_PATH="/opt/homebrew/bin/chromium"
# LLAMA_INDEX_API_KEY = "llx-LfEhUzGZDtDfnWnZMibUyUq69CRf6XURjre6ARUDBh32FTm8"
LLAMA_INDEX_API_KEY = "llx-4VoAUrUHCRA5o7NEdosEe6lAdHep1Xf7rKIug125lYtsDISn"
CONVERT_API_KEY = "yfC2O2Fbw1s1aRND" # Zubilevi

# BROWSER = sync_playwright().start().chromium.launch(headless=True, executable_path=EXECUTABLE_PATH)


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
        'default_css': 'cato.css',
        'default_url': CATO_BLOG
    },
}

SELECTOR = [
    '#b-product-page-content-boxes-1',
    '#vendor-consolidation'
    ]
USE_SELECTOR = False


def convert_url_to_pdf(url, 
                       output, 
                       output_dir=None, 
                       skip_browser=False, 
                       css=None, 
                       no_css=False,
                       playwright=False,
                       only_html=False,
                       api_pdf=False,
                       respect_viewport=True,
                       everything=False,
                       browser=None):
    # import pudb; pudb.set_trace()
# Launch Playwright with Chromium
    # if not skip_browser:
    css_content = None
    if css:
        with open(css, 'r') as file:
            css_content = file.read()
            css_content = css_content.replace("\n", "")

    if not skip_browser and not api_pdf:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True, executable_path=EXECUTABLE_PATH)
            page = browser.new_page()

            # for url in urls:
            print(f"Going to {url}")
            try:
                page.goto(url)
            except:
                print(f"Error: Target closed while navigating to {url}")
            body_dimensions = page.evaluate("document.body.getBoundingClientRect()")
            height = body_dimensions['height']
            width = body_dimensions['width']

            if css and not(no_css):
                print("Applying CSS file to html!")

                page.add_style_tag(content=css_content)

            # Wait for the page to load and CSS to take effect
            # page.wait_for_timeout(1000)

            html = page.content()
            if playwright:
                page.pdf(path="playwright-pdf.pdf")

            if USE_SELECTOR:
                html = soup_extractor(html, SELECTOR)

            with open('page.html', 'w', encoding='utf-8') as file:
                file.write(html)

            browser.close()
            # import time; time.sleep(1)    

            if only_html:
                print("Returning due to only html")
                return
            
    file_name = output
    if not file_name:
        if url.endswith("/"):
            file_name = url.split('/')[-2] + ".pdf"
        else:
            file_name = url.split('/')[-1] + ".pdf"

    if output_dir:
        file_name = f"{output_dir}/{file_name}"
        # print(html)
    if api_pdf:
        print("Generating PDF with API")
        print(f"Output file: {file_name}")

        respect_viewport_str = 'true' if respect_viewport else 'false'

        respect_viewport = 'true'

        convertapi.api_secret = CONVERT_API_KEY
        
        convertapi.convert('pdf', {                                                                                                
            'Url': url,                                                                                                            
            'CookieConsentBlock': 'true',                                                                                          
            'UserCss': css_content,                                                                                                   
            'LoadLazyContent': 'true',                                                                                             
            'MarginLeft': '0',                                                                                                     
            'MarginRight': '0'                                                                                                     
        }, from_format = 'web').save_files(file_name)

        return

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

    if not everything:
        try:
            # if no_css:
            print("Generating PDF...")
            print(f"Output file: {file_name}")
            # This is wkhtmltopdf
            pdfkit.from_file('page.html', file_name, options=options, verbose=True)
            # else:
            #     print(f"Generating PDF with CSS modification from {css}")
            #     print(f"Output file: {file_name}")
            #     pdfkit.from_file('page.html', file_name, options=options, css=css, verbose=True)
        except OSError as e:
            print(f"Error while generating PDF: {e}, we will continue! Good luck!")

        return
    
    print("Trying all the methods for converting PDF")
    print("Will be found in trials")
    print("Weasyprint")
    from weasyprint import HTML
    HTML(string=html).write_pdf("trials/weasy.pdf")

    print("XHTMLTOPDF")
    from xhtml2pdf import pisa
    try:
        with open('trials/xhtmltopdf.pdf', 'w+b') as pdf:
            pisa.CreatePDF(html, dest=pdf)
    except:
        print("Problem in XHTMLTOPDF!")

    print("WKHTMLTOPDF")
    pdfkit.from_file('page.html', 'trials/wkhtmltopdf.pdf', options=options, verbose=True)





        
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


def prase_pdf_with_llama_index(pdf_path, company=None):
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
        required_exts = [".pdf"]
        print("Strart document extrattions")
        file_extractor = {".pdf": parser} # This will take everything for the parser, but we should ignore
        documents = SimpleDirectoryReader(pdf_path, 
                                          recursive=True, 
                                          file_extractor=file_extractor,
                                          required_exts=required_exts).load_data()

    print("Done with document extractions")

    try:
        for d in documents:
            file_name = d.metadata['file_name']
            if company:
                file_path = f"{company}/{file_name}.md"
            else:
                file_path = f"{file_name}.md"                

            with open(file_path, 'w') as file:
                    file.write(d.to_json())
    
    except Exception as e:
        print("Encountered an error")
        print(e)
        import pudb;pudb.set_trace()
        pass


def prepare_folder_for_summarization(path):
    summary_dict = {}

    for file in os.listdir(path):
        if file.endswith(".md"): # This is a file from llama parse, in json
            with open(os.path.join(path, file), 'r') as f:
                content = json.load(f)
                # The -3 is for the md
                summary_dict[file[:-3]] = content["text"]

        if file.endswith(".json"): # This is what we got from the crawler
            with open(os.path.join(path, file), 'r') as f:
                content = json.load(f)
            for document in content:
                url = document['url']
                if url.endswith("/"):
                    title = url.split('/')[-2] + ".pdf"
                else:
                    title = url.split('/')[-1] + ".pdf"
                # Getting the document name
                summary_dict[title] = document['html']

    with open(os.path.join(path, "summary.json"), 'w') as f:
        json.dump(summary_dict, f, indent=4)


def write_to_chroma(path):
    pass
    """

```
from vectordb.chroma.chroma_db import ChromaConfig, ChromaDB
from vectordb.chroma.cohere_ranking import CohereRanker
from vectordb.chroma.jina_embedding import JinaEmbedder


config = ChromaConfig(
    host="40.65.121.170",
    collection_name="quantum",
    ranking=CohereRanker(
        model="rerank-english-v2.0",
        trial_keys= [
            "rxhHpO9s701Pt4FR0PlknloI0yt4eH0IVnTOyrW0",
            "pm5unAQsdb6f5ak8iBmrYQVMmdW1IPF9KWM9ojsC",
            "w6JPx5Fp1TZxIwa6RkpzQyCqQhYfthxbl59HvW2w"
        ]
    ),
    embedding=JinaEmbedder(
        api_key="jina_d01fe168879346329a431b527b071f5bT5sfFKVKLaBqvKNjF8ZaHSWy20GD"
    )
)

newtone_client = ChromaDB(config)
newtone_client.initialize(None)

newtone_client._doc_collection.add(ids=list_of_ids, documents=list_of_documents)
    ```


    with open('../deep_kb.txt', 'r') as f:
        data = f.read()
    lines = data.splitlines()
    data = dict()
    for l in lines:
        if l == '':
            continue
        k,v = l.split(':', 1)
        data[k] = v.strip().rstrip()

    list_of_ids = list(data.keys())
    list_of_documents = list(data.values())

    """



def parse_js_crwaler_json(document):
    with open(document, 'r') as file:
        document_list = json.load(file)

    url_list = [d['url'] for d in document_list]
    return url_list


def parse_yaml_and_convert_files(yaml_file, css, company):

    with open(yaml_file, 'r') as file:
        yaml_content = yaml.safe_load(file)

    for section in yaml_content:
        for section_name, section_content in section.items():
            output_dir = f"{company}/{section_name}"
            os.makedirs(output_dir, exist_ok=True)

            pdf_engine = section_content.get('pdf_engine', False)
            respect_viewport = section_content.get('respect_viewport', True)
            auto_pdf_engine = True if pdf_engine == "auto" else False

            print(f"Generating PDF for {section_name}")
            print(f"Output directory: {output_dir}")
            print(f"Respect viewport: {respect_viewport}")
            print(f"PDF Engine: {pdf_engine}")  
            for link in section_content['links'].split(" "):

                if link.endswith("json"):
                    links = parse_js_crwaler_json(link)
                    for i in links:
                        convert_url_to_pdf(i, 
                                           output=None,
                                           api_pdf=auto_pdf_engine, 
                                           css=css,
                                           output_dir=output_dir,
                                           respect_viewport=respect_viewport)
                    continue

                convert_url_to_pdf(link, 
                                   output=None,
                                   api_pdf=auto_pdf_engine, 
                                   css=css,
                                   output_dir=output_dir,
                                   respect_viewport=respect_viewport)
                

def get_chroma_collection(collection):
    import chromadb
    client = chromadb.HttpClient(host='40.65.121.170')
    collection = client.get_collection(collection)
    collection_data = collection.get()
    print(collection_data['ids']) # Get the documents it based on
    document_structure = creating_claude_xml(collection_data)
    with open(f"{collection}.txt", 'w') as file:
        file.write(document_structure)


SUMMARIZAITON_PROMPT = """
The provided JSON is mapping documents in the following format : { "<filename>": "<content>" }

your job is to factually, accurately and concisely summarize documents. 
you are to make a concise bullet points for each document "content" in the JSON, note that "content" of each "filename" contains a 
professional oriented document, such as a blog post, white-paper, product catalog or the likes of it and is written in Markdown language. 
each document is varying in size and data. you should not repeat yourself,
if you already provided some piece of information, you do not need to include it again.
since each document is different, each might result in a different number of bullet points.
the bullet points are to be used as a knowledge-base for customer journey to get to know Deep-Instinct,
 their offerings and why they are the best-in-class when choosing a solution. as your output is restricted, 
 you can provide the bullet points in batches, each batch should be as large as possible, 
 when afterwards I write "NEXT" you shall provide the next batch until you have exhausted the list to which you will reply "END"

your output should follow this format:

<filename>@<bullet-point-index>: <bullet-point-content>
"""

SUMMARIZAITON_PROMPT_SINGLE_FILE = """
We want to summarize the following document

your job is to factually, accurately and concisely summarize documents. 
you are to make a concise bullet points for the document. Note that this is 
professional oriented document, such as a blog post, white-paper, product catalog or the likes of it and is written in Markdown language. 
each document is varying in size and data. you should not repeat yourself,
if you already provided some piece of information, you do not need to include it again.
the bullet points are to be used as a knowledge-base for customer journey to get to know Deep-Instinct,
their offerings and why they are the best-in-class when choosing a solution. \
as your output is restricted, 
The bullet points should be informative and can be used for RAG puposes, example of such bullet point is:
"Remote Code Injection is a strong attack vector used by adversaries and malware to evade detection by injecting malicious code into different processes.Remote Code Injection is a strong attack vector used by adversaries and malware to evade detection by injecting malicious code into different processes."
Which have deep information and insight about what we're doing
You should provide bullet points covering the entire document, if in your output not includes the entire bullet points 
of the document please write it to me.
Please read the document 5 times before respnding, take you time to make sure you've provided in your response the entire bullet points
You response should include the bullet points only without any additional text,
if you didn't finish with the bullet points, write to me in the end "Didn't finish" - but that's the only text you should write
which is not bullet point

Each bullet points should stand on it's own and should include information without relation to other bullet points

Format:

This is the format you shuold use:

"
{document_name}@<bullet-point-index>: <bullet-point-content>
"

The response contain only bullet points, without any pretext of additions beforehand 

Here's the document:

{document}

"""


# Taking a collection in current structure and changing it to be in Claude format
def creating_claude_xml(collection_data):
     
    documents_list = list(collection_data['ids'])
    bullet_point_list = list(collection_data['documents'])
    result_dict = dict(zip(documents_list, bullet_point_list))

    merged_dict = {}
    for k, v in result_dict.items():
        document_name = k.split("@")[0]
        if document_name not in merged_dict:
            merged_dict[document_name] = []
        merged_dict[document_name].append(v)

     
    document_structure = """
<document index="{index}">
<source>
{name}
</source>
<document_content>
{bullet_points}
</document_content>
</document>
"""

    i = 1
    documents_xml = ""
    for k, v in merged_dict.items():
        bullet_points = "\n".join(v)
        doc_str = document_structure.format(index=i, name=k, bullet_points=bullet_points)
        documents_xml += doc_str
        i += 1

    return documents_xml



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


def summarize_specific_file_llama(file_name, content):
    import requests

    summarize_prompt = SUMMARIZAITON_PROMPT_SINGLE_FILE.format(document_name=file_name, document=content)
    endpoint = 'https://api.together.xyz/v1/chat/completions'
    res = requests.post(endpoint, json={
        "model": "meta-llama/Llama-3-70b-chat-hf",
        "max_tokens": 4000,
        "temperature": 0,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": [
            "<|eot_id|>"
        ],
        "messages": [
            {
                "content": summarize_prompt,
                "role": "user"
            }
        ]
    }, headers={
        "Authorization": "Bearer c945e39ff1f079c7ab33005b14a3c74a1fd563b8050bfd0f7e6644b3e28ac229",
    })

    if res.status_code != 200:
        print("Error happened in summarization of")
        print(file_name)
        return None
    
    decoded_response = json.loads(res.content.decode(), strict=False)

    summary = decoded_response['choices'][0]['message']['content']
    lines_response = summary.splitlines()
    summary_clean = '\n'.join([line for line in lines_response if "@" in line])

    print(file_name)
    print(summary_clean)

    return summary_clean


def summarize_with_llama(markdown_folder):
    files = os.listdir(markdown_folder)
    markdown_files = [file for file in files if file.endswith(".md")]

    for markdown in markdown_files:

        if os.path.exists(f"{markdown_folder}/{markdown}-bulletpints"):
            print(f"Continue with file {markdown} since it exists")
            continue

        with open(f"{markdown_folder}/{markdown}", 'r') as file:
            md_content =json.load(file)

        result = summarize_specific_file_llama(markdown[:-3], md_content['text'])

        if result is None:
            continue

        with open(f"{markdown_folder}/{markdown}-bulletpints", 'w') as file:
            file.write(result)



PROMPT_DESCRIBE_IMAGE = """
Please describe this image, this description will be used for RAG purposes.

This image comes from document with these bullet points, so this is the context
in which the image found, if it can help you providing better description:
{bullet_points}

"""
        
def parse_images(image_folder):

    images = os.listdir(image_folder)

    for image in images:

        image_path = f"{image_folder}/{image}"

        # Image ext
        image_ext = image.split(".")[-1]

        # Taking the image name
        image_name = image

        image_pdf_name = image_name.split(".")[0] + ".pdf"
        bullet_point_name = image_pdf_name + ".md-bulletpints"

        bullet_point_path = "/Users/omriperi/Project/gpt-crawler-py/quantum/markdowns/" + bullet_point_name

        with open(bullet_point_path, 'r') as file:
            bullet_points = file.read()

        image_prompt = PROMPT_DESCRIBE_IMAGE.format(bullet_points=bullet_points)

        from anthropic import AnthropicBedrock
        import base64

        AWS_ACCESS_KEY = ''
        AWS_SECRET_KEY = ''
        AWS_REGION = 'us-west-2'
        ANTROPHIC_MODEL = "anthropic.claude-3-sonnet-20240229-v1:0"

        client = AnthropicBedrock(
            aws_region=AWS_REGION,
            aws_access_key=AWS_ACCESS_KEY,
            aws_secret_key=AWS_SECRET_KEY
        )

        # IMAGE_PATH = "/Users/omriperi/Project/gpt-crawler-py/images/5-tips-for-migrating-ml-models-page3-image2.png"

        with open(image_path, "rb") as f:
            image = base64.b64encode(f.read()).decode("utf-8")
        image_type = f"image/{image_ext}"

        response = client.messages.create(
            max_tokens=4096,
            model=ANTROPHIC_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_type,
                                "data": image,
                            },
                        },
                        {
                            "type": "text",
                            "text": image_prompt
                        }
                    ],
                }
            ],
        )

        # last_bullet_point = int(bullet_points.splitlines()[-1].split("@")[-1].split(":")[0])
        image_description = response.content[0].text.replace("\n", "")
        image_bullet_points = f"\n{image_pdf_name}@{image_name}: {image_description}"
        
        with open(bullet_point_path, 'a') as file:
            file.write(image_bullet_points)
        # Adding image description to bullet point
        print(response)
    
    

def extract_images(pdf_directory):
    files = os.listdir(pdf_directory)
    pdf_files = [file for file in files if file.endswith(".pdf")]

    import fitz  # PyMuPDF library
    # Open the PDF file
    for pdf_file in pdf_files:

        pdf = fitz.open(f"{pdf_directory}/{pdf_file}")

        # Iterate through each page in the PDF
        for page_index in range(len(pdf)):
            # Select the page
            page = pdf[page_index]

            # Iterate through the images on the page
            images = page.get_images()
            for image_index, img in enumerate(page.get_images(), start=1):
                # Get the image properties
                xref = img[0]
                base_image = pdf.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Generate the image file name
                image_filename = f"{pdf_directory}/images/{pdf_file}_{image_index}.{image_ext}"

                # Save the image file
                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)
                    print(f"Extracted image: {image_filename}")

        # Close the PDF file
        pdf.close()


  
# The role of this script is to get list of URL's (Can be) 
@click.command()
@click.argument('urls', type=str, nargs=-1, required=False)
@click.option('-c', '--company', type=click.STRING, required=False,
              help='Company to genereate PDF for')
@click.option('--css', type=click.STRING, required=False,
              help='Specific CSS to use for generation')
@click.option('-o', '--output', type=click.STRING, required=False,
              help='Company to genereate PDF for')
@click.option('-s', '--skip-browser', type=click.BOOL, is_flag=True, default=False,
              help='Skipping the browser')
@click.option('-d', '--debug', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
@click.option('--no-css', type=click.BOOL, is_flag=True, default=False,
              help='Opening the debugger')
@click.option('--only-html', type=click.BOOL, is_flag=True, default=False,
              help='Just create the HTML')
@click.option('--playwright', type=click.BOOL, is_flag=True, default=False,
              help='Generate PDF with Playwright')
@click.option('-l', '--llama-parse', type=click.STRING, required=False,
              help='Generating PDF with llama parse, just a checking')
@click.option('-s', '--summarize', type=click.STRING, required=False,
              help='Generating PDF with llama parse, just a checking')
@click.option('-a', '--api-pdf', type=click.BOOL, is_flag=True, default=False,
              help='Generate PDf with the API')
@click.option('-e', '--everything', type=click.BOOL, is_flag=True, default=False,
              help='Try all the methods for converting PDF')
@click.option('-i', '--images', type=click.BOOL, is_flag=True, default=False,
              help='Try all the methods for converting PDF')
@click.option('-l', '--llama', type=click.BOOL, is_flag=True, default=False,
              help='Try all the methods for converting PDF')
@click.option('-im', '--images-manual', type=click.BOOL, is_flag=True, default=False,
              help='Try all the methods for converting PDF')
@click.option('-p', '--parse-image', type=click.BOOL, is_flag=True, default=False,
              help='Try all the methods for converting PDF')
@click.option('--collection', type=click.STRING, default=None,
              help='Generate PDf with the API')
def click_cli_main(urls,            # List of URL's to convert or a configuration file
                   company,         # Company to generate PDF
                   output,          # The name of the output file
                   skip_browser,    # Skip the browser, use the current page.html
                   debug,           # Openning PUDB at the start of the script 
                   css,             # Specific CSS file to use
                   no_css,          # No-css modifidication on the HTML
                   playwright,      # Download the PDF from playwright
                   llama_parse,     # Use llama_parse to convert PDF's to Markdown
                   summarize,       # Summarization of all the files into one file for Opus
                   only_html,       # Only download the HTML and quit
                   api_pdf,        # Use PDF API to convert the HTML to PDF
                   collection,
                   images,
                   images_manual,
                   everything,
                   llama,
                   parse_image): # Try all the methods to export PDF

    if debug:
        import pudb; pudb.set_trace()

    if collection:
        get_chroma_collection(collection)
        return

    # This is the case in which we want to take markdown & json and merge between them
    if summarize:
        prepare_folder_for_summarization(summarize)
        return

    # This is the case where we're taking data into llama parse
    if llama_parse:
        prase_pdf_with_llama_index(llama_parse)
        return
    
    if llama:
        summarize_with_llama(urls[0])
        return        

    if images:
        convertapi.api_secret = CONVERT_API_KEY
        # Code snippet is using the ConvertAPI Python Client: https://github.com/ConvertAPI/convertapi-python
        convertapi.convert('extract-images', {
            'File': urls[0],
            'ImageOutputFormat': 'png'
        }, from_format = 'pdf').save_files('./images')
        return
    
    if images_manual:
        extract_images(urls[0])
        return
        
    if parse_image:
        parse_images(urls[0])
        return

    if company:
        # company_dict = COMPANY[company]
        # company_css = company_dict['default_css']
        css = f'css/{company}.css'
        # This url is mainly for tries while working, and should
        # url_list = [company_dict['default_url'] ]
        # output = f"{company}/{output}.pdf"
    
    if urls:
        url_list = urls

    if (url_list[0].endswith("json")):
        # It's a local file
        url_list = parse_js_crwaler_json(url_list[0])

    if (url_list[0].endswith("ml")):
        if not company:
            raise Exception("No company provided with yaml")
        # It's a local file
        parse_yaml_and_convert_files(url_list[0], css, company)
        # prase_pdf_with_llama_index(pdf_path=company, company=company)
        return

    for url in url_list:
        convert_url_to_pdf(url, 
                            skip_browser=skip_browser, 
                            output_dir=company, 
                            output=output, 
                            css=css,
                            no_css=no_css,
                            playwright=playwright,
                            only_html=only_html,
                            api_pdf=api_pdf,
                            everything=everything)
    # print(f"PDF generated at {output}")



if __name__ == "__main__":
    # convert_with_pdfratpr()
    click_cli_main()
