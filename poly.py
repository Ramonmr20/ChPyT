import numpy as np
import copy

NUMBER=(int,float,np.int64,complex)

### Individual objects ###
class Symbol:

    objtable = [[0,None]]

    @staticmethod
    def get_obj(key):
        if len(Symbol.objtable)<key:
            raise ValueError("Id not in table")

        return Symbol.objtable[key][1]

    @staticmethod
    def _insert_obj(obj):
        key = len(Symbol.objtable)
        Symbol.objtable.append([key,obj])

        return key

    def __init__(self,ser):
        self.key = Symbol._insert_obj(self)
        self.string = ser
        self.derivative = 0


    def __str__(self):
        string = self.string

        return string

    def __repr__(self):
        return str(self)

    def __add__(self,other):
        if isinstance(other,Symbol):
            newself = self.term()
            newother = other.term()

            return newself + newother
        elif isinstance(other,NUMBER):
            newself = self.term()
            newother = Coef(other).term()

            return newself + newother
        elif isinstance(other,termExpr):
            newself = self.term()

            return newself + other
        elif isinstance(other,extExpr):
            newself = self.term().expr()

            return newself + other
        else:
            raise ValueError("Addition between Symbol and "+str(type(other))+" not supported")

    def __radd__(self,other):

        return self + other

    def __sub__(self,other):
        return self + Coef(-1)*other

    def __rsub__(self,other):
        return Coef(-1)*self + other

    def __mul__(self,other):
        if isinstance(other,Symbol):
            newself = self.term()
            newother = other.term()

            return newself*newother
        elif isinstance(other,NUMBER):
            if other==0:
                return Coef(0).term()
            newself = self.term()
            newother = Coef(other).term()

            return newself*newother
        elif isinstance(other,termExpr):
            newself = self.term()
            return newself*other
        elif isinstance(other,extExpr):
            newself = self.term().expr()
            return newself * other
        else:
            raise ValueError("Multiplication between Symbol and "+str(type(other))+" not supported")

    def __rmul__(self,other):

        return self * other

    def __pow__(self,other):
        return termExpr(Coef(1),np.array([other]),[self.key])


    def __eq__(self,other):

        try:
            if self.key==other.key:
                return True
            else:
                return False
        except:
            return False

    def term(self):
        return termExpr(Coef(1),np.array([1]),[self.key])

    def partial(self,index):
        return Coef(0)


class Coef(Symbol):

    key = 0

    def __init__(self,value):
        self.key = 0
        self.string = str(value)
        self.derivative = 0
        self.value = value
        self.isnumber = True

    def __add__(self,other):
        if isinstance(other,Coef):
            newvalue = self.value + other.value

            return Coef(newvalue)
        elif isinstance(other,NUMBER):
            return Coef(self.value+other)
        else:
            try:
                return other.__radd__(self)
            except:
                raise ValueError("Trying to add a non Coef object to Coef",type(other))

    def __mul__(self,other):
        if isinstance(other,Coef):
            newvalue = self.value * other.value

            return Coef(newvalue)
        elif isinstance(other,NUMBER):
            return Coef(self.value*other)
        elif isinstance(other,Symbol):
            newself = self.term()
            newother = other.term()
            return newself*newother
        elif isinstance(other,termExpr):
            newself = self.term()
            return newself*other
        elif isinstance(other,extExpr):
            newself = self.term().expr()
            return newself*other
        else:
            try:
                return other*self
            except:
                raise ValueError("Trying to multiply a non Coef object to Coef "+str(type(other)))

    def __str__(self):
        return self.string

    def term(self):
        return termExpr(self,np.array([1]),[self.key])

class Zero(Symbol):

    included = False

    def __init__(self):
        if not Zero.included:
            self.key = Symbol._insert_obj(self)
            self.string = "0"
            self.derivative = 0
            self.included = True
        else:
            raise ValueError("to implement")


