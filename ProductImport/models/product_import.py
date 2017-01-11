# -*- coding: utf-8 -*-
from odoo import api, models

import csv
import datetime
import io
import itertools
import logging
import operator
import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import psycopg2


FIELDS_RECURSION_LIMIT = 2
ERROR_PREVIEW_BYTES = 200
_logger = logging.getLogger(__name__)

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

try:
    import odf_ods_reader
except ImportError:
    odf_ods_reader = None

FILE_TYPE_DICT = {
    'text/csv': ('csv', True, None),
    'application/vnd.ms-excel': ('xls', xlrd, 'xlrd'),
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ('xlsx', xlsx, 'xlrd >= 0.8'),
    'application/vnd.oasis.opendocument.spreadsheet': ('ods', odf_ods_reader, 'odfpy')
}
EXTENSIONS = {
    '.' + ext: handler
    for mime, (ext, handler, req) in FILE_TYPE_DICT.iteritems()
}

class odooproduct():
    'To add to Odoo'

    def __init__(self, name, description, priceclass, packageclass,unitsupply, unitsale):
        self.name = name
        self.description = description
        self.priceclass=priceclass
        self.packageclass=packageclass
        self.unitsupply=unitsupply
        self.unitsale=unitsale



    def printall(self):
        print(self.name)
        print(self.description)
        print(self.priceclass)
        print(self.packageclass)
        print(self.unitsupply)
        print(self.unitsale)
        print("")


