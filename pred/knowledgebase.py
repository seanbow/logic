from LogicSimplifier import *

class KnowledgeBase:
    def __init__(self):
        self.KB = []
        self.parser = LogicParser()

    def clear(self):
        ''' Empties the KB. '''
        self.KB = []

    def tell(self, expr, safe=False):
        '''
        Add a new expression to the knowledge base.
        Includes an optional 'safe' flag that ensures no contradiction is
        introduced to the knowledge base. This may cause the telling procedure to
        run slowly.
        '''
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = self.parser.parse(expr)
        ## The knowledge base is kept as a list of clauses. Convert the input
        ## expression to CNF and extract its clauses.
        cnf = LogicSimplifier().to_cnf(new_expression)
        new_clauses = self.clauses_to_sets(cnf.args)
        if not safe or self.ask(Logic.negate(new_expression)) == False:
            ## If the "safe" flag is set, we want to ensure no contradiction is
            ## added to the KB. This may be very slow.
            self.insert_clauses(new_clauses)
        else:
            raise Exception("Error: teaching this sentence would create a contradiction in the KB")

    def unlearn(self, expr):
        '''
        Removes all clauses that make up expr in CNF form from the database.
        '''
        new_expression = None
        if isinstance(expr, Expression):
            new_expression = expr
        else:
            new_expression = self.parser.parse(expr)
        clauses = self.clauses_to_sets(LogicSimplifier().to_cnf(new_expression).args)
        for clause in clauses:
            if clause in self.KB:
                self.KB.remove(clause)

    def resolve(self, clause1, clause2):
        '''
        Generates a list of all possible resolvents of clause1 and clause2
        Inputs: clauses in set form
        Output: list of resolvent clauses
        Example usage:

        >>> kb.resolve({a, ~b, c}, {~a, b, d})
        [{c, a, ~a, d}, {b, c, ~b, d}]
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
        containing the clauses' variables. Requires that the input
        expressions be clauses, i.e. a list of variables OR'd together or
        a single literal.
        Example usage:
        
        >>> clauses_to_sets([(a or b), (~b or c), e])
        [{a, b}, {~b, c}, {e}]
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

    def insert_clauses(self, clauses):
        '''
        Insert a list of clauses into the knowledge base, maintaining a sorted
        order (by clause length) and ignoring duplicates.
        '''
        for clause in clauses:
            self.insert(clause, self.KB)

    def insert(self, clause, KB):
        '''
        Inserts a new clause into the KB argument, maintaining the state of
        sortedness while avoiding inserting duplicates.
        '''
        assert isinstance(clause, set)
        i = 0
        while i < len(KB):
            if clause == KB[i]:
                # duplicate entry, don't add the new clause
                return
            if len(clause) < len(KB[i]):
                KB.insert(i, clause)
                return
            i += 1
        KB.append(clause)

    def ask(self, expression):
        '''
        Asks the KB whether its current knowledge entails the expression.
        Uses an optimized resolution algorithm described in the paper.
        '''
        new_expr = LogicParser().parse(expression)
        new_expr = LogicSimplifier().to_cnf(Logic.negate(new_expr))
        assert new_expr.op == 'and'
        new_clauses = self.clauses_to_sets(new_expr.args)
        newKB = self.KB[:]
        #for clause in new_clauses:
        #    self.insert(clause, newKB)
        while True:
            old_len = len(new_clauses)
            for c1 in new_clauses:
                for c2 in (newKB + new_clauses):
                    if c1 == c2: continue
                    resolvents = self.resolve(c1, c2)
                    if set() in resolvents: return True
                    for clause in resolvents:
                        self.insert(clause, new_clauses)
            ## check if we found any new clauses
            if len(new_clauses) <= old_len:
                ## no new clauses
                return False
    
    def slow_ask(self, expression, verbose=False):
        '''
        Asks the KB whether its current knowledge entails the expression.
        Uses a slow, brute-force resolution algorithm as described in
        Russell & Norvig.
        '''
        new_expr = None
        if isinstance(expression, Expression):
            new_expr = expression
        else:
            new_expr = self.parser.parse(expression)
        ## create newKB = KB && ~expression
        new_expr = LogicSimplifier().to_cnf(Logic.negate(new_expr))
        assert new_expr.op == 'and'
        new_expr_clauses = self.clauses_to_sets(new_expr.args)
        newKB = self.KB[:]
        newKB.extend(new_expr_clauses)
        ## we now have a new knowledge base containing (KB && ~a), where ~a
        ## is the inquiry, in CNF form. Perform the actual resolution step.
        while True:
            new_clauses = []
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
