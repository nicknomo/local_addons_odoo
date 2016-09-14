# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp

import openerp.addons.product.product as native_product


class local_product_uom(models.Model):
    _inherits = {'product.uom':'uid', }
    _name = "localproduct.uom"
    uid = fields.Many2one('product.uom', ondelete='cascade', required=True)
    #This references the conversion class this product belongs to
    localcategory_id = fields.Many2one('productuom.class', 'Unit of Measure Conversion Class', required=True, ondelete='cascade', help="Conversion between Units of Measure can only occur if they belong to the same category. The conversion will be made based on the ratios.")


    #Here we automatically compute the normal UoM category, base on the conversion class.  The normal UoM category is part of the conversion class, so its easy to reference.
    @api.onchange('localcategory_id')
    def onchange_localcategory_id(self):
        self.category_id = self.localcategory_id.catid

    def onchange_type(self, cursor, user, ids, value):
        if value == 'reference':
            return {'value': {'factor': 1, 'factor_inv': 1}}
        return {}




class overloadproduct_uom(models.Model):
    _inherit = 'product.uom'
    #this lets us know if the UoM is sellable
    uom_sell = fields.Boolean('Sellable?', default=True)
    #this will be a hidden field that lets us filter our product specific UoM's from the normal UoM's
    islocaluom = fields.Boolean('Is a product uom?', default=False)
    #We need to make sure the name and category are unique, so we add SQL constraints
    _sql_constraints = [
        ('factor_gt_zero', 'CHECK (factor!=0)', 'The conversion ratio for a unit of measure cannot be 0!'),
        ('uom_uniq', 'UNIQUE (name,category_id)', 'Only one entry for that UOM per category')]

class overloaduom_category(models.Model):
    _inherit = 'product.uom.categ'
    #this will be a hidden field that lets us filter our UoM Conversion Categories from the normal UoM categories
    isuomclass = fields.Boolean('Is a UoM Class?', default=False)
    #We cannot allow duplicate names.  Odoo doesn't normally do this check, but it probably should.
    _sql_constraints = [('name_uniq', 'UNIQUE (name)', 'Product UOM Conversion Class must be unique.')]


class product_uom_class(models.Model):
    _inherits = {'product.uom.categ':'catid'}
    _name = 'productuom.class'
    catid = fields.Many2one('product.uom.categ', ondelete='cascade', required=True)
    #this lets us reference our product specific UoMs from the conversion class.
    localuom = fields.One2many('localproduct.uom', 'localcategory_id', 'Per Product Unit of Measure', required=False, help="Unit of Measure used for this products stock operation.")


    #TODO: Delete records of children


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    uom_class = fields.Many2one('productuom.class', 'Per Product UOM Conversion Class', required=False, help="Unit of Measure class for Per Product UOM")
