# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Andre@ (<a.gallina@cgsoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


from osv import fields, osv
from tools.translate import _
import openerp.addons.decimal_precision as dp


class wizard_modifyorder(osv.osv_memory):

    _name = "wizard.modifyorder"

    _columns = {
        'order_id': fields.many2one('sale.order', 'Sale Order'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'partner_invoice_id': fields.many2one(
            'res.partner', 'Invoice Address'),
        'partner_shipping_id': fields.many2one(
            'res.partner', 'Delivery Address'),
        'order_line': fields.one2many(
            'wizard.order.line', 'order_id', 'Order Lines'),
        }

    def view_init(self, cr, uid, fields_list, context=None):
        res = super(wizard_modifyorder, self).view_init(
            cr, uid, fields_list, context)
        select_order = context['active_ids']
        if len(select_order) > 1:
            raise osv.except_osv(
                _('Errore'),
                _('Select only one Order to modify!'))
        return res

    def default_get(self, cr, uid, fields, context=None):
        if context:
            order_id = context.get('active_id')
            order = self.pool.get('sale.order').browse(
                cr, uid, order_id, context)
            line_value = []
            for line in order.order_line:
                line_value.append({
                    'product_id': line.product_id.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'line_id': line.id,
                    })
            return {
                'order_id': order.id,
                'partner_id': order.partner_id.id,
                'partner_invoice_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'order_line': line_value,

                }

    def write_order(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context)[0]
        sale_order_obj = self.pool.get('sale.order')
        line_order_obj = self.pool.get('sale.order.line')
        if wizard.order_line:
            for line in wizard.order_line:
                line_order_obj.write(
                    cr, uid, line.line_id.id,
                    {'price_unit': line.price_unit,
                     'discount': line.discount,
                     },
                    context)
        if wizard.order_id.picking_ids:
            order = wizard.order_id
            picking_obj = self.pool.get('stock.picking.out')
            for picking in order.picking_ids:
                if picking.partner_id.id != wizard.partner_shipping_id.id:
                    picking_obj.write(
                        cr, uid, picking.id,
                        {'partner_id': wizard.partner_shipping_id.id},
                        context)
        sale_order_obj.write(
            cr, uid, wizard.order_id.id,
            {'partner_invoice_id': wizard.partner_invoice_id.id,
             'partner_shipping_id': wizard.partner_shipping_id.id, },
            context)

        return {'type': 'ir.actions.act_window_close'}

    def onchange_order_id(self, cr, uid, ids, order_id, context=None):
        if not order_id:
            return {}
        order = self.pool.get('sale.order').browse(
            cr, uid, order_id, context)
        line_value = []
        for line in order.order_line:
            line_value.append({
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'line_id': line.id,
                })
        res_value = {
            'order_id': order.id,
            'partner_id': order.partner_id.id,
            'partner_invoice_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'order_line': line_value,
            }
        return {'value': res_value}


class wizard_order_line(osv.osv_memory):

    _name = "wizard.order.line"

    _columns = {
        'order_id': fields.many2one(
            'wizard.modifyorder', 'Order Reference'),
        'line_id': fields.many2one(
            'sale.order.line', 'Line id'),
        'product_id': fields.many2one(
            'product.product', 'Product', readonly=True),
        'price_unit': fields.float(
            'Unit Price', digits_compute=dp.get_precision('Product Price')),
        'discount': fields.float(
            'Discount (%)', digits_compute=dp.get_precision('Discount')),
    }
