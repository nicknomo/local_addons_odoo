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

class odoouom():
    'To add to Odoo'

    def __init__(self, name, factor, size):
        self.name = name
        self.factor = float(factor)
        self.size = size
        self.invfactor = float( 1 / float(factor) )

    def printall(self):
        print()
        print(self.name + " ")
        print(self.factor)
        print(self.invfactor)
        print(self.size + " ")

class UOMimport(models.Model):
    _name = 'dancik.uom_import'

    def getfactor(self,odoouomlist, name):
        for i in range(len(odoouomlist)):
            #print(odoouomlist[i].name, "vs", name)

            if (odoouomlist[i].name == name):
                return odoouomlist[i].factor

    def isinlist(self,list, value):
        for i in range(len(list)):
            if (value == list[i]):
                return True

        return False

    def getposition(self,list, value):
        for i in range(len(list)):
            if (value == list[i]):
                return i

    def getreference(self,umlist, umlistcount):
        highest = 0
        for i in range(len(umlist)):
            if (umlistcount[i] >= umlistcount[highest]):
                highest = i

        return umlist[highest]

    def createodoorecords(self,packageclass,odoouomlist):
        records = self.env['productuom.class'].search([('name','=',packageclass)],limit=1)
        if records:
            newclass = records[0]
        else:
            vals = {'name': packageclass,'isuomclass': True,}
            newclass = self.env['productuom.class'].create(vals)
            #vals = {'isuomclass': True,}
            #newclass.write(vals)

        isrecord = False
        recordnum = 0
        recordcollection=[]
        deletelist= []
        #print("")
        #print("")
        #print("")
        #print("")
        #print("Package CLass: ",packageclass)

        records = self.env['localproduct.uom'].search([('localcategory_id.name', '=', packageclass)],)

        #print("Number of Records:", len(records))
        for z in range(len(records)):
            #print(z,": ",records[z].name)
            recordcollection.append(records[z])

        for x in range(len(odoouomlist)):
            #print("Processing: ",odoouomlist[x].name)
            for y in range(len(recordcollection)):
                if (recordcollection[y].name == odoouomlist[x].name):
                    #print("Found at position: ",y)
                    isrecord = True
                    recordnum = y

            if isrecord:
                existinguom = recordcollection[recordnum]
                vals = {'name': odoouomlist[x].name, 'islocaluom': True, 'factor': odoouomlist[x].factor,
                        'uom_type': odoouomlist[x].size,}
                existinguom.write(vals)
                isrecord=False
                deletelist.append(recordnum)
                #print("Deleted record at: ",recordnum)

            else:
                #print("Creating new record: ",odoouomlist[x].name)
                vals = {'name': odoouomlist[x].name, 'islocaluom': True, 'factor': odoouomlist[x].factor,
                        'uom_type': odoouomlist[x].size, 'localcategory_id': newclass.id,
                        'category_id': newclass.catid.id,}
                newuom = self.env['localproduct.uom'].create(vals)

        deletelist.sort(reverse=True)

        for z in range(len(deletelist)):
            del recordcollection[deletelist[z]]

        #print("Listing stragglers")
        for z in range(len(recordcollection)):
            print("No longer needed: ", recordcollection[z].name)






    def processline(self,packageclass, um1, um2,factors):
        combinedumlist = um1 + um2
        umlist = []
        umlistcount = []
        odoouomlist = []
        completedumlist = []
        for x in range(len(combinedumlist)):
            if (self.isinlist(umlist, combinedumlist[x])):
                position = self.getposition(umlist, combinedumlist[x])
                umlistcount[position] = umlistcount[position] + 1

            else:
                umlist.append(combinedumlist[x])
                umlistcount.append(1)

        #print(umlist)
        #print(umlistcount)

        referenceum = self.getreference(umlist, umlistcount)
        #print(referenceum)

        tempodoouom = odoouom(referenceum, 1, "reference")
        #tempodoouom.printall()
        odoouomlist.append(tempodoouom)

        delpositions = []
        tempsize = "reference"

        for x in range(len(um1)):
            if (um1[x] == referenceum):
                delpositions.append(x)
                if (um2[x] != referenceum):

                    if ( float(factors[x]) == 1.0):
                        tempsize = "reference"
                    if ( float(factors[x]) < 1.0):
                        tempsize = "smaller"
                    if ( float(factors[x]) > 1.0):
                        tempsize = "smaller"
                    if (self.isinlist(completedumlist, um2[x]) == False):
                        tempfactor = float((1 / float(factors[x])))
                        tempodoouom = odoouom(um2[x], tempfactor, tempsize)
                        odoouomlist.append(tempodoouom)
                        completedumlist.append(um2[x])

        #print(delpositions)
        delpositions.sort(reverse=True)
        #print(delpositions)

        for x in range(len(delpositions)):
            #print(delpositions[x])
            del um1[delpositions[x]]
            del um2[delpositions[x]]
            del factors[delpositions[x]]

        #print(um1)
        #print(um2)
        #print(factors)
        delpositions = []

        for x in range(len(um2)):
            if (um2[x] == referenceum):
                delpositions.append(x)
                if (um1[x] != referenceum):

                    if ( float(factors[x]) == 1.0):
                        tempsize = "reference"
                    if ( float(factors[x]) > 1.0):
                        tempsize = "smaller"
                    if ( float(factors[x]) < 1.0):
                        tempsize = "smaller"
                    if (self.isinlist(completedumlist, um1[x]) == False):
                        tempfactor = float(factors[x])
                        tempodoouom = odoouom(um1[x], tempfactor, tempsize)
                        odoouomlist.append(tempodoouom)
                        completedumlist.append(um1[x])

        #print(delpositions)
        delpositions.sort(reverse=True)
        #print(delpositions)

        for x in range(len(delpositions)):
            #print(delpositions[x])
            del um1[delpositions[x]]
            del um2[delpositions[x]]
            del factors[delpositions[x]]

        #print(um1)
        #print(um2)
        #print(factors)
        #print("Printing completed: ", completedumlist)
        flag = 0

        while len(um1):
            if (flag == 1):
                print("Infinite loop detected in: ", packageclass)
                break
            flag = 1
            delpositions = []

            for x in range(len(um1)):
                if self.isinlist(completedumlist, um1[x]):
                    if not self.isinlist(completedumlist, um2[x]):
                        otherfactor = float(self.getfactor(odoouomlist, um1[x]))
                        #print("Printing otherfactor: ", otherfactor)
                        tempfactor = float((1 / float(factors[x]) * float(otherfactor)))
                        #print(tempfactor)
                        if ( float(tempfactor) == 1.0):
                            tempsize = "reference"
                        if ( float(tempfactor) < 1.0):
                            tempsize = "smaller"
                        if ( float(tempfactor) > 1.0):
                            tempsize = "smaller"
                        #print(tempsize)
                        tempodoouom = odoouom(um2[x], tempfactor, tempsize)
                        odoouomlist.append(tempodoouom)
                        completedumlist.append(um2[x])
                        delpositions.append(x)
                        flag = 0

                    else:
                        delpositions.append(x)
                        flag = 0

            #print(delpositions)
            delpositions.sort(reverse=True)
            #print(delpositions)

            for x in range(len(delpositions)):
                del um1[delpositions[x]]
                del um2[delpositions[x]]
                del factors[delpositions[x]]

            #print(um1)
            #print(um2)
            #print(factors)
            #print(completedumlist)

            delpositions = []

            for x in range(len(um2)):
                if self.isinlist(completedumlist, um2[x]):
                    if not self.isinlist(completedumlist, um1[x]):
                        otherfactor = float(self.getfactor(odoouomlist, um2[x]))
                        #print("Printing otherfactor: ", otherfactor)
                        tempfactor = float(float(factors[x]) * float(otherfactor))
                        #print(tempfactor)
                        if ( float(tempfactor) == 1):
                            tempsize = "reference"
                        if ( float(tempfactor) < 1):
                            tempsize = "smaller"
                        if ( float(tempfactor) > 1):
                            tempsize = "smaller"
                        tempodoouom = odoouom(um1[x], tempfactor, tempsize)
                        odoouomlist.append(tempodoouom)
                        completedumlist.append(um1[x])
                        delpositions.append(x)
                        flag = 0

                    else:
                        delpositions.append(x)
                        flag = 0

            #print(delpositions)
            delpositions.sort(reverse=True)
            #print(delpositions)

            for x in range(len(delpositions)):
                del um1[delpositions[x]]
                del um2[delpositions[x]]
                del factors[delpositions[x]]

            #print(um1)
            #print(um2)
            #print(factors)
            #print(completedumlist)

            delpositions = []

        #print(packageclass)

        #for x in range(len(odoouomlist)):
            #print("1",referenceum," = ", odoouomlist[x].factor," ",odoouomlist[x].name)
        #print("")
        self.createodoorecords(packageclass,odoouomlist)




    def readfile(self):
        filename='/var/tmp/package.xls'
        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_index(0)

        row0 = sheet.row(0)

        if ( (row0[23].value!="UDEL") ):
            print("Not correct file type")
            return


        for row in itertools.imap(sheet.row, range(1,sheet.nrows)):
            um1 = []
            um2 = []
            factors = []

            packageclass = unicode(row[0].value)


            if ( (row[7].value !='') and (row[13].value!='') ):
                firstum= unicode(row[7].value)
                um1.append(firstum)
                secondum= unicode(row[13].value)
                um2.append(secondum)
                factor= float(row[1].value)
                factors.append(factor)

            if ( (row[8].value !='') and (row[14].value!='')  ):
                firstum= unicode(row[8].value)
                um1.append(firstum)
                secondum= unicode(row[14].value)
                um2.append(secondum)
                factor= float(row[2].value)
                factors.append(factor)

            if ( (row[9].value !='') and (row[15].value!='')  ):
                firstum= unicode(row[9].value)
                um1.append(firstum)
                secondum= unicode(row[15].value)
                um2.append(secondum)
                factor= float(row[3].value)
                factors.append(factor)

            if ( (row[10].value !='') and (row[16].value!='') ):
                firstum= unicode(row[10].value)
                um1.append(firstum)
                secondum= unicode(row[16].value)
                um2.append(secondum)
                factor= float(row[4].value)
                factors.append(factor)

            if ( (row[11].value !='') and (row[17].value!='') ):
                firstum= unicode(row[11].value)
                um1.append(firstum)
                secondum= unicode(row[17].value)
                um2.append(secondum)
                factor= float(row[5].value)
                factors.append(factor)

            if ( (row[12].value !='') and (row[18].value!='') ):
                firstum= unicode(row[12].value)
                um1.append(firstum)
                secondum= unicode(row[18].value)
                um2.append(secondum)
                factor= float(row[6].value)
                factors.append(factor)

            self.processline(packageclass, um1, um2, factors)

        filenameold = "/var/tmp/package.old"
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






