import csv
import random
from decimal import Decimal as decimal

def format_csv(csv_file):
    """Return dictionary structures with formatted data from the
    provided csv file. """
    with open(csv_file, encoding="utf8", mode='r') as datafile:
        datastream = csv.reader(datafile)
        # attributes = [i for i in datastream.__next__()]
        # raw_dict = {i: [] for i in [j for j in datastream.__next__()]}
        datastream.__next__()  # remove attribute names
        raw_data = [i for i in [j for j in datastream]]
        datafile.close()
    return [i[5:6]+i[1:4]+i[6:] for i in raw_data]

def extract_authors(data):
    """Parse the authors in the provided 2D list and create a dictionary with
    author names as keys and values as isbn list of books written"""
    authors = {}
    for book in data:
        cur_authors = book[2].split('/')
        for cur_auth in cur_authors:
            if cur_auth in authors:
                authors[cur_auth].append(book[0])
            else:
                authors[cur_auth] = [book[0]]
    return authors, [i[:2]+i[3:]+[float(decimal(random.randrange(100, 10001)/100)),
                                  ] for i in data]


