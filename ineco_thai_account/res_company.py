# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

class res_company(osv.osv):
    _inherit = "res.company"
    _description = 'address for vat thai'
    _columns = {
        'ineco_company_name': fields.char('Company Name (VAT)', size=128),                
        'ineco_branch': fields.char('Branch', size=32),
        'ineco_building':fields.char('Building', size=128),
        'ineco_room_no':fields.char('Room No', size=32),
        'ineco_class':fields.char('Floor', size=32),
        'ineco_village':fields.char('Village', size=128),
        'ineco_no':fields.char('No', size=32),
        'ineco_moo':fields.char('Moo', size=32),
        'ineco_alley':fields.char('Soi', size=128),
        'ineco_road':fields.char('Road', size=128),
        'ineco_district':fields.char('Tambon', size=128),
        'ineco_amphoe':fields.char('Amphur', size=128), 
        'ineco_province':fields.char('Province', size=128),       
        'ineco_zip':fields.char('Zip', size=32),    
        'ineco_phone':fields.char('Phone', size=32),
        'ineco_position':fields.char('Position', size=128),
        'ineco_name':fields.char('Signature Name', size=128),
        #Petty Cash
        'date_start': fields.date('Company Start', ),
        'department_code': fields.char('Department Code', size=4,help="Use for Thai VAT report"),

        'cq_postdate_in':fields.many2one('account.account','Post Date Cheque(Receive)'),
        'cq_postdate_out':fields.many2one('account.account','Post Date Cheque(Payment)'),

        'advance':fields.many2one('account.account','Advance Account'),
        'advance_delay':fields.integer('Advance Delay',help="Number of date that request to clear advance"),

        'cash':fields.many2one('account.account','Cash Account'),

        'inter_company_account_id':fields.many2one('account.account','Inter-Company Account'),

        'bank_charge': fields.many2one('account.account','Bank Charge Account',help="Bank Charge Account"),

        'in_invoice_journal_id':fields.many2one('account.journal','Credit Purchase',help='Journal for Credit Purchase'),
        'in_cash_journal_id':fields.many2one('account.journal','Cash Purchase',help='Journal for Cash Purchase'),
        'in_deposit_journal_id':fields.many2one('account.journal','Purchase Deposit',help='Journal Purchase Deposit'),
        'in_refund_journal_id':fields.many2one('account.journal','Credit Note',help='Journal for Purchase Credit Note'),
        'in_charge_journal_id':fields.many2one('account.journal','Debit Note',help='Journal for Purchase Debit Note'),

        'out_invoice_journal_id':fields.many2one('account.journal','Credit Sale',help='Journal for Credit Sale'),
        'out_cash_journal_id':fields.many2one('account.journal','Cash Sale',help='Journal for Cash Sale'),
        'out_deposit_journal_id':fields.many2one('account.journal','Sale Deposit',help='Journal for Sale Deposit'),
        'out_refund_journal_id':fields.many2one('account.journal','Sale Credit Note',help='Journal for Sale Credit Note'),
        'out_charge_journal_id':fields.many2one('account.journal','Sale Debit Note',help='Journal for Sale Debit Note'),

        'in_cheque_journal_id': fields.many2one('account.journal','Cheque Receipt',help="Journal for Cheque Receive"),
        'out_cheque_journal_id': fields.many2one('account.journal','Cheque Payment',help="Journal for Cheque Payment"),

        'advance_journal_id': fields.many2one('account.journal','Advance',help="Journal for Advance"),
        'bank_journal_id': fields.many2one('account.journal','Bank',help="Journal for Bank"),
        'in_petty_journal_id': fields.many2one('account.journal','Petty Cash Receipt',help="Journal for Petty cash Receipt"),
        'out_petty_journal_id': fields.many2one('account.journal','Petty Cash Payment',help="Journal for Petty cash Payment"),

        'in_payment_journal_id': fields.many2one('account.journal','Receipt',help="Journal for Receipt"),
        'out_payment_journal_id': fields.many2one('account.journal','Payment',help="Journal for Payment"),

        'wht_company_id': fields.many2one('account.account','WHT Company',help="Account for wht company"),
        'wht_personal_id': fields.many2one('account.account','WHT Personal',help="Account for wht personal"),
        
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
