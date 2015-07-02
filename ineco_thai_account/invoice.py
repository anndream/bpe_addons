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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class account_invoice(models.Model):

    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        if not payment_term_id:
            # To make sure the invoice due date should contain due date which is
            # entered by user when there is no payment term defined
            return {'value': {'date_due': self.date_due or date_invoice}}
        pterm = self.env['account.payment.term'].browse(payment_term_id)
        pterm_list = pterm.compute(value=1, date_ref=date_invoice)[0]
        if pterm_list:
            return {'value': {'date_due': max(line[0] for line in pterm_list)}}
        #else:
        #    raise except_orm(_('Insufficient Data!'),
        #        _('The payment term of supplier does not have a payment term line.'))

    @api.one
    @api.depends(
    )
    def _get_move_lines(self):
        partial_lines = self.env['account.move.line']
        for line in self.move_id.line_id:
            partial_lines += line
        self.account_move_lines = partial_lines
    
    _inherit = "account.invoice"
    
    bill_due = fields.Date(string='Expected Billing Date', index=True)
    receipt_due = fields.Date(string='Expected Receive Date', index=True)
    date_due = fields.Date(string='Due Date', index=True, copy=False,
        help="If you use payment terms, the due date will be computed automatically at the generation "
             "of accounting entries. The payment term may compute several due dates, for example 50% "
             "now and 50% in one month, but if you want to force a due date, make sure that the payment "
             "term is not set on the invoice. If you keep the payment term and the due date empty, it "
             "means direct payment.")
    partner_delivery_id = fields.Many2one('res.partner', string='Delivery Address')
    period_tax_id = fields.Many2one('account.period', string='Tax Period', index=True)
    tax_option_id = fields.Many2one('account.tax', string='Tax Option')
    commission_sale = fields.Float('Sale Commission')
    commission_other = fields.Float('Other Commission')
    commission_note = fields.Char('Commission Note', size=256)
    commission_pay = fields.Boolean('Pay Commission')
    account_move_lines = fields.Many2many('account.move.line', string='General Ledgers',
        compute='_get_move_lines')
    _columns = {
        #'account_move_lines':fields.function(_get_move_lines, type='many2many', relation='account.move.line', string='General Ledgers'),                
        #'service': fields.boolean('Service'),
    }
    _defaults = {
        #'service': False,
        'commission_sale': 0.0,
        'commission_other': 0.0,
        'commission_pay': False,
    }

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.payment_ids:
                for move_line in inv.payment_ids:
                    if move_line.reconcile_partial_id.line_partial_ids:
                        raise except_orm(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        # POP-002
        self.write({'state': 'cancel', 'move_id': False, 'period_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        self._log_event(-1.0, 'Cancel Invoice')
        return True

    @api.multi
    def action_date_assign(self):
        for inv in self:
            if not inv.date_due:
                res = inv.onchange_payment_term_date_invoice(inv.payment_term.id, inv.date_invoice)
                if res and res.get('value'):
                    inv.write(res['value'])
            if not inv.bill_due:
                if inv.partner_id and inv.partner_id.billing_payment_id:
                    res = inv.onchange_payment_term_date_due(inv.partner_id.billing_payment_id.id, inv.date_invoice)
                    if res and res.get('value'):
                        inv.write(res['value'])         
        return True        

    @api.multi
    def onchange_payment_term_date_due(self, payment_term_id, date_invoice):
        if not date_invoice:
            date_invoice = fields.Date.context_today(self)
        if not payment_term_id:
            return {'value': {'bill_due': self.date_due or date_invoice}}
        pterm = self.env['account.payment.term'].browse(payment_term_id)
        pterm_list = pterm.compute(value=1, date_ref=date_invoice)[0]
        if pterm_list:
            return {'value': {'bill_due': max(line[0] for line in pterm_list)}}

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False

        if partner_id:
            p = self.env['res.partner'].browse(partner_id)
            rec_account = p.property_account_receivable
            pay_account = p.property_account_payable
            if company_id:
                if p.property_account_receivable.company_id and \
                        p.property_account_receivable.company_id.id != company_id and \
                        p.property_account_payable.company_id and \
                        p.property_account_payable.company_id.id != company_id:
                    prop = self.env['ir.property']
                    rec_dom = [('name', '=', 'property_account_receivable'), ('company_id', '=', company_id)]
                    pay_dom = [('name', '=', 'property_account_payable'), ('company_id', '=', company_id)]
                    res_dom = [('res_id', '=', 'res.partner,%s' % partner_id)]
                    rec_prop = prop.search(rec_dom + res_dom) or prop.search(rec_dom)
                    pay_prop = prop.search(pay_dom + res_dom) or prop.search(pay_dom)
                    rec_account = rec_prop.get_by_record(rec_prop)
                    pay_account = pay_prop.get_by_record(pay_prop)
                    if not rec_account and not pay_account:
                        action = self.env.ref('account.action_account_config')
                        msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                        raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('out_invoice', 'out_refund'):
                account_id = rec_account.id
                payment_term_id = p.property_payment_term.id
            else:
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term.id
            fiscal_position = p.property_account_position.id
            bank_id = p.bank_ids and p.bank_ids[0].id or False

        result = {'value': {
            'account_id': account_id,
            'payment_term': payment_term_id,
            'fiscal_position': fiscal_position,
        }}

        if type in ('in_invoice', 'in_refund'):
            result['value']['partner_bank_id'] = bank_id

        if payment_term != payment_term_id:
            if payment_term_id:
                to_update = self.onchange_payment_term_date_invoice(payment_term_id, date_invoice)
                result['value'].update(to_update.get('value', {}))
            #else:
            #    result['value']['date_due'] = False

        if partner_bank_id != bank_id:
            to_update = self.onchange_partner_bank(bank_id)
            result['value'].update(to_update.get('value', {}))

        return result

    #2015-06-13 Change way to grouping GL
    def inv_line_characteristic_hashcode(self, invoice_line):
        """Overridable hashcode generation for invoice lines. Lines having the same hashcode
        will be grouped together if the journal has the 'group line' option. Of course a module
        can add fields to invoice lines that would need to be tested too before merging lines
        or not."""
        return "%s-%s-%s-%s-%s" % (
            invoice_line['account_id'],
            invoice_line.get('tax_code_id', 'False'),
            invoice_line.get('product_id_move', 'False'), #disable this parameter
            invoice_line.get('analytic_account_id', 'False'),
            invoice_line.get('date_maturity', 'False'),
        )

    @api.multi
    def button_clear_tax(self):
        for invoice in self:
            for line in invoice.invoice_line:
                for tax in line.invoice_line_tax_id:
                    line.write({'invoice_line_tax_id': [(3, tax.id)]})
                #print line.invoice_line_tax_id
        return {}

    @api.multi
    def button_add_tax(self):
        for invoice in self:
            for line in invoice.invoice_line:
                if invoice.tax_option_id:
                    line.write({'invoice_line_tax_id': [(6, 0, [invoice.tax_option_id.id])]})
                #print line.invoice_line_tax_id
        return {}

    # 2015-06-13 Remove unused function
    # @api.multi
    # def invoice_validate(self):
    #     for data in self:
    #         if data.period_id and not data.period_tax_id:
    #             data.write({'period_tax_id': data.period_id.id})
    #     return self.write({'state': 'open'})

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Hook method to be overridden in additional modules to verify and
            possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines (as for create())
            :return: the (possibly updated) final move_lines to create for this invoice
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(move_lines)
        move_line_obj = self.pool.get('account.move.line')
        for line in move_lines:
            print line ;
            #line.update({'invoice_number': 'invoice_number'})
        return move_lines

    @api.model
    def line_get_convert(self, line, part, date):
        return {
            'date_maturity': line.get('date_maturity', False),
            'partner_id': part,
            'name': line['name'][:64],
            'date': date,
            'debit': line['price']>0 and line['price'],
            'credit': line['price']<0 and -line['price'],
            'account_id': line['account_id'],
            'analytic_lines': line.get('analytic_lines', []),
            'amount_currency': line['price']>0 and abs(line.get('amount_currency', False)) or -abs(line.get('amount_currency', False)),
            'currency_id': line.get('currency_id', False),
            'tax_code_id': line.get('tax_code_id', False),
            'tax_amount': line.get('tax_amount', False),
            'ref': line.get('ref', False),
            'quantity': line.get('quantity',1.00),
            'product_id': line.get('product_id', False),
            'product_uom_id': line.get('uos_id', False),
            'analytic_account_id': line.get('account_analytic_id', False),
            'invoice_id': self.id,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: