from __future__ import division
from math import *
import sys, os
import pickle
from random import shuffle
import time
from PyQt5 import QtCore, QtWidgets, uic
from get_files import get_file_list
from time import strftime

REPEAT = u'\u21BA'
CHECK = u'\u2713'
XMARK = 'X'

def parse_file_for_vocab(filename, delimiter='-'):
    file = open(filename, 'r')
    lines = file.readlines()
    word_list = []
    for line in lines:
        if len(line) > 1:
            word = []
            parts = line[0:-1].split(' ' + delimiter + ' ') # split by dash, ignore last \n char
            word.append(parts[0].strip(' '))
            word.append(('-'.join(parts[1:len(parts)])).strip(' ')) # account for later dashes
            word_list.append(word)
    return word_list

def delete_message(deck_name):
    s = 'Are you sure you want to delete "{}"?\n(Original text file will not be touched.)'.format(deck_name)
    return s

def resource_file(filename):
    filedir = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(filedir, filename)
    return p

class ImageDialog(QtWidgets.QMainWindow):

    # ---------- init function ----------

    def __init__(self):
        QtWidgets.QDialog.__init__(self)

        # get ui
        self.ui = uic.loadUi(resource_file('flashcards.ui'))
        self.resource_dir = resource_file('.')
        self.default_dir = os.path.expanduser('~')
        self.loaded_decks = {}
        self.loaded_deck_files = {}
        self.staged_deck_name = None
        self.testing_deck_name = None
        self.prompt_word = True
        self.repeat_until_done = True
        self.randomize = True
        self.test_in_progress = False
        self.ui.resumeButton.setEnabled(False)
        self.word_index = 0
        self.remaining_words = []

        self.load_timer()
        self.load_naming_ui()
        self.load_confirm_ui()
        # self.load_resume_ui()
        self.load_message_ui()
        self.ready_ui()


    # ---------- gui preparation (and start) function ----------

    def ready_ui(self):
        self.ui.setWindowTitle('Flash')
        self.connect_buttons()
        self.ui.delimTextEdit.setText('-')
        self.get_saved_decks()
        self.evaluate_randomize()
        self.evaluate_repetition()

        self.ui.actionQuit.triggered.connect(self.warn_before_quitting)
        self.ui.actionLoad.triggered.connect(self.get_deck_txt_file)
        self.ui.actionStart.triggered.connect(self.start_testing)
        # when everything is ready
        self.ui.mainStack.setCurrentIndex(0)
        self.ui.show()
        self.ui.raise_()
        return

    # ---------- auxiliary prep functions ----------

    def connect_buttons(self):


        self.ui.startButton.clicked.connect(self.start_testing)
        self.ui.resumeButton.clicked.connect(self.resume_testing)
        self.ui.backButton.clicked.connect(self.back_to_load)
        self.ui.flipButton.clicked.connect(self.flip_card)
        self.ui.importButton.clicked.connect(self.get_deck_txt_file)
        self.ui.renameButton.clicked.connect(self.rename_current_deck)
        self.ui.deleteButton.clicked.connect(self.delete_deck_function)
        self.ui.stageButton.clicked.connect(self.stage_current_deck)
        self.ui.randomCheckBox.clicked.connect(self.evaluate_randomize)
        self.ui.onceButton.clicked.connect(self.evaluate_repetition)
        self.ui.untilDoneButton.clicked.connect(self.evaluate_repetition)
        self.ui.promptWord.clicked.connect(self.evaluate_prompt)
        self.ui.promptDef.clicked.connect(self.evaluate_prompt)
        self.ui.correctButton.clicked.connect(lambda: self.next_word(True))
        self.ui.incorrectButton.clicked.connect(lambda: self.next_word(False))
        return

    def evaluate_prompt(self):
        self.prompt_word = self.ui.promptWord.isChecked()
        return

    def evaluate_repetition(self):
        self.repeat_until_done = self.ui.untilDoneButton.isChecked()
        if self.ui.untilDoneButton.isChecked():
            self.ui.incorrectButton.setText(REPEAT)
            self.ui.incorrectButton.setStyleSheet('QPushButton {color: rgb(0, 0, 255); font: bold 30pt "Meiryo";}')
        else:
            self.ui.incorrectButton.setText(XMARK)
            self.ui.incorrectButton.setStyleSheet('QPushButton {color: rgb(255, 0, 0); font: bold 24pt "Palatino Linotype";}')
        return

    def evaluate_randomize(self):
        self.randomize = self.ui.randomCheckBox.isChecked()
        return

    def load_timer(self):
        self.test_timer = QtCore.QTimer()
        self.ui.timer.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self.sec_elapsed = 0
        self.display_time()
        self.test_timer.timeout.connect(self.update_timer)
        return

    def load_naming_ui(self):
        self.naming_ui = uic.loadUi(resource_file('namemsgbox.ui'))
        self.naming_ui.setWindowTitle('Name Deck')
        self.naming_ui.buttonDialog.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        return

    def load_command_ui(self):
        self.command_ui = uic.loadUi(resource_file('command.ui'))
        self.command_ui.setWindowTitle('Command')
        self.command_ui.go.clicked.connect(self.run_command)
        self.command_ui.buttonDialog.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        return

    def run_command(self):
        cmdstr = str(self.command_ui.command.toPlainText())
        eval(cmdstr)
        return

    def load_confirm_ui(self):
        self.confirm_ui = uic.loadUi(resource_file('confirmdelete.ui'))
        self.confirm_ui.setWindowTitle('Confirm Delete')
        self.confirm_ui.buttonDialog.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        return

    # def load_resume_ui(self):
    #     self.resume_ui = uic.loadUi(resource_file('resumerestart.ui'))
    #     self.resume_ui.setWindowTitle('Test in Progress!')
    #     self.resume_ui.cancel.clicked.connect(lambda: self.resume_ui.done(-1))
    #     self.resume_ui.resume.clicked.connect(lambda: self.resume_ui.done(0))
    #     self.resume_ui.restart.clicked.connect(lambda: self.resume_ui.done(1))
    #     return

    def load_message_ui(self):
        self.message_ui = uic.loadUi(resource_file('message.ui'))
        self.message_ui.setWindowTitle('Alert')
        self.message_ui.okButton.clicked.connect(lambda: self.message_ui.close())
        return

    # ---------- user input functions ----------

    def get_deck_name(self):
        self.naming_ui.nameTextEdit.setPlainText('')
        retval = self.naming_ui.exec_()
        entered_name = str(self.naming_ui.nameTextEdit.toPlainText())
        self.naming_ui.nameTextEdit.setPlainText('')
        if (retval == 1):
            return entered_name
        else:
            return ''

    def show_message(self, message):
        self.message_ui.messageLabel.setText(message)
        retval = self.message_ui.exec_()
        return retval

    def warn_before_quitting(self):
        self.confirm_ui.setWindowTitle('Confirm Quit')
        self.confirm_ui.messageLabel.setText('Are you sure you want to quit?')     
        retval = self.confirm_ui.exec_()
        if (retval == 1):
            sys.exit()
        else:
            self.confirm_ui.setWindowTitle('Confirm Delete')


    # ---------- active functions ----------

    def get_deck_txt_file(self):
        delim = str(self.ui.delimTextEdit.toPlainText())
        delim = delim.strip(' ')
        
        if len(delim) == 0:
            r = self.show_message('No text file delimiter specified.')
            return
        else:
            d = QtWidgets.QFileDialog
            filename, _ = d.getOpenFileName(self, 'Open text file', self.default_dir, 'Text Files (*.txt)')
            # print(filename)
            if len(filename) > 0:
                words = parse_file_for_vocab(filename, delim)
                if len(words) > 0:
                    # print('filename', filename)
                    self.default_dir = os.path.dirname(os.path.abspath(filename))
                    name = self.get_deck_name()
                    if len(name) > 0:
                        datafilename = 'flashcards_' + name + '_' + time.strftime('%Y%m%d_%H%M%S') + '.deck'
                        deckdata = [name, words]
                        pickle.dump(deckdata, open(resource_file(datafilename), 'wb'))

        self.get_saved_decks()
        return


    def start_testing(self):
        if (self.staged_deck_name == None):
            r = self.show_message('No deck in preview window.')
            return
        else:
            self.ui.cardProgressBar.setMinimum(0)
            self.ui.cardProgressBar.setMaximum(len(self.loaded_decks[self.staged_deck_name]))
            self.ui.cardProgressBar.reset()

            self.reset_clock()
            self.card_setup()
            self.testing_deck_name = self.staged_deck_name
            self.test_in_progress = True
            self.ui.mainStack.setCurrentIndex(1)
        return

    def assess_resume(self):
        if self.test_in_progress:
            self.ui.resumeButton.setEnabled(True)
        else:
            self.ui.resumeButton.setEnabled(False)
        return

    def resume_testing(self):
        if not self.test_in_progress:
            raise Exception
        else:
            self.update_card()
            self.test_timer.start(1000)
            self.ui.mainStack.setCurrentIndex(1)
        return

    def update_timer(self):
        self.sec_elapsed += 1
        self.display_time()
        return

    def display_time(self):
        sep = ' ' if (self.sec_elapsed%2) else ':'
        hrs = int(floor(self.sec_elapsed/3600))
        mins = int(floor((self.sec_elapsed - 3600*hrs)/60))
        secs = (self.sec_elapsed - 3600*hrs - mins*60)
        if (hrs > 0):
            clock_str = '{0}{1}{2}{3}{4}'.format(hrs, sep, str(mins).zfill(2), sep, str(secs).zfill(2))
        else:
            clock_str = '{0}{1}{2}'.format(mins, sep, str(secs).zfill(2))
        self.ui.timer.display(clock_str)
        return

    def card_setup(self):
        self.remaining_words = self.loaded_decks[self.staged_deck_name][:]

        if self.randomize:
            shuffle(self.remaining_words)

        self.update_card()

        return

    def reset_clock(self):
        self.sec_elapsed = 0
        self.display_time()
        self.test_timer.start(1000)
        return

    def update_card(self):
        Nwords = len(self.loaded_decks[self.staged_deck_name])

        if self.prompt_word:
            front = self.remaining_words[0][0]
            back = self.remaining_words[0][1]
        else:
            front = self.remaining_words[0][1]
            back = self.remaining_words[0][0]

        self.set_card_front(front)
        self.set_card_back(back)

        words_done = Nwords - len(self.remaining_words)
        self.ui.cardProgressBar.setValue(words_done)
        self.ui.progressNumber.setText(' {0} / {1} '.format(words_done, Nwords))
        # print('{0} left (of {1})'.format(len(self.remaining_words), Nwords))
        self.ui.cardStack.setCurrentIndex(0)
        return

    def next_word(self, correct):
        current_word = self.remaining_words[0]

        del(self.remaining_words[0])
        if not correct:
            if self.repeat_until_done:
                self.remaining_words.append(current_word)

        if self.randomize:
            shuffle(self.remaining_words)

        if len(self.remaining_words) > 0:
            self.update_card()
        else:
            self.done_function()
        return

    def set_card_front(self, text):
        self.ui.wordLabel.setText(text)
        return

    def set_card_back(self, text):
        self.ui.defLabel.setText(text)
        return

    def back_to_load(self):
        self.test_timer.stop()
        self.display_time()
        self.assess_resume()
        self.ui.mainStack.setCurrentIndex(0)
        return

    def flip_card(self):
        self.ui.cardStack.setCurrentIndex(1)
        return

    def generate_stats(self):
        s = ''
        s += self.testing_deck_name + '\n'

        return s

    def done_function(self):
        self.test_in_progress = False
        statStr = self.generate_stats()
        self.testing_deck_name = None
        self.ui.statsLabel.setText(s)
        self.ui.cardStack.setCurrentIndex(2)
        return

    # ---------- deck save/load/delete functions ----------

    def get_saved_decks(self):
        filenames = get_file_list(self.resource_dir)
        deck_files = []
        for name in filenames:
            if (os.path.splitext(name)[1] == '.deck'): # compare extension of file to deck
                deck_files.append(name)

        for deck_file in deck_files:
            deck = pickle.load(open(resource_file(deck_file), 'rb'))
            try:
                tmp = self.loaded_decks[deck[0]]
            except KeyError:
                self.loaded_decks[deck[0]] = deck[1]
                self.loaded_deck_files[deck[0]] = deck_file
                self.ui.loadedDecks.addItem(deck[0])
        return

    def rename_current_deck(self):
        current_deck_name = str(self.ui.loadedDecks.currentText())
        deck_index = self.ui.loadedDecks.currentIndex()

        new_name = self.get_deck_name()
        if len(new_name) > 0:

            self.loaded_decks[new_name] = self.loaded_decks.pop(current_deck_name)

            newdatafilename = 'flashcards_' + new_name + '_' + time.strftime('%Y%m%d_%H%M%S') + '.deck'
            os.remove(self.loaded_deck_files[current_deck_name])
            self.loaded_deck_files.pop(current_deck_name)
            self.loaded_deck_files[new_name] = newdatafilename

            deckdata = [new_name, self.loaded_decks[new_name]]
            pickle.dump(deckdata, open(resource_file(newdatafilename), 'wb'))

            self.ui.loadedDecks.setItemText(deck_index, new_name)

            if (current_deck_name == self.staged_deck_name):
                self.staged_deck_name = new_name

            return

    def delete_deck_function(self):
        current_deck_name = str(self.ui.loadedDecks.currentText())
        if len(current_deck_name) > 0:
            del_msg = delete_message(current_deck_name)
            self.confirm_ui.messageLabel.setText(del_msg)
            retval = self.confirm_ui.exec_()
            if (retval == 1):
                self.delete_current_deck()
        return

    def delete_current_deck(self):
        current_deck_name = str(self.ui.loadedDecks.currentText())
        deck_index = self.ui.loadedDecks.currentIndex()
        # removals: combobox entry, .deck file, loaded_decks dict, loaded_deck_files dict
        os.remove(self.loaded_deck_files[current_deck_name])
        self.ui.loadedDecks.removeItem(deck_index)
        self.loaded_decks.pop(current_deck_name)
        self.loaded_deck_files.pop(current_deck_name)
        if (current_deck_name == self.staged_deck_name):
            self.ui.previewListWidget.clear()
            self.staged_deck_name = None
        if (current_deck_name == self.testing_deck_name):
            self.test_in_progress = False
            self.assess_resume()
        return

    def stage_current_deck(self):
        preview_length = 50
        current_deck_name = str(self.ui.loadedDecks.currentText())
        if len(current_deck_name) > 0:
            self.ui.previewListWidget.clear()
            words = self.loaded_decks[current_deck_name]
            for w in words:
                textline = '{}: {}'.format(w[0], w[1])
                self.ui.previewListWidget.addItem(textline[:preview_length])
            self.staged_deck_name = current_deck_name
        return

# sys.stdout = open(resource_file('debug_log.txt'), 'a')
# timestamp = strftime('----------  %m/%d/%y %H:%M:%S  ---------')
# print('\n')
# print(len(timestamp)*'-')
# print(timestamp)
# print(len(timestamp)*'-')

app = QtWidgets.QApplication(sys.argv)
window = ImageDialog()
sys.exit(app.exec_())