# -*- coding: utf-8 -*-

##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 - INECO PARTNERSHIP LIMITED (<http://www.ineco.co.th>).
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

    _inherit="account.journal"

    def get_account_journal(self,cr,uid,model,type=False,subtype=False,context=None):

        if not context:
            context={}
        res =False

        company_obj=self.pool.get('res.company')
        company_id = context.get('company_id',False)
        if not company_id:
            company_id= company_obj.get_company(cr,uid,context).id

        company=company_obj.browse(cr,uid,company_id)

        if model=='account.invoice':
            if type=="in_invoice":
                res=company.in_invoice_journal_id and company.in_invoice_journal_id.id or False
            if type=="in_cash":
                res=company.in_cash_journal_id and company.in_cash_journal_id.id or False
            if type=="in_refund":
                res=company.in_refund_journal_id and company.in_refund_journal_id.id or False
            if type=="in_charge":
                res=company.in_charge_journal_id and company.in_charge_journal_id.id or False
            if type=="in_deposit":
                res=company.in_deposit_journal_id and company.in_deposit_journal_id.id or False

            if type=="out_invoice":
                res=company.out_invoice_journal_id and company.out_invoice_journal_id.id or False
            if type=="out_cash":
                res=company.out_cash_journal_id and company.out_cash_journal_id.id or False
            if type=="out_refund":
                res=company.out_refund_journal_id and company.out_refund_journal_id.id or False
            if type=="out_charge":
                res=company.out_charge_journal_id and company.out_charge_journal_id.id or False
            if type=="out_deposit":
                res=company.out_deposit_journal_id and company.out_deposit_journal_id.id or False

        if model=='account.payment':
            if type=="in":
                res=company.in_payment_journal_id and company.in_payment_journal_id.id or False
            if type=="out":
                res=company.out_payment_journal_id and company.out_payment_journal_id.id or False

        if model=='account.advance' or model=='account.advance.clear':
            res=company.advance_journal_id and company.advance_journal_id.id or False

        if model=='account.petty.payment':
            res=company.out_petty_journal_id and company.out_petty_journal_id.id or False

        if model=='account.cash.move': # and type="in":
            res=company.in_petty_journal_id and company.in_petty_journal_id.id or False

        if model=='account.bank.move' or model=='account.bank.transfer':
            res=company.bank_journal_id and company.bank_journal_id.id or False

        if model=='account.cheque.move' and type in ('RP','RR','RC','RS'):
            res=company.in_cheque_journal_id and company.in_cheque_journal_id.id or False

        if model=='account.cheque.move' and type in ('PP','PR','PC'):
            res=company.out_cheque_journal_id and company.out_cheque_journal_id.id or False

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4
