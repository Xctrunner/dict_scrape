"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import requests
from lxml import html
from lxml.etree import tostring
import sqlite3
import string
from time import sleep
import csv

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
language_overlap_dict = {}
for i in range(len(language_list)):
    for j in range(len(language_list)):
        if i != j:
            if language_list[i] in language_list[j]:
                if language_list[i] not in language_overlap_dict:
                    language_overlap_dict[language_list[i]] = [language_list[j]]
                else:
                    language_overlap_dict[language_list[i]].append(language_list[j])


connection = sqlite3.connect('words.db')
cursor = connection.cursor()

# pull in all pure word information so that we have something to search from
pure_word_list_tuples = cursor.execute('''SELECT word FROM pureWords''').fetchall()
pure_word_list = [i[0] for i in pure_word_list_tuples]

# where are we in the pure_place list?
pure_place_tuple = cursor.execute('''SELECT pure_place FROM placeholder''').fetchone()
pure_place = int(pure_place_tuple[0])

spelling_matrix = []
formula_spelling_dict = {}
pron_character_list = []
with open('formula_spelling.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        spelling_matrix.append(row[0])
for i in range(len(spelling_matrix)):
    spelling_matrix[i] = spelling_matrix[i].split(',')
    if i != 0:
        pron_character_list.append(spelling_matrix[i][0])
formula_language_list = spelling_matrix[0][1:]
for i in range(len(formula_language_list)):
    specific_lang_dict = {}
    for j in range(len(spelling_matrix) - 1):
        specific_lang_dict[spelling_matrix[j + 1][0]] = spelling_matrix[j + 1][i + 1]
    formula_spelling_dict[formula_language_list[i]] = specific_lang_dict

root_prefixes = []
root_suffixes = []
root_flex = []
with open('roots.txt', 'r') as rootfile:
    roots = rootfile.readlines()
    for root in roots:
        root = root.strip()
        if root[-1] == '-':
            root_prefixes.append(root[:-1])
        elif root[0] == '-':
            root_suffixes.append(root[1:])
        else:
            root_flex.append(root)


def is_root_word(word):
    for prefix in root_prefixes:
        if word == prefix:
            return True
        elif word.startswith(prefix):
            if is_root_word_no_prefixes(word[len(prefix):]):
                return True
    return is_root_word_no_prefixes(word)


def is_root_word_no_prefixes(word):
    if word in root_suffixes:
        return True
    for root in root_flex:
        if word == root:
            return True
        elif word.startswith(root):
            return is_root_word_no_prefixes(word[len(root):])
    return False



# go through every word in the list
for search_word in pure_word_list[pure_place:]:
# for search_word in ['apple', 'banana', 'currant', 'durian']:
# for search_word in ['run']:
# for search_word in ['cardinal']:
# for search_word in ['emancipist']:
# for search_word in ['aeonian']:
# for search_word in ['cerebrum']:
# for search_word in ['Umayyad']:
# for search_word in ['froufrou']:
# for search_word in ['vernissage']:
# for search_word in ['queen']:

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

            # get syllable number
            header_list = tree.xpath('//div[@class="hdword"]/text()')
            syllable_count = sum([1 if x == '·' else 0 for x in header_list[0]]) + 1

            # get part of speech information
            speech_part_list = tree.xpath('//div[@class="fl"]/text()')
            speech_part = speech_part_list[0] if len(speech_part_list) > 0 else ''
            speech_part_extra_list = tree.xpath('//div[@class="fl-xtra"]/text()')
            speech_part += ' ' + speech_part_extra_list[0] if len(speech_part_extra_list) > 0 else ''

            # alternate spelling information
            spelling_list = tree.xpath('//div[@class="section variants"]/strong/text()')
            alt_spelling = ', '.join(spelling_list) if len(spelling_list) > 0 else ''
            alt_spelling = alt_spelling.replace('·', '')

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
            etymology = ''.join(etymology_list).strip()

            etym_italics_list = tree.xpath('//div[@class="section-content etymology"]//em[not(@class)]//text()')
            etym_italics_list = [s for s in etym_italics_list]
            italics_etymology = '\n'.join(etym_italics_list)
            italics_etymology = italics_etymology.replace('\xa0', '')

            # find all language words in the etymology section and save them
            languages_of_origin = ''
            languages_present = {}
            for lang in language_list:
                index = etymology.find(lang)
                if index != -1:
                    languages_present[lang] = index
            present_lang_list = list(languages_present.keys())
            for lang in present_lang_list:
                if lang in language_overlap_dict.keys():
                    potential_overlaps = language_overlap_dict[lang]
                    is_overlap = False
                    for pot in potential_overlaps:
                        if pot in languages_present and languages_present[lang] == languages_present[pot] + pot.find(lang):
                            is_overlap = True
                    while is_overlap:
                        index = etymology.find(lang, languages_present[lang] + 1)
                        if index != -1:
                            languages_present[lang] = index
                            no_overlap = True
                            for pot in potential_overlaps:
                                if pot in languages_present and languages_present[lang] == languages_present[pot] + pot.find(lang):
                                    no_overlap = False
                            if no_overlap:
                                is_overlap = False
                        else:
                            languages_present.pop(lang)
                            break

            # for key in language_overlap_dict.keys():
            #     if key in languages_present:
            #         for long_word in language_overlap_dict[key]:
            #             short_word_index = languages_present[short_word]
            #             if short_word_index == languages_present[key] + key.find(short_word):
            #                 # TODO do this properly, probably inverting overlap dict, so we are sure it's unique
            #                 index = etymology.find(short_word, short_word_index + 1)
            #                 if index != -1:
            #                     languages_present[short_word] = index
            #                 else:
            #                     languages_present.pop(short_word)
            languages_present = [(lang, languages_present[lang]) for lang in languages_present.keys()]
            languages_of_origin = list(map(lambda x: x[0], sorted(languages_present, key=lambda y: y[1])))
            main_language = languages_of_origin[0]
            languages_of_origin = ', '.join(languages_of_origin)
            print(languages_of_origin)

            # whether the revised icon is present in a given entry
            revised_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-full.jpg"]')
            # whether the new icon is present in a given entry
            new_img_lst = tree.xpath('//img[@src="/skins/default/_assets/img/mw/update-new.jpg"]')

            # list of pronunciation information
            pron_list = tree.xpath('//div[@class="pron"]//text()')
            pron = ''.join(pron_list).strip().split(' \\')[0]
            pron = pron.replace(', ', '\\ \\')
            pron_list = pron.split(' ')
            final_pron_list = []
            for pr in pron_list:
                if '(' in pr:
                    final_pron_list.append(pr.replace('(', '').replace(')', ''))
                    final_pron_list.append(pr[:pr.find('(')] + pr[pr.find(')') + 1:])
                else:
                    final_pron_list.append(pr)
            pron = '\n'.join(final_pron_list)

            # formula spelling
            main_pronunciation = final_pron_list[0].strip('\\')
            formula_spelling = ''
            skip_next = False
            first_part = True
            for i in range(len(main_pronunciation)):
                if skip_next:
                    skip_next = False
                    continue
                char = main_pronunciation[i]
                if main_pronunciation[i:i+2] in pron_character_list:
                    char = main_pronunciation[i:i+2]
                    skip_next = True
                if char in ['\'', '-', 'ˈ', 'ˌ', '¦']:
                    continue

                # TODO handle superscript n
                if main_language in formula_spelling_dict.keys():
                    main_language_key = main_language
                else:
                    main_language_key = 'English'
                formula_part = formula_spelling_dict[main_language_key][char]
                if '/' in formula_part:
                    formula_pieces = formula_part.split('/')
                    if first_part:
                        formula_part = formula_pieces[0]
                    elif i == len(main_pronunciation) - 1 or (main_pronunciation[-2:] in pron_character_list and i == len(main_pronunciation) - 2):
                        formula_part = formula_pieces[2]
                    else:
                        formula_part = formula_pieces[1]
                first_part = False
                formula_spelling += formula_part


            # formulaic
            formulaic = formula_spelling == search_word


            # root word
            is_root = is_root_word(search_word)


            # full definition text
            def_list = tree.xpath('//div[@data-id="definition"]//text()')
            def_list = [s for s in def_list]
            definition = ''.join(def_list)
            definition = definition.replace('\xa0', '')

            def_italics_list = tree.xpath('//div[@data-id="definition"]//em[not(@class)]//text()')
            def_italics_list = [s for s in def_italics_list if s not in ['or', 'also', 'plural']]
            italics_definition = '\n'.join(def_italics_list)
            italics_definition = italics_definition.replace('\xa0', '')

            # put these all together and insert them into the db
            part_list = [search_word, syllable_count, speech_part, alt_spelling, bold_list, italics_definition] +\
                        [italics_etymology, etymology, main_language, languages_of_origin, len(revised_img_lst) > 0] +\
                        [len(new_img_lst) > 0, pron, formula_spelling, formulaic, is_root, definition]
            part_tuple = tuple(part_list)
            insert_string = 'INSERT INTO fullWordsEtym (word, syllables, part, alt_spelling, bold_list,' +\
                          'italics_def_list, italics_etym_list, etymology, main_language, origin_langs, revised, new, ' +\
                          'pronounce, formula, formulaic, is_root, definition) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ' +\
                          '?, ?, ?, ?)'
            cursor.execute(insert_string, part_tuple)
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
