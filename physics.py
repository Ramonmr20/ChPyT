#!/usr/bin/env python3

import poly
import numpy as np
import copy

class ScalarField(poly.Symbol):

    @staticmethod
    def link_antiparticles(a,b):
        a.antiparticle = b.key
        b.antiparticle = a.key

    def __init__(self,symbol,point,key=None):
        if not key:
            self.key = self._insert_obj(symbol,point)
        else:
            self.key = key

        self.string = symbol+"("+str(point)+")"
        self.derivative = 0
        self.antiparticle = self.key
        self.point = point
        self.symbol = symbol

    def _insert_obj(self,symbol,point):

        for ii_entry in range(len(poly.Symbol.objtable)):
            obj = poly.Symbol.objtable[ii_entry][1]
            key = -1
            if isinstance(obj,ScalarField):
                if obj.symbol==symbol and obj.point==point:
                    key = poly.Symbol.objtable[ii_entry][0]
                    break

        if key==-1:
            key = poly.Symbol._insert_obj(self)

        return key

    def get_antiparticle(self):

        if self.antiparticle==self.key:
            return copy.deepcopy(self)

        newfield = ScalarField(poly.Symbol.get_obj(self.antiparticle).symbol,self.point,key=self.antiparticle)
        newfield.antiparticle = self.key
        newfield.derivative = self.derivative

        return newfield

    def partial(self,index):
        return FieldDerivative(self,index)

    def change_point(self,newpoint):
        newField = ScalarField(self.symbol,newpoint)
        newField.antiparticle = self.antiparticle

        return newField

class LorentzIndex1(poly.Symbol):

    def __init__(self,symbol,index):
        self.key = poly.Symbol._insert_obj(self)
        self.string = symbol + "_" + str(index)
        self.derivative = 0
        self.antiparticle = None
        self.index = index

class FieldDerivative(LorentzIndex1):

    def __init__(self,field,index):
        self.key = self._insert_obj(field,index)
        self.string = u"\u2202_" + str(index) + "(" + str(field) + ")"
        self.derivative = 1
        self.antiparticle = field.antiparticle
        self.index = index
        self.parent = field.key
        self.point = field.point

    def _insert_obj(self,field,index):

        for ii_entry in range(len(poly.Symbol.objtable)):
            obj = poly.Symbol.objtable[ii_entry][1]
            key = -1
            if isinstance(obj,FieldDerivative):
                if obj.parent==field.key and obj.index==index:
                    key = poly.Symbol.objtable[ii_entry][0]
                    break

        if key==-1:
            key = poly.Symbol._insert_obj(self)

        return key

    def change_point(self,point):
        return FieldDerivative(poly.Symbol.get_obj(self.parent).change_point(point),self.index)

    def get_antiparticle(self):
        newfieldderivative = FieldDerivative(poly.Symbol.get_obj(self.parent).get_antiparticle(),self.index)

        return newfieldderivative


class Propagator(poly.Symbol):

    def __init__(self,field,pointa,pointb):
        self.key = self._insert_obj(field,pointa,pointb)
        self.field = field
        self.pointa = pointa
        self.pointb = pointb
        self.string = "D_"+str(field.symbol)+"("+str(pointa)+"-"+str(pointb)+")"

    def _insert_obj(self,field,pointa,pointb):

        for ii_entry in range(len(poly.Symbol.objtable)):
            obj = poly.Symbol.objtable[ii_entry][1]
            key = -1
            if isinstance(obj,Propagator):
                if obj.field==field and obj.pointa==pointa and obj.pointb==pointb:
                    key = poly.Symbol.objtable[ii_entry][0]
                    break

        if key==-1:
            key = poly.Symbol._insert_obj(self)

        return key

