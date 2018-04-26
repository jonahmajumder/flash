import sys, os
import pickle
from random import shuffle
import time
from PyQt4 import QtCore, QtGui, uic
from get_files import get_file_list

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

class ImageDialog(QtGui.QMainWindow):

    # ---------- init function ----------

    def __init__(self):
        QtGui.QDialog.__init__(self)

        # get ui
        self.ui = uic.loadUi("flashcards.ui")
        self.ui_dir = os.path.dirname(os.path.abspath(__file__))
        self.loaded_decks = {}
        self.loaded_deck_files = {}
        self.staged_deck_name = None
        self.repeat_until_done = True
        self.randomize = True

        self.load_naming_ui()
        self.load_confirm_ui()
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

        # when everything is ready
        self.ui.mainStack.setCurrentIndex(0)
        self.ui.show()
        self.ui.raise_()
        return

    # ---------- auxiliary prep functions ----------

    def connect_buttons(self):
        self.ui.startButton.clicked.connect(self.start_testing)
        self.ui.backButton.clicked.connect(self.back_to_load)
        self.ui.flipButton.clicked.connect(self.flip_card)
        self.ui.importButton.clicked.connect(self.get_deck_txt_file)
        self.ui.deleteButton.clicked.connect(self.delete_deck_function)
        self.ui.stageButton.clicked.connect(self.stage_current_deck)
        self.ui.randomCheckBox.clicked.connect(self.evaluate_randomize)
        self.ui.onceButton.clicked.connect(self.evaluate_repetition)
        self.ui.untilDoneButton.clicked.connect(self.evaluate_repetition)
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

    def load_naming_ui(self):
        self.naming_ui = uic.loadUi("namemsgbox.ui")
        self.naming_ui.setWindowTitle('Name Deck')
        self.naming_ui.buttonDialog.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        return

    def load_confirm_ui(self):
        self.confirm_ui = uic.loadUi("confirmdelete.ui")
        self.confirm_ui.setWindowTitle('Confirm Delete')
        self.confirm_ui.buttonDialog.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        return

    def load_message_ui(self):
        self.message_ui = uic.loadUi("message.ui")
        self.message_ui.setWindowTitle('Alert')
        self.message_ui.okButton.clicked.connect(lambda: self.message_ui.close())
        return

    # ---------- user input functions ----------

    def get_deck_name(self):
        retval = self.naming_ui.exec_()
        entered_name = str(self.naming_ui.nameTextEdit.toPlainText())
        if (retval == 1):
            return entered_name
        else:
            return ''

    def show_message(self, message):
        self.message_ui.messageLabel.setText(message)
        retval = self.message_ui.exec_()
        return retval

    # ---------- active functions ----------

    def get_deck_txt_file(self):
        delim = str(self.ui.delimTextEdit.toPlainText())
        delim = delim.strip(' ')
        if len(delim) == 0:
            r = self.show_message('No text file delimiter specified.')
            return
        else:
            d = QtGui.QFileDialog
            filename = d.getOpenFileName(self, 'Open text file', os.getcwd())
            if len(filename) > 0:
                words = parse_file_for_vocab(filename, delim)
                if len(words) > 0:
                    name = self.get_deck_name()
                    if len(name) > 0:
                        datafilename = 'flashcards_' + name + '_' + time.strftime('%Y%m%d_%H%M%S') + '.deck'
                        deckdata = [name, words]
                        pickle.dump(deckdata, open(datafilename, 'wb'))

        self.get_saved_decks()
        return

    def start_testing(self):
        if (self.staged_deck_name == None):
            r = self.show_message('No deck in preview window.')
            return
        self.ui.mainStack.setCurrentIndex(1)
        self.ui.cardStack.setCurrentIndex(0)
        self.ui.cardProgressBar.setValue(0)
        return

    def back_to_load(self):
        self.ui.mainStack.setCurrentIndex(0)
        return

    def flip_card(self):
        self.ui.cardStack.setCurrentIndex(1)
        return

    def get_saved_decks(self):
        filenames = get_file_list(self.ui_dir)
        deck_files = []
        for name in filenames:
            if (os.path.splitext(name)[1] == '.deck'): # compare extension of file to deck
                deck_files.append(name)

        for deck_file in deck_files:
            deck = pickle.load(open(deck_file))
            try:
                tmp = self.loaded_decks[deck[0]]
            except KeyError:
                self.loaded_decks[deck[0]] = deck[1]
                self.loaded_deck_files[deck[0]] = deck_file
                self.ui.loadedDecks.addItem(deck[0])
        return

    def delete_deck_function(self):
        current_deck_name = str(self.ui.loadedDecks.currentText())
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
        return

    def stage_current_deck(self):
        preview_length = 50
        current_deck_name = str(self.ui.loadedDecks.currentText())
        self.ui.previewListWidget.clear()
        words = self.loaded_decks[current_deck_name]
        for w in words:
            textline = '{}: {}'.format(w[0], w[1])
            self.ui.previewListWidget.addItem(textline[:preview_length])
        self.staged_deck_name = current_deck_name
        return

app = QtGui.QApplication(sys.argv)
window = ImageDialog()
sys.exit(app.exec_())