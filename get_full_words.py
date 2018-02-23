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

# TODO comment this
session_requests = requests.session()

with open('no_vcs/login_info.txt', 'r') as login_file:
    login_info = login_file.readlines()

# TODO make this input by user
login_payload = {"email": login_info[0].strip(), "password": login_info[1].strip()}

login_url = "https://unabridged.merriam-webster.com/subscriber/lapi/1/subscriber/identity/login/ue"
login_result = session_requests.post(login_url, data=login_payload)

with open('languages.txt', 'r') as lang_file:
    language_list = [i.strip() for i in lang_file]
language_set = set(language_list)

connection = sqlite3.connect('words.db')
cursor = connection.cursor()

pure_word_list_tuples = cursor.execute('''SELECT word FROM pureWords''').fetchall()
pure_word_list = [i[0] for i in pure_word_list_tuples]

pure_place_tuple = cursor.execute('''SELECT pure_place FROM placeholder''').fetchone()
pure_place = int(pure_place_tuple[0])

for search_word in pure_word_list[pure_place:]:

    sw_caps = search_word.upper()

    word_url = 'http://unabridged.merriam-webster.com/unabridged/' + search_word

    res = session_requests.post(word_url)
    tree = html.fromstring(res.content)
    page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')

    start = 0
    show = 0
    first_time = True
    first_non_match = True

    # TODO need to test capitalization
    while True:
        word_page_payload = {"start": str(start), "show": str(show)}
        res = session_requests.post(word_url, data=word_page_payload)
        tree = html.fromstring(res.content)
        page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
        page_list = list(map(lambda x: x.upper(), page_list))
        if sw_caps in page_list[show:]:
            short_list = page_list[show:]
            which = short_list.index(sw_caps) + show
            word_page_payload = {"start": str(start), "show": str(which + start)}
            res = session_requests.post(word_url, data=word_page_payload)
            tree = html.fromstring(res.content)
            page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
            page_list = list(map(lambda x: x.upper(), page_list))

            speech_part_list = tree.xpath('//div[@class="fl"]/text()')
            speech_part = speech_part_list[0] if len(speech_part_list) > 0 else ''

            spelling_list = tree.xpath('//div[@class="section variants"]/strong/text()')
            alt_spelling = spelling_list[0] if len(spelling_list) > 0 else ''

            bold_list = tree.xpath('//div[@data-id="definition"]//strong/text()')
            bold_list = str(list(set(bold_list) - set(':')))

            etymology_list = tree.xpath('//div[@class="section-content etymology"]//text()')
            etym_word_list = []

            punc_str = ''
            for p in string.punctuation:
                punc_str += p
            trans_table = str.maketrans('', '', punc_str)

            for e in etymology_list:
                etym_word_list += e.strip().translate(trans_table).split()
            etymology = ' '.join(etymology_list).strip()

            languages = set(etym_word_list) & language_set
            lang_vector = [False for i in range(len(language_list))]
            for lang in languages:
                lang_vector[language_list.index(lang)] = True

            revised_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-full.jpg"]')
            new_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-new.jpg"]')

            pron_list = tree.xpath('//div[@class="pron"]//text()')
            pron = ''.join(pron_list)

            def_list = tree.xpath('//div[@data-id="definition"]//text()')
            def_list = [s for s in def_list]
            old_def = ''.join(def_list).strip()
            definition = old_def.replace(':\xa0 ', '')

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
        elif first_non_match:
            start += 10
            show = 0
            next_page_payload = {"start": str(start), "show": str(show)}
            res = session_requests.post(word_url, data=next_page_payload)
            tree = html.fromstring(res.content)
            page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
            page_list = list(map(lambda x: x.upper(), page_list))
            if len(page_list) == 0:
                session_requests = requests.session()
                try:
                    result = session_requests.get(login_url)
                except requests.exceptions.ConnectionError:
                    print('got error on: ' + search_word)
                    time.sleep(5)
                finally:
                    # print('inner3')
                    result2 = session_requests.post(login_url, data=login_payload)

                    next_page_payload = {"start": str(start), "show": str(show)}
                    res = session_requests.post(word_url, data=next_page_payload)
                    tree = html.fromstring(res.content)
                    page_list = tree.xpath('//li/a/span[@class="entry-text"]/text()')
                    page_list = list(map(lambda x: x.upper(), page_list))
                    if len(page_list) == 0:
                        if first_time:
                            # TODO save these
                            print('Couldn\'t find word: ' + search_word)
                        break
            first_non_match = False
        else:
            if first_time:
                print('Couldn\'t find word: ' + search_word)
            break

    pure_place += 1
    cursor.execute('''UPDATE placeholder SET pure_place = (?)''', (pure_place,))
    connection.commit()

    if pure_place % 100 == 0:
        print(pure_place)


connection.close()
