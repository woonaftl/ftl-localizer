"""Contains functions which help to (de)localize FTL: Faster Than Light
by copying all strings into one file or vice versa.
"""

import os
import re

from bs4 import BeautifulSoup

EMPTY_XML = '<?xml version="1.0" encoding="utf-8"?> \
<!-- Copyright (c) 2012 by Subset Games. All rights reserved --><FTL></FTL>'

SUPPORTED_LANGUAGES = {'de', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'zh-Hans'}

ALL_TAGS = {'text', 'class', 'desc', 'title', 'short', 'tooltip',
            'unlock', 'flavorType', 'power', 'crewMember'}

BLUEPRINT_TAGS = {'class', 'desc', 'title', 'short', 'tooltip',
                  'unlock', 'flavorType'}

PARENT_TAG_DICT = {'event': 'text',
                   'destroyed': 'text',
                   'deadCrew': 'text',
                   'escape': 'text',
                   'gotaway': 'text',
                   'surrender': 'text',
                   'removeCrew': 'clone'}


def check_dir(directory):
    """Checks if directory exists."""
    if not os.path.isdir(directory):
        raise Exception('Directory not found')


def check_and_create_dir(directory):
    """Checks if directory exists, and creates it if not."""
    if os.path.exists(directory):
        if not os.path.isdir(directory):
            raise Exception('Directory is a file')
    else:
        os.mkdir(directory)


def check_language(lang):
    """Checks if language is supported by FTL."""
    result = None
    if lang in SUPPORTED_LANGUAGES:
        result = lang
    return result


def pretty_xml(soup):
    """Prettifies bs4 trees.
    Prettify used by BeautifulSoup is not consistent with
    XML formatting used in FTL so we need to fix it using
    other means.
    """
    result = soup.prettify(encoding='utf-8').decode('utf-8')
    # regex: remove first space in each line
    result = re.sub(r'\n ', '\n', result)
    # regex : remove newline and indent if this line is a tag but next line is not
    result = re.sub(r'(?<=>)\n *(?! *<)', '', result)
    # regex : remove newline and indent if this line is not a tag but next line is
    result = re.sub(r'(?<!>)\n *(?=</)', '', result)
    # regex: replace spaces with tabs before opening bracket <
    result = re.sub(r'(?<=\s) (?= *<)', '\t', result)
    return result


def parse(workdir):
    """Parse xml files in a folder using BeautifulSoup."""

    def fixbrokenxml(xmldoc, root):
        """Prepare to parse by fixing almost well-formed xml
        This function won't help parsing truly broken xml
        """
        # Adding a root tag if there is none
        if xmldoc.find(f'<{root}>') == -1:
            endroot = xmldoc.find('?>')
            if endroot == -1:
                xmldoc = f'<{root}>{xmldoc}'
            else:
                endroot = endroot + 2
                xmldoc = f'{xmldoc[:endroot]}<{root}>{xmldoc[endroot:]}'
        if xmldoc.find(f'</{root}>') == -1:
            xmldoc = f'{xmldoc}</{root}>'
        # Fixing extra dashes in comments
        xmldoc.replace('<!---', '<!-- -')
        xmldoc.replace('--->', '- -->')
        return xmldoc

    soups = []
    for filename in os.listdir(workdir):
        full_path = os.path.join(workdir, filename)
        if ((full_path[-4:] == '.xml') or (full_path[-11:] == '.xml.append')
                or (full_path[-15:] == '.xml.rawclobber')):
            file = open(full_path, 'r', encoding="utf-8", errors='ignore')
            contents = file.read()
            contents = fixbrokenxml(contents, 'FTL')
            soup = BeautifulSoup(contents, "lxml-xml")
            soups.append([soup, filename])
    print('Finished parsing xml files...')
    return soups


