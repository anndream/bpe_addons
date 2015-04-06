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

class ineco_job_type(osv.osv):
    _name = 'ineco.job.type'
    _description = "Job Type"
    _columns = {
        'name': fields.char('Description', size=128,required=True),
    }
    _sql_constraints = [
        ('name_unique', 'unique (name)', 'Job Type must be unique!')
    ]

class purchase_requisition(osv.osv):
    _inherit = "purchase.requisition"
    _columns = {
        'user_approve_id': fields.many2one('res.users','Approval By', required=True, track_visibility='onchange'),
        'date_approve': fields.datetime('Date Approval', track_visibility='onchange'),
        'user_checked_id': fields.many2one('res.users','Checked By', required=True, track_visibility='onchange'),
        'date_checked': fields.datetime('Date Checked', track_visibility='onchange'),
        'type_of_requirement': fields.selection([('normal','Normal'),('urgent','Urgent'),('shutdown','Shutdown')], 'Type of Requirement', required=True),
        'additional_requirement_manual': fields.boolean('Manual'),
        'additional_requirement_certificate': fields.boolean('Certificate'),
        'additional_requirement_other': fields.boolean('Other'),
        'additional_other': fields.char('Other',size=128),
        'job_type_id': fields.many2one('ineco.job.type','Type of Order',required=True, track_visibility='onchange', ondelete='restrict'),
    }
    _defaults = {
        'additional_requirement_manual': False,
        'additional_requirement_certificate': False,
        'additional_requirement_other': False,
        'type_of_requirement': 'normal',
        'ordering_date': time.strftime('%Y-%m-%d'),
        'name': '/',
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.requisition') or '/'
        context = dict(context or {}, mail_create_nolog=True)
        order =  super(purchase_requisition, self).create(cr, uid, vals, context=context)
        #self.message_post(cr, uid, [order], body=_("RFQ created"), context=context)
        return order

    def _prepare_purchase_order(self, cr, uid, requisition, supplier, context=None):
        supplier_pricelist = supplier.property_product_pricelist_purchase
        emp_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)])
        employee = self.pool.get('hr.employee').browse(cr, uid, emp_ids)
        user_checked_id = False
        user_approve_id = False
        if employee.parent_id and employee.parent_id.user_id :
            user_approve_id = employee.parent_id.user_id.id
        if employee.coach_id and employee.coach_id.user_id :
            user_checked_id =  employee.coach_id.user_id.id

        return {
            'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.temp'),
            'origin': requisition.name,
            'date_order': requisition.date_end or fields.datetime.now(),
            'partner_id': supplier.id,
            'pricelist_id': supplier_pricelist.id,
            'currency_id': supplier_pricelist and supplier_pricelist.currency_id.id or requisition.company_id.currency_id.id,
            'location_id': requisition.procurement_id and requisition.procurement_id.location_id.id or requisition.picking_type_id.default_location_dest_id.id,
            'company_id': requisition.company_id.id,
            'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
            'requisition_id': requisition.id,
            'notes': requisition.description,
            'picking_type_id': requisition.picking_type_id.id,
            'user_approve_id': user_approve_id,
            'user_checked_id': user_checked_id,
            'payment_term_id': supplier.property_supplier_payment_term and supplier.property_supplier_payment_term.id or False, 
        }
    
    def button_check(self,cr,uid,ids,context=None):
        for pr in self.browse(cr,uid,ids):
            pr.write({'user_checked_id': uid,'date_checked': time.strftime('%Y-%m-%d %H:%M:%S')})

    #Approve PR
    def tender_in_progress(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'in_progress', 'user_approve_id': uid, 'date_approve': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)

    def tender_open(self, cr, uid, ids, context=None):
        for data in self.browse(cr, uid, ids):
            if not data.purchase_ids:
                raise osv.except_osv('Warning!', 'You not have any RFQ or Purchase Order.')                
        return self.write(cr, uid, ids, {'state': 'open'}, context=context)

    def onchange_user_id(self, cr, uid, ids, user_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param user_id: User
        @return:  Dictionary of changed values
        """
        value = {'user_approve_id': False,'user_checked_id': False}
        group = self.pool.get('res.groups').browse(cr, uid, [54])
        domain_approve_ids = [x.id for x in group.users]
        domain_approve_ids.remove(1)
        domain = {}
        if user_id:
            emp_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',user_id)])
            employee = self.pool.get('hr.employee').browse(cr, uid, emp_ids)
            if employee.parent_id and employee.parent_id.user_id :
                value.update({'user_approve_id': employee.parent_id.user_id.id })
            if employee.coach_id and employee.coach_id.user_id :
                value.update({'user_checked_id': employee.coach_id.user_id.id })
            if employee.department_id:
                domain = {'account_analytic_id':  ['|','|',('department_id', '=', employee.department_id.id),
                                                   ('parent_id.department_id','=', employee.department_id.id),
                                                   ('project','=',True),('close','=',False)],
                          'user_approve_id': [('id','in',domain_approve_ids)]}
        return {'value': value, 'domain': domain}

class purchase_requisition_line(osv.osv):

    def _product_unit_category (self,cr,uid,ids,context=None):
        res = {
            uom_category_id: False
        }
        for line in self.browse(cr,uid,ids):
            res[line.id]['uom_category_id'] = line.product_id.uom_id.category_id.id
        return res

    _inherit = "purchase.requisition.line"
    _description = "Purchase Requisition Line"
    _columns = {
        'cost': fields.float('Price Unit', digits=(12,2)),
        'note': fields.char('Note', size=254),
        #'uom_category_id': fields.function(_product_unit_category, type="many2one", 
        #                        string='Uom Category', relation="uom.category", multi='_uom_category'),                
    }
    _defaults = {
        'cost': 1.0,
        'note': False,
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, parent_analytic_account, analytic_account, parent_date, date, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'product_uom_id': ''}
        domain = {}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            value = {'product_uom_id': prod.uom_id.id, 'product_qty': 1.0,'cost': prod.standard_price or 0.0}
            domain = {'product_uom_id': [('category_id','=',prod.uom_id.category_id.id)]}
        if not analytic_account:
            value.update({'account_analytic_id': parent_analytic_account})
        if not date:
            value.update({'schedule_date': parent_date})
        return {'value': value,'domain':domain}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: