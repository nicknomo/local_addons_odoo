# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
import openerp.addons.product.product as native_product


# For some reason, odoo's views had trouble finding the category of the uom in sale.order.line on the fly
# This keeps the record in the DB, and allows me to filter UOM categories.
class NewSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    #These computed fields are for calculating the domain on a form edit
    relcatid = fields.Many2one(related='product_uom.category_id',store=True)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        domain = super(NewSaleOrderLine,self).product_id_change()
        return {}
