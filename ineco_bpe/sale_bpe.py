# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO Ltd., Part. (<http://www.ineco.co.th>).
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

from datetime import datetime, timedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow

# class sale_order_line(osv.osv):
#
#     def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
#         tax_obj = self.pool.get('account.tax')
#         cur_obj = self.pool.get('res.currency')
#         res = {}
#         if context is None:
#             context = {}
#         for line in self.browse(cr, uid, ids, context=context):
#             price = line.price_units * (1 - (line.discount or 0.0) / 100.0)
#             taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
#             cur = line.order_id.pricelist_id.currency_id
#             res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
#         return res
#
#     def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
#         """ Wrapper because of direct method passing as parameter for function fields """
#         return self._amount_all(cr, uid, ids, field_name, arg, context=context)
#
#     def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
#         res = {}
#         for order in self.browse(cr, uid, ids, context=context):
#             res[order.id] = {
#                 'price_units': 0.0,
#             }
#             price_units = 0.0
#             for breakdown in order.breakdown_ids:
#                 price_units += breakdown.price_unit
#             #for estimate in order.estimate_ids:
#             #    price_units += estimate.total_cost
#             res[order.id]['price_units'] = price_units
#         return res
#
#     def _get_order_line(self, cr, uid, ids, context=None):
#         result = {}
#         for line in self.pool.get('sale.order.line.estimate').browse(cr, uid, ids, context=context):
#             result[line.sale_line_id.id] = True
#         return result.keys()
#
#     def _get_order_line2(self, cr, uid, ids, context=None):
#         result = {}
#         for line in self.pool.get('sale.order.line.breakdown').browse(cr, uid, ids, context=context):
#             result[line.sale_line_id.id] = True
#         return result.keys()
#
#     _inherit = 'sale.order.line'
#     _columns = {
#         'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
#         'breakdown_ids': fields.one2many('sale.order.line.breakdown','sale_line_id','Breakdown'),
#         'estimate_ids': fields.one2many('sale.order.line.estimate','sale_line_id','Estimates'),
#         'price_units': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Unit Price',
#             store={
#                 'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
#                 #'sale.order.line.estimate': (_get_order_line, [], 10),
#                 'sale.order.line.breakdown': (_get_order_line2, [], 10),
#             },
#             multi='sums', help="The total amount."),
#     }
#
#     def _get_sequence(self, cr, uid, context=None):
#         context = context or {}
#         next_id = False
#         if context.get('lines', False):
#             next_id = len(context.get('lines', False)) + 1
#         else:
#             next_id = 1
#         return next_id
#
#     _defaults = {
#         'sequence': _get_sequence,
#     }
#
#     def write(self, cr, uid, ids, vals, context=None):
#         if context is None:
#             context = {}
#         tl = self.browse(cr,uid,ids)[0]
#         if tl.price_units:
#             vals['price_unit'] = tl.price_units
#         return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)
#
#     def button_dummy(self, cr, uid, ids, context=None):
#         for data in self.browse(cr, uid, ids):
#             data.write({'price_unit': data.price_units})
#         return True


class sale_order_line_breakdown(osv.osv):

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'price_unit': 0.0,
            }
            price_units = 0.0
            for estimate in order.estimate_ids:
                price_units += estimate.total_cost
            res[order.id]['price_unit'] = price_units
        return res

    def _get_order_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line.estimate').browse(cr, uid, ids, context=context):
            result[line.breakdown_id.id] = True
        return result.keys()

    _name = 'sale.order.line.breakdown'
    _description = "Breakdown"
    _columns = {
        'name': fields.char('Breakdown Name',size=254),
        'sale_line_id': fields.many2one('sale.order.line','Sale Line'),
        'sequence': fields.integer('Sequence',required=True),
        'price_unit': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Price Unit',
            multi='sums'),
        # 'price_unit': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Price Unit',
        #     store={
        #         'sale.order.line.breakdown': (lambda self, cr, uid, ids, c={}: ids, [], 10),
        #         'sale.order.line.estimate': (_get_order_line, [], 10),
        #     },
        #     multi='sums', help="The amount without tax.", track_visibility='onchange'),
        'remark': fields.char('Remark', size=64),
        'estimate_ids': fields.one2many('sale.order.line.estimate','breakdown_id','Estimates'),
    }
    _order = 'sale_line_id, sequence'

    def _get_sequence(self, cr, uid, context=None):
        context = context or {}
        next_id = False
        if context.get('lines', False):
            next_id = len(context.get('lines', False)) + 1
        else:
            next_id = 1
        return next_id

    _defaults = {
        'sequence': _get_sequence,
    }


