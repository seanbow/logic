from logicsimplifier import *

class KnowledgeBase:
    def __init__(self):
        self.KB = None

    def teach(self, expr):
        '''
        Add a new expression to the knowledge base.
        '''
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = LogicParser().parse(expr)
        if self.KB:
            ## make sure we are not introducing a direct contradiction
            if self.ask(Expression('not', new_expression)) == False:
                self.KB = Expression('and', self.KB, new_expression)
            else:
                raise Exception("Error: teaching this sentence would create a contradiction in the KB")
        else:
            self.KB = new_expression

    def unlearn(self, expr):
        raise NotImplementedError
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = LogicParser().parse(expr)
        clauses = [clause for clause in self.KB.args]
        print (clauses)

    def resolve(self, clause1, clause2):
        '''
        Generates a list of all possible resolvents of clause1 and clause2
        '''
        assert isinstance(clause1, set)
        assert isinstance(clause2, set)
        resolvents = []
        variables = clause1.union(clause2)
        for var in variables:
            inverted = LogicSimplifier().apply_demorgan(Logic.negate(var))
            if inverted in variables:
                ## found one resolvent
                resolvent = variables.difference(set([var, inverted]))
                if resolvent not in resolvents:
                    resolvents.append(resolvent)
        return resolvents

    def clauses_to_sets(self, clauses):
        '''
        Converts a list of clause Expressions to a list of sets
        containing the clauses' variables.
        Example: [(a or b), (~b or c)] returns [{a, b}, {~b, c}]
        '''
        c_sets = []
        for clause in clauses:
            if clause.op in Logic.UNARY:
                # clause is a negated literal
                c_sets.append(set([clause]))
            elif clause.op in Logic.BINARY:
                # clause is a disjunction of literals
                c_sets.append(set(clause.args))
            else:
                # clause is a literal
                c_sets.append(set([clause]))
        return c_sets

    def ask(self, expression, verbose=False):
        '''
        Asks the KB if the expression is true given its current knowledge.
        Returns True if the expression is definitely true, False if it is
        false or if there is not enough knowledge to determine.
        '''
        new_expr = None
        if isinstance(expression, Expression):
            new_expr = expression
        else:
            new_expr = LogicParser().parse(expression)
        new_expr = Expression('not', new_expr)
        newKB = Expression('and', self.KB, new_expr)
        newKB = LogicSimplifier().to_cnf(newKB)
        assert newKB.op == 'and'
##        print ('New KB:', newKB)
        ## we now have a new knowledge base containing (KB && ~a), where ~a
        ## is the inquiry, in CNF form. Perform the actual resolution step.
        clauses = self.clauses_to_sets(newKB.args)
        new_clauses = []
        while True:
            ## iterate over all pairs of clauses
            if verbose: print('--New Iteration--')
            if verbose: print('Clauses:', clauses)
            for i in range(1, len(clauses)):
                for j in range(i):
                    c1 = clauses[i]
                    c2 = clauses[j]
                    if verbose: print("Resolving ", c1, " and ", c2, "...  ", sep='', end='')
                    resolvents = self.resolve(c1, c2)
                    if verbose: print("Resolvents: ", resolvents)
                    ## check for empty clause
                    if set() in resolvents:
                        if verbose: print("Empty clause present in resolvents. Done.")
                        return True
                    new_clauses.extend(resolvents)
            ## check if any new clauses were added
            ## the next line checks if new_clauses is a subset of clauses
            if all([(c in clauses) for c in new_clauses]):
                if verbose: print ("No new clauses added this iteration. Done.")
                return False
            clauses.extend(new_clauses)
        return newKB
        
        
