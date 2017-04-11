import requests as r
from bs4 import BeautifulSoup
import json
from time import sleep
from nltk.corpus import stopwords
from string import punctuation

from pathlib import Path

class Scrape():

    """

    Contains the methods to scrape and save data.
    Scrapes once, writes it to disk and after that every call to Scrape.read() will
    just read from disk

    """

    REQUEST_TIMEOUT = .5

    @staticmethod
    def _get_links():

        """

        Create a generator that will produce links to data.

        -> gen<string>

        """

        yield 'http://www.politifact.com/truth-o-meter/statements/'
        for i in range(2,665):
            yield 'http://www.politifact.com/truth-o-meter/statements/?page={}'.format(i)

    @staticmethod
    def _process_info_div(div_as_bs_obj):

        """

        Parses a text unit to get source (who said it), statement(what did they say), and (truth) was it true?
jkkgg

        -> bs_obj -> string

        """

        source_q = 'div.statement__body > div.statement__source > a'
        statement_q = 'div.statement__body > p.statement__text > a'
        truth_q = 'div.meter > a > img'

        return {
            'source': div_as_bs_obj.select_one(source_q).text,
            'statement': div_as_bs_obj.select_one(statement_q).text,
            'truth': div_as_bs_obj.select_one(truth_q).get('alt')
        }

    @staticmethod
    def _parse_page(html):

        """

        Grabs all text units of a single paginated page

        string -> List<bs_obj>j

        """

        bs_obj = BeautifulSoup(html, 'lxml')
        selector_query = 'body > div > div > div.pfmaincontent > div.content > div > main > section > div.scoretable__item > div.statement'
        info_divs = bs_obj.select(selector_query)

        return [Scrape._process_info_div(div) for div in info_divs]

    @staticmethod
    def _write_data():

        """
        Runs the scrape and writes your data to disk
        """

        def process_page(url,i):

            print ("{}...".format(i))

            html = r.get(url).text
            sleep(Scrape.REQUEST_TIMEOUT)

            return Scrape._parse_page(html)

        data = [process_page(url,i) for i,url in enumerate(Scrape._get_links())]

        flattened_data = sum(data, [])

        with open("truth_data.json", 'w') as outfile:
            json.dump(flattened_data, outfile)

    @staticmethod
    def read():

        """

        Get the truth data from disk

        """
        data = Path("truth_data.json")

        if not data.is_file():
            Scrape._write_data()

        with open("truth_data.json", 'r') as infile:
            return json.load(infile)

class Truth():

    lies = {'Pants on Fire!', 'Full Flop', 'Mostly False', 'False'}
    truth = {'True', 'Mostly True', 'Half-True', 'No Flip'}

    both = [
            'Pants on Fire!',
            'Full Flop',
            'Mostly False',
            'False',
            'No Flip',
            'Half-True',
            'Mostly True',
            'True'
    ]

    to_int = {truthy:i for i, truthy in enumerate(both)}

class Process():

    puncutation_set = set(punctuation)
    stopwords_set = set(stopwords.words('english'))

    @staticmethod
    def _get_truth_and_convert_to_number(x):

        """

        Truth statement -> Int
        e.g. Pants-On-Fire -> 0

        dict -> Int

        """

        return int(Truth.to_int.get(x.get('truth')))

    @staticmethod
    def _get_statement_and_strip(x):

        """

        Reads json_obj grabs statement and strips punc and lowercases it

        dict -> string

        """

        statement = x.get('statement').strip().lower()
        statement_without_punctuation = ''.join(x for x in statement if x not in puncutation_set)

        return statement_without_puncutation.split(" ")

    @staticmethod
    def clean_data_and_split_statement(json_data):

        return [(
            Process._get_truth_and_convert_to_number(x),
            Process._get_statement_and_strip(x)) for x in json_data]

    @staticmethod
    def all_words(clean_data):

        """
        Returns all words present in statement and the length of the word with the maximum len

        """

        statements = [x[1] for x in clean_data]
        words = set()

        max_len = -float("inf")

        for statement in statement:

            for word in statement:

                words |= word

                max_len = max(len(word), max_len)

        return words, max_len

if __name__ == "__main__":

    data = Scrape.read()
