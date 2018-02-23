"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import requests
from lxml import html
import sqlite3
import time

# start 'er up
session_requests = requests.session()

# get credentials from user-supplied file
with open('no_vcs/login_info.txt', 'r') as login_file:
    login_info = login_file.readlines()

login_payload = {"email": login_info[0], "password": login_info[1]}

# login
login_url = "https://unabridged.merriam-webster.com/subscriber/lapi/1/subscriber/identity/login/ue"
login_result = session_requests.post(login_url, data=login_payload)

# generic search, should bring up everything
search_url = 'http://unabridged.merriam-webster.com/unabridged/**'

# open up database
connection = sqlite3.connect('words.db')
cursor = connection.cursor()

# if we've already found some words, pull them out into a set
word_tuple_list = cursor.execute('''SELECT word FROM pureWordsSup;''').fetchall()
word_set = set([i[0] for i in word_tuple_list])

# find the word number we ended on last time TODO change word_num to go with number in dict?
word_nums = [i[0] for i in cursor.execute('''SELECT word_num FROM pureWordsSup;''').fetchall()]
counter = 0 if len(word_nums) == 0 else max(word_nums)

# if the list of words returned is not empty, True
full_word_list = True

while full_word_list:
    # start is the index of the first word on the page
    next_page_payload = {"start": str(counter)}
    res = session_requests.post(search_url, data=next_page_payload)
    tree = html.fromstring(res.content)
    # grab all entries from the html of the page
    word_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
    # print(word_list)
    # grab superscripts from the html of the page
    sup_list = tree.xpath('//li/a/span[@class="entry-text"]/sup/text()')
    # print(sup_list)

    full_word_list = len(word_list) != 0

    # if we didn't find anything
    if not full_word_list:
        exp = 0
        # wait exponentially longer each time we fail to find anything
        while not full_word_list and exp < 7:
            time.sleep(2 ** exp)
            next_page_payload = {"start": str(counter)}
            res = session_requests.post(search_url, data=next_page_payload)
            tree = html.fromstring(res.content)
            word_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
            sup_list = tree.xpath('//li/a/span[@class="entry-text"]/sup/text()')
            exp += 1
            full_word_list = len(word_list) != 0

    # if we still didn't get anything, log in again and retry
    if not full_word_list:
        session_requests = requests.session()
        login_result = session_requests.get(login_url)
        login_result = session_requests.post(login_url, data=login_payload)

        next_page_payload = {"start": str(counter)}
        res = session_requests.post(search_url, data=next_page_payload)
        tree = html.fromstring(res.content)
        word_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
        sup_list = tree.xpath('//li/a/span[@class="entry-text"]/sup/text()')

    # find words that aren't yet in the list
    # TODO can't read as set anymore
    diff = list(set(word_list) - word_set)
    diff.sort()
    # cursor.executemany('''INSERT INTO pureWordsSup (word, superscript) VALUES (?, ?)''', [(i,) for i in ])
    # connection.commit()

    # add those words into the set
    word_set |= set(word_list)

    # MW does about 30 words per page, maybe 31. Some overlap is allowed here.
    counter += 30

    # give us an update
    if counter % 300 == 0:
        print(counter)
    full_word_list = len(word_list) != 0

# wrap things up
connection.close()
