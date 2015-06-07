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
{
    'name' : 'BPE Modules',
    'version' : '0.1',
    'author' : 'INECO Part.,Ltd.',
    'category': 'BPE',
    'website' : 'http://www.ineco.co.th',
    'summary' : 'Customize modules for BPE',
    'description' : """
#26-01-2015
1. Add cost+on_change in purchase.requisition.line
2. Add user_approve_id,user_checked_id+on_change, type_of_requirement, additional requirement on purchase.requisition
3. Add additional requirement on purchase.order
4. Manual Add context (Calls for Bid)
    search_default_filter_my_checked":uid, "search_default_filter_my_approve":uid
""",
    'depends' : [
        'base','web','purchase','sale','purchase_requisition','analytic',
    ],
    'data' : [
        'sequence.xml',
        'purchase_requisition_view.xml',
        'purchase_view.xml',
        'account_view.xml',
        'product_view.xml',
        'hr_view.xml',
        'sale_view.xml',
        'security.xml',
        'base.xml',
        #'res_users_view.xml',
    ],
    'update_xml' : [
    ],
    'installable' : True,
    'application' : False,
}
