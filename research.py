import os
import requests
from xml.etree import ElementTree

# URL for the arXiv API
url = "http://export.arxiv.org/api/query"
# Parameters for the API query
params = {
    "search_query": "all:quantum computing",
    "start": 0,
    "max_results": 5
}

response = requests.get(url, params=params)
tree = ElementTree.fromstring(response.content)

# Directory to save PDFs
pdf_directory = "./arxiv_pdfs"
os.makedirs(pdf_directory, exist_ok=True)

# Loop through each entry in the response
for entry in tree.findall('{http://www.w3.org/2005/Atom}entry'):
    title = entry.find('{http://www.w3.org/2005/Atom}title').text
    pdf_link = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
    
    if pdf_link is not None:
        pdf_url = pdf_link.attrib['href']
        pdf_response = requests.get(pdf_url)
        
        if pdf_response.status_code == 200:
            # Creating a valid filename from the title
            pdf_filename = title.replace(' ', '_').replace('/', '_').replace('\n', '') + '.pdf'
            pdf_path = os.path.join(pdf_directory, pdf_filename)

            # Saving the PDF
            with open(pdf_path, 'wb') as f:
                f.write(pdf_response.content)
            print(f"Downloaded: {pdf_filename}")