### Expressions ###
class termExpr:

    def __init__(self,coef,body,keys):
        self.coef = coef
        self.body = body
        self.keys = keys
        self.keydict = self._genkeydict()

    def append(self,value=0):
        self.body = np.append(self.body,value)

    def set(self,pos,power):
        self.body[pos] = power

    def expr(self):
        return extExpr(np.array([copy.deepcopy(self)]),self.keys)

    def _genkeydict(self):

        newdict = {}

        for ii_key in range(len(self.keys)):
            newdict[str(self.keys[ii_key])] = ii_key

        return newdict

    def _sync(self,other):
        if not isinstance(other,termExpr):
            try:
                other = other.term()
            except:
                raise ValueError("Trying to sync termExpr with a non termExpr object "+str(type(other)))
        if list(self.keys)==list(other.keys):
            return 0

        newkeys = copy.deepcopy(self.keys)
        for key in other.keys:
            if key not in newkeys:
                newkeys = np.append(newkeys,key)
                self.append()

        newotherbody = np.array([0]*len(newkeys))
        for ii_key in range(len(newkeys)):
            for ii_okey in range(len(other.keys)):
                if newkeys[ii_key]==other.keys[ii_okey]:
                    newotherbody[ii_key] = other.body[ii_okey]

        self.keys = newkeys
        self.keydict = self._genkeydict()
        other.keys = newkeys
        other.keydict = other._genkeydict()
        other.body = newotherbody

    def _set_keys(self,keys):
        self.keys = keys

    def __add__(self,other):
        if isinstance(other,termExpr):
            newself = self.expr()
            newother = other.expr()

            return newself + newother
        elif isinstance(other,NUMBER):
            newself = self.expr()
            newother = Coef(other).term().expr()

            return newself+newother
        elif isinstance(other,extExpr):
            newself = self.expr()

            return newself + other
        else:
            raise ValueError("Trying to add termExpr with a non termExr object "+str(type(other)))

    def __radd__(self,other):
        return self + other

    def __sub__(self,other):
        return self + Coef(-1)*other

    def __rsub__(self,other):
        return Coef(-1)*self + other

    def __mul__(self,other):
        if isinstance(other,termExpr):
            newself = copy.deepcopy(self)
            newother = copy.deepcopy(other)

            newself._sync(newother)

            newbody = newself.body+newother.body
            newcoef = newself.coef*newother.coef

            return termExpr(newcoef,newbody,newself.keys)
        elif isinstance(other,Coef):
            newother = other.term()
            return self*newother
        elif isinstance(other,Symbol):
            newother = other.term()
            return self*newother
        elif isinstance(other,NUMBER):
            newother = Coef(other).term()

            return self*newother
        elif isinstance(other,extExpr):
            newself = self.expr()

            return newself*other
        elif isinstance(other,np.ndarray):
            return np.multiply(self,other)
        else:
            print(isinstance(other,Symbol))
            raise ValueError("Trying to multiply termExpr with a non termExr object "+str(type(other)))

    def __rmul__(self,other):
        return self * other

    def __str__(self):
        string = ""

        if self.coef.isnumber and self.coef.value!=1:
            string += str(self.coef)+"*"
        for ii in range(len(self.body)):
            if self.keys[ii]==Coef.key:
                continue
            elif self.body[ii]==1:
                string += str(Symbol.get_obj(self.keys[ii])) + "*"
            elif self.body[ii]==0:
                continue
            elif self.body[ii]>0:
                string += str(Symbol.get_obj(self.keys[ii]))+ "^" + str(self.body[ii]) + "*"
            else:
                string += str(Symbol.get_obj(self.keys[ii]))+ "^(" + str(self.body[ii]) + ")*"

        string = string[:-1]

        string += " + "

        string = string[:-3]

        # Special case where term = 1
        if string=="":
            string = "1"

        return string

    def __repr__(self):
        return str(self)

    def partial(self,index,simplify=True):

        terms = []

        for ii in range(len(self.body)):
            if self.keys[ii]==Coef.key:
                continue
            elif self.body[ii]==0:
                continue
            else:
                newtermbody = copy.deepcopy(self.body)
                newtermbody[ii] -= 1
                newterm = termExpr(self.coef*(newtermbody[ii]+1),newtermbody,copy.deepcopy(self.keys))

                terms.append(newterm*Symbol.get_obj(self.keys[ii]).partial(index))

        if len(terms)==0:
            return Coef(0)

        for ii_term in range(1,len(terms)):
            terms[0]._sync(terms[ii_term])

        for ii_term in range(1,len(terms)):
            terms[0]._sync(terms[ii_term])

        newexpr = extExpr(terms,terms[0].keys)

        if simplify:
            extExpr.simplifyterms(newexpr)

        return newexpr