class sale_order_line_estimate(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'cost_plus': line.cost * 100 / (100 - line.cost_rate),
                'unit_price': line.cost + (line.cost * line.cost_rate),
                'estimate_cost': line.cost * line.quantity ,
                'total_cost': ((line.cost + (line.cost * line.cost_rate)) * line.quantity) + line.mod_demod,
            }
        return res

    _name = 'sale.order.line.estimate'
    _description = 'Cost Estimate'
    _columns = {
        'name': fields.char('Description',size=254),
        'sale_line_id': fields.many2one('sale.order.line','Sale Line'),
        'breakdown_id': fields.many2one('sale.order.line.breakdown','Breakdown'),
        'sequence': fields.integer('Sequence',required=True),
        'product_id': fields.many2one('product.product','Item',required=True),
        'uom_id': fields.many2one('product.uom', 'UOM', required=True),
        'quantity': fields.integer('Quantity', required=True),
        'cost': fields.float('Supplier Price', required=True),
        'cost_rate': fields.float('Cost Rate', required=True),
        'cost_plus': fields.function(_amount_line, digits_compute=dp.get_precision('Account'), string='Cost Plus',
            store={
                'sale.order.line.estimate': (lambda self, cr, uid, ids, c={}: ids, [], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='onchange'),
        'unit_price': fields.function(_amount_line, digits_compute=dp.get_precision('Account'), string='Price Unit',
            store={
                'sale.order.line.estimate': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                #'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='onchange'),
        'estimate_time': fields.char('Estimate Time', size=64),
        'propose_time': fields.char('Propose Time', size=64),
        'days': fields.char('Days', size=64),
        'ref_no': fields.char('Ref. Cont. No', size=64),
        'estimate_cost': fields.function(_amount_line, digits_compute=dp.get_precision('Account'), string='Estimate Cost',
            store={
                'sale.order.line.estimate': (lambda self, cr, uid, ids, c={}: ids, [], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='onchange'),
        'total_cost': fields.function(_amount_line, digits_compute=dp.get_precision('Account'), string='Total Cost',
            store={
                'sale.order.line.estimate': (lambda self, cr, uid, ids, c={}: ids, [], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='onchange'),
        'extra_cost': fields.float('OT Rate'),
        'standby_cost': fields.float('Standby Rate'),
        'delivery_time': fields.char('Delivery Time', size=64),
        'mod_demod': fields.float('MOD/DEMOD'),
        'remark': fields.char('Remark', size=64),
        'categ_id': fields.related('product_id','categ_id', type='many2one', relation="product.category", string='Category', readonly=True),
        'supplier_id': fields.many2one('res.partner', 'Supplier', domain = [('supplier','=',True)]),
    }
    _order = 'breakdown_id, sequence'

    def _get_sequence(self, cr, uid, context=None):
        context = context or {}
        next_id = False
        if context.get('lines', False):
            next_id = len(context.get('lines', False)) + 1
        else:
            next_id = 1
        return next_id

    _defaults = {
        'sequence': _get_sequence,
        'cost_rate': 0.00,
        'quantity': 1.0,
        'mod_demod': 0.0,
    }
#
#     def create(self, cr, uid, vals, context=None):
#         cost = vals.get('cost',0.0)
#         cost_rate = vals.get('cost_rate',0.0)
#         quantity = vals.get('quantity',0.0)
#         mod_demod = vals.get('mod_demod',0.0)
#         cost_plus = vals.get('cost_plus',0.0)
#         unit_price = vals.get('unit_price',0.0)
#         estimate_cost = vals.get('estimate_cost',0.0)
#         total_cost = vals.get('total_cost',0.0)
#         cost_plus = cost * 100 / (100 - cost_rate)
#         unit_price = cost + cost_plus
#         estimate_cost = cost * quantity
#         total_cost = (unit_price * quantity) + mod_demod
#         vals.update({'cost_plus': cost_plus,'unit_price': unit_price,'estimate_cost':estimate_cost,'total_cost':total_cost})
#         order =  super(sale_order_line_estimate, self).create(cr, uid, vals, context=context)
#         return order
#
    def onchange_product_id(self, cr, uid, ids, product_id, product_name, supplier_id, context=None):
        value = {'name': False}
        domain = {}
        supplier_product_obj = self.pool.get('product.supplierinfo')
        delay = False
        if product_id and not product_name:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            if supplier_id:
                supplier_ids = supplier_product_obj.search(cr, uid, [('product_tmpl_id','=',product.product_tmpl_id.id),
                                                      ('name','=',supplier_id)])
                if supplier_ids:
                    supplier_obj = supplier_product_obj.browse(cr ,uid, supplier_ids)
                    delay = supplier_obj[0].delay
            value.update({'name': product.name,'uom_id':product.uom_id.id,'cost': product.standard_price, 'delivery_time': delay })
        return {'value': value, 'domain': domain}

    def onchange_supplier_id(self, cr, uid, ids, product_id, supplier_id, context=None):
        value = {}
        domain = {}
        supplier_product_obj = self.pool.get('product.supplierinfo')
        delay = False
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            if supplier_id:
                supplier_ids = supplier_product_obj.search(cr, uid, [('product_tmpl_id','=',product.product_tmpl_id.id),
                                                      ('name','=',supplier_id)])
                if supplier_ids:
                    supplier_obj = supplier_product_obj.browse(cr ,uid, supplier_ids)
                    delay = supplier_obj[0].delay
            value.update({'cost': product.standard_price, 'delivery_time': delay })
        return {'value': value, 'domain': domain}

    def onchange_price(self, cr, uid, ids, cost=0.0, cost_rate=0.0, quantity=0.0, mod_demod=0.0 , context=None):
        """ Changes UoM and name if product_id changes.
        @param product_id: Product
        @return:  Dictionary of changed values
        """
        value = {}
        domain = {}
        cost_plus = cost * 100 / (100 - cost_rate)
        unit_price = cost + cost_plus
        estimate_cost = cost * quantity
        total_cost = (unit_price * quantity) + mod_demod
        value.update({'cost_plus': cost_plus,'unit_price': unit_price,'estimate_cost':estimate_cost,'total_cost':total_cost})

        return {'value': value, 'domain': domain}


# class sale_order(osv.osv):
#
#     def _amount_line_tax(self, cr, uid, line, context=None):
#         val = 0.0
#         for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_units * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
#             val += c.get('amount', 0.0)
#         return val
#
#     def _get_order(self, cr, uid, ids, context=None):
#         result = {}
#         for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
#             result[line.order_id.id] = True
#         return result.keys()
#
#     def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
#         """ Wrapper because of direct method passing as parameter for function fields """
#         return self._amount_all(cr, uid, ids, field_name, arg, context=context)
#
#     def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
#         cur_obj = self.pool.get('res.currency')
#         res = {}
#         for order in self.browse(cr, uid, ids, context=context):
#             res[order.id] = {
#                 'amount_untaxed': 0.0,
#                 'amount_tax': 0.0,
#                 'amount_total': 0.0,
#             }
#             val = val1 = 0.0
#             cur = order.pricelist_id.currency_id
#             for line in order.order_line:
#                 val1 += line.price_subtotal
#                 val += self._amount_line_tax(cr, uid, line, context=context)
#             res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
#             res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
#             res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
#         return res
#
#     inherit = 'sale.order'
#     _columns = {
#         'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), string='Taxes',
#             store={
#                 'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
#                 'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
#             },
#             multi='sums', help="The tax amount."),
#     }
