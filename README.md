# Flash: macOS Flashcard Viewing Application

A basic macOS flashcard application built with the Qt Design Framework and Python. The application allows the user to select text files containing vocabulary words/phrases and associated definitions. This file is parsed, and the application allows for user-friendly self-testing and organization of flashcard "decks." Project was recently upgraded to Python 3.6 and Qt5.

Here is what the "load screen" currently looks like.

![Load Screen](screenshots/loadscreen_preview.png){:width="600px"}

The major components of the project are:
* Qt UI files (created and edited in the "[Qt Creator](https://wiki.qt.io/Qt_Creator)" desktop application)
* Python code to reference/modify UI elements and run the application
* The [py2app](https://py2app.readthedocs.io/en/latest/#) utility, allowing for bundling of python code into standalone Mac apps

## FEATURES AND IMPROVEMENTS I HOPE TO IMPLEMENT
- [ ] better graphic design
- [ ] ability to write ignored comments in text file
- [ ] pictures associated with vocab, and the ability to prompt with them
- [X] reverse testing (show definition, require term)
- [ ] pausing and resuming capabilities, while testing
- [ ] done page with stats
- [X] timer
- [ ] support for rich text
- [ ] make full screen mode look good
- [ ] handle keyboard shortcuts (Q for quit, L for load, etc)
- [ ] print to PDF option, where printable template is generated

## KNOWN BUGS
- [X] directory issues with pressing "import"
- [X] deck naming box goes blank issue (multiline issue)
- [ ] recognize all dashes as delimiter?
- [ ] text overflows on sides of card when no spaces present

### Dependencies:

I use a designated Anaconda virtual environment to build and this program. The following is the result of a `condo list` command, displaying installed nonstandard packages:
![Conda List Output](screenshots/conda_list.png){:width="300px"}

Installation of these packages was the result of just 3 conda (or pip) `install` commands:
* pip
* pyqt5
* py2app
* sip

Anaconda should handle the identification and installation of everything else.