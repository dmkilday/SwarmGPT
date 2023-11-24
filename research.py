import os
import requests
from xml.etree import ElementTree

class Research:

    def __init__(self, knowledge_path, search_url):
        self.knowledge_path = knowledge_path
        self.search_url = search_url

    # Searches the research repository using the search term 
    def search(self, search_term, max_results):

        # Parameters for the API query
        params = {
            "search_query": f"all:{search_term}",
            "start": 0,
            "max_results": max_results
        }

        response = requests.get(self.search_url, params=params)
        tree = ElementTree.fromstring(response.content)
        return tree

    # Downloads the list of PDFs in the query response tree
    def download(self, tree):

        # Create the PDF directory if it doesn't already exist
        os.makedirs(self.knowledge_path, exist_ok=True)

        # Loop through each entry in the search response
        for entry in tree.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text
            pdf_link = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]')
            
            # If there is a PDF link
            if pdf_link is not None:
                pdf_url = pdf_link.attrib['href']
                pdf_response = requests.get(pdf_url)
                
                if pdf_response.status_code == 200:
                    # Creating a valid filename from the title
                    pdf_filename = title.replace(' ', '_').replace('/', '_').replace('\n', '') + '.pdf'
                    pdf_path = os.path.join(self.knowledge_path, pdf_filename)

                    # Saving the PDF
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"Downloaded: {pdf_filename}")
