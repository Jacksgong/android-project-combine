#!/usr/bin/python -u

"""
Copyright (C) 2017 Jacksgong(blog.dreamtobe.cn)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from shlex import shlex
from ast import literal_eval

from utils import EXT_KEY_VALUE1, EXT_KEY_VALUE2

ext_case_1 = "IS_DEBUG_SYNC_EXECUTOR = false"
ext_case_2 = "KEY2 = 'value2'"
ext_case_3 = 'KEY3 = "value3"'

ext_wrong_case = 'IS_DEBUG_SYNC_EXECUTOR = properties.getProperty("isDebugSyncExecutor", "false").toBoolean()'


def test_ext_re():
    key, value = EXT_KEY_VALUE2.match(ext_case_1).groups()
    print key + ' : ' + value

    key, value = EXT_KEY_VALUE1.match(ext_case_2).groups()
    print key + ' : ' + value

    key, value = EXT_KEY_VALUE1.match(ext_case_3).groups()
    print key + ' : ' + value

    if EXT_KEY_VALUE1.match(ext_wrong_case) is not None:
        print "wrong match  EXT_KEY_VALUE1 " + ext_wrong_case

    if EXT_KEY_VALUE2.match(ext_wrong_case) is not None:
        print "wrong match  EXT_KEY_VALUE2" + ext_wrong_case


test_ext_re()

TRANSLATION = {
    "true": True,
    "false": False,
    "null": None,
}


class ParseException(Exception):
    def __init__(self, token, line):
        self.token = token
        self.line = line

    def __str__(self):
        return "ParseException at line %d: invalid token %s" % (self.line, self.token)


class GroovyConfigSlurper:
    def __init__(self, source):
        self.source = source

    def parse(self):
        lex = shlex(self.source)
        lex.wordchars += "."
        state = 1
        context = []
        result = dict()
        while 1:
            token = lex.get_token()
            if not token:
                return result
            if state == 1:
                if token == "}":
                    if len(context):
                        context.pop()
                    else:
                        raise ParseException(token, lex.lineno)
                else:
                    name = token
                    state = 2
            elif state == 2:
                if token == "=":
                    state = 3
                elif token == "{":
                    context.append(name)
                    state = 1
                else:
                    raise ParseException(token, lex.lineno)
            elif state == 3:
                try:
                    value = TRANSLATION[token]
                except KeyError:
                    value = literal_eval(token)
                key = ".".join(context + [name]).split(".")
                current = result
                for i in xrange(0, len(key) - 1):
                    if key[i] not in current:
                        current[key[i]] = dict()
                    current = current[key[i]]
                current[key[-1]] = value
                state = 1

# with open("build.gradle", "r") as f:
#     print GroovyConfigSlurper(f).parse()
