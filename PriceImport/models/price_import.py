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

class odoopricelist():
    'To add to Odoo'

    def __init__(self, name, price, uomname):
        self.name = name
        self.price = float(price)
        self.uomname = uomname


    def printall(self):
        print(self.name + " ")
        print(self.price)
        print(self.uomname)
        print("")


class Priceimport(models.Model):
    _name = 'dancik.price_import'



    def createodoorecords(self,priceclass,allpricelists):
        records = self.env['perproduct.priceclass'].search([('name','=',priceclass)],limit=1)
        if records:
            newpriceclass = records[0]
        else:
            vals = {'name': priceclass,}
            newpriceclass = self.env['perproduct.priceclass'].create(vals)


        isrecord = False
        recordnum = 0
        recordcollection=[]
        #print("")
        #print("")
        #print("")
        #print("")
        print("Price CLass: ",priceclass)

        records = self.env['perproduct.pricelist'].search([('priceclass.name', '=', priceclass)],)

        #print("Number of Records:", len(records))
        for z in range(len(records)):
            #print(z,": ",records[z].name)
            recordcollection.append(records[z])

        for x in range(len(allpricelists)):
            print("Processing: ",allpricelists[x].name)
            for y in range(len(recordcollection)):
                if (recordcollection[y].name == allpricelists[x].name):
                    #print("Found at position: ",y)
                    isrecord = True
                    recordnum = y

            if isrecord:
                existinglist = recordcollection[recordnum]
                vals = {'name': allpricelists[x].name, 'price': allpricelists[x].price,
                        'uomname': allpricelists[x].uomname,}
                existinglist.write(vals)
                isrecord=False

            else:
                print("Creating new record: ",allpricelists[x].name)
                vals = {'name': allpricelists[x].name, 'price': allpricelists[x].price,
                        'uomname': allpricelists[x].uomname,'priceclass': newpriceclass.id,}
                newpricelist = self.env['perproduct.pricelist'].create(vals)







    def readfile(self):
        print("Opening file")
        filename = '/var/tmp/pricefile.xlsx'
        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_index(0)
        print("First Row")
        row0 = sheet.row(0)

        if ( (row0[83].value!="$DEL") ):
            #print(row0[83].value)
            print("Not correct file type")
            return
        #print("Starting loop")

        x=1
        #print("rows: ", sheet.nrows)
        while ( x < sheet.nrows ):
            #print("X Start new loop: ", x)
            allpricelists = []
            row = sheet.row(x)
            priceclass = unicode(row[0].value)
            #print("PRICE CLASS: ",priceclass)
            pricelist = unicode(row[1].value)
            price = float(row[41].value)
            uomname = unicode(row[66].value)

            templist = odoopricelist(pricelist,price,uomname)
            allpricelists.append(templist)
            #templist.printall()


            while  ( (x+1) < sheet.nrows ):
                nextrow = sheet.row(x+1)
                if (nextrow[0].value != priceclass):
                    break
                else:
                    pricelist = unicode(nextrow[1].value)
                    price = float(nextrow[41].value)
                    uomname = unicode(nextrow[66].value)
                    templist = odoopricelist(pricelist, price, uomname)
                    allpricelists.append(templist)
                    #templist.printall()
                    x=x+1
                    #print("X: ",x)

            #print("X out of the loop: ", x)
            x=x+1
            self.createodoorecords(priceclass, allpricelists)

        filenameold = "/var/tmp/pricefile.old"
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










