import re

class LogicTokenizer:
    def __init__(self):
        self.token_res =  [ r"(?P<forall>[aA][lL][lL])",
                        r"(?P<exists>[eE][xX][iI][sS][tT][sS])",
                        r"(?P<and>[aA][nN][dD]|\&\&)",       # and
                        r"(?P<or>[oO][rR]|\|\|)",               # or
                        r"(?P<not>\~|\!|not)",                  # not
                        r"(?P<implies>\-\>|\=\>|[iI][mM][pP][lL][iI][eE][sS])", # implies
                        r"(?P<iff>\<\-\>|\<\=\>|iff)",          # iff
                        r"(?P<whitespace>\s+)",                 # whitespace
                        r"(?P<lparen>\()",                      # (
                        r"(?P<rparen>\))",                      # )
                        r"(?P<comma>,)",
                        r"(?P<pred>[A-Z][a-zA-Z0-9]*(?=\())",   # predicates
                        r"(?P<bindingvar>[a-zA-Z0-9]+\.)",      # binding variables
                        r"(?P<var>[a-zA-Z0-9\_]+)"]             # free or bound variables
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
                raise SystemExit('bad string in tokenized')

            groups = match.groups()
            if match.lastgroup == 'var' or match.lastgroup == 'pred':
                self.tokenized.append(Token(match.lastgroup, match.group(0)))
            elif match.lastgroup == 'bindingvar':
                self.tokenized.append(Token(match.lastgroup, match.group(0)[:-1]))
            elif match.lastgroup == 'forall' or match.lastgroup == 'exists':
                self.tokenized.append(Token(match.lastgroup, match.group(0)))
            elif match.lastgroup != 'whitespace':
                self.tokenized.append(Token(match.lastgroup))


            pos = match.end()
        return self.tokenized
                
class Token:
    def __init__(self, type, value=None):
        self.type = type
        self.name = value

    def __repr__(self):
        if self.name == None:
            return 'Token(%s)' % repr(self.type)

        else:
            return 'Token(%s, %s)' % (repr(self.type), repr(self.name))
