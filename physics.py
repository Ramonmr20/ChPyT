#!/usr/bin/env python3

import poly

class ScalarField(poly.Symbol):

    @staticmethod
    def link_antiparticles(a,b):
        a.antiparticle = b.key
        b.antiparticle = a.key

    def __init__(self,symbol,point):
        self.key = self._insert_obj(symbol,point)
        self.string = symbol
        self.derivative = 0
        self.antiparticle = None
        self.point = point

    def _insert_obj(self,symbol,point):

        for ii_entry in range(len(poly.Symbol.objtable)):
            obj = poly.Symbol.objtable[ii_entry][1]
            key = -1
            if isinstance(obj,ScalarField):
                if obj.string==symbol and obj.point==point:
                    key = poly.Symbol.objtable[ii_entry][0]
                    break

        if key==-1:
            key = poly.Symbol._insert_obj(self)

        return key


    def partial(self,index):
        return FieldDerivative(self,index)

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
        self.string = u"\u2202_" + str(index) + "(" + field.string + ")"
        self.derivative = 1
        self.antiparticle = field.antiparticle
        self.index = index
        self.parent = field.key

    def _insert_obj(self,field,index):

        for ii_entry in range(len(poly.Symbol.objtable)):
            obj = poly.Symbol.objtable[ii_entry][1]
            key = -1
            if isinstance(obj,FieldDerivative):
                print(obj.parent,field.key,obj.parent==field.key)
                print(obj.index,index,obj.index==index)
                if obj.parent==field.key and obj.index==index:
                    key = poly.Symbol.objtable[ii_entry][0]
                    break

        if key==-1:
            key = poly.Symbol._insert_obj(self)

        return key
