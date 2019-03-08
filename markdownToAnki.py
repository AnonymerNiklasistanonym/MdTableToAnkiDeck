#!/usr/bin/env python3

import sys
import re
import os.path
from typing import Optional, Match
from shutil import copyfile

import genanki
import pytablewriter
import random


def cli_open_man_page():
    print("Create an anki deck with an input markdown table document\n" +
          "\t$ python markdownToAnki.py ./markdownFile -enabledOption\n\n" +
          "\t-d\t\t\tActivate debugging\n" +
          "\t-out-anki filePath\tCustom anki deck output file path\n" +
          "\t-out-md filePath\tCustom markdown doc output file path\n" +
          "\t-resource-prefix prefix\tCustom image path prefix (if image is\n" +
          "\t\t\t\tin a directory and not root enter the\n" +
          "\t\t\t\tdirectory as prefix [e.g. \"pictures\"])")
    sys.exit(0)


def cli_show_version():
    print("0.0.1")
    sys.exit(0)


debug: bool = False
remove_file_paths: list = []


class RegexHelper(object):
    """
    Helps matching strings with regex strings
    """
    rematch: Optional[Match[str]]
    match_string: str

    def __init__(self, input_string: str):
        """
        :param input_string: The string the string that should be matched
        """
        self.match_string = input_string

    def match(self, regular_expression: str):
        """
        :param regular_expression: The regex string
        """
        self.rematch = re.match(regular_expression, self.match_string)
        return bool(self.rematch)

    def group(self, group_index: int):
        """
        :param group_index: The regex match group index
        """
        return self.rematch.group(group_index)


class AnkiDeckCreator(object):
    """
    Helps creating a anki deck
    """

    def __init__(self, deck_info=None):
        # Check first if there is a deck id and if not create one
        if deck_info is None:
            deck_info = {"id": None, "name": "Test"}
        if deck_info['id'] is None:
            self.deck_id = random.randint(100000, 999999)
        else:
            self.deck_id = int(deck_info['id'])
        # Get the deck name
        self.deck_name = deck_info['name']
        # Create variables for files + list with all the notes
        self.files = set()
        self.note_matrix = []
        # Create a deck and a model for the cards with MathJax support
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.mathJax_template_code = """
            <script type="text/x-mathjax-config">
            MathJax.Hub.processSectionDelay = 0;
            MathJax.Hub.Config({
            messageStyle: 'none',
            showProcessingMessages: false,
            tex2jax: {
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true
            }
            });
            </script>
            <script type="text/javascript">
            (function() {
            if (window.MathJax != null) {
                var card = document.querySelector('.card');
                MathJax.Hub.Queue(['Typeset', MathJax.Hub, card]);
                return;
            }
            var script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/' + 
                '2.7.1/MathJax.js?config=TeX-MML-AM_CHTML';
            document.body.appendChild(script);
            })();
            </script>"""
        self.model = genanki.Model(
            6666666666,
            'Card with MathJax',
            fields=[{'name': 'Question'}, {'name': 'Answer'}],
            templates=[{
                'name': 'Card 1',
                'qfmt': '{{Question}}' +
                        self.mathJax_template_code,
                'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}' +
                        self.mathJax_template_code,
            }])

    def add_note(self, note_id: str, note_question: str, note_answer: str,
                 note_files: list):
        """
        Add an anki note/card
        :param note_id: The id of the note
        :param note_question: The question
        :param note_answer: The answer
        :param note_files: The connected files
        """
        # Concatenate all files for the export later
        self.files.update(note_files)
        # If the note has no id assign one with the unique question/answer
        if note_id is '':
            note_id = genanki.guid_for(note_question, note_answer)
        # Append the current note to the note matrix
        self.note_matrix.append([
            note_id,
            note_question.replace('\n', '<br>').replace('\r', ''),
            note_answer.replace('\n', '<br>').replace('\r', '')
        ])
        # Remove all the custom file paths from the cards for anki
        for remove_file_path in remove_file_paths:
            note_question = note_question\
                .replace('"' + remove_file_path + '/', '"')
            note_answer = note_answer\
                .replace('"' + remove_file_path + '/', '"')
        # Add the note to the deck
        self.deck.add_note(genanki.Note(
            guid=note_id,
            model=self.model,
            fields=[note_question.replace('<br>', '\n'),
                    note_answer.replace('<br>', '\n')]))

        if debug:
            print("note added", note_id, note_question, note_answer, note_files)

    def write_to_file_anki(self, file_name: str):
        """
        Write the anki file to a specific file
        :param file_name: The file name (Without `.apkg`)
        """
        my_package = genanki.Package(self.deck)
        # Copy files from other paths into the current directory
        files_to_delete = set()
        for file in self.files:
            for remove_file_path in remove_file_paths:
                if remove_file_path in file:
                    file_to_delete_later = file\
                        .replace(remove_file_path + '/', '')
                    copyfile(file, file_to_delete_later)
                    files_to_delete.add(file_to_delete_later)
                    self.files.remove(file)
                    self.files.add(file_to_delete_later)
                    if debug:
                        print("delete file later", file_to_delete_later)
        my_package.media_files = list(self.files)
        my_package.write_to_file(file_name + '.apkg')
        # Delete copied files
        if debug:
            print("files_to_delete", files_to_delete)
        for delete_file in files_to_delete:
            os.remove(delete_file)

    def write_to_file_md(self, file_name: str):
        """
        Write the markdown file to a specific file
        :param file_name: The file name (Without `.md`)
        """
        writer = pytablewriter.MarkdownTableWriter()
        writer.table_name = self.deck_name + ' (' + str(self.deck_id) + ')\n'
        writer.headers = ["id", "question", "answer"]
        writer.value_matrix = self.note_matrix
        # Beautify the table
        writer.margin = 1
        # Write to file
        with open(file_name + '.md', 'w') as file:
            writer.stream = file
            writer.write_table()


