from logicparser import *


def FlattenedExpression(op, *args):
    return LogicSimplifier().flatten(Expression(op, *args))

class LogicSimplifier:
    def to_cnf(self, s):
        assert isinstance(s, Expression)
        new = self.eliminate_biconditionals(s)
        new = self.eliminate_implications(new)
        new = self.apply_demorgan(new)
        new = self.distribute_or_over_and(new)
        new = self.flatten(new)
        ## handle all cases uniformly; if the input is a single variable, create
        ## an expression and[s]
        if new.op != 'and':
            new = Expression('and', new)
        return new

    def eliminate_biconditionals(self, s):
        '''Recursively searches the expression for <->, replacing every instance:
        A <-> B becomes (A -> B) and (B -> A)'''
        assert isinstance(s, Expression)
        A = None
        B = None
        if len(s.args) == 1:
            ## unary operator
            A = self.eliminate_biconditionals(s.args[0])
        elif len(s.args) == 2:
            ## binary operator, maybe iff
            A = self.eliminate_biconditionals(s.args[0])
            B = self.eliminate_biconditionals(s.args[1])
            if s.op == 'iff':
                # replace the <->:
                # A <-> B becomes ((A -> B) and (B -> A))
                subexp1 = Expression('implies', A, B)
                subexp2 = Expression('implies', B, A)
                return Expression('and', subexp1, subexp2)
        if A and B:
            return Expression(s.op, A, B)
        elif A:
            return Expression(s.op, A)
        else:
            return Expression(s.op)
    
    def eliminate_implications(self, s):
        '''Recursively searches the expression for ->, replacing every instance.
        Example: A -> B becomes ~A or B'''
        assert isinstance(s, Expression)
##        print(s)
        A = None
        B = None
        if len(s.args) == 1:
            ## unary operator
            A = self.eliminate_implications(s.args[0])
        elif len(s.args) == 2:
            ## binary operator, maybe ->
            A = self.eliminate_implications(s.args[0])
            B = self.eliminate_implications(s.args[1])
            if s.op == 'implies':
                # replace the ->:
                subexp1 = Expression('not', A)
                subexp2 = B
                return Expression('or', subexp1, subexp2)
        if A and B:
            return Expression(s.op, A, B)
        elif A:
            return Expression(s.op, A)
        else:
            return Expression(s.op)

    def apply_demorgan(self, s):
        '''Function that "moves the not inwards" by repeated applications
        of DeMorgan's rule; example, ~(a or b) will become (~a and ~b)'''
        # unlike eliminate_iffs/implications, this proceeds in a top-down
        # rather tha bottom-up fashion. First eliminate a not at the top level
        # and then proceed downwards.
        assert isinstance(s, Expression)
        newexp = Expression(s.op, *s.args)
        #print(newexp)
        if s.op == 'not':
            assert len(s.args) == 1
            inner = s.args[0]
            # check for a double negation
            if inner.op == 'not':
                # this is simple, we can just remove both nots
                newexp = inner.args[0]
            # check for and/or for demorgan
            elif inner.op == 'and':
                ## apply demorgan
                A = Expression('not', inner.args[0])
                B = Expression('not', inner.args[1])
                newexp = Expression('or', A, B)
            elif inner.op == 'or':
                ## apply demorgan
                A = Expression('not', inner.args[0])
                B = Expression('not', inner.args[1])
                newexp = Expression('and', A, B)
        if len(newexp.args) == 1:
            A = self.apply_demorgan(newexp.args[0])
            return Expression(newexp.op, A)
        elif len(newexp.args) == 2:
            A = self.apply_demorgan(newexp.args[0])
            B = self.apply_demorgan(newexp.args[1])
            return Expression(newexp.op, A, B)
        else:
            return newexp

    def flatten(self, s):
        '''This function flattens nestings of the same operator into a
        single expression with >2 arguments. For example, and(and(a, b), c) would
        become and(a, b, c).

        CAUTION: Most algorithms in this code do NOT work with a flattened
        logic structure; they break if any expression contains more than two
        arguments. Use this only before distribute_or_over_and, which requires it'''
        assert isinstance(s, Expression)
        if s.op == 'and':
            args = list(s.args)
            for nested in s.args:
                if nested.op == 'and':
                    args.extend(list(nested.args))
                    args.remove(nested)
                    s.args = tuple(args)
        elif s.op == 'or':
            args = list(s.args)
            for nested in s.args:
                if nested.op == 'or':
                    args.extend(list(nested.args))
                    args.remove(nested)
                    s.args = tuple(args)
        for arg in s.args:
            self.flatten(arg)
        return s

    def distribute_or_over_and(self, s):
        # search for any expression that looks like (a or (b and c)) and convert
        # it to (a or b) and (a or c)
        assert isinstance(s, Expression)
        self.flatten(s)
        if s.op == 'or':
            if len(s.args) == 1:
                return self.distribute_or_over_and(s.args[0])
            ## Distribute over one group at a time. Find the first group
            ## that is a set of and'd expressions
            conj = None
            conjugates = [arg for arg in s.args if arg.op == 'and']
            if conjugates != []:
                conj = conjugates[0]
            if not conj:
                return FlattenedExpression('or', *map(self.distribute_or_over_and, s.args))
            ## create an expression of everything except for the and'd expression
            ## of interest
            other_exprs = [arg for arg in s.args if arg is not conj]
            remaining = None
            if len(other_exprs) == 1:
                remaining = other_exprs[0]
            else:
                remaining = FlattenedExpression('or', *other_exprs)
            ## Now actually perform the distribution by ORing each element of
            ## conj with everything else, and throwing it all together in an AND
            ## We also need to recursively distribute among the child expressions
            distributed_exprs = [FlattenedExpression('or', c, remaining) for c in conj.args]
            return FlattenedExpression('and', *map(self.distribute_or_over_and, distributed_exprs))
        elif s.op == 'and':
            return FlattenedExpression('and', *map(self.distribute_or_over_and, s.args))
        return s  