def delocalize(workdir, outputdir, language_attr, empty_string='TEXT_NOT_FOUND',
               ignore_continue=True):
    """Makes xml files more convenient to edit by inserting text
    strings from separate text files directly into data files.

    :param workdir: Work directory where all input
        xml files are located.

    :param outputdir: Creates a folder with this name
        and puts all result files there.

    :param language_attr: Determines xml attribute "language" which
        will be searched in text files for insertion into data files.

    :param empty_string: If there is no text string with selected
        language found, this will be inserted instead, to help
        find missing strings.

    :param ignore_continue: If True, do not replace continue id
        with Continue... text.
    """

    def append_to_dict(dictionary, string, name):
        """Append an entry to the dictionary.
        Returns 1 if string is doubly defined in the dictionary.
        Dictionary for delocalize() follows structure
        {id_defined_by_text_attr : localizable_text_string}
        Reversed structure from localize()
        """
        result = 0
        if string in dictionary:
            result = 1
        dictionary[name] = string
        return result

    def fill_dict(soups, lang):
        """Populates dictionary with text strings."""

        def need_to_save_to_dict(tag):
            """Conditions that can be used by bs4 find_all function."""
            _result = False
            if tag.name == 'text':
                if (tag.string is not None) and ('name' in tag.attrs):
                    if 'language' in tag.attrs:
                        _result = tag['language'] == lang
                    else:
                        _result = lang is None
            return _result

        result = {}
        for soup in soups:
            addition_counter = 0
            doubly_defined_counter = 0
            for text_tag in soup[0].find_all(need_to_save_to_dict):
                res = append_to_dict(
                    result, text_tag.string, text_tag['name']
                )
                doubly_defined_counter += res
                addition_counter += 1
            if addition_counter > 0:
                print(f'Saved {addition_counter} strings from {soup[1]}...')
            if doubly_defined_counter > 0:
                print(f'Found {doubly_defined_counter} doubly defined strings in {soup[1]}...')
        print('Finished filling the dictionary with text strings...')
        return result

    def replace_ids_with_texts(soups, dictionary):
        """Locate text ids in bs4 trees and replace them
        with matching text strings from the dictionary.
        """

        def need_to_delocalize(tag):
            """Conditions that can be used by bs4 find_all function."""
            result = False
            if tag.name in ALL_TAGS:
                if (tag.string is None) and ('id' in tag.attrs):
                    result = (not ignore_continue) or (tag['id'] != 'continue')
            return result

        def get_text_string(tag):
            """Safer function to get value from dictionary."""
            result = None
            if 'id' in tag.attrs:
                if tag['id'] in dictionary:
                    result = dictionary[tag['id']]
            return result

        for soup in soups:
            replacement_counter = 0
            for text_tag in soup[0].find_all(need_to_delocalize):
                text_string = get_text_string(text_tag)
                if text_string is not None:
                    text_tag.string = text_string
                else:
                    text_tag.string = empty_string
                del text_tag['id']
                replacement_counter += 1
            if replacement_counter > 0:
                new_file = open(os.path.join(outputdir, soup[1]), 'w+', encoding='utf-8')
                new_file.write(pretty_xml(soup[0]))
                print(f'Replaced {replacement_counter} strings in {soup[1]}...')
        print('Finished replacing ids with text strings...')

    check_dir(workdir)
    check_and_create_dir(outputdir)
    language = check_language(language_attr)
    print('Started parsing xml files...')
    all_bs4_trees = parse(workdir)
    locale_dict = fill_dict(all_bs4_trees, language)
    replace_ids_with_texts(all_bs4_trees, locale_dict)
    print('SUCCESS')


