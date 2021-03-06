from collections import defaultdict
import subprocess   
from copy import copy
import os
import numpy as np
from .ring import *
from random import sample
from .utils import save_graphviz,view_graphviz
def CartesianProduct_aut(A,B):
    alpha1 = [(a,b) for a in A._alphabet for b in B._alphabet]
    states = [(p,q) for p in A._states for q in B._states]
    transitions = {}
    alphabet = []
    for a in alpha1:
        alphabet.append(a[0]+"#"+a[1])    
    for x in states:
        for a in alphabet:
            transitions[(tuple(x),a)] = [(A._transitions[(x[0],a[0])][0],B._transitions[(x[1],a[2])][0])]
    initial_states = []
    final_states = []
    for x in A._initial_states:
        for y in B._initial_states:
            initial_states.append((x,y))
    for x in A._final_states:
        for y in B._final_states:
            final_states.append((x,y))
    return Automaton(transitions,initial_states,final_states,alphabet=alphabet)    

def random_automaton(size, alphabet):
    states = range(size)
    transition = {}
    for x in states:
        for a in alphabet:
            transition[(x,a)] = sample(states,1)
    return Automaton(transition,sample(states,1),sample(states,1),states,alphabet)
    
    
class Automaton(object):
    def __init__(self, transitions, initial_states, final_states, states=None, alphabet=None, aut_type="boolean"):
        r"""
        INPUT:

        - ``transitions`` - dictionnary of (state, letter) -> list of states
        - ``initial_states`` - list of states
        - ``final_states`` - list of states
        - ``states`` - set of states
        - ``alphabet`` - set of letters
        - ``aut_type`` - type of automaton (boolean or buchi for now).
        OUTPUT:

        automata

        EXAMPLES::

            sage: from pysemigroup import Automaton
            sage: d={('p','a'):'q',('q','a'):'p',('p','b'):'p',('q','b'):'q'}
            sage: A= Automaton(d,['p'],['p'])
        """

        self._transitions = dict(transitions)

        if alphabet:
             self._alphabet = set(alphabet)
        else:
            alphabet = set([])
            for i in transitions:
                alphabet.add(i[1])
            self._alphabet = alphabet
        if states:
            self._states = set(states)
        else:
            states = set([])
            for i in transitions:
                    states = states|set([i[0]])
                    states = states|set(transitions[i])
            self._states = states

        self._initial_states = list(initial_states)
        self._final_states = list(final_states)
        self._is_semigroup_computed = False
        self._type = aut_type
    @classmethod
    def from_letter(Automaton, letter,alphabet=None):
        r"""
        convert word into the minimal deterministic automaton that recognized word

        INPUT:

        - ``letter`` - string different from the empty word

        OUTPUT :

        automaton

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: A = Automaton.from_letter('a')
            sage: A
            Automaton of 2 states
            sage: A.is_accepted("a")
            True
            sage: A.is_accepted("")
            False
        """
        if (letter == ''):
            raise ValueError("input must be non-empty word")
        initial_states = [0]
        final_states = [1]
        transitions = {(0,letter):[1]}
        if alphabet:
            return Automaton(transitions, initial_states, final_states,alphabet=alphabet)
        else:    
            return Automaton(transitions, initial_states, final_states,alphabet=set([letter]))
    def rename_letters(self, dic):
        alphabet = set()
        for x in self._alphabet:
            if dic[x] in alphabet:
                raise ValueError("input must be a bijection")
            else:
                alphabet.add(dic[x])
        transitions = {}
        for x in self._transitions:
            transitions[(x[0],dic[x[1]])] = self._transitions[x]

        self._alphabet = alphabet
        self._transitions = transitions

    @classmethod    
    def from_empty_string(Automaton,letters):
        r"""

        INPUT:

            - ``letters`` -- list of letters

        OUTPUT :

        automaton

        EXAMPLES::
        """
        initial_states = [0]
        final_states = [0]   
        transitions = {}     
        for a in letters:
            transitions[(0,a)] = [1]
        return Automaton(transitions, initial_states, final_states)
        
        
    @classmethod
    def from_theirs(Automaton, their):
        r"""
        Convert sage automaton to ours

        INPUT:

        - ``their`` - instance of finite_state_machine.Automaton

        OUTPUT :

        Automaton

        EXAMPLES:: 
       
            sage: from pysemigroup import Automaton
            sage: d = {('p','a'):'q',('q','a'):'p',('p','b'):'p',('q','b'):'q'}     
            sage: A = Automaton(d,['p'],['q'])
            sage: B = A.to_theirs()
            sage: B
            Automaton with 2 states
            sage: Automaton.from_theirs(B)
            Automaton of 2 states

        """

        initial_states = [s.label() for s in their.initial_states()]
        final_states = [s.label() for s in their.final_states()]
        transitions = defaultdict(list)
        for t in their.transitions():
             stateA = t.from_state.label()
             stateB = t.to_state.label()
             if len(t.word_in) != 1:
                 raise NotImplementedError("we assume len(t.word_in) == 1 in the following code")
             letter = t.word_in[0]
             transitions[(stateA,letter)].append(stateB)
        return Automaton(transitions, initial_states, final_states)
       
        
    def to_sage_automaton(self):
        r"""
        Return Sage version of this automaton.

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: d = {('p','a'):'q',('q','a'):'p',('p','b'):'p',('q','b'):'q'}
            sage: A = Automaton(d,['p'],['q'])
            sage: A
            Automaton of 2 states
            sage: B = A.to_theirs()
            sage: B
            Automaton with 2 states
            sage: B.initial_states()
            ['p']
            sage: B.final_states()
            ['q']
            
        Non deterministic example::
            
            sage: d = {('p','a'):['q','p'],('q','a'):'p',('p','b'):'p'}
            sage: A = Automaton(d,['p'],['q'])
            sage: B = A.to_theirs()
            sage: B  
            Automaton with 2 states


        """
        L = []
        for ((stateA,letter), statesB) in self._transitions.iteritems():
            for stateB in statesB:
                L.append((stateA,stateB,letter))
        from sage.combinat.finite_state_machine import Automaton as Automaton_theirs
        return Automaton_theirs(L, initial_states=self._initial_states, final_states=self._final_states)
    def view(self,save_to_file=None,extension="svg"):
        r"""
        """
        view_graphviz(self.graphviz_string(),save_to_file=save_to_file,extension=extension)
    def save(self,save_to_file,extension="svg"):
        r"""
        """
        save_graphviz(self.graphviz_string(),save_to_file,extension=extension)            
    def __repr__(self):
        r"""
        String representation.

        EXAMPLES::

            sage: from pysemigroup import Automaton
            sage: d={('p','a'):'q',('q','a'):'p',('p','b'):'p',('q','b'):'q'}
            sage: A= Automaton(d,['p'],['p'])
            sage: A
            Automaton of 2 states
        """
        s = "%s automaton of %s states" %(self._type,len(self._states))
        return s
    def __pos__(self):
        return self
        
    def __add__(self, other):
        r"""
        Return an automaton that compute the union of self and other.

        INPUT:

        -  ``self`` -  Automaton
        -  ``other`` -  Automaton

        OUTPUT:

        Automaton

        EXAMPLES:

        Here is a first test::

            sage: from pysemigroup import Automaton
            sage: d={('p','a'):'q',('q','a'):'p',('p','b'):'p',('q','b'):'q'}
            sage: A= Automaton(d,['p'],['p'])
            sage: A + A
            Automaton of 4 states
            sage: A + A + A
            Automaton of 6 states
        """
        alphabet = self._alphabet.union(other._alphabet)
        d = {}
        count = 0
        for i in self._states:
            d[(i,0)] = count
            count = count+1
        for i in other._states:
            d[(i,1)] = count
            count = count+1
        transitions = {}
        for x in self._transitions:
            transitions[(d[(x[0],0)],x[1])] = []
            for y in self._transitions[x]:
                transitions[(d[(x[0],0)],x[1])].append(d[(y,0)])
        for x in other._transitions:
            transitions[(d[(x[0],1)],x[1])] = []
            for y in other._transitions[x]:
                transitions[(d[(x[0],1)],x[1])].append(d[(y,1)])

        initial_states = []
        final_states = []
        for x in self._initial_states:
            initial_states.append(d[(x,0)])
        for x in other._initial_states:
            initial_states.append(d[(x,1)])
        for x in self._final_states:
            final_states.append(d[(x,0)])
        for x in other._final_states:
            final_states.append(d[(x,1)])

        return Automaton(transitions, initial_states, final_states,alphabet=alphabet)
         
    def __mul__(self, other):
        r"""
        Return an automaton that compute the concatenation of self and other.

        INPUT:

        -  ``self`` -  Automaton
        -  ``other`` -  Automaton

        OUTPUT:

        Automaton

        EXAMPLES::
            sage: from pysemigroup import Automaton
            sage: e = {('p', 'a'): ['q'], ('p', 'b'): ['p'], ('q', 'a'): ['q'], ('q', 'b'): ['q']}
            sage: d = {('p', 'a'): ['p'], ('p', 'b'): ['q'], ('q', 'a'): ['q'], ('q', 'b'): ['q']}
            sage: A = Automaton(d, ['p'] ,['p'])
            sage: B = Automaton(e, ['p'] ,['p'])
            sage: C = A*B
            sage: C.is_accepted("aab")
            True
            sage: C.is_accepted("b")
            True
            sage: C.is_accepted("a")
            True
            sage: C.is_accepted("ab")
            True
            sage: C.is_accepted("bab")
            False
        """
        alphabet = self._alphabet.union(other._alphabet)
        d = {}
        count = 0
        for i in self._states:
            d[(i,0)] = count
            count = count+1
        for i in other._states:
            d[(i,1)] = count
            count = count+1
        initial_states = []
        empty_word = (len (set(self._initial_states).intersection(self._final_states)) > 0)
        for i in self._initial_states:
            initial_states.append(d[(i,0)])
        if empty_word :
            for i in other._initial_states:
                initial_states.append(d[(i,1)])
        final_states = []
        for i in other._final_states:
            final_states.append(d[(i,1)])
        transitions = {}
        for x in self._transitions:
            transitions[(d[(x[0],0)],x[1])] = []
            for y in self._transitions[x]:
                transitions[(d[(x[0],0)],x[1])].append(d[(y,0)])
                if y in self._final_states:
                    for z in other._initial_states:
                        if transitions[(d[(x[0],0)],x[1])].count(d[(z,1)]) == 0:
                            transitions[(d[(x[0],0)],x[1])].append(d[(z,1)])
        for x in other._transitions:
            transitions[(d[(x[0],1)],x[1])] = []
            for y in other._transitions[x]:
                transitions[(d[(x[0],1)],x[1])].append(d[(y,1)])
        return Automaton(transitions, initial_states, final_states,alphabet=alphabet)

    def __neg__(self) :
        r"""
        Return the complement of self

        OUTPUT:

        Automaton

        EXAMPLES::
        """

   
        A = self.deterministic_automaton()
        final_states = []
        for i in (A._states - set(A._final_states)):
            final_states.append(i)
        return Automaton(A._transitions, A._initial_states, final_states,alphabet=A._alphabet,states=A._states)

    def intersection(self, other):
        r"""

        OUTPUT:

        automaton 

        EXAMPLE::

        """
        return (-((-(self))+(-(other))))

 

        
    def __sub__(self, other):
        r"""

        OUTPUT:

        automaton 

        """
        return  self.intersection(-(other))




    def kleene_star(self):
        r"""
        Return the Kleen power of self

        INPUT:

        -  ``self`` -  Automaton

        OUTPUT:

        Automaton

        EXAMPLES::
            sage: from pysemigroup import Automaton
            sage: d = { ('p', 'a') : 'q', ('q','b') :'r' }
            sage: A = Automaton(d, ['p'] ,['r'])
            sage: A.is_accepted('ab')
            True
            sage: A.is_accepted('')
            False
            sage: A.is_accepted('abab')
            False
            sage: B = A.kleene_star()
            sage: B.is_accepted('')
            True
            sage: B.is_accepted('ab')
            True
            sage: B.is_accepted('abab')
            True
            sage: B.is_accepted('aba')
            False
        """
        transitions = {}
        for x in self._transitions:
            transitions[x] = []
            for y in self._transitions[x]:
                transitions[x].append(y)
                if y in self._final_states:
                    for z in self._initial_states:
                        if transitions[x].count(z) == 0:
                            transitions[x].append(z)
        final_states = []
        for i in set(self._initial_states)|set(self._final_states):
            final_states.append(i)
        return Automaton(transitions, self._initial_states, final_states,alphabet=self._alphabet)
    def __xor__(self,exponent):
        return self.__pow__(exponent)
    
    def __pow__(self, exponent):
        r"""
        Return power of self.

        INPUT:

        -  ``exponent`` -  integer or string

        OUTPUT:

        automaton

        EXAMPLES::

        """
        if exponent == "_star":
            return self.kleene_star()
        elif exponent == 1:
            return self
        elif exponent <= 0:
            raise ValueError("Exponent must be strictly positive")
        else:
            return self.__pow__(exponent-1)*self

    def is_accepted(self, u):
        r"""
        Return whether u is in self.

        INPUT:

        -  ``u`` -  word

        OUTPUT:

        boolean

        EXAMPLES::
            sage: from pysemigroup import Automaton
            sage: d = {('p', 'a'): ['p'], ('p', 'b'): ['p', 'q']}
            sage: A = Automaton(d,['p'],['q'])
            sage: A.is_accepted('bab')
            True
            sage: A.is_accepted('ba')
            False
        """
        q = set(self._initial_states)
        for i in range(len(u)):
            qp = []
            for j in q:
                if (j,u[i]) in self._transitions:
                    qp.extend(self._transitions[(j,u[i])])
            q = set(qp)
        return not (set(q).intersection(set(self._final_states)) == set())

    def is_deterministic(self):
        r"""
        Return whether the automaton is deterministic.

        INPUT:

        -  ``self`` -  Automaton

        OUTPUT:

        boolean

        EXAMPLES:
            sage: from pysemigroup import Automaton
            sage: d={('q', 'b'): 'q', ('p', 'a'): 'q', ('q', 'a'): 'p', ('p', 'b'): 'p'}
            sage: A= Automaton(d,['p'],['q'])
            sage: A.is_deterministic()
            True
            sage: d={('p', 'a'): ['q','p'], ('p', 'b'): 'p'}
            sage: A= Automaton(d,['p'],['q'])
            sage: A.is_deterministic()
            False
        """
        for x in self._transitions:
            if len(self._transitions[x]) > 1:
                return False
        return True

    def reverse_transitions(self):
        r"""
        Reverse the transitions of self

        EXAMPLES:

            sage: from pysemigroup import Automaton
            sage: d={('q', 'b'): 'q', ('q', 'a'): 'p', ('p', 'b'): 'p'}
            sage: A = Automaton(d,['p'],['q'])
            sage: A.reverse_transitions()
            sage: A._transitions
            {('p', 'a'): ['q'], ('p', 'b'): ['p'], ('q', 'b'): ['q']}
            sage: A._initial_states
            ['q']
            sage: A._final_states
            ['p']
        """
        transitions = {}
        for i in self._alphabet:
            for j in self._states:
                for k in self._states:
                    if (k,i) in self._transitions:
                        if self._transitions[(k,i)].count(j)>0:
                            if (j,i) in transitions:
                                transitions[(j,i)].append(k)
                            else:
                                transitions[(j,i)] = [k]
        self._transitions = transitions
        buff = self._initial_states
        self._initial_states = self._final_states
        self._final_states = buff

    def trim_automata(self):
        r"""
        Trim the automaton self

        EXAMPLES:

            sage: from pysemigroup import Automaton
            sage: d={('q', 'b'): 'q', ('q', 'a'): 'p', ('p', 'b'): 'p'}
            sage: A = Automaton(d,['p'],['q'])
            sage: A.trim_automata()
            sage: A._transitions
            {('p', 'b'): 'p'}
        """
        reach = self._initial_states
        new = True
        while new:
            new = False

            for i in reach:
                for j in self._alphabet:
                    if (i,j) in self._transitions:
                        S = set(self._transitions[(i,j)])
                        for k in S:
                            if reach.count(k) == 0:
                                new = True
                                reach.append(k)
        transitions = {}
        for i in reach:
            for j in self._alphabet:
                if (i,j) in self._transitions:
                    transitions[(i,j)] = self._transitions[(i,j)]
        final_states = []
        for i in self._final_states:
            if i in reach:
                final_states.append(i)
        self._transitions = transitions
        self._final_states = final_states


    def rename_states(self):
        r"""
        Rename the states of self

        EXAMPLES:

            sage: from pysemigroup import Automaton
            sage: d = {('p', 'a'): 'p', ('p', 'b'): ['q', 'p'], (frozenset(['a']), 'a'): 'b'}
            sage: A = Automaton(d,['p'],['q'])
            sage: sorted(A._states) 
            [frozenset({'a'}), 'b', 'p', 'q']
            sage: A.rename_states()
            sage: sorted(A._states)
            [0, 1, 2, 3]
        """
        l = list(self._states)
        states = set(range(len(l)))
        transitions = {}
        for i in self._transitions:
            transitions[(l.index(i[0]),i[1])]=[]
            for j in self._transitions[i]:
                transitions[(l.index(i[0]),i[1])].append(l.index(j))

        initial_states = []
        final_states = []
        for i in self._initial_states:
            initial_states.append(l.index(i))

        for i in self._final_states:
            final_states.append(l.index(i))
        self._initial_states = initial_states
        self._final_states = final_states
        self._transitions = transitions
        self._states = states
        
    def is_finite_state_reachable(self):
        r"""
        Return whether the 

        OUTPUT:

        Boolean

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: d = {('p', 'a'): ['p'], ('p', 'b'): ['p', 'q']}
            sage: A = Automaton(d, ['p'], ['q'])
            sage: A.is_finite_state_reachable()
            True

        """    
        if len(set(self._initial_states).intersection(set(self._final_states))) > 0:
            return True
        to_test = set(self._initial_states)
        tested = set()
        while to_test:
            state = to_test.pop()
            tested.add(state)
            for a in self._alphabet:
                if (state,a) in self._transitions:
                    for b in self._transitions[(state,a)]:
                        if b not in tested:
                            to_test.add(b)
                        if b in self._final_states:
                            return True
        return False                                        
    
    def deterministic_automaton(self, rename_states=False):
        r"""
        Return a deterministic version of the automaton by the powerset method.

        INPUT:

        - ``rename_states`` -- bool (default: False),

        OUTPUT:

        Automaton

        EXAMPLES::

            sage: from pysemigroup import Automaton
            sage: d = {('p', 'a'): ['p'], ('p', 'b'): ['p', 'q']}
            sage: A = Automaton(d, ['p'], ['q'])
            sage: A
            Automaton of 2 states
            sage: A.deterministic_automaton()
            Automaton of 4 states

        TESTS::

            sage: A.is_deterministic()
            False
            sage: A.is_accepted('baaa')
            False
            sage: A.is_accepted('baaab')
            True
            sage: B = A.deterministic_automaton()
            sage: B.is_deterministic()
            True
            sage: B.is_accepted('baaa')
            False
            sage: B.is_accepted('baaab')
            True
        """

        transitions = {}
        init_states = frozenset(self._initial_states)
        reach = set([init_states])
        new = True
        while new :
           new = False
           for i in reach:
               for j in self._alphabet:
                   if not ((i,j) in transitions):
                       succi = []
                       for k in i:
                           if (k,j) in self._transitions :
                               succi.extend(self._transitions[(k,j)])
                           else :
                               succi.extend([()])
                       succi = frozenset(succi)
                       if not succi in reach :
                           reach = reach | set([succi])
                           new = True
                       transitions[(i,j)] = [succi]
        final_states = []
        for i in reach:
            if not(set(self._final_states).intersection(i) == set()):
                final_states.append(i)
        A = Automaton(transitions=transitions,states=reach,initial_states=[init_states],
                     final_states=final_states)
        if rename_states:
            A.rename_states()
        return A
    def minimal_automaton(self,algorithm=None,rename_states=True):
        r"""
        Minimize the automaton self

        INPUT:

        - ``algorithm`` -- None, or "Brzozowski" or "Moore" or "Hopcroft"
        - ``rename_states`` -- bool (default: True),

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: d = {('p', 'a'): ['p'], ('p', 'b'): ['p', 'q']}
            sage: A = Automaton(d, ['p'],['q'])
            
        ::
        
            sage: B = A.minimal_automaton()
            sage: B
            Automaton of 2 states
            sage: B._states
            {0, 1}            

        ::
        
            sage: C = A.minimal_automaton(algorithm="Brzozowski")
            sage: C
            Automaton of 2 states
            sage: C._states
            {0, 1}
            
        ::
        
            sage: D = A.minimal_automaton(algorithm="Moore")
            sage: D
            Automaton of 2 states
            sage: D._states
            {0, 1}    
        

        """        
        if (algorithm is None) or (algorithm == "Hopcroft"):
            R = self._minimal_automaton_hopcroft()
        elif algorithm == "Moore":
            their = self.to_theirs()
            their = their.determinisation()            
            M = their.minimization(algorithm=algorithm)
            R = Automaton.from_theirs(M)
        elif algorithm == "Brzozowski":
            their = self.to_theirs()
            M = their.minimization(algorithm=algorithm)
            R = Automaton.from_theirs(M)
        else:
            raise NotImplementedError("Algorithm '"+algorithm+"' is not implemented. Choose 'Hopcroft' or 'Moore' or 'Brzozowski'")   
        if rename_states:
            R.rename_states()
        return R  
    
    def _minimal_automaton_hopcroft(self):
        r"""
        Minimize the automaton self

        EXAMPLES::

            

        """
        AD = self.deterministic_automaton(rename_states=True)
        P = set([frozenset(AD._final_states),frozenset(AD._states)-frozenset(AD._final_states)])
        W = set([frozenset(AD._final_states)])
        first = True
        while len(W) > 0 :
            A = W.pop()
            for c in AD._alphabet:
                X = set([])
                for i in AD._states :
                    if (i,c) in AD._transitions:
                        if len(set(AD._transitions[(i,c)]).intersection(A)) > 0:
                            X.add(i)
                            first = True
                if len(X) > 0:
                    Pp = set([])
                    Pp = copy(P)
                    for Y in P:
                        if (len(Y.intersection(X)) > 0) and (len(Y-X)>0) :
                            Pp.remove(Y)
                            Pp.add(frozenset(Y.intersection(X)))
                            Pp.add(frozenset((Y-X)))

                            if (Y in W):
                                W.remove(Y)
                                W.add(frozenset(Y.intersection(X)))
                                W.add(frozenset(Y-X))
                            else:
                                if len(Y.intersection(X)) <= len(Y - X):
                                    W.add(frozenset(Y.intersection(X)))
                                else :
                                    W.add(frozenset(Y-X))                
                    P= copy(Pp)
        states =[]       
        for i in P:
            if not (i==set([])):                  
                states.append(tuple(i))
        transitions =  {}
        for i in states:
            for j in AD._alphabet:
                p = AD._transitions[(i[0],j)]
                for k in states:
                    if k.count(p[0]) > 0:
                        transitions[(i,j)] = [k]                          
        final_states = []
        initial_states = []
        for i in states:
            if i.count(AD._initial_states[0]) > 0 :
                # la ligne qui suit semble effacer l'info accumulee
                initial_states = [i]

            if len(set(i).intersection(set(AD._final_states))) > 0 :
                final_states.append(i)

        B = Automaton(transitions=transitions,states=states,initial_states=initial_states,
                     final_states=final_states)
        return B

    def word_to_transitions(self, u):
        r"""
        Return the application from the set of states to set of states induced by the word u

        EXAMPLES::
            sage: from pysemigroup import Automaton
            sage: d = {(0, 'a'): [1], (1, 'a'): [0]}
            sage: B = Automaton(d,[0],[1])
            sage: B.is_equivalent("aa","aaa")
            False
            sage: B.is_equivalent("aa","aaaa")
            True
            sage: B.word_to_transitions("aa")
            {0: 0, 1: 1}
        """
        if not self.is_deterministic() :
            print('The automaton must be deterministic')
        else:
            d={}
            for i in self._states:
                q = i
                fail = False
                for j in range(len(u)):
                    if ((q,u[j]) in self._transitions) and not fail:
                        q = self._transitions[(q,u[j])][0]
                    else :
                        fail = True
                if not fail:
                    d[i] = q

            return d


    def is_equivalent(self, u, v):
        r"""
        Return wether u is syntatically equivalent to v for Automaton self
        INPUT :
        -  ``self`` -  Automaton
         -  ``u`` -  string
         -  ``v`` -  string

         OUTPUT:

        boolean

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: d = {(0, 'a'): [1], (1, 'a'): [0]}
            sage: B = Automaton(d,[0],[1])
            sage: B.is_equivalent("aa","aaa")
            False
            sage: B.is_equivalent("aa","aaaa")
            True
                
        """

        d_u = self.word_to_transitions(u)
        d_v = self.word_to_transitions(v)
        for i in self._states:
            if ((i in d_u) and (i in d_v)):
                if not (d_u[i] == d_v[i]) :
                    return False
            else :
                if ((i in d_u) and not (i in d_v)) or ((i in d_v) and not (i in d_u)):
                    return False
        return True
    def graphviz_string(self): 
        r"""
        Return graphviz representation of self. 
        INPUT :
        -  ``self`` -  Automaton

         OUTPUT:

        string

        EXAMPLES::
        
            sage: from pysemigroup import Automaton
            sage: d = {(0, 'a'): [1], (1, 'a'): [0]}
            sage: B = Automaton(d,[0],[1])
            sage: B.graphviz_string()
            'digraph {\n ranksep=0.5;\n d2tdocpreamble = "\\usetikzlibrary{automata}";\n d2tfigpreamble = "\\tikzstyle{every state}= [ draw=blue!50,very thick,fill=blue!20]  \\tikzstyle{auto}= [fill=white]";\n node [style="state"];\n edge [lblstyle="auto",topath="bend right", len=4  ]\n  "0" [label="0",style = "state, initial"];\n  "1" [label="1",style = "state, accepting"];\n  "0" -> "1" [label="a"];\n  "1" -> "0" [label="a"];\n}'
                
        """

        s = 'digraph {\n node [margin=0 shape=circle style=filled]\n edge [len =2]\n' 
        for x in self._states:
            s = s+'  "'+str(x)+'" [label="'+str(x)+'" '
            if x in self._initial_states:
                if x in self._final_states:
                    s = s+'shape = doublecircle fillcolor = "#aaff80" '
                else:
                    s = s+'fillcolor = "#aaff80"'
            else:
                if x in self._final_states:
                    s = s+'shape = doublecircle fillcolor = lightblue '
                else:
                    s = s+' fillcolor = lightblue'
                    
                   
            s = s+"];\n"
        for x in self._states:        
            for y in self._states:
                edge = []
                for a in self._alphabet:
                    if (x,a) in self._transitions and y in self._transitions[(x,a)]:
                        edge.append(a)
                if len(edge)>0:
                    s = s+ '  "'+str(x)+'" -> "'+str(y)+'" [label="'+str(edge.pop())
                    while len(edge)>0:
                        s = s+ ','+str(edge.pop())
                    s = s + '"'
                    if y == x:
                        s =  s+ ',topath="loop above"'
                    s = s + '];\n'
        s = s+'}'
        return s
    
    def to_dot(self, file_name):
        r"""
        Save to filename a dot file representing the automata. 
        INPUT :
        -  ``self`` -  Automaton
        -  ``file_name`` -  string        
        """
        s = self.graphviz_string()
        f = file(file_name+".dot",'w')  
        f.write(s)
        f.close()

    def to_gif(self, file_name, prog="dot"):
        r"""
        Save to filename a gif file representing the automata obtained with prog (dot neato circo).
        INPUT :
        -  ``self`` -  Automaton
        -  ``file_name`` -  string 
        -  ``prog`` -  string          
        """

        self.to_dot(file_name)
        if prog in ["dot","circo","neato"]:              
            os.system(prog+' -Tgif  '+file_name+'.dot -o'+file_name+'.gif')
            os.system('rm '+file_name+'.dot')
        else:
            raise ValueError("Unimplemented prog="+prog)


    def to_svg(self, file_name, prog="dot"):
        r"""
        Save to filename a gif file representing the automata obtained with prog (dot neato circo).
        INPUT :
        -  ``self`` -  Automaton
        -  ``file_name`` -  string 
        -  ``prog`` -  string          
        """
 
        self.to_dot(file_name)
        if prog in ["dot","circo","neato"]:              
            os.system(prog+' -Tsvg  '+file_name+'.dot -o'+file_name+'.svg')
            os.system('rm '+file_name+'.dot')
        else:
            raise ValueError("Unimplemented prog="+prog)
    def identity_on_automata_ring(self):
        r"""
        """
        d = {}
        if self._type == "boolean":
            return hash_matrix(np.identity(len(self._states),dtype=int))
        if self._type == "buchi":
            for x in range(len(self._states)):
                for y in range(len(self._states)):
                    if x == y:
                        d[(x,y)]=1
                    else:
                        d[(x,y)]=0
            return RingMatrix((len(self._states),len(self._states)),d)        
        raise ValueError("Automaton type"+self._type+" is unsupported yet")

    def letter_to_algebra(self,letter,verbose=True):
        r"""
        return a matrix representing letter action on state.
        The return type depend on the choosed of aut_type in init. Only work
        for boolean and buchi type.
        INPUT :
        -  ``self`` -  Automaton
        -  ``letter`` -  string 
        OUTPUT :
        - an object representing matrix on adequate ring
        """
        if self._type == "boolean":
            states = list(self._states)
            n = len(states)
            L = []
            for x in range(n):
                Lx = list()
                for y in range(n):
                    if ((states[x],letter) in self._transitions)  and (states[y] in self._transitions[(states[x],letter)]):
                        Lx.append(1)
                    else:
                        Lx.append(0)
                L.append(Lx)
            return hash_matrix(L)
        if self._type == "buchi":
            d = {}
            states = self._states       
            for y in states:
                for z in states:
                    d[(y,z)] = "-oo"            
                    if ((y,letter) in self._transitions) and (z in self._transitions[(y,letter)]):
                        if (z in self._final_states):
                            d[(y,z)] = 1
                        else:
                            d[(y,z)] = 0
                    else:
                        d[(y,z)] = "-oo"
            fctx = BuchiMatrix((self._states,self._states),d)            
            return fctx
        raise ValueError("Automaton type"+self._type+" is unsupported yet")

