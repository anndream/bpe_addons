# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 INECO Part., Ltd. (<http://www.ineco.co.th>).
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

from datetime import datetime
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
import time

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
        'additional_requirement_manual': fields.boolean('Manual'),
        'additional_requirement_certificate': fields.boolean('Certificate'),
        'additional_requirement_other': fields.boolean('Other'),
        'additional_other': fields.char('Other',size=128),
        'user_approve_id': fields.many2one('res.users','Approval By', required=True, track_visibility='onchange'),
        'date_approve': fields.datetime('Date Approval', track_visibility='onchange'),
        'user_checked_id': fields.many2one('res.users','Checked By', required=True, track_visibility='onchange'),
        'date_checked': fields.datetime('Date Checked', track_visibility='onchange'),
        'rfq_no': fields.char('RFQ No', size=32, track_visibility='onchange'),
        'rfq_date': fields.date('RFQ Date', track_visibility='onchange'),
    }
    _defaults = {
        'additional_requirement_manual': False,
        'additional_requirement_certificate': False,
        'additional_requirement_other': False,
        'rfq_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.order.rfq'),
        'rfq_date': time.strftime('%Y-%m-%d'),
    }
    _order = 'name desc'

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            new_po_no = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
            po.write({'name': new_po_no})
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)        
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid, 'user_approve_id': uid,'date_approve': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True
    
    def button_check(self,cr,uid,ids,context=None):
        for po in self.browse(cr,uid,ids):
            po.write({'user_checked_id': uid,'date_checked': time.strftime('%Y-%m-%d %H:%M:%S')})

    def button_approve(self,cr,uid,ids,context=None):
        for po in self.browse(cr,uid,ids):
            po.write({'user_approve_id': uid,'date_approve': time.strftime('%Y-%m-%d %H:%M:%S')})
    