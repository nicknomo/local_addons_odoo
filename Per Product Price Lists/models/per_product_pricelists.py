# -*- coding: utf-8 -*-
from odoo import api, models, fields


class perproductpricelist(models.Model):
    _name = "perproduct.pricelist"
    name = fields.Char('Price List', required=True, index=True)
    uomname = fields.Char('UOM', required=True)
    priceclass = fields.Many2one('perproduct.priceclass', index=True, ondelete='cascade', required=True)
    price = fields.Float('Price', digits=0, required=True)

    _sql_constraints = [('price_gt_zero', 'CHECK (price>=0)', 'Price must be greater than or equal to zero!'),
                        ('pricelist_uniq', 'UNIQUE (name,priceclass)', 'Pricelist+Priceclass must be unique')]


class perproductpriceclass(models.Model):
    _name = "perproduct.priceclass"
    name = fields.Char('Price List', index=True, required=True)
    pricelists = fields.One2many('perproduct.pricelist', 'priceclass', index=True, ondelete='set null', required=False)
    _sql_constraints = [('priceclass_uniq', 'UNIQUE (name)', 'Priceclass must be unique')]



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    #This field will let us choose if we are using per product uom on the product
    price_class = fields.Many2one('perproduct.priceclass', 'Per Product Pricing', ondelete='restrict',required=False, help="Per Product Price Class")


    #When price_class is changed, we need to update pricing
    @api.onchange('price_class')
    def onchange_price_class(self):
        vals = []
        vals = self.calculatevalues()

        if not vals: return

        if vals[0]:
            self.list_price=vals[0]

        if vals[1]:
            self.standard_price=vals[1]


    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        vals = []
        vals = self.calculatevalues()

        if not vals: return

        if vals[0]:
            self.list_price = vals[0]

        if vals[1]:
            self.standard_price = vals[1]

        super(ProductTemplate, self)._onchange_uom_id()

    @api.onchange('uom_po_id')
    def _onchange_uom_po_id(self):
        vals = []
        vals = self.calculatevalues()

        if not vals: return

        if vals[0]:
            self.list_price = vals[0]

        if vals[1]:
            self.standard_price = vals[1]

    def calculatevalues(self):
        pricerecord = self.price_class

        if not pricerecord:
            print("no Price Record")
            return False

        packagerecord = self.uom_class

        if not packagerecord:
            print("no Package Record")
            return False

        pricelistrecords = pricerecord.pricelists

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
                    print("No viable Pricelists")
                    #print("Product: ", product.name, " - Missing LL and LP in price class ", product.priceclass)
                    return False

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
            return False

        saleuomrecord = self.uom_id
        supplyuomrecord = self.uom_po_id

        if not saleuomrecord:
            print("No saleuomrecord")
            return False

        if not supplyuomrecord:
            print("No supplyuomrecord")
            return False

        uomrecords = packagerecord.localuom
        if uomrecords:
            hasunitsale = False
            hasunitprice = False
            hasunitcost = False

            for z in range(len(uomrecords)):
                #print(uomrecords[z].name," vs ",product.unitsale," ", product.unitsupply," ", unitprice)

                if not hasunitsale:
                    if (uomrecords[z].name == self.uom_id.name):
                        hasunitsale = True
                        #saleuomrecord = uomrecords[z]
                        if (hasunitsale and hasunitprice and hasunitcost): break

                if not hasunitcost:
                    if (uomrecords[z].name == self.uom_po_id.name):
                        hasunitcost = True
                        #supplyuomrecord = uomrecords[z]
                        if (hasunitsale and hasunitprice and hasunitcost): break

                if not hasunitprice:
                    if (uomrecords[z].name == unitprice):
                        hasunitprice = True
                        priceuomrecord = uomrecords[z]
                        if (hasunitsale and hasunitprice and hasunitcost): break


            if not (hasunitsale):
                #print("Product: ", product.name, " - Sale UOM (", product.unitsale, ") not found in Package Class ", product.packageclass)
                print("Sale Unit not found")
                return False

            if not (hasunitprice):
                #print("Product: ", product.name, " - Pricing UOM (", unitprice, ") not found in Package Class ", product.packageclass)
                print("Pricing Unit not found")
                return False

            if not (hasunitcost):
                print(self.uom_po_id, " ",self.uom_po_id.name)
                print("Cost Unit not found")
                return False


            #print("Product: ", product.name, " - Supply UOM (",product.unitsupply,") not found in Package Class ", product.packageclass)

        else:
            print("No uomrecords value")
            return False

        # Find factor to convert price UOM to sale UOM
        if (saleuomrecord.uom_type == 'bigger'):
            salefactor = saleuomrecord.factor_inv
        else:
            salefactor = saleuomrecord.factor

        if (priceuomrecord.uom_type == 'bigger'):
            pricefactor = priceuomrecord.factor_inv
        else:
            pricefactor = priceuomrecord.factor

        convfactor = float(float(pricefactor) / float(salefactor))
        convlistprice = float(float(listprice) * float(convfactor))
        convlistprice = round(convlistprice, 2)

        if (supplyuomrecord.uom_type == 'bigger'):
            costfactor = supplyuomrecord.factor_inv
        else:
            costfactor = supplyuomrecord.factor

        convfactor = float(float(pricefactor) / float(costfactor))
        convcost = float(float(cost) * float(convfactor))
        convcost = convcost * .925
        convcost = round(convcost, 2)
        # print('Product: ',product.name,' ',listprice,' ',unitprice,' and ',convlistprice,' ',saleuomrecord.name)

        vals = []
        vals.append(convlistprice)
        vals.append(convcost)
        return vals


