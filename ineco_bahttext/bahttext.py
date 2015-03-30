# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-Now Ineco Part., Ltd. (<http://www.ineco.co.th>).
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

import os
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools import float_round, float_is_zero, float_compare
from openerp.tools.translate import _

class ineco_bahttext(osv.osv):
    _name = 'ineco.bahttext'
    _description = "Bahttext Function"
    _auto = False
    _columns = {
    }
    
    def init(self, cr):
        SITE_ROOT = os.path.abspath(os.path.dirname(__file__))
        SQL_FILE = "%s/bahttext.sql" % (SITE_ROOT)
        file = open(SQL_FILE,'r')   
        cr.execute(file.read())
    
    