"""
Work of Walter Martin (owner), 2018.
May be used commercially with permission of owner.
May not be distributed or modified without explicit permission of owner.
"""

import sqlite3
import argparse


# table for words pulled directly from the ** search
def create_pure():

    create_pure_table = \
        """
        CREATE TABLE IF NOT EXISTS pureWords (
        word_num INTEGER PRIMARY KEY,
        word VARCHAR(100));
        """

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute(create_pure_table)
    connection.close()


def create_pure_sup():

    create_pure_table = \
        """
        CREATE TABLE IF NOT EXISTS pureWordsSup (
        word_num INTEGER PRIMARY KEY,
        superscript INTEGER,
        word VARCHAR(100));
        """

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute(create_pure_table)
    connection.close()


# table with full information about each word
def create_full():

    create_full_table_1 = \
        """
        CREATE TABLE IF NOT EXISTS fullWordsEtym (
        word_num INTEGER PRIMARY KEY,
        word VARCHAR(100),
        part VARCHAR(50),
        alt_spelling VARCHAR(100),
        bold_list VARCHAR(500),
        etymology VARCHAR(1000),
        """

    create_full_table_2 = ''
    with open('languages.txt', 'r') as f:
        for line in f.readlines():
            line = line.strip().lower()
            line = line.replace('-', '_')
            create_full_table_2 += line + ' BOOL,\n'
    print(create_full_table_2)

    create_full_table_3 = \
        """
        revised BOOL,
        new BOOL,
        pronounce VARCHAR(100),
        definition VARCHAR(1000) );
        """

    create_full_table = create_full_table_1 + create_full_table_2 + create_full_table_3

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute(create_full_table)
    connection.close()


# table holding index of current search through pureWords
def create_placeholder():

    create_placeholder_table = \
        """
        CREATE TABLE IF NOT EXISTS placeholder (
        ind INTEGER PRIMARY KEY,
        pure_place INTEGER,
        full_place INTEGER );
        """

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()
    cursor.execute(create_placeholder_table)
    connection.close()


# reset the placeholder in pureWords
def reset_placeholder():

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    cursor.execute('''UPDATE placeholder SET pure_place = 0;''')

    connection.commit()
    connection.close()


# cleans out the pure word table to run from the beginning and resets placeholder
def empty_pure():

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    cursor.execute('''DELETE FROM pureWords;''')
    cursor.execute('''UPDATE placeholder SET pure_place = 0;''')

    connection.commit()
    connection.close()


# cleans out the pure word table to run from the beginning and resets placeholder
def empty_full():

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    # TODO change to fullWords
    cursor.execute('''DELETE FROM fullWordsEtym;''')

    connection.commit()
    connection.close()


# deletes full_words table
def del_full():

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    cursor.execute('''DROP TABLE fullWords''')

    connection.commit()
    connection.close()


def del_full_etym():

    connection = sqlite3.connect('words.db')
    cursor = connection.cursor()

    cursor.execute('''DROP TABLE fullWordsEtym''')

    connection.commit()
    connection.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--fullClear", help="input word to look up", action="store_true")
    args = parser.parse_args()

    if args.fullClear:
        empty_full()
        reset_placeholder()