class Diagram:#(poly.termExpr):

    def _divide_factor_corr(term,point=None):

        factor = copy.deepcopy(term)
        corr = np.array([])

        for ii_body in range(len(term.body)):
            obj_key = term.keys[ii_body]
            if obj_key != poly.Coef.key:
                obj = poly.Symbol.get_obj(obj_key)

                if isinstance(obj,ScalarField) or isinstance(obj,FieldDerivative):
                    factor.body[ii_body] = 0

                    if point:
                        for ii in range(term.body[ii_body]):
                            corr = np.append(corr,obj.change_point(point))
                    else:
                        for ii in range(term.body[ii_body]):
                            corr = np.append(corr,obj)

        return factor, corr

    @staticmethod
    def check_amputation(diagram,external_points=None,internal_points=None):

        if not external_points or not internal_points:
            if not diagram.adjacency:
                raise ValueError("Cannot generate adjacency without the external and internal points")
        else:
            if not diagram.adjacency:
                diagram.adjacency = Diagram.gen_adjacency(diagram,external_points,internal_points)


        amputated = True
        for ii in range(len(diagram.adjacency)):
            internal = diagram.adjacency[ii][:-len(diagram.adjacency)]
            external = diagram.adjacency[ii][-len(diagram.adjacency):]

            external_noself = [external[jj] for jj in range(len(external)) if jj!=ii]

            if sum(internal)==1 and sum(external_noself)==1:
                amputated = False

        return amputated


    @staticmethod
    def check_disconnected(diagram):

        propagators_list = []

        for ii in range(len(diagram.propagators.terms[0].body)):
            obj = poly.Symbol.get_obj(diagram.propagators.terms[0].keys[ii])
            if isinstance(obj,Propagator) and diagram.propagators.terms[0].body[ii]!=0:
                propagators_list.append(obj)

        line_propagators = [propagators_list[0]]
        line_points = [propagators_list[0].pointa,propagators_list[0].pointb]

        searchfinished = False
        while not searchfinished:
            searchfinished = True
            for ii in range(1,len(propagators_list)):
                if propagators_list[ii] in line_propagators:
                    continue

                if propagators_list[ii].pointa in line_points or propagators_list[ii].pointb in line_points:
                    searchfinished = False
                    line_propagators.append(propagators_list[ii])

                    if propagators_list[ii].pointa not in line_points:
                        line_points.append(propagators_list[ii].pointa)

                    if propagators_list[ii].pointb not in line_points:
                        line_points.append(propagators_list[ii].pointb)

        return len(propagators_list)==len(line_propagators)

    @staticmethod
    def gen_adjacency(diagram,external_points,internal_points):

        propagators = diagram.propagators.terms[0]

        external_points_pos = {}
        for ii in range(len(external_points)):
            external_points_pos[str(external_points[ii])] = ii

        internal_points_pos = {}
        for ii in range(len(internal_points)):
            internal_points_pos[str(internal_points[ii])] = ii

        # Conected interacting diagrams will only have information in internal points rows
        adjacency = np.zeros((len(internal_points),len(external_points)+len(internal_points)),dtype=int)

        for ii in range(len(propagators.body)):
            if propagators.keys[ii]==poly.Coef.key:
                continue

            obj = poly.Symbol.get_obj(propagators.keys[ii])
            if not isinstance(obj,Propagator) or propagators.body[ii]==0:
                continue

            if obj.pointa in internal_points:
                if obj.pointb in external_points:
                    column = external_points_pos[str(obj.pointb)]
                elif obj.pointb in internal_points:
                    column = len(external_points) + internal_points_pos[str(obj.pointb)]

                adjacency[internal_points_pos[str(obj.pointa)],column] += 1

            if obj.pointb in internal_points:
                if obj.pointa in external_points:
                    column = external_points_pos[str(obj.pointa)]
                elif obj.pointa in internal_points:
                    column = len(external_points) + internal_points_pos[str(obj.pointa)]

                adjacency[internal_points_pos[str(obj.pointb)],column] += 1

        rows = tuple([tuple(adjacency[ii,:]) for ii in range(len(adjacency[:,0]))])

        return rows


    @staticmethod
    def wick_contration(corr):

        diagram = Diagram(poly.Coef(1).term().expr(),poly.Coef(1).term().expr())

        if len(corr)==2:
            if isinstance(corr[0],ScalarField) and isinstance(corr[1],ScalarField):
                if corr[0].symbol==corr[1].get_antiparticle().symbol:
                    diagram.propagators *= Propagator(corr[0],corr[0].point,corr[1].point)
                    return diagram
                else:
                    return poly.Coef(0)
            elif isinstance(corr[0],ScalarField) and isinstance(corr[1],FieldDerivative):
                if corr[0].symbol==poly.Symbol.get_obj(corr[1].parent).get_antiparticle().symbol:
                    diagram.propagators *= Propagator(corr[0],corr[0].point,corr[1].point)
                    return diagram
                else:
                    return poly.Coef(0)
            elif isinstance(corr[0],FieldDerivative) and isinstance(corr[1],ScalarField):
                if poly.Symbol.get_obj(corr[0].parent).symbol==corr[1].get_antiparticle().key:
                    diagram.propagators *= Propagator(corr[1],corr[0].point,corr[1].point)
                    return diagram
                else:
                    return poly.Coef(0)
            elif isinstance(corr[0],FieldDerivative) and isinstance(corr[1],FieldDerivative):
                if poly.Symbol.get_obj(corr[0].parent).symbol==poly.Symbol.get_obj(corr[0].parent).get_antiparticle().symbol:
                    diagram.propagators *= Propagator(poly.Symbol.getobj(corr[0].parent),corr[0].point,corr[1].point)
                    return diagram
                else:
                    return poly.Coef(0)
            else:
                raise ValueError("Unsupported object in wick contraction "+str(type(corr[0]))+str(type(corr[1])))

        elif len(corr)%2!=0:
            return poly.Coef(0)
        else:
            skip_fields = []
            for ii in range(1,len(corr)):
                if ii in skip_fields:
                    continue

                equal_fields = [ii]
                for jj in range(ii+1,len(corr)):
                    if corr[ii].key==corr[jj].key:
                        equal_fields.append(jj)
                        skip_fields.append(jj)

                #TODO: separate compute wick_contractions separately. If first one is 0, do not compute the second. This will save time (?)
                diagram += len(equal_fields)*Diagram.wick_contration([corr[0],corr[ii]])*Diagram.wick_contration(np.append(corr[1:ii],corr[ii+1:]))


            if isinstance(diagram,diagExpr):
                diagExpr.simplifyterms(diagram)

            return diagram

    def generate(corr,operatorlist):

        if isinstance(corr,poly.extExpr):
            if len(corr.terms)==1:
                corrterm = corr.terms[0]
            else:
                raise ValueError("Correlation function is an expression with more than 1 term")
        elif isinstance(corr,poly.termExpr):
            corrterm = corr
        else:
            raise ValueError("Correlation function is of unsupported type "+str(type(corr)))

        prefactor = 1
        fields = np.array([])

        newfactor, newfields = Diagram._divide_factor_corr(corrterm)

        external_points = [field.point for field in newfields]
        internal_points = []

        prefactor *= newfactor
        fields = np.append(fields,newfields)

        if isinstance(operatorlist,poly.termExpr):
            operatorlist = [operatorlist]

        int_point = 1
        for operator in operatorlist:
            internal_point = poly.Symbol("int"+str(int_point))
            internal_points = np.append(internal_points,internal_point)

            if isinstance(operator,poly.extExpr):
                if len(operator.terms)==1:
                    operatorterm = operator.terms[0]
                else:
                    raise ValueError("Operator is an expression with more than 1 term\n"+str(operator))
            elif isinstance(operator,poly.termExpr):
                operatorterm = operator
            else:
                raise ValueError("Operator is of unsupported type "+str(type(corr))+"\n"+str(operator))

            newfactor, newfields = Diagram._divide_factor_corr(operatorterm,internal_point)

            prefactor *= newfactor
            fields = np.append(fields,newfields)

            int_point += 1

        diagrams = Diagram.wick_contration(fields)
        conn_diagrams = diagExpr([])
        for diagram in diagrams.terms:
            if Diagram.check_disconnected(diagram):
                diagram.adjacency = Diagram.gen_adjacency(diagram,external_points,internal_points)
                if Diagram.check_amputation(diagram):
                    conn_diagrams.terms = np.append(conn_diagrams.terms,diagram)

        return conn_diagrams

    def __init__(self,expr,propagators):
        self.expr = expr
        self.propagators = propagators
        self.string = str(propagators)
        self.adjacency = None

    def __mul__(self,other):
        newdiagram = copy.deepcopy(self)

        if isinstance(other,poly.Coef) and other.value==0:
            return poly.Coef(0)
        elif isinstance(other,poly.Coef):
            newdiagram.expr *= other

            return newdiagram
        elif isinstance(other,poly.NUMBER):
            newdiagram.expr *= poly.Coef(other)

            return newdiagram
        elif isinstance(other,diagExpr):
            return diagExpr([copy.deepcopy(self)])*other
        elif isinstance(other,Diagram):
            newdiagram.expr *= other.expr
            newdiagram.propagators *= other.propagators

            return newdiagram
        else:
            if isinstance(other,poly.extExpr):
                newdiagram.expr *= other

                return newdiagram
            else:
                try:
                    return other.__rmul__(self)
                except:
                    raise ValueError("Unsupported multiplication for diagram and "+str(type(other)))

    def __rmul__(self,other):
        return self*other

    def __add__(self,other):
        if isinstance(other,Diagram):
            return diagExpr([copy.deepcopy(self),copy.deepcopy(other)])
        elif isinstance(other,diagExpr):
            return diagExpr([copy.deepcopy(self)])+other

        elif isinstance(other,poly.Coef) and other.value==0:
            return copy.deepcopy(self)
        else:
            raise ValueError("Error adding Diagram to type",type(other))

    def __radd__(self,other):
        return self+other

    def __str__(self):

        string = ""

        if str(self.expr)!="1":
            string += "[" + str(self.expr) + "]"

        if str(self.propagators)!="1":
            string += str(self.propagators)
        else:
            string = "0"

        return string

    def __repr__(self):
        return str(self)

