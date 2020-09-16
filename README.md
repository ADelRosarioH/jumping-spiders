# jumping-spiders
Web crawlers to collect prices of everything in Dominican Republic

Remember to change proxy to: torporxy:8118

# readme

I'm not in the mood of writing something super detailed, but it has been in my head for a while and 
I can't be able to concentrate in what's next, because of thinking of what is done.

# Architecture overview
- Web crawling and scraping is done using Scrapy
- Spider scheduling is done using scrapyd
- Distributed crawling, scrapyd host management and crawling tasks scheduling is donde using Gerapy
- Proxy and IP rotation is done using Tor and Privoxy
- File synching is done using crontab + bash + rsync
- Data wrangling is done using crontab + bash + Openrefine
- Unprocessed files are going to be stored in AWS S3 as backup
- Processed files are going to be stored in AWS S3 as backup
- Processed files are going to be stored in postgresql by script 

## stuff that I need to figure out
- Where to analyze the data, python vs sql
- What kind of analysis to make
- search engine stuff
- API monolith, serverless or dockerized
- front end stuff
- logo, basic branding stuff
- images using google search api 
- launch strategy

# Data Pipeline
- Spiders scrape data from website
- Spider generates feed
- feed is sync daily to openrefine input directory
- openrefine cleans up the files in input directory applying operations
- openrefine exports cleaned files to output directory
- bash script uploads unprocessed files from input directory to AWS S3 and then removes them from input directory
- bash script uploads processed files from output directory to AWS S3 and then removes them from output directory
- bash script loads data to database

# File cleanup retry
- Locate file in unprocessed directory or download from AWS S3 backup
- Copy file to openrefine input directory
- Execute openrefine cleanup
- Replace cleanup file in AWS S3 processed directory
- Delete data from date range from database
- loads new data to database

This avoids recrawling the website.

# websites
- PriceRunner (https://www.pricerunner.com/)
- PriceSpy (https://pricespy.co.uk/)
- PCPartPicker (https://pcpartpicker.com/)

# Webapp
- Name: Preciopolis (http://preciopolis.com)
- Features:
  - Product Price Scraping
  - Product Search & Categorization
  - Product Price Breakdown by Merchant 
  - Product Price History (Step Graph)

# List of stores
- [ ] proconsumidor.gob.do
- [ ] https://sirena.do
- [ ] https://supermercadosnacional.com
- [ ] https://tienda.farmaciacarol.com
- [ ] https://supermerca.do
- [ ] https://www.amorossa.com/
- [ ] https://www.zuniflor.com.do
- [ ] https://tikiti.com.do/
- [ ] 