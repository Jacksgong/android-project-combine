from shlex import shlex
from ast import literal_eval

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


with open("build.gradle", "r") as f:
    print GroovyConfigSlurper(f).parse()
