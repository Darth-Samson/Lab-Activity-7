# scrapetest.py
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Open the sample page
html = urlopen("http://www.pythonscraping.com/pages/page1.html")

# Parse the HTML using BeautifulSoup
bsObj = BeautifulSoup(html, "html.parser")

# Print the page title
print("Title of the page:", bsObj.title.string)

# Print the first h1 tag (if it exists)
h1_tag = bsObj.h1
if h1_tag:
    print("H1 text:", h1_tag.get_text())

# Print all links (hrefs) on the page
print("\nLinks found:")
for link in bsObj.find_all("a"):
    print("-", link.get("href"))
