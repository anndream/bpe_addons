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

import time

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class hr_department(osv.osv):
    _inherit = 'hr.department'
    _columns = {
        'petty_account_id': fields.many2one('account.account','Petty Cash Account'),
    }


class hr_expense_expense(osv.osv):

    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.total_amount
            res[expense.id] = total
        return res

    def _get_expense_from_line(self, cr, uid, ids, context=None):
        return [line.expense_id.id for line in self.pool.get('hr.expense.line').browse(cr, uid, ids, context=context)]

    _inherit = 'hr.expense.expense'
    _columns = {
        'amount': fields.function(_amount, string='Total Amount', digits_compute=dp.get_precision('Account'),
            store={
                'hr.expense.line': (_get_expense_from_line, ['unit_amount','unit_quantity','tax_id'], 10)
            }),
    }

    def action_move_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
            #if not exp.employee_id.address_home_id:
            #    raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            #if not exp.employee_id.address_home_id.property_account_payable.id:
            #    raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            if not exp.department_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a department.'))
            if not exp.department_id.petty_account_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a Petty Account on department.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency

            #create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)

            #one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)

            #create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            #acc = exp.employee_id.address_home_id.property_account_payable.id
            acc = exp.employee_id.department_id.petty_account_id.id
            eml.append({
                    'type': 'dest',
                    'name': exp.department_id.name,
                    'price': total,
                    'account_id': acc,
                    #'date_maturity': exp.date_confirm,
                    #'date': exp.date_confirm,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and exp.currency_id.id or False,
                    'ref': exp.name
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, exp.employee_id.address_home_id, exp.date_confirm, context=context)), eml)
            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'done'}, context=context)
        return True

    def move_line_get(self, cr, uid, expense_id, context=None):
        res = []
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        if context is None:
            context = {}
        exp = self.browse(cr, uid, expense_id, context=context)
        company_currency = exp.company_id.currency_id.id

        for line in exp.line_ids:
            mres = self.move_line_get_item(cr, uid, line, context)
            if not mres:
                continue
            res.append(mres)

            #Calculate tax according to default tax on product
            taxes = []
            #Taken from product_id_onchange in account.invoice
            if line.product_id:
                fposition_id = False
                fpos_obj = self.pool.get('account.fiscal.position')
                fpos = fposition_id and fpos_obj.browse(cr, uid, fposition_id, context=context) or False
                product = line.product_id
                taxes = [line.tax_id] or []
                #Remove by ME
                #taxes = product.supplier_taxes_id
                #If taxes are not related to the product, maybe they are in the account
                if not taxes:
                    a = product.property_account_expense.id #Why is not there a check here?
                    if not a:
                        a = product.categ_id.property_account_expense_categ.id
                    a = fpos_obj.map_account(cr, uid, fpos, a)
                    taxes = a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False
            if not taxes:
                continue
            tax_l = []
            base_tax_amount = line.total_amount
            #Calculating tax on the line and creating move?
            for tax in tax_obj.compute_all(cr, uid, taxes,
                    line.unit_amount ,
                    line.unit_quantity, line.product_id,
                    exp.user_id.partner_id)['taxes']:
                tax_code_id = tax['base_code_id']
                if not tax_code_id:
                    continue
                res[-1]['tax_code_id'] = tax_code_id
                ##
                is_price_include = tax_obj.read(cr,uid,tax['id'],['price_include'],context)['price_include']
                if is_price_include:
                    ## We need to deduce the price for the tax
                    res[-1]['price'] = res[-1]['price'] - tax['amount']
                    # tax amount countains base amount without the tax
                    base_tax_amount = (base_tax_amount - tax['amount']) * tax['base_sign']
                else:
                    base_tax_amount = base_tax_amount * tax['base_sign']

                assoc_tax = {
                             'type':'tax',
                             'name': line.ref,
                             'price_unit': tax['price_unit'],
                             'quantity': 1,
                             'price': tax['amount'] or 0.0,
                             'account_id': tax['account_collected_id'] or mres['account_id'],
                             'tax_code_id': tax['tax_code_id'],
                             'tax_amount': tax['amount'] * tax['base_sign'],
                             'date_maturity': line.date_value,
                             'date': line.date_value,
                             'partner_id': line.partner_id.id,
                             'base_amount': line.untaxed_amount or 1.0,
                             }
                tax_l.append(assoc_tax)

            res[-1]['tax_amount'] = cur_obj.compute(cr, uid, exp.currency_id.id, company_currency, base_tax_amount, context={'date': exp.date_confirm})
            res += tax_l
        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        company = line.expense_id.company_id
        property_obj = self.pool.get('ir.property')
        if line.product_id:
            if line.account_id:
                acc = line.account_id
            else:
                acc = line.product_id.property_account_expense
            if not acc:
                acc = line.product_id.categ_id.property_account_expense_categ
            if not acc:
                raise osv.except_osv(_('Error!'), _('No purchase account found for the product %s (or for his category), please configure one.') % (line.product_id.name))
        else:
            acc = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', context={'force_company': company.id})
            if not acc:
                raise osv.except_osv(_('Error!'), _('Please configure Default Expense account for Product purchase: `property_account_expense_categ`.'))
        return {
            'type':'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit':line.unit_amount,
            'quantity':line.unit_quantity,
            'price':line.total_amount,
            'account_id':acc.id,
            'product_id':line.product_id.id,
            'uos_id':line.uom_id.id,
            'account_analytic_id':line.analytic_account.id,
            'ref': line.ref,
            'date': line.date_value,
        }

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        partner_id  = self.pool.get('res.partner')._find_accounting_partner(part).id
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': x.get('partner_id', partner_id) ,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price']>0 and x['price'],
            'credit': x['price']<0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', False),
            'amount_currency': x['price']>0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity',1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
            'base_amount': x.get('base_amount'),
        }

