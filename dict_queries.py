"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import sqlite3
import argparse
import os


# looks for an exact match to the word parameter and returns it
def fetch_exact_word(word):
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT * FROM fullWordsEtym WHERE word = (?)''', (word,)).fetchall()

    connection.close()

    return format_tuple_list(word_tuple_list)


# looks for an exact match of a word and a close match to the part of speech
def fetch_word_pos(word, speech_part):
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT * FROM fullWordsEtym WHERE word = (?) AND part LIKE (?)''',
                                     (word, speech_part + "%")).fetchall()

    connection.close()

    return format_tuple_list(word_tuple_list)


# gets all words marked as new and prints them to a text file
def fetch_new_words():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT (word) FROM fullWordsEtym WHERE new = ?''', (True,)).fetchall()

    connection.close()

    if word_tuple_list:
        with open('results/new.txt', 'wb') as new_file:
            for word_tuple in word_tuple_list:
                new_file.write((word_tuple[0] + os.linesep).encode('utf-8'))


# gets all words marked as revised and prints them to a text file
def fetch_revised_words():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT (word) FROM fullWordsEtym WHERE revised = ?''', (True,)).fetchall()

    connection.close()

    if word_tuple_list:
        with open('results/revised.txt', 'wb') as revised_file:
            for word_tuple in word_tuple_list:
                revised_file.write((word_tuple[0] + os.linesep).encode('utf-8'))


# takes the return from the database and formats it nicely, currently ignoring language information
def format_tuple_list(word_tuple_list):
    if not word_tuple_list:
        return None

    word_string = ''

    for tup in word_tuple_list:
        # skip id
        word_string += 'Word: ' + tup[1] + '\n'
        if tup[2] != '':
            word_string += '# Syllables: ' + tup[2] + '\n'
        if tup[3]
            word_string += 'Part of speech: ' + tup[3] + '\n'
        if tup[4] != '':
            word_string += 'Alternate spelling: ' + tup[4] + '\n'
        if tup[5] != '[]':
            word_string += 'Bolded words in entry: ' + tup[5] + '\n'
        if tup[6] != '':
            word_string += 'Etymology section: ' + tup[6] + '\n'
        if tup[135] != '':
            word_string += 'Pronunciation: ' + tup[135] + '\n'
        if tup[136] != '':
            word_string += 'Definition: ' + tup[136] + '\n'

    return word_string


def get_column_list():
    first_chunk = ['Word #', 'Word', '# Syllables', 'Part of Speech', 'Alt Spelling', 'Bold List', 'Etymology']
    third_chunk = ['Revised', 'New', 'Pronunciation', 'Definition']
    with open('languages.txt', 'r') as lang_file:
        second_chunk = [i.strip() for i in lang_file]
    return first_chunk + second_chunk + third_chunk


def format_pandas(word_list):
    import pandas as pd
    dframe = pd.DataFrame(word_list, columns=get_column_list())
    return dframe


def write_to_excel(dframe):
    dframe.to_excel('full_sheet.xlsx')


def db_to_excel():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    full_word_list = cursor.execute('''SELECT * FROM fullWordsEtym''').fetchall()

    connection.close()

    dframe = format_pandas(full_word_list)

    write_to_excel(dframe)


# CLI information for actually running the program
def parse_cla():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word", help="input word to look up")
    parser.add_argument("--part", help="part of speech")
    parser.add_argument("--new", help="output all words with new icon", action="store_true")
    parser.add_argument("--revised", help="output all words with revised icon", action="store_true")
    parser.add_argument("--excel", help="convert current database to excel spreadsheet", action="store_true")
    args = parser.parse_args()

    if args.excel:
        db_to_excel()

    if args.word:
        # if a part of speech was given, use it
        if args.part:
            word_string = fetch_word_pos(args.word, args.part)
        else:
            word_string = fetch_exact_word(args.word)

        if word_string is None:
            # TODO should try to run approx query
            print('None')
        else:
            print(word_string)
    else:
        if args.new:
            fetch_new_words()
        if args.revised:
            fetch_revised_words()


if __name__ == '__main__':
    parse_cla()
