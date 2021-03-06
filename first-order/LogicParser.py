import re
from LogicTokenizer import *

class Logic:
    BINARY = ['and', 'or', 'implies', 'iff']
    UNARY = ['not']
    QUANTIFIERS = ['forall', 'exists']
    OPS = BINARY + UNARY + QUANTIFIERS
    Precedence = {'not' : 5,
                  'and' : 4,
                  'or' : 3,
                  'implies' : 2,
                  'iff' : 1,
                  'forall' : 0,
                  'exists' : 0}

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

class QuantifiedExpression (Expression):
    def __init__(self, op, var, boundexpr=None):
        assert isinstance(boundexpr, Expression) or boundexpr == None
        if op not in Logic.QUANTIFIERS:
            raise Exception("Error: Bad quantifier")
        self.op = op
        self.var = var
        if boundexpr:
            self.args = [boundexpr]
        else:
            self.args = []

    def __eq__(self, other):
        if other is self: return True
        else:
            return (isinstance(other, QuantifiedExpression) and
                    other.op == self.op and
                    other.var == self.var and
                    other.args == self.args)

    def __call__(self, expr):
        if len(self.args) != 0:
            raise Exception("Error: Quantifier alreay contains expression")
        if not isinstance(expr, Expression):
            raise Exception("Error: QuantifiedExpression must have an Expression as args")
        return QuantifiedExpression(self.op, self.var, expr)

    def __repr__(self):
        return '%s %s.(%s)' % (self.op, self.var, ''.join(map(repr, self.args)))

