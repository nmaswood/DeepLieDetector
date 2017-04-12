import requests as r
from bs4 import BeautifulSoup
import json
from time import sleep
import re
import keras
import keras.preprocessing.text
import numpy as np
from pathlib import Path

from keras.preprocessing.sequence import pad_sequences

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

    lies = {'Pants on Fire!', 'Full Flop', 'Mostly False', 'False', 'Half Flip'}
    truth = {'True', 'Mostly True', 'Half-True', 'No Flip'}

    both = [
            'Pants on Fire!',
            'Full Flop',
            'Mostly False',
            'False',
            'Half Flip',
            'No Flip',
            'Half-True',
            'Mostly True',
            'True'
    ]

    to_int = {truthy:i for i, truthy in enumerate(both)}

class Process():

    @staticmethod
    def _get_truth_and_convert_to_number(x):

        """

        Truth statement -> Int
        e.g. Pants-On-Fire -> 0

        dict -> Int

        """

        truth_value = x.get('truth')

        return int(Truth.to_int.get(truth_value))

    @staticmethod
    def _get_statement_and_strip(x):

        """

        Reads json_obj grabs statement and strips punc and lowercases it

        dict -> string

        """

        statement = x.get('statement')

        statement = re.sub(r'''[()'",.]''', '', statement).strip()

        return keras.preprocessing.text.text_to_word_sequence(statement, lower=True, split=" ")

    @staticmethod
    def _clean_data_and_split_statement(json_data):

        return [(
            Process._get_truth_and_convert_to_number(x),
            Process._get_statement_and_strip(x)) for x in json_data]

    @staticmethod
    def _all_words(clean_data):

        """
        Returns all words present in statement and the length of the word with the maximum len

        """

        statements = [x[1] for x in clean_data]
        words = set()

        max_len = -float("inf")

        for statement in statements:

            for word in statement:
                words.add(word)

            max_len = max(len(statement), max_len)

        return sorted(list(words)), max_len

    @staticmethod
    def _all_chars(all_words):

        """

        Returns all words present in statement and the length of the word with the maximum len

        """

        s = set()
        l = -float("inf")
        for word in all_words:
            s |= set(word)
            l = max(l, len(s))

        return sorted(list(s)), l

    @staticmethod
    def _vectorize(clean_data, vocab, max_word_len):

        # Reserve 0 for masking via pad_sequences

        vocab_size = len(vocab) + 1

        word_idx = {c: i + 1 for i, c in enumerate(vocab)}

        xs_and_ys = [Process._vectorize_one(statement, word_idx, truthy, max_word_len) for truthy, statement in clean_data]

        X = [x[0] for x in xs_and_ys]
        y = [x[1] for x in xs_and_ys]

        return X,y, word_idx

    @staticmethod
    def _vectorize_one(statement, vocab_dict, truthy, max_word_len):

        """

        Converts one sentence and one truthy value into an x and y vector respectively

        """

        X = [vocab_dict[word] for word in statement]

        y = np.zeros(len(Truth.to_int))

        y[truthy] = 1

        return X,y

    @staticmethod
    def data_init(json_data):

        """

        Combines all the previous methods to clean and vectorize data

        """

        clean_data = Process._clean_data_and_split_statement(json_data)
        all_words, max_word_len = Process._all_words(clean_data)
        X,y, word_index = Process._vectorize(clean_data, all_words, max_word_len)

        X = pad_sequences(X, maxlen = max_word_len),

        return Data(
                data = data,
                clean_data = clean_data,
                words = all_words,
                word_index = word_index,
                vocab_size = len(all_words) + 1,
                max_word_len = max_word_len,
                X = X,
                y = y)


class Data():

    """

    A struct to hold all the vectorized data information

    """

    def __init__(self,

            data,
            clean_data,
            words,
            word_index,
            vocab_size,
            max_word_len,
            X,
            y):
        """
        data
            The original untouched data
        clean_data
            The cleaned data
        word_index
            mapping from words to indexes
        vocab_size
            Amount of words in vocab
        max_word_len
            The maximum length of a statement
        X
            The statements as vectors
        y
            The truth values as vectors
        """

        self.data = data
        self.clean_data = clean_data
        self.word_index = word_index
        self.vocab_size = vocab_size
        self.max_word_len = max_word_len
        self.X = X
        self.y = y

    def __getitem__(self, key):

        return getattr(self, key)


if __name__ == "__main__":

    data = Scrape.read()
    data_processed = Process.data_init(data)