class diagExpr:

    def __init__(self,terms):
        self.terms = terms

    def __mul__(self,other):
        if isinstance(other,poly.Coef):
            if other.value==0:
                return poly.Coef(0)
            else:
                newself = copy.deepcopy(self)
                for ii_term in newself.terms:
                    newself.terms[ii_term].expr *= other

                return newself

        elif isinstance(other,diagExpr):
            newexpr = diagExpr([])

            for iiterm in self.terms:
                for jjterm in other.terms:
                    newexpr.terms = np.append(newexpr.terms,iiterm*jjterm)

                    diagExpr.simplifyterms(newexpr)

            return newexpr
        else:
            raise ValueError("multiplication not implemented for diagExpr and "+str(type(other)))

    def __add__(self,other):
        if isinstance(other,Diagram):
            return copy.deepcopy(self) + diagExpr([copy.deepcopy(other)])
        elif isinstance(other,poly.Coef):
            if other.value==0:
                return copy.deepcopy(self)
            else:
                raise ValueError("Addition between diagExpr and non zero number")
        elif not isinstance(other,diagExpr):
            try:
                return other+self
            except:
                raise ValueError("Addition between diagExpr and ",type(other))

        newself = copy.deepcopy(self)
        newself.terms = np.append(newself.terms,other.terms)

        diagExpr.simplifyterms(newself)

        return newself

    def __radd__(self,other):
        return self+other

    @staticmethod
    def simplifyterms(self):

        # Clean empty propagators
        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if str(self.terms[ii_term].propagators)=="1":
                terms_to_drop.append(ii_term)

        newExpr = diagExpr([])
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newExpr.terms = np.append(newExpr.terms,self.terms[ii_term])

        self.terms = newExpr.terms

        # Sync terms
        for ii_term in range(1,len(self.terms)):
            self.terms[0].expr._sync(self.terms[ii_term].expr)
            self.terms[0].propagators._sync(self.terms[ii_term].propagators)

        for ii_term in range(1,len(self.terms)):
            self.terms[0].expr._sync(self.terms[ii_term].expr)
            self.terms[0].propagators._sync(self.terms[ii_term].propagators)

        for ii_term in range(1,len(self.terms)):
            poly.extExpr.simplifyterms(self.terms[ii_term].expr)

        # Sum equal terms
        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                for jj_term in range(ii_term+1,len(self.terms)):
                    if jj_term not in terms_to_drop:
                        iibody_nocoef = np.append(self.terms[ii_term].propagators.terms[0].body[:self.terms[ii_term].propagators.terms[0].keydict[str(poly.Coef.key)]],self.terms[ii_term].propagators.terms[0].body[self.terms[ii_term].propagators.terms[0].keydict[str(poly.Coef.key)]+1:])
                        jjbody_nocoef = np.append(self.terms[jj_term].propagators.terms[0].body[:self.terms[jj_term].propagators.terms[0].keydict[str(poly.Coef.key)]],self.terms[jj_term].propagators.terms[0].body[self.terms[jj_term].propagators.terms[0].keydict[str(poly.Coef.key)]+1:])
                        if np.array_equal(iibody_nocoef,jjbody_nocoef):
                            terms_to_drop.append(jj_term)
                            self.terms[ii_term].expr += self.terms[jj_term].expr

        newExpr = diagExpr([])
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newExpr.terms = np.append(newExpr.terms,self.terms[ii_term])

        self.terms = newExpr.terms

        # Remove 0s
        terms_to_drop = []
        for ii_term in range(len(self.terms)):
            if str(self.terms[ii_term].expr)=="0":
                terms_to_drop.append(ii_term)

        newExpr = diagExpr([])
        for ii_term in range(len(self.terms)):
            if ii_term not in terms_to_drop:
                newExpr.terms = np.append(newExpr.terms,self.terms[ii_term])

        self.terms = newExpr.terms


    def __str__(self):

        if len(self.terms)==0:
            return "0"

        string = ""
        for term in self.terms:
           string += str(term) + " + "

        string = string[:-3]

        return string

    def __repr__(self):
        return str(self)
