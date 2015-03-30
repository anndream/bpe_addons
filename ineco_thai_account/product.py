# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today INECO LTD,. PART. (<http://www.ineco.co.th>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# 2014-10-24    POP-001    change _price_get from uom_po_id as standard_price (old uom_id)

from openerp.osv import fields, osv

class product_template(osv.osv):
    
    _inherit = 'product.template'

    def _price_get(self, cr, uid, products, ptype='list_price', context=None):
        if context is None:
            context = {}

        if 'currency_id' in context:
            pricetype_obj = self.pool.get('product.price.type')
            price_type_id = pricetype_obj.search(cr, uid, [('field','=',ptype)])[0]
            price_type_currency_id = pricetype_obj.browse(cr,uid,price_type_id).currency_id.id

        res = {}
        product_uom_obj = self.pool.get('product.uom')
        for product in products:
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost price for users not in this group
            # We fetch the standard price as the superuser
            if ptype != 'standard_price':
                res[product.id] = product[ptype] or 0.0
            else:
                res[product.id] = product.sudo()[ptype]
            if ptype == 'list_price':
                res[product.id] += product._name == "product.product" and product.price_extra or 0.0
            if 'uom' in context:
                #POP-001
                if ptype == 'list_price':
                    uom = product.uom_id or product.uos_id
                    res[product.id] = product_uom_obj._compute_price(cr, uid,
                            uom.id, res[product.id], context['uom'])
                else:
                    uom = product.uom_po_id or product.uos_id
                    res[product.id] = product_uom_obj._compute_price(cr, uid,
                            uom.id, res[product.id], context['uom'])
                    
            # Convert from price_type currency to asked one
            if 'currency_id' in context:
                # Take the price_type currency from the product field
                # This is right cause a field cannot be in more than one currency
                res[product.id] = self.pool.get('res.currency').compute(cr, uid, price_type_currency_id,
                    context['currency_id'], res[product.id],context=context)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: