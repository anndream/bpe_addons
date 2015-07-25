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

from openerp.osv import osv, fields

class account_journal(osv.osv):

    _inherit = 'account.journal'
    
    _columns = {
        'print_sale_tax': fields.boolean('Print Tax Report'), #To be remove because Tax Report from GL Only
        'customer': fields.boolean('Customer Payment'),
        'supplier': fields.boolean('Supplier Payment'),
        'customer_invoice': fields.boolean('Customer Invoice'),
        'supplier_invoice': fields.boolean('Supplier Invoice'),
        'customer_refund': fields.boolean('Customer Refund'),
        'supplier_refund': fields.boolean('Supplier Refund'),
        'petty_cash': fields.boolean('Petty Cash'),
        'receipt_journal_id': fields.many2one('account.journal','Receipt Journal'),
        'active': fields.boolean('Active'),
    }
    
    _defaults = {
        'print_sale_tax': True,
        'customer': False,
        'supplier': False,
        'customer_invoice': False,
        'supplier_invoice': False,
        'customer_refund': False,
        'supplier_refund': False,
        'pett_cash': False,
        'active': True,
    }