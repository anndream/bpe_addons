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

from openerp import api
from openerp.osv import fields, osv

class res_users(osv.osv):
    
    def _get_department(self, cr, uid, ids, name, args, context=None):
        res = {}
        for user in self.browse(cr, uid, ids, context=context):
            res[user.id] = {
                'department_id': False,
            }
            if user.employee_ids and user.employee_ids[0].department_id :
                res[user.id] = {
                    'department_id':  user.employee_ids[0].department_id.id,
                }
        return res
    
    _inherit = 'res.users'
    _columns = {
        'department_id': fields.function(_get_department, type="many2one", 
                                string='Department', relation="hr.department", multi='_get_department'),                
    }