class extExpr:

    @staticmethod
    def add(self,other):
        if not isinstance(self,extExpr) or not isinstance(other,extExpr):
            raise ValueError("Tryint to add non extExpr")
        else:
            res = self + other
            extExpr.simplifyterms(res)

            return res

    @staticmethod
    def mul(self,other):
        if not isinstance(self,extExpr) or not isinstance(other,extExpr):
            raise ValueError("Tryint to add non extExpr")
        else:
            res = self * other
            extExpr.simplifyterms(res)

            return res

    def _genkeydict(self):

        newdict = {}

        for ii_key in range(len(self.keys)):
            newdict[str(self.keys[ii_key])] = ii_key

        return newdict


    def __init__(self,terms=[],keys=[]):
        if len(terms)==0:
            self.terms = np.array([termExpr(Coef(0),[1],[Coef.key])],dtype=termExpr)
            self.keys = self.terms[0].keys
            self.keydict = self._genkeydict()
        elif len(terms[0].body)!=len(keys):
            raise ValueError("len terms != len keys")
        else:
            self.terms = terms
            self.keys = keys
            self.keydict = self._genkeydict()

    def __str__(self):
        string = ""

        # TODO consider negative coefficients so that there is no +- something
        for term in self.terms:
            string += str(term) + " + "

        string = string[:-3]

        return string

    def __repr__(self):
        return str(self)

    def _addemptytoterms(self):
        for term in self.terms:
            term.append(0)

    def _set_keys(self,keys):
        self.keys = keys
        self.keydict = self._genkeydict()
        self._update_termskeys(keys,self.keydict)

    def _update_termskeys(self,keys,keydict):
        for term in self.terms:
            term._set_keys(keys)
            term.keydict = keydict

    def _sync(self,other):
        if not isinstance(other,extExpr):
            try:
                other = other.expr()
            except:
                try:
                    other = other.term().expr()
                except:
                    raise ValueError("Trying to sync expr with a non expr type")

        newkeys = copy.deepcopy(self.keys)
        for key in other.keys:
            if key not in newkeys:
                newkeys = np.append(newkeys,key)
                self._addemptytoterms()

        newotherterms = []
        for oterm in other.terms:
            nt = termExpr(oterm.coef,np.array([0]*len(newkeys)),oterm.keys)

            for ii_key in range(len(newkeys)):
                for ii_okey in range(len(other.keys)):
                    if newkeys[ii_key]==other.keys[ii_okey]:
                        nt.set(ii_key,oterm.body[ii_okey])

            newotherterms.append(nt)

        self._set_keys(newkeys)
        other.terms = newotherterms
        other._set_keys(newkeys)

    @staticmethod
    def simplifyterms(self):

        # Sum equal terms
        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if ii_term in terms_to_drop:
                continue
            for jj_term in range(ii_term+1,len(self.terms)):
                if jj_term in terms_to_drop:
                    continue
                if Coef.key in self.keydict:
                    iibody_nocoef = np.append(self.terms[ii_term].body[:self.keydict[str(Coef.key)]],self.terms[ii_term].body[self.keydict[str(Coef.key)]+1:])
                    jjbody_nocoef = np.append(self.terms[jj_term].body[:self.keydict[str(Coef.key)]],self.terms[jj_term].body[self.keydict[str(Coef.key)]+1:])
                else:
                    iibody_nocoef = self.terms[ii_term].body
                    jjbody_nocoef = self.terms[jj_term].body
                if np.array_equal(iibody_nocoef,jjbody_nocoef):
                    self.terms[ii_term].coef += self.terms[jj_term].coef
                    terms_to_drop.append(jj_term)

        newterms = np.array([],dtype=termExpr)
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newterms = np.append(newterms,self.terms[ii_term])

        self.terms = newterms

        # Delete 0s
        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if self.terms[ii_term].coef.value==0:
                terms_to_drop.append(ii_term)

        newterms = np.array([],dtype=termExpr)
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newterms = np.append(newterms,self.terms[ii_term])

        # If it is empty, return 0 expression
        if len(newterms)==0:
            newb = [0]*len(self.keys)
            for ii_key in range(len(self.keys)):
                if self.keys[ii_key]==Coef.key:
                    newb[ii_key] = 1
            newterms = np.append(newterms,termExpr(Coef(0),newb,self.keys))

        self.terms = newterms

    def __add__(self,other):
        if isinstance(other,extExpr):

            newself = copy.deepcopy(self)
            newother = copy.deepcopy(other)

            newself._sync(newother)

            newterms = copy.deepcopy(newself.terms)
            for term in newother.terms:
                newterms = np.append(newterms,term)

            newkeys = newself.keys

            newexpr = extExpr(newterms,newkeys)
            extExpr.simplifyterms(newexpr)

            return newexpr

        elif isinstance(other,NUMBER):
            newother = Coef(other).term().expr()

            return self + newother

        elif isinstance(other,Coef):
            newother = other.term().expr()

            return self + newother

        elif isinstance(other,termExpr):
            newother = other.expr()

            return self + newother
        else:
            raise ValueError("Addition between extExpr and "+str(type(other))+" not implemented")

    def __radd__(self,other):
        return self + other

    def __mul__(self,other):
        if isinstance(other,extExpr):

            newself = copy.deepcopy(self)
            newother = copy.deepcopy(other)

            newself._sync(newother)

            newterms = np.array([],dtype=termExpr)

            for interm in newself.terms:
                for jterm in newother.terms:
                    newterms = np.append(newterms,interm*jterm)

            newexpr = extExpr(newterms,newself.keys)
            extExpr.simplifyterms(newexpr)

            return newexpr

        elif isinstance(other,NUMBER):
            if other==0:
                return Coef(0).term().expr()

            newother = Coef(other).term().expr()

            return self*newother
        elif isinstance(other,Symbol):
            newother = other.term().expr()

            return self * newother
        elif isinstance(other,termExpr):
            newother = other.expr()

            return self*newother
        else:
            raise ValueError("Multiplication between extExpr and "+str(type(other))+" not implemented")

    def __rmul__(self,other):
        return self*other

    def __sub__(self,other):
        return self + Coef(-1)*other

    def __rsub__(self,other):
        return Coef(-1)*self + other

    def partial(self,index,simplify=True):

        newself = copy.deepcopy(self)

        newExpr = Coef(0).term().expr()

        for term in newself.terms:
            newExpr += term.partial(index)

        if simplify:
            extExpr.simplifyterms(newExpr)

        return newExpr
