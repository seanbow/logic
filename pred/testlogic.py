from KnowledgeBase import *
from time import clock

f = open('tests.txt', 'r')
testid = -1
naive_times = []
fast_times = []
num_clauses = []
kb = KnowledgeBase()
line = f.readline()
while line != '':
    line = line.strip()
    #print(line)
    if line == 'KB:':
        kb.clear()
        testid += 1
        print("Running test %d...  "%testid, end='')
    elif line == 'ASSERT:':
        num_clauses.append(len(kb.KB))
        line = f.readline().strip()
        #print(line)
        ## Check with the naive algorithm
        startTime = clock()
        assert kb.slow_ask(line)
        naive_times.append(clock() - startTime)
        ## Check with optimized algorithm
        startTime = clock()
        assert kb.ask(line)
        fast_times.append(clock() - startTime)
        print("Passed.")
    elif line != '':
        kb.tell(line)
    line = f.readline()
        
