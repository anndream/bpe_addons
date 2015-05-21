# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


from openerp.osv import osv, fields, expression

class product_template(osv.osv):

    def _check_duplicate_code(self, cr, uid, ids, context=None):
        for id in ids:
            print "Checking"
            product = self.read(cr, uid, id, ['default_code'], context=context)
            product_code = product['default_code']
            product_ids = self.search(cr, uid, [('default_code','=',product_code)])
            target_ids = product_ids.remove(id)
            if target_ids:
                return True
        return False

    inherit = 'product.template'

    _constraints = [(_check_duplicate_code, 'You assgined code duplicate.', ['default_code'])]
