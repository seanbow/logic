import re
from LogicTokenizer import *

class Logic:
    OPS = ['not', 'and', 'or', 'implies', 'iff']
    BINARY = ['and', 'or', 'implies', 'iff']
    UNARY = ['not']
    Precedence = {'not' : 5,
                  'and' : 4,
                  'or' : 3,
                  'implies' : 2,
                  'iff' : 1}

    def negate(s):
        '''
        Returns the negation of an expression.
        Useful so you don't need to type Expression('not', s).
        Also works with unparsed strings, e.g. Not('a => b')
        '''
        if isinstance(s, Expression):
            return Expression('not', s)
        else:
            return Expression('not', LogicParser().parse(s))

class Expression:
    '''
    A class representing an expression of propositional logic.
    Contains either an operator and arguments or a single variable.
    Examples: Expression('P') -> the variable P
              Expression('not', Expression('P')) -> ~P
              Expression('and', Expression('P'), Expression('Q')) -> P && Q

    Allows for operator expressions, e.g. Expression('and'). These expressions
    are especially handy because they can be called on other expressions. For example,
    you can define AND = Expression('and'), and calling AND(a, b) results in
    Expression('and', a, b) or (a and b). This is done by overriding the __call__ method.
    '''
    def __init__(self, op, *args):
        self.op = op
        self.args = args
        
    def __repr__(self):
        if len(self.args) == 0:
            # constant or operator with no arguments (e.g. 'F' or 'and')
            return str(self.op)
        elif self.op in Logic.UNARY:
            # unary operator plus its argument
            if (self.op == 'not'):
                return '~' + repr(self.args[0])
            return self.op + repr(self.args[0])
        else:
            # infix operator and its two or more arguments
            # "or more" example: Expression('and', P, Q, R) -> P && Q && R.
            return '(%s)' % (' '+self.op+' ').join(map(repr, self.args))

    def __eq__(self, other):
        return (other is self) or (isinstance(other, Expression)
                                   and self.op == other.op
                                   and self.args == other.args)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.op) ^ hash(self.args)

    def print_detailed(self):
        print(self.detail_string())

    def detail_string(self):
        s = ''
        if self.op in Logic.OPS:
            s = self.op + '('
        else:
            s = self.op
        arg_strs = [arg.detail_string() for arg in self.args]
        s += ', '.join(arg_strs)
        if self.op in Logic.OPS:
            s += ')'
        return s
        
    def __call__(self, *args):
        if len(self.args) != 0:
            raise Exception("Cannot call an expression with variables")
        if self.op not in Logic.OPS:
            raise Exception("Cannot call a variable")
        if self.op in Logic.UNARY and len(args) > 1:
            raise Exception("Cannot apply a unary operator to more than one argument")
        return Expression(self.op, *args)

class LogicParser:
    def token(self, destructive=1):
        ''' Retrieves the next token from the input string (after
        it has been tokenized).
        Destructive sets whether to advance the token pointer; using
        destructive=0 gives you look-ahead abilities'''
        if self.tokens == []:
            return None
        result = self.tokens[0]
        if destructive:
            self.tokens = self.tokens[1:]
        return result
    
    def parse(self, string):
        '''
        Parses a string of propositional logic, returning an Expression that
        represents the original string.
        Example:
        "a -> b" returns Expression('implies', Expression('a'), Expression('b'))
        "a and b or c or d" returns an Expression that represents, using prefix notation
            for readability: or[or[and[a, b], c], d]
        '''
        self.tokens = LogicTokenizer().tokenize(string)

        RPN = []
        op_stack = []

        token = self.token()
        while token != None:
            #print('RPN = ', RPN, '; op stack = ', op_stack, sep='')
            if token.type == 'var':
                RPN.append(token)
            elif token.type == 'lparen':
                op_stack.append(token)
            elif token.type == 'rparen':
                ## until we find the open paren, pop items off the stack
                ## into the output string
                while op_stack[-1].type != 'lparen':
                    RPN.append(op_stack.pop())
                assert op_stack[-1].type == 'lparen'
                op_stack.pop() # remove the lparen, discarding it
            elif token.type in Logic.OPS:
                while (op_stack != [] and op_stack[-1].type in Logic.OPS and
                       ((Logic.Precedence[op_stack[-1].type] >= Logic.Precedence[token.type] and
                        op_stack[-1].type != 'not') or
                       (Logic.Precedence[op_stack[-1].type] > Logic.Precedence[token.type] and
                        op_stack[-1].type == 'not'))):
                    ## pop off all higher precedence operators
                    ## note: the >= in the above condition rather than > is to
                    ## ensure proper associative behavior:
                    ## a -> b -> c should be interpreted as (a -> b) -> c rather
                    ## than a -> (b -> c).
                    ## Additionally, the shunting algorithm wasn't made to handle unary operators ('not')
                    ## and breaks unless they're handled specially. If they're present, they should be
                    ## considered to have lower precedence than themself so the algorithm doesn't try to
                    ## negate nothing and cause an exception.
                    RPN.append(op_stack.pop())
                op_stack.append(token)
            ## read the next token
            token = self.token()
        ## no more tokens to read here, push the rest onto our output stack
        while op_stack != []:
            op = op_stack.pop()
            if op.type == 'lparen' or op.type == 'rparen':
                raise Exception("String has mismatched parens")
            RPN.append(op)
        #print(RPN)
        ## RPN now contains our original string in reverse polish notation
        ## parse the RPN to create an Expression representing our string.
        # it is easiest to reverse the RPN string so we can use pop()
        eval_stack = []
        RPN.reverse()
        #print(RPN)
        while RPN != []:
            tok = RPN.pop()
            if tok.type not in Logic.OPS:
                ## tok is a variable; convert it to an expression and place it
                ## on the stack
                eval_stack.append(Expression(tok.name))
            elif tok.type in Logic.UNARY:
                ## token is a unary operator. convert it to an expression
                ## and apply it to the top of the stack
                if len(eval_stack) < 1:
                    raise Exception("Error: malformed input string")
                op = Expression(tok.type)
                arg = eval_stack.pop()
                eval_stack.append(op(arg))
            elif tok.type in Logic.BINARY:
                ## Same as unary but with two arguments
                if len(eval_stack) < 2:
                    raise Exception("Error: malformed input string")
                op = Expression(tok.type)
                # note: because we are evaluating arguments in the opposite
                # order of how they were originally present in the string, we
                # need to reverse the order for binary operators
                arg1 = eval_stack.pop()
                arg2 = eval_stack.pop()
                eval_stack.append(op(arg2, arg1))
            else:
                raise Exception("Error: malformed input string")
        ## Hopefully we're done parsing now and the result is left on the stack
        if len(eval_stack) != 1:
            raise Exception("Error: malformed input string")
        return eval_stack[0]
       
