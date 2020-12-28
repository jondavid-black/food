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

import codecs
import re
from logging import getLogger
from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter

# Format string used to render debug output
_DEBUG_FORMAT = '%03d %5s %s%s%s'

# ANSI color escape codes for highlighting debug output
_ANSI_GRAY = '\033[1;30m'
_ANSI_YELLOW = '\033[1;33m'
_ANSI_RED = '\033[1;31m'
_ANSI_BLUE = '\033[1;34m'
_ANSI_RESET = '\033[0m'

class MarkSpelling(object):
    """
    Instances of MarkSpelling can be used to spell check documentation written in Markdown.
    Code snippets and in-line HTML will be excluded from checks.
    """

    def __init__(self, pwl, language='en_GB', errortotalprev=0):
        self.logger = getLogger('markdown-spellchecker')
        self.spellcheck = SpellChecker(language, filters=[URLFilter, EmailFilter])
        self.pwl = pwl
        self.errortotalprev = errortotalprev
        self.errortotal = 0
        self.regexhtmldirty = re.compile(r'\<(?!\!--)(.*?)\>')
        self.regexhtmlclean = re.compile(r'\`.+?\`')
        self.regexlink = re.compile(r'\[(.+?)\]\(.+?\)')
        self.regexurl = re.compile(r'https?://\S+')
        self.regexlinkid = re.compile(r'\[\S+\]:\s[^{\s]*')
        self.regexlinkparam = re.compile(r'{:\S+="\S+"}')
        self.regexliquidtag = re.compile(r'{%.+%}')
        self.regexliquidobject = re.compile(r'{{.+}}')

    def checkcodeblock(self, line, incodeblock):
        if line.startswith('```') or line == '---':
            return not incodeblock
        return incodeblock

    def checkline(self, line, linenumber, filename, incodeblock=False):
        line = line.strip()
        errorline = line
        errorcount = 0
        wasincodeblock = incodeblock
        incodeblock = self.checkcodeblock(line, incodeblock)
        errorwords = list()
        if not wasincodeblock and not incodeblock:
            self.logger.debug(_DEBUG_FORMAT, linenumber, 'RAW', _ANSI_GRAY, line, _ANSI_RESET)
            line = self.regexhtmldirty.sub('', line)  # strip html tags
            line = self.regexhtmlclean.sub('', line)  # strip inline code
            line = self.regexlinkid.sub('', line)  # strip link ids
            line = self.regexlinkparam.sub('', line)  # strip link params
            line = self.regexlink.sub(r'\1', line)  # strip basic links
            line = self.regexurl.sub('', line)  # strip URLs
            # if we were to detect liquid comment blocks, we should do it here
            line = self.regexliquidtag.sub('', line)  # strip liquid tags
            line = self.regexliquidobject.sub('', line)  # strip liquid objects
            line = line.strip()
            self.logger.debug(_DEBUG_FORMAT, linenumber, 'CLEAN', '', line, '')
            self.spellcheck.set_text(line)
            for err in self.spellcheck:
                self.logger.debug(_DEBUG_FORMAT, linenumber, 'WARN', _ANSI_YELLOW, "'%s' not found in main dictionary" % err.word, _ANSI_RESET)
                if not self.pwl or not self.pwl.check(err.word):
                    self.logger.debug(_DEBUG_FORMAT, linenumber, 'ERROR', _ANSI_RED, "'%s' not found in custom dictionary" % err.word, _ANSI_RESET)
                    errorcount += 1
                    errorwords.append(err.word)
        else:
            self.logger.debug(_DEBUG_FORMAT, linenumber, 'CODE', _ANSI_BLUE, line, _ANSI_RESET)

        for word in errorwords:
            errorline = errorline.replace(word, _ANSI_RED + word + _ANSI_GRAY)

        if errorwords:
            self.logger.error('%s:%4d |%s', filename, linenumber, _ANSI_GRAY + errorline + _ANSI_RESET)

        return (errorcount, incodeblock)

    def checklinelist(self, linelist, filename):
        errorcount = 0
        incodeblock = False
        for linenumber, line in enumerate(linelist, start=1):
            (lineerrors, incodeblock) = self.checkline(line, linenumber, filename, incodeblock)
            errorcount += lineerrors
        return errorcount

    def checkfile(self, filename):
        self.logger.debug('Checking file "%s"', filename)
        fileerrors = 0
        with codecs.open(filename, 'r', encoding='UTF-8') as markdownfile:
            lines = markdownfile.readlines()
            fileerrors = self.checklinelist(lines, filename)
        self.logger.info('%d errors in total in %s', fileerrors, filename)
        return fileerrors

    def checkfilelist(self, filenameslist):
        for filename in filenameslist:
            self.errortotal += self.checkfile(filename)

        return self.errortotal