def localize(workdir, outputdir, language_attr, check_same_strings=False, split_result=False):
    """Prepares xml files for localization by moving all text
    strings from data files into separate text files which
    can be different for each language.

    :param workdir: Work directory where all input xml
        files are located.

    :param outputdir: Creates a folder with this name
        and puts all result files there.

    :param language_attr: Determines xml attribute "language"
        in result localization file.

    :param check_same_strings: If True, tries to combine
        exactly same text strings into one.

    :param split_result: If False, all files with text strings
        will be combined, otherwise, files will be split into
        categories based on source file.
    """

    def append_to_dict(dictionary, string, name, source):
        """Append an entry to the dictionary.
        Returns 1 if string is doubly defined in the dictionary.
        Dictionary for localize() follows structure
        {localizable_text_string : id_defined_by_text_attr}
        Reversed structure from delocalize()
        """
        result = 0
        if string in dictionary:
            result = 1
        dictionary[string] = [name, source]
        return result

    def fill_dict(soups):
        """Populates dictionary with text strings that are already
        defined in text files.
        """
        result = {}
        for soup in soups:
            addition_counter = 0
            doubly_defined_counter = 0
            for text_tag in soup[0].find_all('text'):
                if text_tag.string is not None:
                    if 'name' in text_tag.attrs:
                        res = append_to_dict(result, text_tag.string, text_tag['name'], soup[1])
                        doubly_defined_counter += res
                        addition_counter += 1
            if addition_counter > 0:
                print(f'Copied {addition_counter} strings from {soup[1]}...')
            if doubly_defined_counter > 0:
                print(f'Found {doubly_defined_counter} doubly defined strings in {soup[1]}...')
        print('Finished copying already localized text...')
        return result

    def copy_new_ids(soups, dictionary):
        """Find text strings that need to be localized in bs4 trees,
        assign ids to them,
        replace text strings with links to text file
        using newly assigned id,
        create new xml files if there are any changes.
        """

        def get_textid(tag):
            """Check if there is a need to localize tag and
            get a short (and hopefully unique) id for text tag,
            keeps names as close to vanilla as possible
            """

            def get_sibling_number(_tag):
                """Get order number of tag counting only
                sibling tags with same name
                """
                _result = '1'
                before = 0
                prevtag = _tag.previous_sibling
                while prevtag is not None:
                    if prevtag.name == _tag.name:
                        before += 1
                    prevtag = prevtag.previous_sibling
                if before > 0:
                    _result = str(before + 1)
                return _result

            def get_child_str(parents):
                """Forms text ids from parent tags following structure
                c1_c2_c1_c10...
                """
                _result = ''
                for parent_tag in reversed(parents[:-1]):
                    if parent_tag.name == 'choice':
                        _result = f'{_result}_c{get_sibling_number(parent_tag)}'
                if parents[0].name in PARENT_TAG_DICT:
                    _result = f'{_result}_{PARENT_TAG_DICT[parents[0].name]}'
                else:
                    _result = f'{_result}_{parents[0].name}'
                return _result

            def get_attr(_tag):
                """Safer function to get attribute."""
                if 'name' in _tag.attrs:
                    return f'_{_tag["name"]}'
                else:
                    return ''

            result = None
            parent_list = list(tag.parents)
            if len(parent_list) > 2:
                parent_top = parent_list[-3]
                if (tag.name == 'text') and ('name' not in tag.attrs):
                    if parent_top.name == 'textList':
                        result = f'text{get_attr(parent_top)}_{get_sibling_number(tag)}'
                    elif parent_top.name == 'event':
                        result = f'event{get_attr(parent_top)}{get_child_str(parent_list[:-2])}'
                    elif parent_top.name == 'eventList':
                        result = f'event{get_attr(parent_top)}_' \
                                 f'{get_sibling_number(parent_list[-4])}' \
                                 f'{get_child_str(parent_list[:-3])}'
                    elif parent_top.name == 'ship':
                        result = f'ship{get_attr(parent_top)}_{parent_list[-4].name}' \
                                 f'{get_child_str(parent_list[:-3])}'
                elif tag.name in BLUEPRINT_TAGS:
                    if parent_top.name[-9:] == 'Blueprint':
                        result = f'{parent_top.name[:-9]}{get_attr(parent_top)}_{tag.name}'
                elif tag.name == 'power':
                    if parent_top.name == 'crewBlueprint' and parent_list[0].name == 'powerList':
                        result = f'{parent_top.name[:-9]}{get_attr(parent_top)}_{tag.name}' \
                                 f'{get_sibling_number(tag)}'
                elif tag.name == 'crewMember':
                    result = f'name_crewMember_{tag.string}'
            return result

        def need_to_localize(tag):
            """Conditions that can be used by bs4 find_all function."""
            result = False
            if tag.name in ALL_TAGS:
                if (tag.string is not None) and (not tag.string.isdigit()):
                    result = (tag.name != 'text') or ('name' not in tag.attrs)
            return result

        def get_existing_id(tag):
            """Trying to find existing id with
            exact string match in the dictionary
            """
            result = None
            if tag.string in dictionary:
                result = dictionary[tag.string][0]
            return result

        for soup in soups:
            repeat_counter = 0
            addition_counter = 0
            for text_tag in soup[0].find_all(need_to_localize):
                existing_id = None
                if check_same_strings:
                    existing_id = get_existing_id(text_tag)
                if existing_id is None:
                    # Assigning new id
                    text_id = get_textid(text_tag)
                    if text_id is not None:
                        append_to_dict(dictionary, text_tag.string, text_id, soup[1])
                        text_tag.contents = []
                        text_tag['id'] = text_id
                        addition_counter += 1
                else:
                    # Found repeating string, don't generate new id
                    text_tag.contents = []
                    text_tag['id'] = existing_id
                    repeat_counter += 1
            if (addition_counter > 0) or (repeat_counter > 0):
                new_file = open(os.path.join(outputdir, soup[1]), 'w+', encoding='utf-8')
                new_file.write(pretty_xml(soup[0]))
            if addition_counter > 0:
                print(f'Copied {addition_counter} strings from {soup[1]}...')
            if repeat_counter > 0:
                print(f'Found {repeat_counter} repeats in {soup[1]}...')
        print('Finished copying new text...')

    def locale_file_out(dictionary, filename, source, lang):
        """Creates xml file using data from dictionary with strings
        from matching source.
        """

        def create_locale_tree():
            """Creates a new bs4 tree.
            Caution: outed strings are deleted from dictionary.
            """

            def append_new_tag(tree, string, name):
                """Append a tag to bs4 tree"""
                new_tag = tree.new_tag('text')
                new_tag.string = string
                new_tag['name'] = name
                if lang is not None:
                    new_tag['language'] = lang
                new_tree_root.append(new_tag)

            new_tree = BeautifulSoup(EMPTY_XML, "lxml-xml")
            new_tree_root = new_tree.find('FTL')
            dict_for_delete = {}
            for entry in dictionary:
                if (source is None) or (source in dictionary[entry][1]):
                    append_new_tag(new_tree, entry, dictionary[entry][0])
                    dict_for_delete[entry] = []
            for entry in dict_for_delete:
                del dictionary[entry]
            return new_tree

        locale_file = open(os.path.join(outputdir, filename), 'w+', encoding='utf-8')
        locale_file.write(pretty_xml(create_locale_tree()))
        print(f'Finished creating result file {filename}...')

    # Main
    check_dir(workdir)
    check_and_create_dir(outputdir)
    language = check_language(language_attr)
    print('Started parsing xml files...')
    all_bs4_trees = parse(workdir)
    locale_dict = fill_dict(all_bs4_trees)
    copy_new_ids(all_bs4_trees, locale_dict)

    # Creating result file(s)
    if split_result:
        locale_file_out(locale_dict, 'text_events.xml.append', 'event', language)
        locale_file_out(locale_dict, 'text_blueprints.xml.append', 'blueprint', language)
        locale_file_out(locale_dict, 'text_achievements.xml.append', 'achievement', language)
        locale_file_out(locale_dict, 'text_sectorname.xml.append', 'sector', language)
        locale_file_out(locale_dict, 'text_tooltips.xml.append', 'tooltip', language)
        locale_file_out(locale_dict, 'text_tutorial.xml.append', 'tutorial', language)
        locale_file_out(locale_dict, 'text_misc.xml.append', None, language)
    else:
        if language is not None:
            locale_file_name = f'text-{language}.xml'
        else:
            locale_file_name = 'text_misc.xml'
        locale_file_out(locale_dict, locale_file_name, None, language)
    print('SUCCESS')
