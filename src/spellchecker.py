#!/usr/bin/env python3

# Copyright 2016 Science & Technology Facilities Council
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import glob
import os
import enchant
import os.path
import configparser
import json
import sys
import logging
import argparse
from markspelling import MarkSpelling


def configurelogger(config, args):
    log_format = '%(levelname)6s: %(message)s'
    log_level = logging.INFO
    log_file = ''

    if config.getboolean('DEFAULT', 'log_debug'):
        log_level = logging.DEBUG

    if args.debug:
        log_level = logging.DEBUG

    if config.getboolean('DEFAULT', 'log_to_file'):
        log_file = abspath('spellchecker.log')

    logging.basicConfig(level=log_level, format=log_format, filename=log_file)

    return logging.getLogger('markdown-spellchecker')


def errortotalfunct(errortotal, errortotalprev, file_state):
    logger = logging.getLogger('markdown-spellchecker')
    logger.info('Number of spelling errors: %d', errortotal)
    logger.info('Threshold for failure: %d', errortotalprev)
    if errortotal <= errortotalprev:
        logger.info('Pass.')
        return True
    else:
        logger.error('Failed.')
        return False


def abspath(path):
    """Return an absolute form of path relative to this script"""
    root = os.path.dirname(os.path.realpath(__file__))
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    return path


def verifydirectorysource(path):
    logger = logging.getLogger('markdown-spellchecker')
    if not os.path.exists(path):
        logger.error('Source directory "%s" does not exist', path)
        return False
    if os.listdir(path) == []:
        logger.error('No .md files to evaluate')
        return False
    return True


def loadpwl(filename):
    logger = logging.getLogger('markdown-spellchecker')
    if os.path.exists(filename):
        logger.debug('PWL file found')
        pwl = enchant.request_pwl_dict(filename)
        logger.debug('PWL file loaded')
        return pwl
    else:
        logger.error('PWL file "%s" does not exist', filename)
        sys.exit(1)
    return None


def getfilenameslist(path):
    return glob.glob(os.path.join(path, "*.md"))


def main():
    parser = argparse.ArgumentParser(description='Processes Markdown documents for spellchecking')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging.')
    parser.add_argument('paths', metavar='PATH', type=str, nargs='*', help='Paths of files to check.')
    args = parser.parse_args()

    if not args.paths:
        sys.exit(0)

    config = configparser.ConfigParser()
    config.read(abspath('config.ini'))

    logger = configurelogger(config, args)

    file_state = abspath(config.get('DEFAULT', 'file_state'))
    check_state = config.get('DEFAULT', 'check_state').lower() == 'true'
    personal_word_list = abspath(config.get('DEFAULT', 'personal_word_list'))
    spelling_language = config.get('DEFAULT', 'spelling_language')

    pwl = loadpwl(personal_word_list)

    errortotalprev = 0
    if check_state:
        try:
            with open(file_state, 'r') as scorefile:
                errortotalprev = json.load(scorefile)
        except FileNotFoundError:
            logger.warning('JSON score file "%s" was not found', file_state)
    else:
        file_state = None

    mspell = MarkSpelling(pwl, spelling_language, errortotalprev)
    errortotal = mspell.checkfilelist(args.paths)
    passed = errortotalfunct(errortotal, errortotalprev, file_state)

    if check_state and file_state:
        # Save errortotal to json file for future use
        with open(file_state, 'w') as outfile:
            json.dump(errortotal, outfile)

    if not passed:
        sys.exit(1)


if __name__ == '__main__':
    main()
