import numpy as np
import copy

NUMBER=(int,float)

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
        elif isinstance(other,extExpr):
            raise ValueError("not implemented yet, add symb expr")
        else:
            raise ValueError("Addition between Symbol and "+str(type(other))+" not supported")

    def __radd__(self,other):

        return self + other

    def __mul__(self,other):
        if isinstance(other,Symbol):
            newself = self.term()
            newother = other.term()

            return newself*newother
        elif isinstance(other,NUMBER):
            newself = self.term()
            newother = Coef(other).term()

            return newself*newother
        elif isinstance(other,extExpr):
            raise ValueError("not implemented yet, add symb expr")
        else:
            raise ValueError("Multiplication between Symbol and "+str(type(other))+" not supported")

    def __rmul__(self,other):

        return self * other

    def term(self):
        return termExpr(Coef(1),np.array([1]),[self.key])



class Coef(Symbol):

    key = 0

    def __init__(self,value):
        self.key = 0
        self.string = str(value)
        self.derivative = 0
        self.value = value
        self.isnumber = True

    def __add__(self,other):
        if isinstance(self,Coef):
            newvalue = self.value + other.value

            return Coef(newvalue)
        else:
            raise ValueError("Trying to add a non Coef object to Coef")

    def __mul__(self,other):
        if isinstance(self,Coef):
            newvalue = self.value * other.value

            return Coef(newvalue)
        else:
            raise ValueError("Trying to multiply a non Coef object to Coef")

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
            print("to implement")


### Expressions ###
class termExpr:

    def __init__(self,coef,body,keys):
        self.coef = coef
        self.body = body
        self.keys = keys

    def append(self,value=0):
        self.body = np.append(self.body,value)

    def set(self,pos,power):
        self.body[pos] = power

    def expr(self):
        return extExpr(np.array([copy.deepcopy(self)]),self.keys)

    def _sync(self,other):
        if not isinstance(other,termExpr):
            raise ValueError("Trying to sync termExpr with a non termExpr object "+str(type(other)))
        if self.keys==other.keys:
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
        other.keys = newkeys
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
        else:
            raise ValueError("Trying to add termExpr with a non termExr object "+str(type(other)))

    def __radd__(self,other):
        return self + other

    def __mul__(self,other):
        if isinstance(other,termExpr):
            self._sync(other)

            newbody = self.body+other.body
            newcoef = self.coef*other.coef

            return termExpr(newcoef,newbody,self.keys)
        else:
            raise ValueError("Trying to multiply termExpr with a non termExr object")

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

        return string

    def __repr__(self):
        return str(self)


class extExpr:

    @staticmethod
    def add(self,other):
        if not isinstance(self,extExpr) or not isinstance(other,extExpr):
            raise ValueError("Tryint to add non extExpr")
        else:
            res = self + other
            res._simplifyterms()

            return res

    @staticmethod
    def mul(self,other):
        if not isinstance(self,extExpr) or not isinstance(other,extExpr):
            raise ValueError("Tryint to add non extExpr")
        else:
            res = self * other
            res._simplifyterms()

            return res


    def __init__(self,terms=[],keys=[]):
        if len(terms)==0:
            self.terms = np.array([termExpr(Coef(0),[1],[Coef.key])],dtype=termExpr)
            self.keys = self.terms[0].keys
        elif len(terms[0].body)!=len(keys):
            raise ValueError("len terms != len keys")
        else:
            self.terms = terms
            self.keys = keys

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
        self._update_termskeys(keys)

    def _update_termskeys(self,keys):
        for term in self.terms:
            term._set_keys(keys)

    def _sync(self,other):
        if not isinstance(other,extExpr):
            raise ValueError("Trying to sync expr with a non expr type")

        newkeys = copy.deepcopy(self.keys)
        for key in other.keys:
            if key not in newkeys:
                newkeys.append(key)
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

    def _simplifyterms(self):

        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if ii_term in terms_to_drop:
                continue
            for jj_term in range(ii_term+1,len(self.terms)):
                if jj_term in terms_to_drop:
                    continue
                if np.array_equal(self.terms[ii_term].body,self.terms[jj_term].body):
                    self.terms[ii_term].coef += self.terms[jj_term].coef
                    terms_to_drop.append(jj_term)

        newterms = np.array([],dtype=termExpr)
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newterms = np.append(newterms,self.terms[ii_term])

        self.terms = newterms

    def __add__(self,other):
        if isinstance(other,extExpr):

            self._sync(other)

            newterms = copy.deepcopy(self.terms)
            for term in other.terms:
                newterms = np.append(newterms,term)

            newkeys = self.keys

            return extExpr(newterms,newkeys)
        else:
            raise ValueError("Addition between extExpr and "+str(type(other))+" not implemented")

    def __mul__(self,other):
        if isinstance(other,extExpr):

            self._sync(other)

            newterms = np.array([],dtype=termExpr)

            for interm in self.terms:
                for jterm in other.terms:
                    newterms = np.append(newterms,interm*jterm)

            return extExpr(newterms,self.keys)


        else:
            raise ValueError("Addition between extExpr and "+str(type(other))+" not implemented")
