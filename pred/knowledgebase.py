from logicsimplifier import *

class KnowledgeBase:
    def __init__(self):
        self.KB = []

    def clear(self):
        self.KB = []

    def teach(self, expr):
        '''
        Add a new expression to the knowledge base.
        '''
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = LogicParser().parse(expr)
        ## The knowledge base is kept as a list of clauses. Convert the input
        ## expression to CNF and extract its clauses.
        cnf = LogicSimplifier().to_cnf(new_expression)
        new_clauses = self.clauses_to_sets(cnf.args)
        if self.ask(Logic.negate(new_expression)) == False:
            ## make sure we aren't introducing a contradiction into the KB.
            ## TODO figure out how to do this more efficiently
            for clause in new_clauses:
                if clause not in self.KB:
                    self.KB.append(clause)
        else:
            raise Exception("Error: teaching this sentence would create a contradiction in the KB")
        

    def unlearn(self, expr):
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = LogicParser().parse(expr)
        clauses = self.clauses_to_sets(LogicSimplifier().to_cnf(new_expression).args)
        for clause in clauses:
            if clause in self.KB:
                self.KB.remove(clause)

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
        ## create newKB = KB && ~expression
        new_expr = LogicSimplifier().to_cnf(Logic.negate(new_expr))
        assert new_expr.op == 'and'
        new_expr_clauses = self.clauses_to_sets(new_expr.args)
        newKB = self.KB[:]
        newKB.extend(new_expr_clauses)
        ## we now have a new knowledge base containing (KB && ~a), where ~a
        ## is the inquiry, in CNF form. Perform the actual resolution step.
        new_clauses = []
        while True:
            ## iterate over all pairs of clauses
            if verbose: print('--New Iteration--')
            if verbose: print('Clauses:', newKB)
            for i in range(1, len(newKB)):
                for j in range(i):
                    c1 = newKB[i]
                    c2 = newKB[j]
                    if verbose: print("Resolving ", c1, " and ", c2, "...  ", sep='', end='')
                    resolvents = self.resolve(c1, c2)
                    if verbose: print("Resolvents: ", resolvents)
                    ## check for empty clause
                    if set() in resolvents:
                        if verbose: print("Empty clause present in resolvents. Done.")
                        return True
                    new_clauses.extend(resolvents)
            ## check if any new clauses were added
            ## the next line checks if new_clauses is a subset of newKB
            if all([(c in newKB) for c in new_clauses]):
                if verbose: print ("No new clauses added this iteration. Done.")
                return False
            newKB.extend(new_clauses)
        return newKB
        
        