class MdExtractor:
    """
    Helper to extract information from the markdown document
    """
    def __init__(self):
        self.table_regex = r"^.*?\|\s(.*?)\s\|\s(.*?)\s\|\s(.*?)\s\|.*$"
        self.title_regex = r"^\#\s(.+?)\s\((.+?)\)"
        self.title_regex_without_id = r"^\#\s(.+)\n"
        self.image_src_regex = r"<img\s*src=\"(.*?)\".*?>"

    def extract_note(self, markdown_row: str) -> Optional[dict]:
        """
        Extract an anki note from a row of a markdown table line
        :param markdown_row: Markdown table line
        :return: A dictionary with the `id`, `answer`, `question`, `files` of
        the note
        """
        md_test = RegexHelper(markdown_row)
        if md_test.match(self.table_regex):
            connected_files = list(re.findall(self.image_src_regex,
                                              md_test.group(2))) + \
                              list(re.findall(self.image_src_regex,
                                              md_test.group(3)))
            return dict(id=md_test.group(1), question=md_test.group(2),
                        answer=md_test.group(3), files=connected_files)
        else:
            return None

    def extract_deck_info(self, md_line: str) -> Optional[dict]:
        """
        Extract an anki deck name and optional id from a line of a markdown doc
        :param md_line: Markdown file line
        :return: A dictionary with `id`, (optional) `name` of the anki deck
        """
        md_test = RegexHelper(md_line)
        # First test for title and deck id
        if md_test.match(self.title_regex):
            return dict(id=md_test.group(2), name=md_test.group(1))
        # Then check if only a title can be found
        elif md_test.match(self.title_regex_without_id):
            return dict(id=None, name=md_test.group(1))
        else:
            return None


# Main method (This will not be executed when file is imported)
if __name__ == '__main__':

    ANKI_FILE_NAME = None
    MD_OUTPUT_FILE_NAME = None
    nextAnkiOutFilePath = False
    nextMdOutFilePath = False
    nextRmResPrefix = False

    argsToRemove = []

    # Go through all arguments to activate options
    for x in sys.argv:
        if x == "--help" or x == "-help" or x == "-h":
            cli_open_man_page()
        if x == "--version" or x == "-version" or x == "-v":
            cli_show_version()
        if x == "-d":
            argsToRemove.append(x)
            debug = True

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    if debug:
        print("args", sys.argv)

    for x in sys.argv:
        if nextAnkiOutFilePath:
            nextAnkiOutFilePath = False
            ANKI_FILE_NAME = x
            argsToRemove.append(x)
        if nextMdOutFilePath:
            nextMdOutFilePath = False
            MD_OUTPUT_FILE_NAME = x
            argsToRemove.append(x)
        if nextRmResPrefix:
            nextRmResPrefix = False
            remove_file_paths.append(x)
            argsToRemove.append(x)
        if x == "-out-anki":
            nextAnkiOutFilePath = True
            argsToRemove.append(x)
        if x == "-out-md":
            nextMdOutFilePath = True
            argsToRemove.append(x)
        if x == "-rm-res-prefix":
            nextRmResPrefix = True
            argsToRemove.append(x)

    for rmArg in argsToRemove:
        sys.argv.pop(sys.argv.index(rmArg))
    argsToRemove = []

    if debug:
        print("args after removals", sys.argv)
        print("remove_file_paths", remove_file_paths)

    if len(sys.argv) < 2:
        print('No markdown file was specified!')
        sys.exit(1)

    # Constants
    MARKDOWN_FILE_NAME = sys.argv[1] + '.md'
    if ANKI_FILE_NAME is None:
        ANKI_FILE_NAME = sys.argv[1]
    if MD_OUTPUT_FILE_NAME is None:
        MD_OUTPUT_FILE_NAME = sys.argv[1]

    if not os.path.isfile(MARKDOWN_FILE_NAME):
        print('Markdown file was not found: "' + MARKDOWN_FILE_NAME + '"')
        sys.exit(1)

    # Object that helps to extract markdown line information
    md_extractor: MdExtractor = MdExtractor()
    # Object that helps creating the anki deck
    deck_creator: Optional[AnkiDeckCreator] = None
    # Walking match variable if a note was matched
    walk: Optional[dict] = None
    # Count the matches to ignore the first two lines of the table (the header)
    counter: int = 0
    # Indicate if a deck name was extracted
    deck_name_extracted: bool = False

    # Open file to read it
    with open(MARKDOWN_FILE_NAME) as md_table_file:
        for line in md_table_file:
            if not deck_name_extracted:
                deck_name_extracted = True
                deck_information = md_extractor.extract_deck_info(line)
                if deck_information is None:
                    print('No deck info was found')
                    sys.exit(1)
                else:
                    deck_creator = AnkiDeckCreator(deck_information)
            walk = md_extractor.extract_note(line)
            if debug:
                print("walk", walk)
            if walk is not None:
                counter += 1
                # Ignore heading
                if counter > 1:
                    deck_creator.add_note(
                        note_id=walk['id'],
                        note_question=walk['question'],
                        note_answer=walk['answer'],
                        note_files=walk['files'])

    if counter <= 1:
        print('No anki notes were found')
        sys.exit(1)

    # Write deck to file
    if deck_creator is not None:
        deck_creator.write_to_file_anki(ANKI_FILE_NAME)
        deck_creator.write_to_file_md(MD_OUTPUT_FILE_NAME)
