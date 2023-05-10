# from math import prod
import json
from odoo import api, fields, models, _
from multiprocessing.dummy.connection import Client
from typing import OrderedDict
from urllib import response
from xml.etree.ElementPath import prepare_descendant
from odoo.http import request, Response
from odoo import http
from math import ceil
from datetime import datetime, timedelta
import math
from ..controllers.product_controller import calculate_kpy
# from ..controllers.product_controller import _get_product_image_url
from ..controllers.product_controller import set_paginations
from ..controllers.product_controller import _calculate_gold_weight
from ..controllers.product_controller import cleanhtml
from ..controllers.product_controller import get_images_url
from ..controllers.product_controller import product_template_image
from ..controllers.product_controller import seller_shop_image
from ..controllers.product_controller import webclient_subscription_image
from odoo_rest_framework import login_required, response_json,public_route,jwt_http
from odoo.exceptions import UserError, AccessDenied, ValidationError, AccessError, MissingError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import ensure_db, Home, SIGN_UP_REQUEST_PARAMS
from odoo.addons.auth_signup.models.res_users import SignupError
from werkzeug.wrappers import Request, Response

class SellerController(http.Controller):

    @login_required('/seller-reivew/create', auth="public", method=['POST'], type='http', csrf=False)
    def create_seller_reivew(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        # user_id = str(kwargs['user_id']) if kwargs.get('user_id') else None
        # user = request.env['res.users'].sudo().search([('id', '=', user_id)]) #
        user = request.env.user
        shop_id = str(kwargs['shop_id']) if kwargs.get('shop_id') else None
        msg = str(kwargs['msg']) if kwargs.get('msg') else None
        rating = str(kwargs['rating']) if kwargs.get('rating') else None

        message = None
        success = False
        seller_id = seller_review = None

        if user.partner_id:
            if shop_id:
                shop = request.env['seller.shop'].sudo().search([('id', '=', shop_id)])
                seller_id = shop.seller_id.id
                reviewed_customer = request.env['seller.review'].sudo().search([('partner_id', '=', user.partner_id.id),('marketplace_seller_id', '=', seller_id)])
                if not reviewed_customer:
                    if rating and msg and user and seller_id:
                        try:
                            seller_review = request.env['seller.review'].sudo().create({
                                'title': 'review of ' + user.partner_id.name,
                                'marketplace_seller_id': seller_id,
                                'partner_id': user.partner_id.id,
                                'email': user.partner_id.email,
                                'rating': int(rating),
                                'msg': msg,
                            })
                            if seller_review:
                                message = 'Seller Review Create Successful'
                                success = True
                        except Exception as e:
                            message = str(e)
                else:
                    message = "User Already given review for this shop!!!"

        result = {
                  'success': success,
                  'message': message,
                  'data': seller_review.title if seller_review else None
                    }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)#response_json(success=success, data=None,message=message)

    @public_route('/seller/register', auth="public", method=['POST'], type='http', csrf=False)
    def seller_register(self, *args, **kwargs):
        message = success = None
        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)

        [mm] = request.env['res.country'].search_read([('code', 'like', 'MM')])
        data['country_id'] = mm['id']

        user = None
        user_data = {
            'login': data['login'],
            'name': data['name'],
            'password': data['password'],
            # 'confirm_password': data['confirm_password'],
            'country_id': data['country_id'],
        }

        registered_user = None
        try:
            signed_user = request.env['res.users'].sudo().signup(user_data, None)
            if signed_user:
                registered_seller = request.env['res.users'].sudo().search([('login', '=', data['login'])])

                partner_data = {
                    'seller': True,
                    'email': data['email'],
                    'url_handler': data['name'],
                    'user_ids': registered_seller.ids,
                    'user_id': registered_seller.id,
                }

                if registered_seller:
                    registered_seller.write({
                        'sel_groups_1_9_10': 1,
                        'sel_groups_65_66_67_69': 66
                    })
                    registered_seller.partner_id.sudo().write(partner_data)
                    registered_seller.partner_id.set_to_pending()
                    # registered_seller.partner_id.approve()
                    message = 'Seller Registration Successful'
                    success = True

        except (SignupError, ValidationError) as e:
            message = str(e)
            success = False

        result = {
            'message': message,
            'success': success
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)


def get_auth_signup_qcontext(self):
    """ Shared helper returning the rendering context for signup and reset password """
    qcontext = {k: v for (k, v) in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
    qcontext.update(self.get_auth_signup_config())
    if not qcontext.get('token') and request.session.get('auth_signup_token'):
        qcontext['token'] = request.session.get('auth_signup_token')
    if qcontext.get('token'):
        try:
            # retrieve the user info (name, login or email) corresponding to a signup token
            token_infos = request.env['res.partner'].sudo().signup_retrieve_info(qcontext.get('token'))
            for k, v in token_infos.items():
                qcontext.setdefault(k, v)
        except:
            qcontext['error'] = _("Invalid signup token")
            qcontext['invalid_token'] = True
    return qcontext