class hr_expense_line(osv.osv):

    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'total_amount': 0.0,
                'untaxed_amount': 0.0,
            }
            tax_l = []
            taxes = [line.tax_id] or []
            base_tax_amount = line.unit_amount * line.unit_quantity
            total_amount = base_tax_amount
            #Calculating tax on the line and creating move?
            for tax in tax_obj.compute_all(cr, uid, taxes,
                    line.unit_amount ,
                    line.unit_quantity, line.product_id,
                    line.expense_id.user_id.partner_id)['taxes']:
                is_price_include = tax_obj.read(cr,uid,tax['id'],['price_include'],context)['price_include']
                if is_price_include:
                    ## We need to deduce the price for the tax
                    #res[-1]['price'] = res[-1]['price'] - tax['amount']
                    # tax amount countains base amount without the tax
                    base_tax_amount = (base_tax_amount - tax['amount']) * tax['base_sign']
                else:
                    base_tax_amount = base_tax_amount * tax['base_sign']
                total_amount = base_tax_amount + tax['amount'] #tax['amount'] * tax['base_sign']
            res[line.id]['total_amount'] = total_amount
            res[line.id]['untaxed_amount'] = base_tax_amount
        return res

    _inherit = 'hr.expense.line'
    _columns = {
        'tax_id': fields.many2one('account.tax','Tax',domain=[('type_tax_use','=','purchase')]),
        'account_id': fields.many2one('account.account','Account', required=True),
        'total_amount': fields.function(_amount, string='Total', digits_compute=dp.get_precision('Account'),multi="_amount"),
        'untaxed_amount': fields.function(_amount, string='Untaxed Amount', digits_compute=dp.get_precision('Account'),multi="_amount"),
        'partner_id': fields.many2one('res.partner','Supplier', domain=[('customer','=',False)]),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        res = {}
        account_tax = self.pool.get('account.tax')
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            res['name'] = product.name
            amount_unit = product.price_get('standard_price')[product.id]
            res['unit_amount'] = amount_unit
            res['uom_id'] = product.uom_id.id
            res['account_id'] = product.property_account_expense.id
            taxes = account_tax.browse(cr, uid, map(lambda x: x.id, product.supplier_taxes_id))
            if taxes:
                res['tax_id'] = taxes[0].id
        return {'value': res}