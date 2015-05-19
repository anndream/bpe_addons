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
        'internal_number': fields.char('Internal Number', size=32),
    }
    _defaults = {
        'additional_requirement_manual': False,
        'additional_requirement_certificate': False,
        'additional_requirement_other': False,
        'rfq_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.order.rfq'),
        'rfq_date': fields.date.context_today, #time.strftime('%Y-%m-%d'),
    }
    _order = 'name desc'

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.temp') or '/'
        context = dict(context or {}, mail_create_nolog=True)
        order =  super(purchase_order, self).create(cr, uid, vals, context=context)
        self.message_post(cr, uid, [order], body=_("RFQ created"), context=context)
        return order

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            #new_po_no = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
            #po.write({'name': new_po_no})
            if not po.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)        
        self.pool.get('purchase.order.line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid, 
                                       'user_approve_id': uid, 'date_approve': time.strftime('%Y-%m-%d %H:%M:%S')})
        return True
    
    def button_check(self,cr,uid,ids,context=None):
        for po in self.browse(cr,uid,ids):
            if not po.internal_number:
                new_po_no = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
            else:
                new_po_no = po.name ;
            po.write({'name': new_po_no, 'user_checked_id': uid,'date_checked': time.strftime('%Y-%m-%d %H:%M:%S'),'internal_number': new_po_no})

    def button_approve(self,cr,uid,ids,context=None):
        for po in self.browse(cr,uid,ids):
            po.write({'user_approve_id': uid,'date_approve': time.strftime('%Y-%m-%d %H:%M:%S')})

    def action_cancel_draft(self, cr, uid, ids, context=None):
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state':'draft', 'shipped':0, 'date_approve': False, 'date_checked': False})
        self.set_order_line_status(cr, uid, ids, 'draft', context=context)
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            self.delete_workflow(cr, uid, [p_id]) # TODO is it necessary to interleave the calls?
            self.create_workflow(cr, uid, [p_id])
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    