# Code written by Sarah Lang with assistance of ChatGPT 4o
# Date: September 2024


import csv
import requests
from bs4 import BeautifulSoup
import re

# Function to extract bibliographic data from the XML
def extract_metadata(mets_link):
    response = requests.get(mets_link)
    soup = BeautifulSoup(response.content, 'xml')

    # Find the bibliographicCitation element
    citation = soup.find('dct:bibliographicCitation')
    
    if citation:
        bibliographic_description = citation.text

        # Regular expressions to extract details from the citation text
        author_search = re.match(r"^([^:]+):", bibliographic_description)
        title_search = re.match(r"^(?:[^:]+:\s)?(.*?)(?:\s-\s|$)", bibliographic_description)
        publishing_place_search = re.search(r"-\s(.*?)(?:\s:\s)", bibliographic_description)
        publisher_search = re.search(r":\s(.*?)(?:,\s|\s|$)", bibliographic_description)
        year_search = re.search(r",\s(\d{4})", bibliographic_description)
        
        # Extracting values
        author = author_search.group(1) if author_search else None
        title = title_search.group(1) if title_search else None
        publishing_place = publishing_place_search.group(1) if publishing_place_search else None
        publisher = publisher_search.group(1) if publisher_search else None
        year = year_search.group(1) if year_search else None
        
        return bibliographic_description, author, title, publishing_place, publisher, year
    return None, None, None, None, None, None

# Function to transform image link into viewer and METS links
def transform_links(image_link):
    # Extract the book signature (e.g., nd-779) and image number (e.g., 00099)
    parts = image_link.split('/')
    signature = parts[-2]  # Signature is 'nd-779'
    image_file = parts[-1]  # Image file is '00099.jpg'
    image_number = image_file.replace('.jpg', '')

    # Construct the viewer link
    viewer_link = f"https://diglib.hab.de/drucke/{signature}/start.htm?image={image_number}"

    # Construct the METS XML link
    mets_link = f"https://diglib.hab.de/drucke/{signature}/mets.xml"

    return viewer_link, mets_link

# Main function to process the CSV and scrape metadata
def scrape_metadata(input_csv, output_csv):
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile, \
         open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = ['original_image_link', 'viewer_link', 'mets_link', 'bibliographical_description',
                      'author', 'title', 'publishing_place', 'publisher', 'publication_year']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        writer.writeheader()

        for row in reader:
            image_link = row['image_link']

            # Transform links
            viewer_link, mets_link = transform_links(image_link)
            
            # Extract metadata
            bibliographical_description, author, title, publishing_place, publisher, year = extract_metadata(mets_link)

            # Writing the data to the CSV
            writer.writerow({
                'original_image_link': image_link,
                'viewer_link': viewer_link,
                'mets_link': mets_link,
                'bibliographical_description': bibliographical_description,
                'author': author,
                'title': title,
                'publishing_place': publishing_place,
                'publisher': publisher,
                'publication_year': year
            })

# Run the script
input_csv = 'deduped_image_links.csv'
output_csv = 'output_hab_imgs_metadata.csv'
scrape_metadata(input_csv, output_csv)

