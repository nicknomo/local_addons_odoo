# -*- coding: utf-8 -*-
from openerp import api, models, fields
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp

import openerp.addons.product.product as native_product


class local_product_uom(models.Model):
    _inherit = "product.uom"
    _name = "localproduct.uom"
    _parent_store = True
    _parent_name = 'category_id'
    parent_left = fields.Integer('Parent Left',index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    uom_sell = fields.Boolean('Sellable?', change_default=True)

    name = fields.Char('Local Unit of Measure', required=True, translate=True)
    category_id = fields.Many2one('productuom.class', 'Unit of Measure Category', required=True, ondelete='cascade', help="Conversion between Units of Measure can only occur if they belong to the same category. The conversion will be made based on the ratios.")


    def name_create(self, cr, uid, name, context=None):
        """ The UoM category and factor are required, so we'll have to add temporary values
            for imported UoMs """
        if not context:
            context = {}
        uom_categ = self.pool.get('productuom.class')
        values = {self._rec_name: name, 'factor': 1}
        # look for the category based on the english name, i.e. no context on purpose!
        # TESt2
        if not context.get('default_category_id'):
            categ_misc = 'Unsorted/Imported Units'
            categ_id = uom_categ.search(cr, uid, [('name', '=', categ_misc)])
            if categ_id:
                values['category_id'] = categ_id[0]
            else:
                values['category_id'] = uom_categ.name_create(
                    cr, uid, categ_misc, context=context)[0]
        uom_id = self.create(cr, uid, values, context=context)
        return self.name_get(cr, uid, [uom_id], context=context)[0]


class product_uom_class(models.Model):
    _name = 'productuom.class'
    name = fields.Char('Name', required=True, translate=True)
    child_ids = fields.One2many('localproduct.uom','category_id','Child Tags')
    localuom = fields.One2many('localproduct.uom', 'id', 'Per Product Unit of Measure', required=True, help="Unit of Measure used for this products stock operation.")

    _sql_constraints = [('name_uniq','UNIQUE (name)','Product UOM Conversion Class must be unique.')]


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    uom_class = fields.Many2one('productuom.class', 'Per Product UOM Conversion Class', required=False, help="Unit of Measure class for Per Product UOM")
