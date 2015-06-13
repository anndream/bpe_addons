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

# POP-001    2013-07-31    Disable when change partner to change due date too.
# POP-002    2013-08-24    Cancel invoice reset period_id = False
# POP-003    2013-08-27    Add Commission
# POP-004    2013-09-09    Change Manual Post when validate invoice
# POP-005    2014-01-07    Change Date Due in account.invoice

from openerp.osv import fields, osv
import time
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import itertools
from lxml import etree

class account_voucher_addline(osv.osv):
    _name = 'account.voucher.addline'
    _columns = {
        'name': fields.char('Description', size=64),
        'account_name': fields.related('account_id','name', type='char', size=128, relation='account.account', store=True, string='Account Name'),
        'account_id': fields.many2one('account.account','Account',required=True),
        'voucher_id': fields.many2one('account.voucher','Voucher'),
        'debit': fields.float('Debit', digits_compute=dp.get_precision('Account')),
        'credit': fields.float('Credit', digits_compute=dp.get_precision('Account')),
    }
    _defaults = {
        'name': '...',
    }
    
class account_voucher(osv.osv):
    
    def _get_move_lines(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            id = invoice.id
            res[id] = []
            if not invoice.move_id:
                continue
            data_lines = [x for x in invoice.move_id.line_id]
            partial_ids = []
            for line in data_lines:
                partial_ids.append(line.id)
            res[id] =[x for x in partial_ids]
        return res
    
    _inherit = "account.voucher"
    _columns = {
        'account_move_lines':fields.function(_get_move_lines, type='many2many', 
            relation='account.move.line', string='General Ledgers'),      
        'wht_ids': fields.one2many('ineco.wht', 'voucher_id', 'WHT'),
        #'cheque_id': fields.many2one('ineco.cheque','Cheque'),        
        'bill_number': fields.char('Billing No', size=64),
        'receipt_number': fields.char('Receipt No', size=64),
        'period_tax_id': fields.many2one('account.period', 'Tax Period'),
        'account_model_id': fields.many2one('account.model', 'Model'),
        'addline_ids': fields.one2many('account.voucher.addline','voucher_id','Add Line'),
        'cheque_ids': fields.many2many('ineco.cheque', 'voucher_cheque_ids', 'voucher_id', 'cheque_id', 'Cheque'),      
    }

    def button_billing_no(self, cr, uid, ids, context=None):
        next_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.billing.no') or '/'
        self.write(cr, uid, ids, {'bill_number':next_no})
        return True

    def button_receipt_no(self, cr, uid, ids, context=None):
        next_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.receipt.no') or '/'
        self.write(cr, uid, ids, {'reference':next_no})
        return True

    def button_loadtemplate(self, cr, uid, ids, context=None):
        for data in self.browse(cr, uid, ids):
            if data.account_model_id:
                for line in data.account_model_id.lines_id:
                    addline = self.pool.get('account.voucher.addline')
                    addline.create(cr, uid, {
                        'account_id': line.account_id.id,
                        'name': line.name,
                        'debit': line.debit,
                        'credit': line.credit,
                        'voucher_id': data.id,
                    })
        #self.write(cr, uid, ids, {'state':'approve'})
        return True
    
    def _get_wht_total(self, cr, uid, voucher_id, context=None):
        _amount_tax = 0.0
        voucher = self.browse(cr, uid, voucher_id)
        for wht in voucher.wht_ids:
            _amount_tax += wht.tax or 0.0
        return round(_amount_tax, 2)

    def _get_template_debit_total(self, cr, uid, voucher_id, context=None):
        _amount_tax = 0.0
        voucher = self.browse(cr, uid, voucher_id)
        for wht in voucher.addline_ids:
            _amount_tax += wht.debit or 0.0
        return round(_amount_tax, 2)

    def _get_template_credit_total(self, cr, uid, voucher_id, context=None):
        _amount_tax = 0.0
        voucher = self.browse(cr, uid, voucher_id)
        for wht in voucher.addline_ids:
            _amount_tax += wht.credit or 0.0
        return round(_amount_tax, 2)
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}           
        default.update({
            'wht_ids':False,
        })
        return super(account_voucher, self).copy(cr, uid, id, default, context)

    def template_move_line_create(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        move_line_pool = self.pool.get('account.move.line')
        for line in voucher_brw.addline_ids:
            debit = credit = 0.0
            debit = line.debit
            credit = line.credit 
            if debit < 0: credit = -debit; debit = 0.0
            if credit < 0: debit = -credit; credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #set the first line of the voucher
            move_line = {
                    'name': line.name or line.account_name or '/',
                    'debit': debit,
                    'credit': credit,
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'journal_id': voucher_brw.journal_id.id,
                    'period_id': voucher_brw.period_id.id,
                    'partner_id': voucher_brw.partner_id.id,
                    'currency_id': company_currency <> current_currency and  current_currency or False,
                    'amount_currency': company_currency <> current_currency and sign * voucher_brw.amount or 0.0,
                    'date': voucher_brw.date,
                    'date_maturity': voucher_brw.date_due
                }
            move_line_pool.create(cr, uid, move_line)
        return True

    def wht_move_line_create(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        move_line_pool = self.pool.get('account.move.line')
        for wht in voucher_brw.wht_ids:
            debit = credit = 0.0
            if voucher_brw.type in ('purchase', 'payment'):
                credit = wht.tax
            elif voucher_brw.type in ('sale', 'receipt'):
                debit = wht.tax
            if debit < 0: credit = -debit; debit = 0.0
            if credit < 0: debit = -credit; credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #set the first line of the voucher
            move_line = {
                    'name': 'WHT NO: ' + wht.name or '/',
                    'debit': debit,
                    'credit': credit,
                    'account_id': wht.account_id.id,
                    'move_id': move_id,
                    'journal_id': voucher_brw.journal_id.id,
                    'period_id': voucher_brw.period_id.id,
                    'partner_id': voucher_brw.partner_id.id,
                    'currency_id': company_currency <> current_currency and  current_currency or False,
                    'amount_currency': company_currency <> current_currency and sign * voucher_brw.amount or 0.0,
                    'date': voucher_brw.date,
                    'date_maturity': voucher_brw.date_due
                }
            move_line_pool.create(cr, uid, move_line)
        return True
    
    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        voucher_brw = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        account_id = voucher_brw.account_id.id
        debit = credit = 0.0
        if voucher_brw.type in ('purchase', 'payment'):
            credit = voucher_brw.paid_amount_in_company_currency
            credit -= self._get_wht_total(cr, uid, voucher_id, context) or 0.0
            account_id = voucher_brw.journal_id.default_credit_account_id.id
        elif voucher_brw.type in ('sale', 'receipt'):
            debit = voucher_brw.paid_amount_in_company_currency
            debit -= self._get_wht_total(cr, uid, voucher_id, context) or 0.0
            account_id = voucher_brw.journal_id.default_debit_account_id.id
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        move_line = {
                'name': voucher_brw.name or voucher_brw.account_id.name or '/',
                'debit': debit,
                'credit': credit,
                #'account_id': voucher_brw.account_id.id,
                'account_id': account_id,
                'move_id': move_id,
                'journal_id': voucher_brw.journal_id.id,
                'period_id': voucher_brw.period_id.id,
                'partner_id': voucher_brw.partner_id.id,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * abs(voucher_brw.amount) or 0.0,
                'date': voucher_brw.date,
                'date_maturity': voucher_brw.date_due or False,
            }
        return move_line
        
    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            ######
            # Create the account move record.
            try:
                move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
                # Get the name of the account_move just created
                name = move_pool.browse(cr, uid, move_id, context=context).name
                # Create the first line of the voucher
                move_line_id = move_line_pool.create(cr, uid, 
                    self.first_move_line_get(cr,uid,voucher.id, move_id, 
                        company_currency, current_currency, context), context)
                move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
                
                #WHT Tax Amount
                wht_total = self._get_wht_total(cr, uid, voucher.id, context)
                if voucher.type in {'sale','receipt'}:
                    line_total = move_line_brw.debit - move_line_brw.credit + wht_total
                elif voucher.type in {'purchase','payment'}:
                    line_total = move_line_brw.debit - move_line_brw.credit - wht_total
                else:
                    line_total = move_line_brw.debit - move_line_brw.credit
                if wht_total:
                    self.wht_move_line_create(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                    
                #Create Template Move Line    
                if voucher.addline_ids and voucher.payment_option == 'without_writeoff':
                    self.template_move_line_create(cr, uid, voucher.id, move_id, company_currency, current_currency, context)
                template_debit = self._get_template_debit_total(cr, uid, voucher.id, context)
                template_credit = self._get_template_credit_total(cr, uid, voucher.id, context)
                
                if voucher.payment_option == 'without_writeoff':
                    line_total = (move_line_brw.debit + template_debit) - (move_line_brw.credit + template_credit)
                    
                rec_list_ids = []
                if voucher.type == 'sale':
                    line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                elif voucher.type == 'purchase':
                    line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
                
                # Create one move line per voucher line where amount is not 0.0
                line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
    
                if wht_total:
                    if voucher.type in {'purchase','payment'}:
                        line_total = round(line_total,4) - round(wht_total,4)
                    elif voucher.type in {'sale','receipt'}: 
                        line_total = round(line_total,4) + round(wht_total,4)
                
                if voucher.payment_option == 'without_writeoff' and round(line_total,4):
                    raise osv.except_osv('Unreconciled', 'Please input data in template tab to balance debit and credit.')
                
                # Create the writeoff line if needed
                ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, context)
                if ml_writeoff:
                    move_line_pool.create(cr, uid, ml_writeoff, context)
                # We post the voucher.
                self.write(cr, uid, [voucher.id], {
                    'move_id': move_id,
                    'state': 'posted',
                    'number': name,
                })
                if voucher.journal_id.entry_posted:
                    move_pool.post(cr, uid, [move_id], context={})
                # We automatically reconcile the account move lines.
                reconcile = False
                for rec_ids in rec_list_ids:
                    if len(rec_ids) >= 2:
                        reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
            except:
                cr.rollback()
                raise osv.except_osv('Error', 'Validation error please contact administrator.')
        return True
