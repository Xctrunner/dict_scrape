import sqlite3

connection = sqlite3.connect('words.db')
cursor = connection.cursor()

etym_list_tuples = cursor.execute('''SELECT etymology FROM fullWords''').fetchall()
etym_list = [str(i[0]) + '\n' for i in etym_list_tuples]

word_dict = {}
for et in etym_list:
    et_list = et.split()
    for e in et_list:
        if e[0].isupper():
            if e in word_dict:
                word_dict[e] += 1
            else:
                word_dict[e] = 1

count_max = 0
for w in word_dict:
    count_max = max(count_max, word_dict[w])

print(count_max)
count_list = [[] for _ in range(count_max + 1)]
for w in word_dict:
    count_list[word_dict[w]].append(w)

count_list.reverse()
count_str_list = [str(i) + '\n' for i in count_list]
print(len(count_str_list))
full_list = [i for i in count_str_list if len(i) > 3]
print(len(full_list))
smaller_list = full_list[:-3]

with open('common_words.txt', 'w') as f:
    f.writelines(smaller_list)
