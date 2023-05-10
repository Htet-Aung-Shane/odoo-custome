import json
from multiprocessing.dummy.connection import Client
from random import random
from typing import OrderedDict
from urllib import response
from xml.etree.ElementPath import prepare_descendant
from odoo.http import request, Response
from odoo import http
from math import ceil
from datetime import datetime, timedelta
from odoo_rest_framework import login_required, response_json,public_route,jwt_http
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError, MissingError, QWebException
from odoo.exceptions import UserError, AccessDenied, ValidationError, AccessError, MissingError
from ast import literal_eval
import random
import logging
_logger = logging.getLogger(__name__)
from werkzeug.wrappers import Request, Response
import os
from twilio.rest import Client

class UserController(http.Controller):
    @public_route('/user/login', auth="public", method=['POST'],type='http',csrf=False)
    def authenticate(self, **kwargs):
        db = request.session.db
        message = ""
        success = False

        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)
        authenticate_data = None

        if not data.get('login') or not data.get('password'):  # or not data.get('noti_token'):
            return jwt_http.errcode(code=400,
                                    message='LOGIN: missing 2 required positional arguments: "email" or "password"')

        # _logger.info("login,psw,noti token", data.get('login'),data.get('password'), data.get('noti_token'))
        try:
            authenticate = jwt_http.do_login(data.get('login'), data.get('password'), data.get('noti_token'))
            if authenticate.status_code == 200:
                success = True
                message = "Authenticated!"
                authenticate_data = json.loads(authenticate.data)
        except Exception as e:
            message = "Credential doesn't match!" ##str(e)
            success = False
            authenticate_data = None
        
        result = {
            # 'message': message,
            # 'success': success,
            'data': authenticate_data
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)

        # return json.dumps(json.loads(authenticate.data))

    @public_route('/user/register', auth="public", method=['POST'], type='http', csrf=False)
    def user_register(self, **kwargs):
        website = request.env['website'].get_default_website()

        # registered_user = request.env['res.users']
        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)
        # check if phone(login) already exist in res.users
        # print('data',data)

        [mm] = request.env['res.country'].search_read([('code', 'like', 'MM')])
        data['lang'] = 'en_US'
        data['country_id'] = mm['id']
        data['signup_type'] = 'register'

        user = request.env['res.users'].sudo().search([('login', '=', data['login'])])
        message = success = None
        registered_user = None
        otp_code = None
        if not user:
            user_data = {
                'name': data['name'] if data.get('name') else None,
                'login': data['login'] if data.get('login') else None,
                'password': data['password'] if data.get('password') else None,
                # 'sel_groups_1_9_10':9
            }
            try:
                registered_user = request.env['res.users'].sudo().signup(user_data, None)
                if registered_user:
                    #create partner for registered user
                    partner_data = {
                        'name': data['name'] if data.get('name') else None,
                        'email': data['login_email'] if data.get('login_email') else None,
                        'phone': data['phone'] if data.get('phone') else None,
                        'company_id': website.company_id.id if website else None,
                        'type': 'contact',
                        'township_id': data['township_id'] if data.get('township_id') else None,
                        'state_id': data['state_id'] if data.get('state_id') else None,
                        'city_id': data['city_id'] if data.get('city_id') else None,
                        'zip': data['zip'] if data.get('zip') else None,
                        'country_id': data['country_id'] if data.get('country_id') else None,
                        'street': data['street'] if data.get('street') else None,
                    }

                    user = request.env['res.users'].sudo().search([('login', '=', data['login'])])

                    if user:
                        user.partner_id.sudo().write(partner_data)

                        # create delivery address
                        delivery_address_partner = request.env['res.partner'].sudo().create({
                            'parent_id': user.partner_id.id,
                            'name': data['name'] if data.get('name') else None,
                            'email': data['login'] if data.get('login') else None,
                            'phone': data['phone'] if data.get('phone') else None,
                            'country_id': data['country_id'] if data.get('country_id') else None,
                            'company_id': website.company_id.id,
                            'state_id': data['state_id'] if data.get('state_id') else None,
                            'city_id': data['city_id'] if data.get('city_id') else None,
                            'township_id': data['township_id'] if data.get('township_id') else None,
                            'type': 'delivery',  # delivery
                            'street': data['street'] if data.get('street') else None,
                        })

                        # create user otp to verify otp code set by user
                        otp_code = random.randint(100000, 999999)
                        # Authenticate with Trillo OTP
                        # Download the helper library from https://www.twilio.com/docs/python/install
                        import os
                        from twilio.rest import Client
                        # Set environment variables for your credentials
                        # Read more at http://twil.io/secure
                        account_sid = "AC2041126f09718c920991224696c598e1"
                        auth_token = "ed79c4ac24c347d85bc8ed60a32f3e04"
                        client = Client(account_sid, auth_token)

                        # user_id = json.loads(authenticate.data)['data']['user']['id']
                        twillo_message = client.messages.create(
                            body=otp_code,
                            from_="+15855410794",
                            to="+959422997233"
                        )
                        user_otp = request.env['res.users.otp'].create({
                            'user_id': user.id,
                            'code': otp_code,
                            'expire_date': datetime.now().strftime('%Y-%m-%d')
                        })

                        message = 'User Create Successful!!!'
                        success = True

            except SignupError as e:
                message = str(e)
        else:
            # return response_json(success=False, data=None, message="User Already Exist")
            message = 'User Already Exist'
            success = False

        result = {
            'message': message,
            'success': success,
            'data':
                {
                 'user_id': user.id,
                 # 'otp_code': otp_code
                 }
                }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return jwt_http.response(data=result)#json.dumps(result)

    @login_required('/user/detail', auth="public", method=['POST'], type='http', csrf=False)
    def user_detail(self, **kwargs):
        # print(kwargs,"*"*10)
        user_id = kwargs['user_id'] if kwargs['user_id'] else None
        user = request.env['res.users'].sudo().search([('id', '=', user_id)])

        address = get_addresss(user.partner_id)
        delivery_address = []
        child_partner_id = None
        for child_partner in user.partner_id.child_ids:
            if child_partner.type == 'delivery':
                del_addr = get_addresss(child_partner)
                val = {
                    'child_partner_id': child_partner.id,
                    'delivery_address': del_addr
                }
                delivery_address.append(val)
                # child_partner_id = child_partner.id

        # shops followed by user
        shop_ids = request.env['shop.follower'].sudo().search(
            [('user_id', '=', user.id), ('follow', '=', True)]).shop_id.ids

        sale_order = request.env['sale.order'].sudo().search(
            [('partner_id', '=', user.partner_id.id), ('state', '=', 'draft')], limit=1, order='id desc')
        sale_order_lines = []
        if sale_order.order_line:
            for line in sale_order.order_line:
                group_line = request.env['product.group.line'].sudo().search([('product_template_id', '=', line.product_id.product_tmpl_id.id)])
                product_set = None
                if group_line.group_id.id:
                    product_set = request.env['product.set.line'].sudo().search([('product_group_id', '=', group_line.group_id.id)])
                if group_line.group_id:
                    val = {
                        "groupId": group_line.group_id.id if group_line else None,
                        "qty": 1,
                        "setId": product_set.id if product_set else None,
                        "shopId": group_line.group_id.shop_id.id if group_line else None,
                        "tmpId": line.product_id.product_tmpl_id.id,
                    }
                    sale_order_lines.append(val)

        data = {
            'user_id': user.id,
            'user_name': user.name,
            'email': user.partner_id.email,
            'address': address,
            'address_arr': {
                'street': user.partner_id.street,
                'zip': user.partner_id.zip,
                'township_id': {
                    'id': user.partner_id.township_id.id,
                    'code': user.partner_id.township_id.code,
                    'name': user.partner_id.township_id.name,
                    'city_id': [user.partner_id.city_id.id, user.partner_id.city_id.name]
                },
                'state_id': {
                    'id': user.partner_id.state_id.id,
                    'code': user.partner_id.state_id.code,
                    'name': user.partner_id.state_id.name,
                    'country_id':[user.partner_id.country_id.id,user.partner_id.country_id.name],
                        },
                'city_id': {
                    'id': user.partner_id.city_id.id,
                    'code': user.partner_id.city_id.code,
                    'name': user.partner_id.city_id.name,
                    'state_id': [user.partner_id.state_id.id,user.partner_id.state_id.name]
                    },
                'country_id':
                    {
                        'id':user.partner_id.country_id.id,
                        'code': user.partner_id.country_id.code,
                        'name': user.partner_id.country_id.name,
                    },

            },
            'delivery_address': delivery_address,
            'partner_id': user.partner_id.id,
            # 'child_partner_id': child_partner_id,
            'phone': user.partner_id.phone,
            'followed_shop_ids': shop_ids,
            'sale_order': {
                    'id': sale_order.id if sale_order else None,
                    'order_no': sale_order.name if sale_order else None,
                    'product': len(sale_order.order_line) if sale_order else None,
                    'date': sale_order.date_order.strftime('%Y-%m-%d') if sale_order else None,
                    'discount': 0,
                    'subtotal': sale_order.amount_total if sale_order else None,
                    'delivery_fee': 0,
                    'mdr_rate': 0,
                    'cupon': None,
                    'total': sale_order.amount_total if sale_order else None,
                    'order_line': sale_order_lines
            }
        }

        result = {
            'message': 'User Detail Info',
            'success': True,
            'data': data
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#

        # return json.dumps(result)
        #jwt_http.response(data=result)#json.dumps(result)#response_json(success=True, data=result,message="Succeful")

    @login_required('/user/update', auth="public", method=['POST'], type='http', csrf=False)
    def user_update(self, **kwargs):
        # change name, phone, email
        # user_id = kwargs['user_id'] if kwargs['user_id'] else None
        # name = kwargs['name'] if kwargs.get('name') else None
        # phone = kwargs['phone'] if kwargs.get('phone') else None
        # email = kwargs['email'] if kwargs.get('email') else None
        # password = kwargs['password'] if kwargs.get('password') else None

        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        login_data = json.loads(my_json)

        # user_id = kwargs['user_id'] if kwargs['user_id'] else None
        user = request.env['res.users'].sudo().search([('id', '=', login_data['user_id'])])

        message = data = None
        success = False

        try:
            authenticate = jwt_http.do_login(user.login, login_data.get('password'), login_data.get('noti_token'))

            if authenticate.status_code == 200:
                updated_user = user.sudo().write({
                    'name': login_data['name'] if login_data['name'] else user.name,
                    # 'login': phone if phone else user.phone,
                    # 'email': email if email else user.email
                })

                updated_partner = user.partner_id.sudo().write({
                    'email': login_data['email'] if login_data['email'] else user.partner_id.email,
                    'phone': login_data['phone'] if login_data['phone'] else user.partner_id.phone,
                    'mobile': login_data['phone'] if login_data['phone'] else user.partner_id.mobile
                })
                message = 'Update User Info Successful!!!',
                success = True
                data = updated_partner
            else:
                message = "Wrong Password!!"

        except Exception as e:
            # print('e',str(e))
            message = "Wrong Password!!"

        result = {
            'message': message,
            'success': success,
            # 'data': data
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#

        # return json.dumps(result)
        # jwt_http.response(data=result)#json.dumps(result)#response_json(success=True, data=result,message="Succeful")

    # create address with type=delivery in partner of current login user
    @login_required('/user/address/add', auth="public", methods=["POST"], type='http', csrf=False)
    def add_addresses(self, **kwargs):
        [mm] = request.env['res.country'].search_read([('code', 'like', 'MM')])

        user_id = kwargs['user_id'] if kwargs['user_id'] else None
        message = success = None
        try:
            user = request.env['res.users'].sudo().search([('id', '=', user_id)])
            if user:
                partner = request.env['res.partner'].sudo().create({
                    'parent_id': user.partner_id.id,
                    'name': kwargs['name'] if kwargs.get('name') else '',
                    'street': kwargs['street'] if kwargs.get('street') else '',
                    'city_id': kwargs['city_id'] if kwargs.get('city_id') else '',
                    'township_id': kwargs['township_id'] if kwargs.get('township_id') else '',
                    'state_id': kwargs['state_id'] if kwargs.get('state_id') else '',
                    'country_id': mm['id'],
                    'zip': kwargs['zip'] if kwargs.get('zip') else '',
                    'email': kwargs['email'] if kwargs.get('email') else '',
                    'phone': kwargs['phone'] if kwargs.get('phone') else '',
                    'type': kwargs['type'] if kwargs.get('type') else 'delivery'#delivery
                })
                message='Successful!!'
                success = True
            else:
                message = 'User does not exist!!'
                success = False
        except MissingError as err:
            message = str(err)
            success = False

        result ={
            'message':message,
            'success':success,

        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)#jwt_http.response(data=result)#json.dumps(result)#response_json(success=True, data=None, message="successful!!")

    @login_required('/user/address/update', auth="public", methods=["POST"], type='http', csrf=False)
    def update_addresses(self, **kwargs):
        [mm] = request.env['res.country'].search_read([('code', 'like', 'MM')])
        user_id = kwargs['user_id'] if kwargs['user_id'] else None
        # partner_id = kwargs['partner_id'] if kwargs['partner_id'] else None
        user = request.env['res.users'].sudo().search([('id', '=', user_id)])

        message = success = None
        try:
            partner = request.env['res.partner'].browse(user.partner_id.id)
            if partner:
                partner.write({
                    # 'parent_id': user.partner_id.id,
                    # 'name': kwargs['name'] if kwargs.get('name') else '',
                    'street': kwargs['street'] if kwargs.get('street') else '',
                    'city_id': kwargs['city_id'] if kwargs.get('city_id') else '',
                    'township_id': kwargs['township_id'] if kwargs.get('township_id') else '',
                    'state_id': kwargs['state_id'] if kwargs.get('state_id') else '',
                    'country_id': mm['id'],
                    'zip': kwargs['zip'] if kwargs.get('zip') else '',
                    # 'email': kwargs['email'] if kwargs.get('email') else '',
                    # 'phone': kwargs['phone'] if kwargs.get('phone') else '',
                    # 'type': kwargs['type'] if kwargs.get('type') else ''
                })
                message = "Update Successful!!"
                success = True
                # return response_json(success=True, data=None, message="Update Successful!!")
            else:
                message = "Update Cancel!!"
                success = False
        except MissingError as err:
            message = str(err)
            success = False

        result = {
            'message': message,
            'success': success
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)#jwt_http.response(data=result)#json.dumps(result)

    @public_route('/address/info', auth="public", methods=["POST"], type='http', csrf=False)
    def address_info(self, **kwargs):
        # [country] = request.env['res.country'].search_read([('name', '=', 'Myanmar')], fields=['id','name'])
        # country = request.env['res.country'].sudo().search([('name', '=', 'Myanmar')], fields=['id','code','name'], limit=1)
        # states = request.env['res.country.state'].sudo().search([('country_id', '=', country['id'])])
        # states = request.env['res.country.state'].search_read([('country_id', '=', country['id'])], fields=['id','code','name'], order='code')
        # cities = request.env['res.city'].sudo().search([('state_id', 'in', states['id'])], fields=['id','code', 'name'], order='code')
        # townships = request.env['res.township'].search_read([('city_id', 'in', cities.ids)], fields=['id','code', 'name'],order='code')

        country = request.env['res.country'].sudo().search([('name', '=', 'Myanmar')], limit=1)
        states = request.env['res.country.state'].sudo().search([('country_id', '=', country.id)])
        cities = request.env['res.city'].sudo().search([('state_id', 'in', states.ids)], order='code')
        townships = request.env['res.township'].sudo().search([('city_id', 'in', cities.ids)], order='code')

        country_list = request.env['res.country'].sudo().search_read([('id', '=', country.id)], fields=['id','code','name'], limit=1)
        state_list = request.env['res.country.state'].sudo().search_read([('id', 'in', states.ids)], fields=['id','code','name','country_id'], order='code')
        city_list = request.env['res.city'].sudo().search_read([('id', 'in', cities.ids)], fields=['id','code', 'name','state_id'], order='code')
        township_list = request.env['res.township'].sudo().search_read([('id', 'in', townships.ids)], fields=['id','code', 'name','city_id'],order='code')


        result = {
            'message': "Country, State, City, Township",
            'success': True,
            'data':
                {
                    'country': country_list,
                    'states': state_list,
                    'cities': city_list,
                    'townships': township_list,
                }
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#

        # return json.dumps(result)

    @public_route('/otp/send', auth="public", method=['POST'], type='http', csrf=False)
    def forgot_password(self, **kwargs):
        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)
        authenticate_data = None
        message = None
        success = False

        if data.get('login'):
            # user = request.env['res.users'].search([('login', '=', data.get('login'))])
            user = request.env['res.users'].sudo().search([('login', '=', data['login'])])
            if user:
                # create user otp to verify otp code set by user
                otp_code = random.randint(100000, 999999)
                # Authenticate with Trillo OTP
                # Download the helper library from https://www.twilio.com/docs/python/install
                # import os ===========================
                # from twilio.rest import Client============================
                # Set environment variables for your credentials
                # Read more at http://twil.io/secure
                account_sid = "AC2041126f09718c920991224696c598e1"
                auth_token = "ed79c4ac24c347d85bc8ed60a32f3e04"
                client = Client(account_sid, auth_token)

                # user_id = json.loads(authenticate.data)['data']['user']['id']
                twillo_message = client.messages.create(
                    body=otp_code,
                    from_="+15855410794",
                    to="+959422997233"
                )
                user_otp = request.env['res.users.otp'].create({
                    'user_id': user.id,
                    'code': otp_code,
                    # 'expire_date': datetime.now().strftime('%Y-%m-%d')
                })
                message = "Send OTP Successful!!!"
                success = True
                authenticate_data = {
                        'user_id': user.id,
                        'user_name': user.name
                    }

        result = {
            'message': message,
            'success': success,
            'data': authenticate_data
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)

    @public_route('/user/change_password', type='http', auth="public", methods=['POST'], csrf=False)
    def change_password(self, **kwargs):
        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)

        message = None
        success = False

        if data.get('user_id'):
            user = request.env['res.users'].sudo().search([('id', '=', data.get('user_id'))])
            if user:
                try:
                    if data['new_password'] == data['confirm_password']:
                        # if request.env['res.users'].change_password(user.password, data['new_password']):
                        if user.write({
                            'password': data['new_password']
                        }):
                            message = 'Password changed successfully'
                            success = True
                        # return {'status': True, 'message': ''}
                except AccessDenied as e:
                    message = e.args[0]
                    success = False
                    # if message == AccessDenied().args[0]:
                    #     message = 'The old password you provided is incorrect, your password was not changed.'
                except UserError as e:
                    message = e.args[0]
                    success = False
            else:
                message = "There is no user!"
                success = False

        result = {
            'message': message,
            'successs': success,
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)

    @public_route('/opt/authenticate', auth="public", method=['POST'], type='http', csrf=False)
    def otp_authenticate(self, **kwargs):
        user_id = kwargs['user_id'] if kwargs.get('user_id') else None
        otp = kwargs['otp'] if kwargs.get('otp') else None

        headers = request.httprequest.headers
        raw_body_data = http.request.httprequest.data
        my_json = raw_body_data.decode('utf8').replace("'", '"')
        data = json.loads(my_json)

        message = None
        success = False

        if otp and user_id:
            last_user_otp = request.env['res.users.otp'].search([('user_id','=', user_id), ('use_date', '=', False)], limit=1, order='id desc')

            if last_user_otp:
                if str(otp) != last_user_otp.code:
                    message = 'Wrong OTP code!'
                    success = False
                else:
                    last_user_otp.write({
                        'use_date': datetime.now().strftime('%Y-%m-%d'),
                    })
                    message = 'Authentication Successful'
                    success = True
        result = {
            'message': message,
            'success': success,
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)


    @login_required('/web/session/logout/json', auth="public", methods=["POST"], type='http', csrf=False)
    def logout(self):
        request.session.logout(keep_db=True)
        request.session.uid = None
        request.session.sale_order_id = None
        return {'message': 'Logged out successfully.'}

def check_otp(user_id, otp_code):
    if otp_code and user_id:
        last_user_otp = request.env['res.users.otp'].search([('user_id', '=', user_id), ('use_date', '=', False)],
                                                            limit=1, order='id desc')

        if last_user_otp:
            if otp_code != last_user_otp.code:
                message = 'Wrong OTP code!'
                success = False
            else:
                last_user_otp.write({
                    'use_date': datetime.now().strftime('%Y-%m-%d'),
                })
                message = 'Success'
                success = True

def get_addresss(partner):
    address = None
    if partner:
        if partner.street:
            if address:
                address = address + ',' + partner.street
            else:
                address = partner.street
        if partner.township_id:
            if address:
                address = address + ',' + partner.township_id.name
            else:
                address = partner.township_id.name
        if partner.city_id:
            if address:
                address = address + ',' + partner.city_id.name
            else:
                address = partner.city_id.name
        if partner.state_id:
            if address:
                address = address + ',' + partner.state_id.name
            else:
                address = partner.state_id.name
        if partner.zip:
            if address:
                address = address + ',' + partner.zip
            else:
                address = partner.zip
        if partner.country_id:
            if address:
                address = address + ',' + partner.country_id.name
            else:
                address = partner.country_id.name

    return address




