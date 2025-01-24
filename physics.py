#!/usr/bin/env python3

import poly

class ScalarField(poly.Symbol):

    @staticmethod
    def link_antiparticles(a,b):
        a.antiparticle = b.key
        b.antiparticle = a.key

    def __init__(self,symbol,point):
        self.key = poly.Symbol._insert_obj(self)
        self.string = symbol
        self.derivative = 0
        self.antiparticle = None
        self.point = point

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
        self.key = poly.Symbol._insert_obj(self)
        self.string = u"\u2202_" + str(index) + "(" + field.string + ")"
        self.derivative = 1
        self.antiparticle = field.antiparticle
        self.index = index
        self.parent = field.key
