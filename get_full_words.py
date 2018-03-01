"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import requests
from lxml import html
import sqlite3
import string
from time import sleep

session_requests = requests.session()

# get login info
with open('no_vcs/login_info.txt', 'r') as login_file:
    login_info = login_file.readlines()

# create payload and log in
login_payload = {"email": login_info[0].strip(), "password": login_info[1].strip()}
login_url = "https://unabridged.merriam-webster.com/subscriber/lapi/1/subscriber/identity/login/ue"
login_result = session_requests.post(login_url, data=login_payload)

# get list of languages from etymology search
with open('languages.txt', 'r') as lang_file:
    language_list = [i.strip() for i in lang_file]
language_set = set(language_list)

connection = sqlite3.connect('words.db')
cursor = connection.cursor()

# pull in all pure word information so that we have something to search from
pure_word_list_tuples = cursor.execute('''SELECT word FROM pureWords''').fetchall()
pure_word_list = [i[0] for i in pure_word_list_tuples]

# where are we in the pure_place list?
pure_place_tuple = cursor.execute('''SELECT pure_place FROM placeholder''').fetchone()
pure_place = int(pure_place_tuple[0])

# go through every word in the list
for search_word in pure_word_list[pure_place:]:

    # useful later for case-sensitive comparison
    sw_caps = search_word.upper()

    # get entries from an individual page
    word_url = 'http://unabridged.merriam-webster.com/unabridged/' + search_word
    res = session_requests.post(word_url)
    tree = html.fromstring(res.content)
    page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')

    # useful state variables
    start = 0
    show = 0
    first_time = True
    first_non_match = True

    # TODO need to test capitalization
    while True:
        # get the page for an individual word
        word_page_payload = {"start": str(start), "show": str(show)}
        res = session_requests.post(word_url, data=word_page_payload)
        tree = html.fromstring(res.content)
        # look at page of entries, capitalize all of them
        page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
        page_list = list(map(lambda x: x.upper(), page_list))
        # if current search word is in these entries
        if sw_caps in page_list[show:]:
            # find placement of search word, navigate to its full entry
            short_list = page_list[show:]
            which = short_list.index(sw_caps) + show
            word_page_payload = {"start": str(start), "show": str(which + start)}
            res = session_requests.post(word_url, data=word_page_payload)
            tree = html.fromstring(res.content)
            page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
            page_list = list(map(lambda x: x.upper(), page_list))

            # get part of speech information
            speech_part_list = tree.xpath('//div[@class="fl"]/text()')
            speech_part = speech_part_list[0] if len(speech_part_list) > 0 else ''

            # alternate spelling information
            spelling_list = tree.xpath('//div[@class="section variants"]/strong/text()')
            alt_spelling = spelling_list[0] if len(spelling_list) > 0 else ''

            # a list of bolded words in the definition
            bold_list = tree.xpath('//div[@data-id="definition"]//strong/text()')
            bold_list = str(list(set(bold_list) - set(':')))

            # the full text of the word's etymology section
            etymology_list = tree.xpath('//div[@class="section-content etymology"]//text()')
            etym_word_list = []

            # clean this etymology section up
            punc_str = ''
            for p in string.punctuation:
                punc_str += p
            trans_table = str.maketrans('', '', punc_str)

            for e in etymology_list:
                etym_word_list += e.strip().translate(trans_table).split()
            etymology = ' '.join(etymology_list).strip()

            # find all language words in the etymology section and save them
            languages = set(etym_word_list) & language_set
            lang_vector = [False for i in range(len(language_list))]
            for lang in languages:
                lang_vector[language_list.index(lang)] = True

            # whether the revised icon is present in a given entry
            revised_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-full.jpg"]')
            # whether the new icon is present in a given entry
            new_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-new.jpg"]')

            # list of pronunciation information
            pron_list = tree.xpath('//div[@class="pron"]//text()')
            pron = ''.join(pron_list)

            # full definition text
            def_list = tree.xpath('//div[@data-id="definition"]//text()')
            def_list = [s for s in def_list]
            old_def = ''.join(def_list).strip()
            definition = old_def.replace(':\xa0 ', '')

            # put these all together and insert them into the db
            part_list = [search_word, speech_part, alt_spelling, bold_list, etymology] + lang_vector + \
                        [len(revised_img_lst) > 0, len(new_img_lst) > 0, pron, definition]
            part_tuple = tuple(part_list)
            insert_1 = '''INSERT INTO fullWordsEtym (word, part, alt_spelling, bold_list, etymology, '''
            lang_list_str = ', '.join(language_list) + ', '
            insert_2 = lang_list_str.replace('-', '_')
            insert_3 = '''revised, new, pronounce, definition) VALUES (?, ?, ?, ?, ?, '''
            insert_4 = '''?, ''' * len(language_list)
            insert_5 = '''?, ?, ?, ?)'''
            cursor.execute(insert_1 + insert_2 + insert_3 + insert_4 + insert_5, part_tuple)
            connection.commit()

            show = which + 1
            first_time = False
        # if we can't find the word in these entries
        elif first_non_match:
            # try checking the next page
            start += 10
            show = 0
            next_page_payload = {"start": str(start), "show": str(show)}
            res = session_requests.post(word_url, data=next_page_payload)
            tree = html.fromstring(res.content)
            page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
            page_list = list(map(lambda x: x.upper(), page_list))
            # if entry list is empty
            if len(page_list) == 0:
                # try logging in again
                session_requests = requests.session()
                try:
                    result = session_requests.get(login_url)
                except requests.exceptions.ConnectionError:
                    print('got error on: ' + search_word)
                    sleep(5)
                finally:
                    # print('inner3')
                    result2 = session_requests.post(login_url, data=login_payload)

                    # if we log in fine, try searching for the word again
                    next_page_payload = {"start": str(start), "show": str(show)}
                    res = session_requests.post(word_url, data=next_page_payload)
                    tree = html.fromstring(res.content)
                    page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
                    page_list = list(map(lambda x: x.upper(), page_list))
                    # if the entry list is still empty, give up
                    if len(page_list) == 0:
                        if first_time:
                            # TODO save these
                            print('Couldn\'t find word: ' + search_word)
                        break
            first_non_match = False
        # else (meaning we can't find the word and we're on the second or more pages of entries
        else:
            if first_time:
                print('Couldn\'t find word: ' + search_word)
            break

    # update position in pure list
    pure_place += 1
    cursor.execute('''UPDATE placeholder SET pure_place = (?)''', (pure_place,))
    connection.commit()

    if pure_place % 100 == 0:
        print(pure_place)


connection.close()
