# A Computer Vision Dataset for Alchemical Illustrations
This repo contains my work on annotating images from https://alchemie.hab.de/bilder for computer vision (object detection) as part of my 2024-08 NFDI4Memory Fair Data Fellowship, including scraping the images.

## The data and what to use it for 
HAB's alchemy portal (https://alchemie.hab.de) offers IconClass categories extended specifically to tag alchemy images. 
A number of book pages containing such illustrations (digitized in the project) were tagged using those categories.
Amongst them are alchemical instruments, in which I am particularly intersted.

To make the data usable for computer vision (specifically object detection), the locations of the objects on the images need to be specified in a usable image annotation format (such as MS COCO) so they can be used to train machine learning algorithms.

To make that possible, this script allows me (and you) to select a number of those categories, then the links to all images tagged with this category will be scraped from the webpage and later downloaded.

## This script
The script (`scrape-hab-alchemyImgs.py`) takes the categories from the categories csv file (`hab-alchemical-categories-links.csv`) that needs to be present in the same folder as your script for this to work. 

This file only contains the categories I was interested in (alchemical laboratory instruments, but there are more categorgies!), so if you want to download anything else, you need to extend that csv file (`hab-alchemical-categories-links.csv`). You address them in the script via their `categoryShorttitle` so the name you put in this field needs to be exactly the same as what you put in `categories_to_process` in `scrape-hab-alchemyImgs.py` (around 150 lines in is where the 'main part' begins, look there). 

Run the phython script to scrape your chosen image categories:
```
python3 scrape-hab-alchemyImgs.py
```
It will first save all links it scraped in a csv file (`all_image_links.csv`), 
then deduplicate them (so you only download each image once, as that meets my use case, adapt as needed) 
and save the result of that deduplication process in a csv file (`deduped_image_links.csv`) as well.
Finally, it will use the deduplicated csv file to download the images using wget. 

## Usage recommendations 
I recommend trying out the script using a category that only contains a few images (such as 'cupel'), then delete all files that were created by the script (not the categories csv but the log, the other csvs and the folders with the downloaded images). This isn't strictly necessary but may prevent confusion and duplicated downloads.

My goal was to only download the least amount of images necessary. That's why it makes sense that after you have done the test run, you select all the categories you want and download them in one go (that way deduplication will be the most effective, saving you from unnecessarily downloading some images multiple times). 
The deduplicated csv file (`deduped_image_links.csv`) still documents all the categories it was tagged with for your future reference. 

Success or any problems are logged in the log (`image_download.log`) and the terminal. 

---

# Book Metadata Scraper

I later added two scripts for scraping and processing metadata for the books included in the dataset. It is important to have an overview over which books and images are included in the dataset as not to mix up the training and evaluation data. 

The Python script `extract-hab-metadata-from-image-links.py` scrapes bibliographic metadata from HAB's digital library based on image links provided in a CSV file (). It constructs viewer and METS XML links from the image links, fetches the metadata stored in the XML file, and extracts the author, title, publishing place, publisher, and publication year, where available. The results are saved into a new CSV file.
Run as follows: 
```
python3 extract-hab-metadata-from-image-links.py
```
I set the input to be the file 'deduped_image_links.csv' (outputted by the script above) and the output will be named 'output_hab_imgs_metadata.csv'. However, you can adapt this to your own needs in the "Run the script" section of the code (towards the very end, denoted by a comment). 

The script will achieve the following things: 
- **Transforms image links**: Converts image links into viewer links and METS XML links. These make it easier for you to click into the book, as the links we saved before only lead to the downloadable image from where there is no way to directly look though the book (in case you need context or need to find out what book the image is actually from). 
- **Fetches XML metadata**: Retrieves bibliographic metadata stored in the METS XML files for each book. However, the HAB METS service seems to be somewhat faulty at this point, so most entries offer no bibliographic metadata there or, if they do, it is incomplete. I'm told this is being investigated. Until then, you should be able to get all the information from [HAB's OPAC library system/online catalog](https://opac.lbs-braunschweig.gbv.de/DB=2/LNG=DU/) using the signatures available to you in the data.

The script will generate a new CSV file containing the following fields:
- **original_image_link:** The original image link from the input.
- **viewer_link:** The transformed viewer link.
- **mets_link:** The link to the METS XML file.
- **bibliographical_description:** The full bibliographic citation string.
- **author:** The author, if available.
- **title:** The title of the work.
- **publishing_place:** The place of publication, if available.
- **publisher:** The publisher, if available.
- **publication_year:** The publication year, if available.

The `mets.xml` file only contains an unstructured bibliographical description, however, if present, the fields seem to be separated in a standardized manner. However, since most of my books did not have any or only incomplete bibliographical references there, the extraction of the relevant entities might be faulty. I did not fix this because it mostly wasn't relevant anyway but you might if you re-use this script for your own data. 

This is an example of a bibliographical description (almost complete but missing the author/editor):
```
<dct:bibliographicCitation>Dyas Chymica Tripartita, Das ist: Sechs Herrliche Teutsche Philosophische Tractätlein ... - Franckfurt am Mayn : Jennis, 1625</dct:bibliographicCitation>
```

Examples like this might produce errors: 
```
<dct:bibliographicCitation>Libavius, Andreas: Alchymia Andreæ Libavii, Recognita, Emendata, Et aucta</dct:bibliographicCitation>
```
The output in this case should look like:
```
original_image_link,viewer_link,mets_link,bibliographical_description,author,title,publishing_place,publisher,publication_year
https://diglib.hab.de/drucke/nd-123/00123.jpg,https://diglib.hab.de/drucke/nd-123/start.htm?image=00123,https://diglib.hab.de/drucke/nd-123/mets.xml,"Libavius, Andreas: Alchymia Andreæ Libavii, Recognita, Emendata, Et aucta","Libavius, Andreas","Alchymia Andreæ Libavii, Recognita, Emendata, Et aucta",None,None,None
```

Required libraries can be installed like so:
```
pip install requests beautifulsoup4 lxml
```

## Sorting the book metadata output by pages included
This script will use the output of the last one and only reduce it so that there's only one line for each book/signature included but this line has a list of all the pages from this book that were included in the dataset. 

Run as follows: 
```
python3 get-hab-img-metadata-for-dataset.py
```
The naming of the last two python scripts is a little bit confusing, sorry about that. They need to be run in the order they are listed here.
I set the input to be the file 'output_hab_imgs_metadata.csv' (outputted by the script above) and the output will be named 'hab-dataset-img-metadata.csv'. However, you can adapt this to your own needs in the "Run the script" section of the code (towards the very end, denoted by a comment). 

The output can be imported in a sheet software of your choice, however, please note that LibreOffice for some reason omits page numbers from entries where there is only one page number. Initially, I suspected this was due to different CSV quoting options (one single page is treated like an integer and the field is not in double quotes in the CSV output, whereas the lines with multiple comma-separated page numbers are in quotes) but this didn't make a difference. The error does not appear when importing to GoogleSheets, for instance, so I didn't fix it - but please be aware of this caveat. 
Once it's imported, you can fill in the gaps in the metadata using the library system. 

