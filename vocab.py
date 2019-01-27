from random import shuffle
from getch import getch
import sys


def parse_file_for_vocab(filename):
    file = open(filename, 'r')
    lines = file.readlines()
    word_list = []
    for line in lines:
        if len(line) > 1:
            word = []
            parts = line[0:-1].split(' - ') # split by dash, ignore last \n char
            word.append(parts[0].strip(' '))
            word.append(('-'.join(parts[1:len(parts)])).strip(' ')) # account for later dashes
            word_list.append(word)
    return word_list

def get_yesno(prompt):
    answered = False
    ans_list = ['n','y']
    sys.stdout.write(prompt + ' (y/n) ')
    while not answered:
        trial_ans = getch()
        try:
            ans_ind = ans_list.index(trial_ans.lower())
            return ans_list[ans_ind]
        except ValueError:
            pass

def main():
    unit = input('Unit Number: ')
    lecture = input('Lecture Number: ')
    part = raw_input('Lecture Section (if applicable): ')

    filename = 'VocabTxt{}/lec{}_{}{}vocab.txt'.format(unit, unit, lecture, part)

    try:
        f = open(filename, 'r')
        f.close()
    except IOError:
        print('Specified text file does not exist.')
        return

    words = parse_file_for_vocab(filename)
    Nwords = len(words)

    shuffle(words)

    # test the user on the words
    incorrect = []

    for i in range(Nwords):
        sys.stdout.write(words[i][0] + ' ({}/{})'.format(i+1,Nwords))
        ch = getch()
        sys.stdout.write('\n' + words[i][1] + '\n')
        ans = get_yesno('Correct?')
        sys.stdout.write('\n\n')
        if not ['n','y'].index(ans): # i.e. incorrect
            incorrect.append(words[i])

    for word in incorrect:
        sys.stdout.write(word[0] + ': ' + word[1] + '\n')

if __name__ == '__main__':
    main()