class Productimport(models.Model):
    _name = 'dancik.product_import'



    def createodoorecords(self,product):

        pricerecord = self.env['perproduct.priceclass'].search([('name', '=', product.priceclass)], limit=1)

        if pricerecord:
            priceclassid = pricerecord[0].id
        else:
            #print("Product: ", product.name, " - non-existent price class ", product.priceclass)
            return


        packagerecord = self.env['productuom.class'].search([('name', '=', product.packageclass)], limit=1)

        if packagerecord:
            packageclassid = packagerecord[0].id
        else:
            #print("Product: ", product.name, " - non-existent package class ", product.packageclass)
            return


        pricelistrecords = pricerecord[0].pricelists

        if pricelistrecords:
            hasLL = False
            hasLP = False
            hasD1 = False

            for z in range(len(pricelistrecords)):
                if not hasLL:
                    if (pricelistrecords[z].name == "LL"):
                        hasLL=True
                        LLrecord=pricelistrecords[z]
                        if (hasLL and hasD1): break
                        continue

                if not hasLP:
                    if (pricelistrecords[z].name == "LP"):
                        hasLP=True
                        LPrecord=pricelistrecords[z]
                        continue

                if not hasD1:
                    if (pricelistrecords[z].name == "D1"):
                        hasD1=True
                        D1record=pricelistrecords[z]
                        if (hasLL and hasD1): break
                        continue

            if not hasLL:
                if hasLP:
                    LLrecord=LPrecord
                else:
                    #print("Product: ", product.name, " - Missing LL and LP in price class ", product.priceclass)
                    return

            if not hasD1:
                #print("Product: ", product.name, " - Missing D1 in price class, using LP ", product.priceclass)
                D1record=LPrecord

            #print(product.name," with price class ",product.priceclass)
            #print("D1: ",D1record.price," LP: ",LLrecord.price," UOM: ",LLrecord.uomname)
            unitprice = LLrecord.uomname
            listprice = LLrecord.price
            cost= D1record.price


        else:
            #print("Product: ", product.name, " - No valid Price Lists found in ", product.priceclass)
            return

        uomrecords = packagerecord[0].localuom

        if uomrecords:
            hasunitsale = False
            hasunitprice = False

            for z in range(len(uomrecords)):
                #print(uomrecords[z].name," vs ",product.unitsale," ", product.unitsupply," ", unitprice)

                if not hasunitsale:
                    if (uomrecords[z].name == product.unitsale):
                        hasunitsale = True
                        saleuomrecord = uomrecords[z]
                        if (hasunitsale and hasunitprice): break

                if not hasunitprice:
                    if (uomrecords[z].name == unitprice):
                        hasunitprice = True
                        priceuomrecord = uomrecords[z]
                        if (hasunitsale and hasunitprice): break


            if not (hasunitsale):
                #print("Product: ", product.name, " - Sale UOM (", product.unitsale, ") not found in Package Class ", product.packageclass)
                return

            if not (hasunitprice):
                #print("Product: ", product.name, " - Pricing UOM (", unitprice, ") not found in Package Class ", product.packageclass)
                return

            supplyuomrecord = saleuomrecord
            #print("Product: ", product.name, " - Supply UOM (",product.unitsupply,") not found in Package Class ", product.packageclass)


        else:
            #print("Product: ", product.name, " - No UOM records found in ", product.packageclass)
            return


        #Find factor to convert price UOM to sale UOM
        if (saleuomrecord.uom_type == 'bigger'):
            salefactor = saleuomrecord.factor_inv
        else:
            salefactor = saleuomrecord.factor

        if (priceuomrecord.uom_type == 'bigger'):
            pricefactor = priceuomrecord.factor_inv
        else:
            pricefactor = priceuomrecord.factor

        convfactor= float(float(pricefactor)/float(salefactor))
        convlistprice = float(float(listprice) * float(convfactor))
        convlistprice = round(convlistprice,2)
        convcost = float(float(cost) * float(convfactor))
        convcost = convcost * .925
        convcost = round(convcost,2)
        #print('Product: ',product.name,' ',listprice,' ',unitprice,' and ',convlistprice,' ',saleuomrecord.name)

        vals = {'name': product.name, 'uom_class': packageclassid, 'price_class': priceclassid, 'price': convlistprice,
                'standard_price': convcost, 'uom_id': saleuomrecord.uid.id,
                'uom_po_id': saleuomrecord.uid.id,}

        records = self.env['product.product'].search([('name', '=', product.name)], limit=1)


        if records:
            print("Found ",product.name)
            newproduct = records[0]
            newproduct.write(vals)
            newtemplate = newproduct.product_tmpl_id
            tempvals = {'standard_price': convcost,}
            newtemplate.write(tempvals)

        else:
            print("Creating ",product.name)
            tempvals = {'name': product.name,}
            newproduct = self.env['product.product'].create(tempvals)
            newproduct.write(vals)
            newtemplate = newproduct.product_tmpl_id
            tempvals2 = {'standard_price': convcost,}
            newtemplate.write(tempvals2)



    def readfile(self):
        print("Opening file")
        filename='/var/tmp/itemfile.xlsx'
        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_index(0)
        print("First Row")
        row0 = sheet.row(0)

        if ( (row0[147].value!="IFLAGS") ):
            #print(row0[83].value)
            print("Not correct file type")
            return
        #print("Starting loop")


        #print("rows: ", sheet.nrows)
        for row in itertools.imap(sheet.row, range(1, sheet.nrows)):
            #print("X Start new loop: ", x)
            #name, description, pricefile, packagefile,unitsupply, unitprice
            name = unicode(row[1].value + row[2].value + row[3].value)
            description = unicode(row[7].value + "," + row[8].value)
            priceclass = row[107].value
            packageclass = row[108].value
            if ( (priceclass == "") or (packageclass == "") ):
                #print("Item: ", name, " missing Price or Pacakage class")
                continue
            priceclass = unicode(row[107].value)
            packageclass = unicode(row[108].value)
            unitsupply = unicode(row[20].value)
            unitsale = unicode(row[86].value)


            if (unitsupply == ""):
                unitsupply = unitsale

            if (unitsale=="") :
                #print("Item ",name," lacks unit of sale")
                continue

            tempproduct = odooproduct(name, description, priceclass, packageclass,unitsupply,unitsale)
            #tempproduct.printall()

            self.createodoorecords(tempproduct)

        filenameold = "/var/tmp/itemfile.old"
        try:
            os.remove(filenameold)
        except OSError:
            print("Can't Delete for unknown reason")
            pass

        try:
            os.rename(filename, filenameold)
        except OSError:
            print("Can't rename")
            pass











