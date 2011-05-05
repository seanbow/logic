import re

class LogicTokenizer:
    def __init__(self):
        self.token_res =  [r"(?P<and>[aA][nN][dD]|\&\&)",       # and
                        r"(?P<or>[oO][rR]|\|\|)",               # or
                        r"(?P<not>\~|\!|not)",                  # not
                        r"(?P<implies>\-\>|\=\>|[iI][mM][pP][lL][iI][eE][sS])", # implies
                        r"(?P<iff>\<\-\>|\<\=\>|[iI][fF][fF])",          # iff
                        r"(?P<whitespace>\s+)",                 # whitespace
                        r"(?P<lparen>\()",                      # (
                        r"(?P<rparen>\))",                      # )
                        r"(?P<var>[a-zA-Z0-9\_]+)"]             # variable names
        self.pattern = '|'.join(self.token_res)
        self.regex = re.compile(self.pattern)

    def tokenize(self, string):
        pos = 0
        N = len(string)
        self.tokenized = []
        while pos < N:
            #print('searching for token in ' + string[pos:])
            match = self.regex.match(string, pos)
            if match == None:
                raise Exception('Error: malformed input string.')

            groups = match.groups()
            if match.lastgroup != 'var' and match.lastgroup != 'whitespace':
                self.tokenized.append(Token(match.lastgroup))
            elif match.lastgroup == 'var':
                self.tokenized.append(Token(match.lastgroup, match.group(0)))

            pos = match.end()
        return self.tokenized
                
class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value
        self.name = value

    def __repr__(self):
        if self.value == None:
            return 'Token(%s)' % repr(self.type)

        else:
            return 'Token(%s, %s)' % (repr(self.type), repr(self.value))
