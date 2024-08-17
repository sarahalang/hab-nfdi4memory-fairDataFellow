# A Computer Vision Dataset for Alchemical Illustrations
This repo contains my work on annotating images from https://alchemie.hab.de/bilder for computer vision (object detection) as part of my 2024-08 NFDI4Memory Fair Data Fellowship, including scraping the images.

## The data and what to use it for 
HAB's alchemy portal (https://alchemie.hab.de) offers IconClass categories extended specifically to tag alchemy images. 
A number of book pages containing such illustrations (digitized in the project) were tagged using those categories.
Amongst them are alchemical instruments, in which I am particularly intersted.

To make the data usable for computer vision (specifically object detection), the locations of the objects on the images need to be specified in a usable image annotation format (such as MS COCO) so they can be used to train machine learning algorithms.
To make that possible, this script allows me (and you) to select a number of those categories, then the links to all images tagged with this category will be scraped from the webpage and later downloaded.

## This script
The script takes the categories from the categories csv file that needs to be present in the same folder as your script for this to work. This file only contains the categories I was interested in (alchemical laboratory instruments, but there are more categorgies!), so if you want to download anything else, you need to extend that csv file. 

Run the phython script to scrape your chosen image categories:
```
python3 scrape-hab-alchemyImgs.py
```
It will first save all links it scraped in a csv file,
then deduplicate them (so you only download each image once, as that meets my use case, adapt as needed) 
and save the result of that deduplication process in a csv file as well.
Finally, it will use the deduplicated csv file to download the images using wget. 

## Usage recommendations 
I recommend trying out the script using a category that only contains a few images (such as 'cupel'), then delete all files that were created by the script (not the categories csv but the log, the other csvs and the folders with the downloaded images). This isn't strictly necessary but may prevent confusion and duplicated downloads.
My goal was to only download the least amount of images necessary. That's why it makes sense that after you have done the test run, you select all the categories you want and download them in one go (that way deduplication will be the most effective, saving you from unnecessarily downloading some images multiple times). 
The deduplicated csv file still documents all the categories it was tagged with for your future reference. 
Success or any problems are logged in the log and the terminal. 
