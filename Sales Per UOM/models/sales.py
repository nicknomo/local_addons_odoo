# -*- coding: utf-8 -*-
from odoo import api, models, fields


# For some reason, odoo's views had trouble finding the category of the uom in sale.order.line on the fly
# This keeps the record in the DB, and allows me to filter UOM categories.
class NewSaleOrder(models.Model):
    _inherit = 'sale.order'
    # These computed fields are for calculating the quick quoter data
    quoteproduct = fields.Many2one('product.product', string='Product:', domain=[('sale_ok', '=', True)], change_default=True, ondelete='cascade')
    quoteproductuom = fields.Many2one('product.uom','Price Uom:',ondelete='cascade')
    quoteqty = fields.Integer('Pricing Qty:', default=1)

    quoteuomprice = fields.Char('List Price:',compute='_computeuomprice')
    quoteuomcost = fields.Char('Cost Price:', compute='_computeuomcost')

    quoteuserprice = fields.Float('Sale Price:')
    quoteexactuomqty = fields.Char('Est. Sale Qty:',compute='_computeexactsaleqty')

    quotesaleqty = fields.Integer('Sale Qty:')
    quotesaleuom = fields.Char('Sale UoM', compute='_computesaleuom')
    quotesaleuomcat = fields.Integer('Cat ID',default=1)
    #quotesaleuom = fields.Many2one(related='quoteproduct.uom_id',ondelete='cascade')
    quotecost = fields.Float('Line Price', compute='_computecost')

    quoteactualprice = fields.Float('sell at this price:', compute='_computeactualprice')
    quoteblank = fields.Char(' ', readonly="True")
    quotepriceuom = fields.Char('Sell @ PRiCE UM:', compute='_computepriceuom')


    # The default onchange returns a domain, but it also does other stuff. Since we set a default domain, we want don't want it to return a domain
    # So we make a call to the original onchange, and just absorb the return value.  It still does all the other stuff

    @api.multi
    @api.onchange('quoteproduct')
    def quoteproduct_id_change(self):


        if not self.quoteproduct:
            self.quoteqty = False
            self.quoteproductuom = False
            self.quoteuserprice = False
            self.quotesaleqty = False
            self.quotesaleuomcat = 1
            return {}

        product = self.quoteproduct

        if (product.uom_id):
            vals = {}
            #self.quoteproductuom = product.uom_id
            self.quotesaleuomcat = self.quoteproduct.uom_id.category_id.id
            domain = {'quoteproductuom': [('category_id', '=', self.quotesaleuomcat)]}
            vals['quoteproductuom'] = self.quoteproduct.uom_id
            self.update(vals)

            priceclass = self.quoteproduct.price_class
            pricelistrecords = priceclass.pricelists

            if pricelistrecords:
                hasLL = False

                for z in range(len(pricelistrecords)):
                    if not hasLL:
                        if (pricelistrecords[z].name == "LL"):
                            hasLL = True
                            LLrecord = pricelistrecords[z]
                            if (hasLL): break

                if hasLL:
                    unitprice = LLrecord.uomname
                    packageclass = self.quoteproduct.uom_class
                    uomrecords = packageclass.localuom

                    if uomrecords:
                        hasunitprice = False

                        for y in range(len(uomrecords)):
                            if not hasunitprice:
                                if (uomrecords[y].name == unitprice):
                                    hasunitprice = True
                                    priceuomrecord = uomrecords[y]
                                    if (hasunitprice): break

                        if hasunitprice:
                            self.quoteproductuom = priceuomrecord.uid

                        else: self.quoteproductuom = product.uom_id

                    else: self.quoteproductuom = product.uom_id


                else:
                    self.quoteproductuom = product.uom_id

            else:
                self.quoteproductuom = product.uom_id

            return {'domain': domain}

        return {}

    @api.depends('quoteproduct')
    def _computesaleuom(self):
        self.quotesaleuom = self.quoteproduct.uom_id.name
        return {}

    @api.depends('quoteproductuom')
    def _computepriceuom(self):
        if not self.quoteproductuom: return {}
        self.quotepriceuom = '' + self.quoteproductuom.name + ''
        return {}

    @api.depends('quoteproduct','quoteproductuom')
    def _computeuomprice(self):
        price = self.quoteproduct.list_price
        uom = self.quoteproduct.uom_id
        newuom = self.quoteproductuom

        if uom and newuom and price:
            if (uom.uom_type == 'bigger'):
                salefactor = uom.factor_inv
            else:
                salefactor = uom.factor

            if (newuom.uom_type == 'bigger'):
                pricefactor = newuom.factor_inv
            else:
                pricefactor = newuom.factor

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(price) * float(convfactor))
            convprice = round(convprice, 2)
            self.quoteuserprice = convprice
            self.quoteuomprice= '' + str(convprice) + ' / ' + newuom.name
            return {}

        self.quoteuomprice = 'N/A'
        return {}

    @api.depends('quoteproduct', 'quoteproductuom')
    def _computeuomcost(self):
        cost = self.quoteproduct.standard_price
        uom = self.quoteproduct.uom_po_id
        newuom = self.quoteproductuom

        if uom and newuom and cost:
            if (uom.uom_type == 'bigger'):
                salefactor = uom.factor_inv
            else:
                salefactor = uom.factor

            if (newuom.uom_type == 'bigger'):
                pricefactor = newuom.factor_inv
            else:
                pricefactor = newuom.factor

            if (pricefactor == 0):
                self.quoteuomcost = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(cost) * float(convfactor))
            convprice = round(convprice, 2)
            self.quoteuomcost= '' + str(convprice) + ' / ' + newuom.name
            return {}

        self.quoteuomcost = 'N/A'
        return {}


    @api.depends('quoteproduct', 'quoteproductuom', 'quoteqty')
    def _computeexactsaleqty(self):
        qty = self.quoteqty
        uom = self.quoteproduct.uom_id
        newuom = self.quoteproductuom

        if uom and newuom and qty:
            if (uom.uom_type == 'bigger'):
                salefactor = uom.factor_inv
            else:
                salefactor = uom.factor

            if (newuom.uom_type == 'bigger'):
                qtyfactor = newuom.factor_inv
            else:
                qtyfactor = newuom.factor

            if (qtyfactor == 0):
                self.quoteexactuomqty = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(qtyfactor))
            convqty = float(float(qty) * float(convfactor))
            convqty = round(convqty, 2)
            import math
            suggestedqty = math.ceil(convqty)
            self.quotesaleqty = int(suggestedqty)
            self.quoteexactuomqty= str(convqty) + " " + uom.name
            return {}

        self.quoteexactuomqty = 'N/A'
        return {}


    @api.depends('quoteproduct', 'quoteproductuom', 'quotesaleqty', 'quotesaleuom', 'quoteuserprice')
    def _computecost(self):
        qty = self.quotesaleqty
        price = self.quoteproduct.list_price
        uom = self.quoteproduct.uom_id
        newuom = self.quoteproductuom

        if uom and newuom and price:
            if (uom.uom_type == 'bigger'):
                salefactor = uom.factor_inv
            else:
                salefactor = uom.factor

            if (newuom.uom_type == 'bigger'):
                pricefactor = newuom.factor_inv
            else:
                pricefactor = newuom.factor

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(price) * float(convfactor))
            convprice = round(convprice, 2)

            if ( (self.quoteproduct.list_price > 0) and (convprice > 0) and (qty >= 1)  ):
                newfactor = float(self.quoteuserprice / convprice)
                realprice = float (self.quoteproduct.list_price * newfactor * qty)
                realprice = round(realprice, 2)
                self.quotecost = realprice


    @api.depends('quoteproduct', 'quoteproductuom', 'quotesaleqty', 'quotesaleuom', 'quoteuserprice')
    def _computeactualprice(self):
        qty = self.quotesaleqty
        price = self.quoteproduct.list_price
        uom = self.quoteproduct.uom_id
        newuom = self.quoteproductuom

        if uom and newuom and price:
            if (uom.uom_type == 'bigger'):
                salefactor = uom.factor_inv
            else:
                salefactor = uom.factor

            if (newuom.uom_type == 'bigger'):
                pricefactor = newuom.factor_inv
            else:
                pricefactor = newuom.factor

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(price) * float(convfactor))
            convprice = round(convprice, 2)


            if ((self.quoteproduct.list_price > 0) and (convprice > 0) and (qty >= 1)):
                newfactor = float(self.quoteuserprice / convprice)
                realprice = float(self.quoteproduct.list_price * newfactor * 1)
                realprice = round(realprice, 2)
                self.quoteactualprice = realprice


    @api.multi
    def newlinecreate(self):

        if not (self.quoteproduct and self.quotesaleqty and self.quoteproductuom and self.quoteactualprice):
            return

        if not (self.quoteproduct.description):
            description = self.quoteproduct.name
        else:
            description = self.quoteproduct.description


        vals = {'order_id': self.id, 'name': description, 'price_unit': self.quoteactualprice, 'product_id': self.quoteproduct.id, 'product_uom_qty': self.quotesaleqty, 'product_uom': self.quoteproduct.uom_id.id}
        newline = self.env['sale.order.line'].create(vals)
        newline.product_id_change()
        tempvals = { 'price_unit': self.quoteactualprice, }
        newline.write(tempvals)
        self.quoteproduct = False





