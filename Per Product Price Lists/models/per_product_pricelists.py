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
        nothingreallymatters=True
        #test

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        super(ProductTemplate, self)._onchange_uom_id()

    @api.onchange('uom_po_id')
    def _onchange_uom_po_id(self):
        nothingreallymatters = True