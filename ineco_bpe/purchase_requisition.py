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

    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = {}
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            result[po.requisition_id.id] = True
        return result.keys()

    def _get_requisition_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.requisition.line').browse(cr, uid, ids, context=context):
            result[line.requisition_id.id] = True
        return result.keys()

    def _get_ready_product (self,cr,uid,ids,name,arg,context=None):
        res =  {}
        for pr in self.browse(cr, uid, ids):
            res[pr.id] = {
                'rfq_ready': False
            }
            sql = """
                select count(*) from purchase_requisition_line prl
                where requisition_id = %s and (rfq_ready = False or rfq_ready is null)
            """
            cr.execute(sql % (pr.id))
            output = cr.fetchone()
            if output and output[0] == 0.0:
                if pr.state == 'cancel':
                    res[pr.id]['rfq_ready'] = False
                else:
                    res[pr.id]['rfq_ready'] = True
            else:
                res[pr.id]['rfq_ready'] = False
        return res
    
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
        'rfq_ready': fields.function(_get_ready_product, method=True, type='boolean', string="RFQ Ready",
            store={
                'purchase.requisition': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                'purchase.requisition.line': (_get_requisition_line, [], 10),
                'purchase.order': (_get_purchase_order, [], 10),
            },
            multi='_rfq_ready'),
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

    def _prepare_purchase_order_line(self, cr, uid, requisition, requisition_line, purchase_id, supplier, context=None):
        if context is None:
            context = {}
        po_line_obj = self.pool.get('purchase.order.line')
        product_uom = self.pool.get('product.uom')
        product = requisition_line.product_id
        default_uom_po_id = product.uom_po_id.id
        ctx = context.copy()
        ctx['tz'] = requisition.user_id.tz
        date_order = requisition.ordering_date and fields.date.date_to_datetime(self, cr, uid, requisition.ordering_date, context=ctx) or fields.datetime.now()
        qty = product_uom._compute_qty(cr, uid, requisition_line.product_uom_id.id, requisition_line.product_qty, default_uom_po_id)
        supplier_pricelist = supplier.property_product_pricelist_purchase and supplier.property_product_pricelist_purchase.id or False
        vals = po_line_obj.onchange_product_id(
            cr, uid, [], supplier_pricelist, product.id, qty, default_uom_po_id,
            supplier.id, date_order=date_order,
            fiscal_position_id=supplier.property_account_position,
            date_planned=requisition_line.schedule_date,
            name=False, price_unit=False, state='draft', context=context)['value']
        vals.update({
            'order_id': purchase_id,
            'product_id': product.id,
            'account_analytic_id': requisition_line.account_analytic_id.id,
            'name': requisition_line.note or '-',
        })
        return vals
    
    def button_check(self,cr,uid,ids,context=None):
        for pr in self.browse(cr,uid,ids):
            pr.write({'user_checked_id': uid,'date_checked': time.strftime('%Y-%m-%d %H:%M:%S')})

    def tender_reset(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft',
                                  'date_approve': False,
                                  'date_checked': False})
        for p_id in ids:
            # Deleting the existing instance of workflow for PO
            self.delete_workflow(cr, uid, [p_id])
            self.create_workflow(cr, uid, [p_id])
        return True

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

    def _get_ready_product (self,cr,uid,ids,name,arg,context=None):
        res =  {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'rfq_ready': False
            }
            if line.product_id:
                sql = """
                    select product_id from purchase_order po
                    join purchase_order_line pol on po.id = pol.order_id
                    where requisition_id = %s and product_id = %s and po.state not in ('cancel')
                """
                cr.execute(sql % (line.requisition_id.id, line.product_id.id))
                output = cr.fetchone()
                if output and output[0]:
                    res[line.id]['rfq_ready'] = True
                else:
                    res[line.id]['rfq_ready'] = False
        return res

    def _get_purchase_order(self, cr, uid, ids, context=None):
        result = {}
        for po in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
            for line in po.requisition_id.line_ids:
                result[line.id] = True
        return result.keys()

    def _get_requisition(self, cr, uid, ids, context=None):
        result = {}
        for pr in self.pool.get('purchase.requisition').browse(cr, uid, ids, context=context):
            for line in pr.line_ids:
                result[line.id] = True
        return result.keys()

    _inherit = "purchase.requisition.line"
    _description = "Purchase Requisition Line"
    _columns = {
        'cost': fields.float('Price Unit', digits=(12,4)),
        'note': fields.char('Note', size=254),
        'rfq_ready': fields.function(_get_ready_product, method=True, type='boolean', string="RFQ Ready",
            store={
                'purchase.requisition.line': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                'purchase.requisition': (_get_requisition, [], 10),
                'purchase.order': (_get_purchase_order, [], 10),
            },
            multi='_rfq_ready'),
    }
    _defaults = {
        'cost': 1.0000,
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