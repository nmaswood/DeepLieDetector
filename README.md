# DeepLieDetector
This code does two things:

* Collects lie data from politic fact via built in scraper 
* Builds a neural network that given an aribtrary statement from the news does its best to determine whether or not that statement is a lie

## Scrape Data from Politic Fact

If the data is present on disk, `Scrape.read() `will just read data from disk. If the data is not present it will be scraped.

```python

from data import Scrape

# collects all data from http://www.politifact.com/truth-o-meter/statements

my_scraped_data = Scrape.read()

```


