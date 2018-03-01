"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import sqlite3
import argparse


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


def fetch_new_words():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT (word) FROM fullWordsEtym WHERE new = True''').fetchall()

    connection.close()

    return format_tuple_list(word_tuple_list)

def fetch_revised_words():
    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    word_tuple_list = cursor.execute('''SELECT (word) FROM fullWordsEtym WHERE revised = True''').fetchall()

    connection.close()

    return format_tuple_list(word_tuple_list)


# takes the return from the database and formats it nicely, currently ignoring language information
def format_tuple_list(word_tuple_list):
    if not word_tuple_list:
        return None

    word_string = ''

    for tup in word_tuple_list:
        # skip id
        word_string += 'Word: ' + tup[1] + '\n'
        if tup[2] != '':
            word_string += 'Part of speech: ' + tup[2] + '\n'
        if tup[3] != '':
            word_string += 'Alternate spelling: ' + tup[3] + '\n'
        if tup[4] != '[]':
            word_string += 'Bolded words in entry: ' + tup[4] + '\n'
        if tup[5] != '':
            word_string += 'Etymology section: ' + tup[5] + '\n'
        if tup[134] != '':
            word_string += 'Pronunciation: ' + tup[134] + '\n'
        if tup[135] != '':
            word_string += 'Definition: ' + tup[135] + '\n'

    return word_string


# CLI information for actually running the program
def parse_cla():
    parser = argparse.ArgumentParser()
    parser.add_argument("--word", help="input word to look up")
    parser.add_argument("--part", help="part of speech")
    parser.add_argument("--new", help="output all words with new icon", action="store_true")
    parser.add_argument("--revised", help="output all words with revised icon", action="store_true")
    args = parser.parse_args()

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
