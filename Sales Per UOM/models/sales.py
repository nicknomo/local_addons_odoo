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

    quoteuomprice = fields.Char('List:',compute='_computeuomprice')
    quoteuomcost = fields.Char('Cost:', compute='_computeuomcost')

    quoteuserprice = fields.Float('Sale Price:')
    quoteexactuomqty = fields.Char('Est Qty:',compute='_computeexactsaleqty')

    quotesaleqty = fields.Integer('Sale Qty:')
    quotesaleuom = fields.Char('Sale UoM', compute='_computesaleuom')
    #quotesaleuom = fields.Many2one(related='quoteproduct.uom_id',ondelete='cascade')
    quotecost = fields.Float('Line Price', compute='_computecost')

    quoteactualprice = fields.Float('sell at this price:', compute='_computeactualprice')


    # The default onchange returns a domain, but it also does other stuff. Since we set a default domain, we want don't want it to return a domain
    # So we make a call to the original onchange, and just absorb the return value.  It still does all the other stuff

    @api.multi
    @api.onchange('quoteproduct')
    def quoteproduct_id_change(self):
        product = self.quoteproduct

        if (product.uom_id):
            vals = {}
            self.quoteproductuom = product.uom_id
            domain = {'quoteproductuom': [('category_id', '=', self.quoteproduct.uom_id.category_id.id)]}
            vals['quoteproductuom'] = self.quoteproduct.uom_id
            self.update(vals)
            return {'domain': domain}

        else:
            self.quoteqty = False
            self.quoteproductuom = False
            self.quoteuserprice = False
            self.quotesaleqty = False

        return {}

    @api.depends('quoteproduct')
    def _computesaleuom(self):
        self.quotesaleuom = self.quoteproduct.uom_id.name
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
            self.quoteuomprice= '' + str(convprice) + ' per  ' + newuom.name
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
                self.quoteuomprice = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(cost) * float(convfactor))
            convprice = round(convprice, 2)
            self.quoteuomcost= '' + str(convprice) + ' per  ' + newuom.name
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
                pricefactor = newuom.factor_inv
            else:
                pricefactor = newuom.factor

            if (pricefactor == 0):
                self.quoteuomprice = 'Div By 0'
                return {}

            convfactor = float(float(salefactor) / float(pricefactor))
            convprice = float(float(qty) * float(convfactor))
            convprice = round(convprice, 2)
            self.quoteexactuomqty= str(convprice) + " " + uom.name
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
                self.quotecost = realprice


    @api.depends('quoteproduct', 'quoteproductuom', 'quotesaleqty', 'quotesaleuom', 'quoteuserprice')
    def _computeactualprice(self):
        self.quoteactualprice = 1



