import json
from multiprocessing.dummy.connection import Client
from typing import OrderedDict
from urllib import response
from xml.etree.ElementPath import prepare_descendant
from odoo.http import request, Response
from odoo import http
from math import ceil
import pytz
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import math
import re
import logging
from datetime import timedelta, date, datetime
from odoo_rest_framework import login_required, response_json,jwt_http
from xmlrpc import client
from werkzeug.wrappers import Request, Response
#from tkinter.tix import Form

from ..controllers.product_controller import calculate_kpy

_logger = logging.getLogger(__name__)

remove_host_url = request.httprequest.host_url
CLEANR = re.compile('<.*?>')
default_image_shop = 'default-img-shop.png'

class SaleController(http.Controller):

    @login_required('/sale-order/create', type='http', auth="public", methods=['POST'], csrf=False)
    def sale_order_create(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        user_id = kwargs['user_id'] if kwargs.get('user_id') else None
        partner_shipping_id = kwargs['partner_shipping_id'] if kwargs.get('partner_shipping_id') else None
        shop_branch_id = kwargs['shop_branch_id'] if kwargs.get('shop_branch_id') else None
        product_template_ids = kwargs['products'] if kwargs.get('products') else None

        so_list = []
        current_sale_order = None
        gram = price = 0
        sale_order_line = []
        message = 'No Sale Order'
        success = False
        data = None
        partner_id = request.env['res.users'].sudo().search([('id', '=', user_id)]).partner_id

        if not partner_shipping_id:
            partner_shipping_id = request.env['res.partner'].sudo().search(
                [('parent_id', '=', partner_id.id), ('type', '=', 'contact')], limit=1).id
        # print('partner_id,user_id=>',partner_id,user_id)

        if product_template_ids:
            for prod_tmpl in product_template_ids:
                product_template = request.env['product.template'].sudo().search([('id','=',prod_tmpl['tmpId']),('active','=',True)])
                product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', product_template.id),('active', '=', True)])

                group = request.env['product.group'].sudo().search(
                    [('id', '=', prod_tmpl['groupId']), ('active', '=', True)])

                product_set = request.env['product.set'].sudo().search(
                    [('id', '=', prod_tmpl['setId']), ('active', '=', True)])

                sale_price = discounted_price = discount_value = total_qty_kyat = total_qty_gram = sale_price_unit = 0
                discount_type = deal_offer_name = None

                if product_template and prod_tmpl['qty']:
                    sale_price, discounted_price, discount_type, discount_value, deal_offer_name,\
                    total_qty_kyat, total_qty_gram, sale_price_unit, total_qty_petha, total_qty_yway = calculate_kpy(product_template, prod_tmpl['qty'], group, product_set)

                    sale_order_line.append((0, 0,
                                        {
                                            'product_id': product.id,
                                            'kyat': product_template.kyat,
                                            'petha': product_template.petha,
                                            'yway': product_template.yway,
                                            'petha_dec': product_template.petha_dec,
                                            'yway_dec': product_template.yway_dec,
                                            'total_qty_kyat': total_qty_kyat,
                                            'product_uom_qty': total_qty_gram,
                                            'total_qty_gram': total_qty_gram,
                                            'price_unit': sale_price_unit,
                                            'discount_fix': discount_value if discount_type == 'fixed' else 0,
                                            'discount': discount_value if discount_type == 'percentage' else 0,
                                            'tax_id': False,
                                            'use_price': product_template.use_price
                                        }))
                    if product.sh_bundle_product_ids:
                        for bundle_line in product.sh_bundle_product_ids:
                            total_qty_kyat, total_qty_gram = calculate_product_uom_qty(bundle_line.kyats, bundle_line.petha, bundle_line.yway, 0, 0)
                            sale_order_line.append((0, 0,
                                                    {
                                                        'product_id': bundle_line.sh_product_id.id,
                                                        'kyat': bundle_line.kyats,
                                                        'petha': bundle_line.petha,
                                                        'yway': bundle_line.yway,
                                                        'petha_dec': 0,
                                                        'yway_dec': 0,
                                                        'total_qty_kyat': total_qty_kyat,
                                                        'product_uom_qty': total_qty_gram,
                                                        'total_qty_gram': total_qty_gram,
                                                        'price_unit': sale_price_unit,
                                                        # 'discount_fix': discount_value if discount_type == 'fixed' else 0,
                                                        # 'discount': discount_value if discount_type == 'percentage' else 0,
                                                        'tax_id': False,
                                                        'use_price': bundle_line.sh_product_id.product_tmpl_id.use_price
                                                    }))


                    gram = total_qty_gram
                    price = sale_price_unit

            try:
                val = {
                    'partner_id': partner_id.id,
                    # 'partner_shipping_id': partner_shipping_id,
                    'currency_id': request.env.company.currency_id.id,
                    'date_order': datetime.today(),
                    'order_line': sale_order_line,
                }
                so = request.env['sale.order'].sudo().create(val)
                if partner_shipping_id:
                    so.write({
                        'partner_shipping_id': partner_shipping_id,
                    })

                current_sale_order = so

                data = {
                    'id': current_sale_order.id if current_sale_order else None,
                    'order_no': current_sale_order.name if current_sale_order else None,
                    'product': len(current_sale_order.order_line) if current_sale_order else None,
                    'date': current_sale_order.date_order.strftime('%Y-%m-%d') if current_sale_order else None,
                    'discount': 0,
                    'subtotal': current_sale_order.amount_total if current_sale_order else None,
                    'delivery_fee': 0,
                    'mdr_rate': 0,
                    'cupon': None,
                    'total': current_sale_order.amount_total if current_sale_order else None
                }

                message = 'Sale Order Create Successful'
                success = True

                #confirm sale order
                # so.action_confirm()
                # so_list.append({'sale_order_id': so.id,
                #                 'sale_order_name': so.name})
            except Exception as e:
                # print('msg sale order=>',e)
                message = str(e)
                success = False



        result ={
                'success': success,
                'message': message,
                'data': data,
                }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)

    @login_required('/sale-order/update', type='http', auth="public", methods=['POST'], csrf=False)
    def sale_order_update(self, **kwargs):
        # response_context = {'status': True}
        sale_order_id = kwargs['sale_order_id'] if kwargs.get('sale_order_id') else None

        product_template_ids = kwargs['products'] if kwargs.get('products') else None

        # product_id = kwargs['product_id'] if kwargs.get('product_id') else None
        # add_qty = kwargs['add_qty'] if kwargs.get('add_qty') else None
        # remove_qty = kwargs['remove_qty'] if kwargs.get('remove_qty') else None

        message = None
        success = False

        current_sale_order = request.env['sale.order'].search([('id', '=', sale_order_id)])
        if sale_order_id is not None:
            request.session['sale_order_id'] = sale_order_id

        if product_template_ids:
            for prod_tmpl in product_template_ids:
                product_template = request.env['product.template'].sudo().search([('id', '=', prod_tmpl['tmpId']), ('active','=', True)])
                product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', prod_tmpl['tmpId']), ('active', '=', True)])

                group = request.env['product.group'].sudo().search(
                    [('id', '=', prod_tmpl['groupId']), ('active', '=', True)])

                product_set = request.env['product.set'].sudo().search(
                    [('id', '=', prod_tmpl['setId']), ('active', '=', True)])

                line = current_sale_order.order_line.search([('order_id', '=', sale_order_id), ('product_id', '=', product.id)], limit=1)
                if line:
                    if prod_tmpl.get('qty'):
                        total_added_qty = int(prod_tmpl['qty']) + int(line.product_uom_qty)
                        prod_virtual_available = int(line.product_id.virtual_available)
                        if prod_virtual_available < total_added_qty and not line.product_id.allow_out_of_stock_order:
                            message = 'The maximum quantity available for this item is ' + str(prod_virtual_available) + '.'
                            success = False

                        else:
                            if total_added_qty > 0:
                                sale_price, discounted_price, discount_type, discount_value, deal_offer_name, \
                                total_qty_kyat, total_qty_gram, sale_price_unit, total_qty_petha, total_qty_yway = calculate_kpy(product_template,
                                                                                                prod_tmpl['qty'], group,
                                                                                                product_set)

                                line.update({
                                    'kyat': product_template.kyat,
                                    'petha': product_template.petha,
                                    'yway': product_template.yway,
                                    'petha_dec': product_template.petha_dec,
                                    'yway_dec': product_template.yway_dec,
                                    'total_qty_kyat': total_qty_kyat,
                                    'product_uom_qty': total_qty_gram,
                                })
                                success = True
                                message = "Update Cart Successful!!!"

                            else:
                                line.unlink()
                                success = True
                                message = "Update Cart Successful!!!"

                    # line_prod = line.product_id
                    # prod_virtual_available = int(line_prod.virtual_available)
                    # if prod_virtual_available < total_added_qty and not line_prod.allow_out_of_stock_order:
                    #     message = 'The maximum quantity available for this item is ' + str(
                    #         prod_virtual_available) + '.'
                    #     success = False

        result = {
            'message': message,
            'success': success,
            'data': None,
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)

    @login_required(['/list/sale_order'], type='http', auth='public', method=['POST'], csrf=False, cors="*")
    def sale_order_list(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        user_id = kwargs['user_id'] if kwargs.get('user_id') else None
        user = request.env['res.users'].sudo().search([('id', '=', user_id)])

        sale_orders = request.env['sale.order'].sudo().search([('partner_id', '=', request.env.user.partner_id.id), ('state', '=', 'draft')], limit=limit, offset=offset,order=order)
        message = None
        success = False
        sale_order_list = []

        if sale_orders:
            for so in sale_orders:
                order_status = None
                if so.state == 'draft':
                    order_status = 'Onprogress'
                elif so.state == 'sale':
                    order_status = 'Success'
                elif so.state == 'cancel':
                    order_status = 'Cancelled'
                val = {
                    'id': so.id,
                    'name': so.name,
                    'amount': so.amount_total,
                    'payment_method': None,
                    'shop': None,
                    'date': so.date_order.strftime('%Y-%m-%d'),
                    'order_status': order_status,
                }
                sale_order_list.append(val)
                message = 'Sale Order List'
                success = True

        result = {
            'success': success,
            'message': message,
            'data': sale_order_list,
            }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)

    @login_required('/sale-order/confirm', type='http', auth="public", methods=['POST'], csrf=False)
    def create_invoices(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        acquirer_id = kwargs['acquirer_id'] if kwargs.get('acquirer_id') else None
        sale_order_id = kwargs['sale_order_id'] if kwargs.get('sale_order_id') else None
        user = request.env.user
        partner = request.env.user.partner_id

        message = None
        success = False
        data = None

        # check payment type and create payment transaction
        if acquirer_id:
            acquirer = request.env['payment.acquirer'].sudo().browse(acquirer_id)
            if sale_order_id:
                current_sale_order = request.env['sale.order'].search([('id', '=', sale_order_id)])

                #add bank charges as  product to sale order line
                bank_charges_product = request.env['product.product'].search([('name', '=', 'Bank Charges'),('active','=',True)])
                if bank_charges_product:
                    current_sale_order.write({
                        'order_line': [
                            (0, 0,
                             {
                                 'product_id': bank_charges_product.id,
                                 'kyat': 0,
                                 'petha': 0,
                                 'yway': 0,
                                 'petha_dec': 0,
                                 'yway_dec': 0,
                                 'total_qty_kyat': 0,
                                 'product_uom_qty': 1,
                                 'total_qty_gram': 0,
                                 'price_unit': acquirer.bank_charges if acquirer else 0,
                                 # 'discount_fix': discount_value if discount_type == 'fixed' else 0,
                                 # 'discount': discount_value if discount_type == 'percentage' else 0,
                                 'tax_id': False,
                                 # 'use_price': bundle_line.sh_product_id.product_tmpl_id.use_price
                             })
                        ]
                    })
                if current_sale_order:
                    current_sale_order.action_confirm()
                    invoice = current_sale_order._create_invoices()
                    invoice.action_post()
                    journal_id = request.env['account.journal'].search([
                            ('name', '=', acquirer.display_name),
                            ('type', 'in', ('bank', 'cash')),
                            ('company_id', '=', request.env.user.company_id.id)], limit=1)

                    if not journal_id:
                        journal_id = request.env['account.payment']._get_default_journal()
                    # payment = request.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                    #     'payment_date': invoice.date,
                    #     'journal_id': journal_id.id,
                    # })
                    payment = request.env['account.payment'].create({
                        'payment_type': 'inbound',
                        'amount': invoice.amount_total,
                        'partner_id': invoice.partner_id.id,
                        'date': invoice.invoice_date.strftime('%Y-%m-%d'),
                        'ref': invoice.name,
                        'journal_id': journal_id.id,
                        'reconciled_invoice_ids': invoice.id,
                    })

                    if acquirer.provider == 'kbzpay':
                        res = acquirer.kbz_payment_request(payment)
                        success = True
                        data = res
                    if acquirer.provider == 'mpu':
                        res = acquirer.mpu_payment_request(payment)
                        success = True
                        data = res

                # result = {
                #     'message': 'Successful',
                #     'success': True,
                #     'data': res['payment_response']
                # }
                #
                # headers = {'Content-Type': 'application/json'}
                # return Response(json.dumps(result), headers=headers)
                # return {res['payment_response']}

                # invoice = current_sale_order._create_invoices()
                # invoice.action_post()
                # action_data = invoice.action_register_payment()
                # print('action_data',action_data)
                # journal_id = request.env['account.journal'].search([
                #         ('name', '=', 'KBZ Pay'),
                #         ('type', 'in', ('bank', 'cash')),
                #         ('company_id', '=', request.env.user.company_id.id)], limit=1)
                # # make payment
                # payment = request.env['account.payment.register'].with_context(active_model='account.move', active_ids=invoice.ids).create({
                #     'payment_date': invoice.date,
                #     'journal_id':journal_id.id,
                # })._create_payments()
                #
                # print('wizard=>', payment)

        result = {
            'success': success,
            'message': message,
            'data': data,
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)


def calculate_product_uom_qty(kyat, petha, yway, petha_dec, yway_dec):
    total_qty_kyat = 0
    price_unit = 0
    total_petha = petha + petha_dec
    total_yway = yway + yway_dec
    if kyat:
        total_qty_kyat += kyat
    if petha:
        total_qty_kyat += total_petha / 16
    if yway:
        total_qty_kyat += total_yway / 128

    total_qty_gram = total_qty_kyat * 16.606
    return total_qty_kyat , total_qty_gram






