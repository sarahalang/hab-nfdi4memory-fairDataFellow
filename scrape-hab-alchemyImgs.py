#!/usr/bin/python3 
# this code was written using AI coding assistance by ChatGPT 4o 
# author: Sarah Lang
# date: August 2024
#-------------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import csv
import os
import wget
import logging

#-------------------------------------------------------------------------------

# Setup logging
logging.basicConfig(filename='image_download.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

#-------------------------------------------------------------------------------
def get_category_links_from_csv(csv_file_path):
    # Initialize an empty dictionary to store the category data
    category_links = {}

    # Read the CSV file and extract 'categoryShorttitle' 
    # and ' HAB category images link' columns
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            category_shorttitle = row['categoryShorttitle'].strip()
            hab_category_link = row['HAB category images link'].strip()
            category_links[category_shorttitle] = hab_category_link

    return category_links

#-------------------------------------------------------------------------------

# Define the path to the uploaded CSV file
csv_file_path = 'hab-alchemical-categories-links.csv'
category_links = get_category_links_from_csv(csv_file_path)
# Display the dictionary
#print(category_links)

#-------------------------------------------------------------------------------
# Function to extract image links from a single page
def extract_image_links(page_url, category):
  image_links = []
  # Send a GET request to the page
  response = requests.get(page_url)  
  # Parse the HTML content of the page
  soup = BeautifulSoup(response.text, 'html.parser') 
  # Find all <a> tags
  links = soup.find_all('a', href=True)
  # List to store relevant links
  relevant_links = []

  # Iterate over all <a> tags
  for link in links:
    # Check if the <a> tag contains an <img> tag with a src attribute
    img_tag = link.find('img', src=True)
    if img_tag:
        relevant_links.append(link['href'])

  # Print relevant links
  for link in relevant_links:
    #print(f"Relevant link (thumbnail): {link}")
    pass
    
  print('Relevant links (number): ' + str(len(relevant_links)))
  print('1st link (example): ' + relevant_links[0])
  
  # Process each thumbnail
  for thumbnail in relevant_links:
      if "start.htm?image=" in thumbnail:
        base_url = thumbnail.split("start.htm?image=")[0]
        image_number = thumbnail.split("start.htm?image=")[1]
        image_link = f"{base_url}{image_number}.jpg"
        image_links.append((category, image_link))
  
  print('1st DL link (example):\n' + str(image_links[0]))
  #print('---')
    
  return image_links
#-------------------------------------------------------------------------------

# Function to determine the total number of pages and images
def get_total_pages_and_images(start_url):
    response = requests.get(start_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract the total number of images from the pager div
    pager = soup.find('div', class_='pager').text
    total_images = int(pager.split('available')[0].strip())
    
    # Extract the total number of pages by counting the page links
    page_links = soup.find_all('span', class_='page')
    if page_links:
        # Navigate to the <a> tag and get its text content 
        last_page_link = page_links[-1].find('a').text
        total_pages = int(last_page_link)
        #last_page_link = page_links[-1].find('a')['href']
        #total_pages = int(last_page_link.split('page=')[1].split('&')[0])
    else:
        total_pages = 1
    
    return total_pages, total_images

#-------------------------------------------------------------------------------

# Function to scrape image links from all pages
def scrape_all_pages(start_url, category):
    total_pages, total_images = get_total_pages_and_images(start_url)
    print('There should be ' + str(total_pages) + 
          ' page(s) to scrape, containing ' + str(total_images) + 
          ' images in total.')
    all_image_links = []
    current_page = 1
    
    while current_page <= total_pages:
        page_url = f"{start_url}&page={current_page}"
        print(f"Scraping page {current_page}...")
        
        # Extract image links from the current page
        image_links = extract_image_links(page_url, category)
        all_image_links.extend(image_links)
        
        current_page += 1
    
    # Verify if the total number of links matches the total number of images
    if len(all_image_links) != total_images:
        print(f"Warning: Expected {total_images} images, " +
               "but  found {len(all_image_links)} links.")
    else:
        print(f"Successfully scraped all {total_images} image links.")
    
    return all_image_links
    
#-------------------------------------------------------------------------------

# Function to deduplicate and merge categories
def deduplicate_image_links(image_links):
    dupe_counter = 0
    deduplicated = {}
    for category, link in image_links:
        if link in deduplicated:
            deduplicated[link] += f" {category}"
            dupe_counter += 1
        else:
            deduplicated[link] = category
	# Convert deduplicated dictionary to a list of tuples
    print(str(dupe_counter) + ' links were present multiple times "
          + "in the dataset.')
    return [(categories, link) for link, categories in deduplicated.items()]  

#-------------------------------------------------------------------------------

# MAIN Part of the code 

#-------------------------------------------------------------------------------

# Best run all categories at once, or else deduplication isn't that effective
# Delete all files and data before re-running the code to be safe
# deduplication should take care of links scraped multiple times
# but files may be downloaded again, defeating the purpose of deduplication
# if you don't clean out data you already have locally beforehand 

# Define the categories to process
categories_to_process = ["ampullae", "ollae", "cucurbitae", 
                         "retorts", "rosenhut", "cupel", "crucible", 
                         "alembics", "furnace", "otherAlchemicalTools"]  
                         # Add more categories as needed
print('We are processing the following categories/pages:')
for category in categories_to_process:
  print('Link (' + category + '): ' + category_links[category])
print('---')

#-------------------------------------------------------------------------------

# Initialize an empty list to store all image links
all_image_links = []

# Iterate over each category and scrape the corresponding links
for category in categories_to_process:
    base_url = category_links[category]
    print('---\nProcessing category: ' + category)
    image_links = scrape_all_pages(base_url, category)
    all_image_links.extend(image_links)

# Write all the collected image links to a single CSV file
with open('all_image_links.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['category', 'image_link'])  # Write the header row
    writer.writerows(all_image_links)  # Write the data rows

print("All image links have been scraped and saved to 'all_image_links.csv'.")

#-------------------------------------------------------------------------------

# Deduplicate the image links and merge categories
deduplicated_links = deduplicate_image_links(all_image_links)

#-------------------------------------------------------------------------------

# Write the deduplicated results to a CSV file
with open('deduped_image_links.csv', 'w', newline='') as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow(['categories', 'image_link'])  # Write the header row
	writer.writerows(deduplicated_links)  # Write the data rows

print("Image links have been scraped, deduplicated, "
       + "and saved to 'deduped_image_links.csv'.")
logging.info(f"Total deduplicated links: {len(deduplicated_links)}")

#-------------------------------------------------------------------------------

# Dictionary to track which images have been processed
processed_images = {}

# Read the CSV file
with open('deduped_image_links.csv', 'r') as csvfile:
	reader = csv.reader(csvfile)
	next(reader)  # Skip the header row
    
	for row in reader:
		category, link = row
		# this part of the code is partially redundant/unnecesarily complicated
		if link in processed_images:
		    # If the image has already been processed, 
		    # add the category to the existing entry
			processed_images[link] += f" {category}"
		else:
		    # If the image hasn't been processed yet, add it to the dictionary
			processed_images[link] = category
			
# Track how many images are downloaded
downloaded_images_count = 0

# Ensure directories are created and images are downloaded only once
for link, categories in processed_images.items():
    try:
        # Get the first/main category
        main_category = categories.split()[0]

        # Create the directory if it doesn't exist
        if not os.path.exists(main_category):
            os.makedirs(main_category)
        
        # Determine the filename with signature and image basename
        # Extract the signature from the URL
        # Assuming the signature is the directory path before the basename
        # Example URL: http://diglib.hab.de/drucke/137-18-eth-1s/00021.jpg
        # Signature: 137-18-eth-1s
        signature = link.split('/')[-2]
        # Extract the basename
        basename = os.path.basename(link)
        # Combine signature and basename for the filename
        image_filename = f"{signature}_{basename}"
        image_path = os.path.join(main_category, image_filename)
        
        # Download the image into the main category directory
        logging.info(f"Downloading image ({image_filename}): " +
                       "{link} to {image_path}")
        wget.download(link, image_path)
        downloaded_images_count += 1
    
    except Exception as e:
        logging.error(f"Error downloading {link}: {e}")

print("\nAll images have been downloaded and organized with deduplication. ")
print(f"Total images downloaded: {downloaded_images_count}.")
logging.info(f"Total images downloaded: {downloaded_images_count}") 

#-------------------------------------------------------------------------------



