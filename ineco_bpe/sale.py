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

class sale_order(osv.osv):

    _inherit = 'sale.order'
    _description = "BPE Sales Order"

    _columns = {
        'origin': fields.text('Source Document', help="Reference of the document that generated this sales order request."),
        'rev': fields.char('Revision', size=32, required=True),
        'subject': fields.char('Subject', size=254, required=True),
        'refer': fields.char('Job Refer', size=254, required=True),
        'sale_remark_id': fields.many2one('sale.order.remark','Remarks'),
        'sale_document_ids': fields.many2many('sale.order.document.require','sale_order_document_rel','sale_order_id','document_id','Document Required'),
    }

    _defaults = {
        'rev': False,
        'subject': False,
        'refer': False,
    }

class sale_order_line(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res

    _inherit = 'sale.order.line'
    _columns = {
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price'), readonly=True, states={'draft': [('readonly', False)]}),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }

class sale_order_remark(osv.osv):
    _name = 'sale.order.remark'
    _columns = {
        'name': fields.char('Reamrk Description', size=254, required=True)
    }
    _order = 'name'
    _defaults = {
        'name': False,
    }
    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Remark must be unique!')
    ]

class sale_order_document_require(osv.osv):
    _name = 'sale.order.document.require'
    _columns = {
        'name': fields.char('Document Name', size=254, required=True)
    }
    _order = 'name'
    _defaults = {
        'name': False,
    }
    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Document Required must be unique!')
    ]