class Predicate (Expression):
    pass

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

    def parse_tokens(self, tokens):
        '''
        Parses a set of logic tokens, returning an Expression representing their
        meaning.
        Example:
        >>> t = LogicTokenizer().tokenize('a -> (b && c)')
        >>> parse_tokens(t)
        implies[a, and[b, c]]
        '''
        self.tokens = tokens
        RPN = []
        op_stack = []

        bound = []
        num_pushed_parens = 0
        token = self.token()
        while token != None:
            #print('RPN = ', RPN, '; op stack = ', op_stack, sep='')
            if token.type == 'exists' or token.type == 'forall':
                ## keep track of which variable the quantifier binds by storing it in
                ## the token's name field
                assert self.token(0).type == 'bindingvar'
                token.name = self.token(0).name
                op_stack.append(token)
            elif token.type == 'pred':
                op_stack.append(token)
            elif token.type == 'comma':
                token = self.token(0)
                while op_stack[-1].type != 'lparen':
                    RPN.append(op_stack.pop())
            elif token.type == 'bindingvar':
                bound.append(token.name)
                ## give the binding var's opening paren a 'name' so we can easily
                ## identify this variable's scope. If there is no opening paren, the
                ## scope will be until the end of the string.
                if self.token(0).type == 'lparen':
                    self.token(0).name = token.name
            elif token.type == 'var':
                if token.name in bound:
                    RPN.append(Token('boundvar', token.name))
                else:
                    RPN.append(Token('freevar', token.name))
            elif token.type == 'lparen':
                op_stack.append(token)
            elif token.type == 'rparen':
                ## until we find the open paren, pop items off the stack
                ## into the output string
                while op_stack[-1].type != 'lparen':
                    RPN.append(op_stack.pop())
                assert op_stack[-1].type == 'lparen'
                ## check if we're ending a bound variable's scope
                if op_stack[-1].name:
                    bound.remove(op_stack[-1].name)
                op_stack.pop() # remove the lparen, discarding it
                ## check if those parens were for a predicate or quantifier
                if (op_stack[-1].type == 'pred' or op_stack[-1].type == 'exists'
                    or op_stack[-1].type == 'forall'):
                    ## make sure the function call is matched with its arguments
                    RPN.append(op_stack.pop())
            elif token.type in Logic.OPS:
                while (op_stack != [] and op_stack[-1].type in Logic.OPS and
                       Logic.Precedence[op_stack[-1].type] >= Logic.Precedence[token.type]):
                    ## pop off all higher precedence operators
                    ## note: the >= in the above condition rather than > is to
                    ## ensure proper associative behavior:
                    ## a -> b -> c should be interpreted as (a -> b) -> c rather
                    ## than a -> (b -> c).
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
        print(RPN)

        
    def parse(self, string):
        '''
        Parses a string of first-order logic, returning an Expression that
        represents the original string.
        Example:
        "a -> b" returns Expression('implies', Expression('a'), Expression('b'))
        "a and b or c or d" returns an Expression that represents, using prefix notation
            for readability: or[or[and[a, b], c], d]
        '''
        self.tokens = LogicTokenizer().tokenize(string)
        

        RPN = []
        op_stack = []

        bound = []
        num_pushed_parens = 0
        token = self.token()
        while token != None:
            #print('RPN = ', RPN, '; op stack = ', op_stack, sep='')
            if token.type == 'exists' or token.type == 'forall':
                ## keep track of which variable the quantifier binds by storing it in
                ## the token's name field
                assert self.token(0).type == 'bindingvar'
                token.name = self.token(0).name
                op_stack.append(token)
            elif token.type == 'pred':
                op_stack.append(token)
            elif token.type == 'comma':
                token = self.token(0)
                while op_stack[-1].type != 'lparen':
                    RPN.append(op_stack.pop())
            elif token.type == 'bindingvar':
                bound.append(token.name)
                ## give the binding var's opening paren a 'name' so we can easily
                ## identify this variable's scope. If there is no opening paren, the
                ## scope will be until the end of the string.
                if self.token(0).type == 'lparen':
                    self.token(0).name = token.name
            elif token.type == 'var':
                if token.name in bound:
                    RPN.append(Token('boundvar', token.name))
                else:
                    RPN.append(Token('freevar', token.name))
            elif token.type == 'lparen':
                op_stack.append(token)
            elif token.type == 'rparen':
                ## until we find the open paren, pop items off the stack
                ## into the output string
                while op_stack[-1].type != 'lparen':
                    RPN.append(op_stack.pop())
                assert op_stack[-1].type == 'lparen'
                ## check if we're ending a bound variable's scope
                if op_stack[-1].name:
                    bound.remove(op_stack[-1].name)
                op_stack.pop() # remove the lparen, discarding it
                ## check if those parens were for a predicate or quantifier
                if (op_stack[-1].type == 'pred' or op_stack[-1].type == 'exists'
                    or op_stack[-1].type == 'forall'):
                    ## make sure the function call is matched with its arguments
                    RPN.append(op_stack.pop())
            elif token.type in Logic.OPS:
                while (op_stack != [] and op_stack[-1].type in Logic.OPS and
                       Logic.Precedence[op_stack[-1].type] >= Logic.Precedence[token.type]):
                    ## pop off all higher precedence operators
                    ## note: the >= in the above condition rather than > is to
                    ## ensure proper associative behavior:
                    ## a -> b -> c should be interpreted as (a -> b) -> c rather
                    ## than a -> (b -> c).
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
        print(RPN)
        ## RPN now contains our original string in reverse polish notation
        ## parse the RPN to create an Expression representing our string.
        # it is easiest to reverse the RPN string so we can use pop()
        eval_stack = []
        RPN.reverse()
        while RPN != []:
            print('---New Iteration---')
            print('Stack: ')
            [x.print_detailed() for x in eval_stack]
            tok = RPN.pop()
            print('Next Token: %s' % tok.type)
            if tok.type not in Logic.OPS:
                ## tok is a variable or predicate; convert it to an expression and place it
                ## on the stack
                if tok.type == 'pred':
                    eval_stack.append(Predicate(tok.type))
                eval_stack.append(Expression(tok.name))
            elif tok.type in Logic.UNARY:
                ## token is a unary operator. convert it to an expression
                ## and apply it to the top of the stack
                if len(eval_stack) < 1:
                    raise Exception("Error: malformed input string")
                op = Expression(tok.type)
                arg = eval_stack.pop()
                eval_stack.append(op(arg))
            elif tok.type in Logic.QUANTIFIERS:
                if len(eval_stack) < 1:
                    raise Exception("Error: malformed input string")
                op = QuantifiedExpression(tok.type, tok.name)
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
        print('Done! Result: ', end='')
        [x.print_detailed() for x in eval_stack]
        if len(eval_stack) != 1:
            raise Exception("Error: malformed input string")
        return eval_stack[0]

if __name__=="__main__":
    P = LogicParser
