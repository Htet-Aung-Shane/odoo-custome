# from math import prod
import json
from multiprocessing.dummy.connection import Client
from typing import OrderedDict
from urllib import response
from xml.etree.ElementPath import prepare_descendant
from odoo.http import request, Response
from odoo import http
from math import ceil
from datetime import datetime, timedelta
import math
import re
from odoo_rest_framework import login_required, response_json,jwt_http,public_route
from odoo.exceptions import UserError, MissingError, QWebException
from werkzeug.wrappers import Request, Response

from ..controllers.product_controller import calculate_kpy
# from ..controllers.product_controller import _get_product_image_url
from ..controllers.product_controller import set_paginations
from ..controllers.product_controller import _calculate_gold_weight
from ..controllers.product_controller import cleanhtml
from ..controllers.product_controller import get_images_url
from ..controllers.product_controller import product_template_image
from ..controllers.product_controller import seller_shop_image
from ..controllers.product_controller import webclient_subscription_image

default_image_shop = 'default-img-shop.png'
remove_host_url = request.httprequest.host_url
CLEANR = re.compile('<.*?>')
default_url = remove_host_url + "webclient/static/default_img/" + default_image_shop
acquirer_image=['payment.acquirer','image_128']
cash_img_url = remove_host_url + "webclient/static/default_img/cash.png"
class ShopController(http.Controller):
    
    @public_route(['/list/shops'], type='http', auth='public', methods=['POST'], csrf=False)
    def get_shop_list(self, **kwargs):
        #return shop list sort by shop's active plan level
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        order = str(kwargs['order']) if kwargs.get('order') else None
        plan_slug = str(kwargs['plan_slug']) if kwargs.get('plan_slug') else None
        section = str(kwargs['section']) if kwargs.get('section') else None

        model_name = 'seller.shop'
        filters = [('active','=',True),('is_published','=',True)]

        if plan_slug:
            filters.append(('plan_slug', '=', plan_slug))

        fields = ['id', 'name', 'active_plan', 'level','url','promoted_shop_sections']
        default_order ="level desc"
        domain = []
        if order:
            default_order = default_order + ','+ order

        #get shops sort by active plan level
        # items = request.env[model_name].sudo().search_read(filters, fields=fields, offset=offset, order='level desc')
        items = request.env[model_name].sudo().search(filters, order=default_order, limit=limit)
        # print('shop items',items)

        # remove_host_url = request.httprequest.host_url
        # logo_url = remove_host_url+"web/image/seller.shop/{id}/shop_logo/"
        # banner_url = remove_host_url+"web/image/seller.shop/{id}/shop_banner/"

        shop_list = []
        if items:
            for shop in items:
                
                shop_logo_url = shop_banner_url = sub_plan_logo_url = default_url

                if shop.shop_logo:
                    shop_logo_url = get_images_url(shop.id,seller_shop_image[0],seller_shop_image[1])

                if shop.shop_banner:
                    shop_banner_url = get_images_url(shop.id,seller_shop_image[0],seller_shop_image[2])

                if shop.active_plan.logo:
                    sub_plan_logo_url = get_images_url(shop.active_plan.id, webclient_subscription_image[0], webclient_subscription_image[1])

                shop_address = _get_shop_address(shop)

                sections = request.env['promoted.section'].sudo().search([('id','in',shop.promoted_shop_sections.ids)])
                section_list = []
                if sections:
                    for sec in sections:
                       section_list.append(sec.name)
                shop_url = shop.url.rsplit("/")

                #seller branch
                branch_filters = [('active', '=', True)]

                if shop:
                    branch_filters.append(('seller_shop_id', '=', shop.id))
                branch_fields = ['id', 'name', 'address', 'branch_latitude', 'branch_longitude', 'seller_shop_id']
                branches = request.env['seller.branch'].sudo().search_read(branch_filters, fields=branch_fields, limit=limit,
                                                                      offset=offset,
                                                                      order=order)
                branch_list = []

                if branches:
                    for branch in branches:
                        val = {
                            'id': branch['id'] or None,
                            'name': branch['name'] or None,
                            'address': branch['address'] or None,
                            'branch_latitude': branch['branch_latitude'] or None,
                            'branch_longitude': branch['branch_longitude'] or None,
                            'seller_shop_id': branch['seller_shop_id'][0] or None,
                        }
                        branch_list.append(val)


                #acquirer list
                acquirer_list = []
                # acquirer_filters = [('active', '=', True)]

                acquirer_filters = [('state', 'in', ('enabled', 'test'))]
                if shop:
                    acquirer_filters.append(('seller_shop_id', 'in', shop.ids))

                acquirers = request.env['payment.acquirer'].sudo().search(acquirer_filters, limit=limit, offset=offset,
                                                                          order=order)


                if acquirers:
                    for acquirer in acquirers:
                        acquirer_image_url = get_images_url(acquirer.id, acquirer_image[0], acquirer_image[1])
                        val = {
                            'id': acquirer.id,
                            'name': acquirer.name,
                            # 'shop_id': acquirer.seller_shop_id.name,
                            'image_url': acquirer_image_url
                        }
                        acquirer_list.append(val)


                    acquirer_list.append({
                        'id': None,
                        'name': 'cash',
                        # 'shop_id': acquirer.seller_shop_id.name,
                        'image_url': cash_img_url
                    })


                val = {
                    'id': shop.id,
                    'name': shop.name,
                    'sub_plan_level': shop.active_plan.level if shop.active_plan else 0,
                    'sub_plan_type': shop.active_plan.name if shop.active_plan else "",
                    'sub_plan_slug': shop.active_plan.slug,
                    'sub_plan_logo_url': sub_plan_logo_url,
                    'shop_slug': shop_url[1] if len(shop_url) > 1 else "",
                    'promoted_shop_sections': section_list,
                    'fb_url': shop.fb_url,
                    'tt_url': shop.tt_url,
                    'inst_url': shop.inst_url,
                    'shop_logo_url': shop_logo_url,
                    'shop_banner_url': shop_banner_url,
                    'shop_address': shop_address,
                    'branches': branch_list,
                    'acquirer_list': acquirer_list
                }

                if section:
                    if section_list:
                        if section in section_list:
                            if plan_slug:
                                if shop.plan_slug == plan_slug:
                                    shop_list.append(val)
                            shop_list.append(val)
                else:
                    if plan_slug:
                        if shop.plan_slug == plan_slug:

                            shop_list.append(val)
                    else:
                        shop_list.append(val)


        total_items = len(shop_list)
        # sorted_item_list = shop_list.sort(key=lambda a: a['sub_plan_level'],reverse=True)

        message = success = None
        if len(shop_list) >= 1:
            message = 'Shop List'
            success = True
        else:
            message = 'NO Shop'
            success = False

        result = {
            'success': success,
            'message': message,
            'paginate_info':
                {
                 'limit': limit,
                 'current_page': page,
                 'total_items': total_items,
                 'total_pages': ceil(total_items/limit),
                },
            'data': shop_list,
            }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)#jwt_http.response(data=result)#
        # return response_json(success=True,message="Hello",data=result)

    @public_route(['/detail/shop'], type='http', auth='public', methods=['POST'], csrf=False)
    def get_shops_detail(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        seller_shop_id = kwargs['seller_shop_id'] if kwargs.get('seller_shop_id') else None
        categ_id = kwargs['categ_id'] if kwargs.get('categ_id') else None

        model_name = 'seller.branch'
        filters =[('active', '=', True)]

        if seller_shop_id:
            filters.append(('seller_shop_id', '=', seller_shop_id))
        fields = ['id', 'name', 'address', 'branch_latitude', 'branch_longitude', 'seller_shop_id']
        branches = request.env[model_name].sudo().search_read(filters, fields=fields, limit=limit, offset=offset,
                                                              order=order)
        branch_list = []
        if branches:
            for branch in branches:
                val ={
                    'id': branch['id'] or None,
                    'name': branch['name'] or None,
                    'address': branch['address'] or None,
                    'branch_latitude': branch['branch_latitude'] or None,
                    'branch_longitude': branch['branch_longitude'] or None,
                    'seller_shop_id': branch['seller_shop_id'][0] or None,
                }
                branch_list.append(val)

        result = None
        message = success = items = None

        try:
            seller_shop = request.env['seller.shop'].sudo().browse(seller_shop_id)

            if seller_shop:
                reviews_filter = [('marketplace_seller_id', '=', seller_shop.seller_id.id)]
                reviews = request.env['seller.review'].sudo().search_read(reviews_filter, fields=['partner_id','rating','create_date','msg','email'],
                                                                          limit=None,
                                                                          offset=offset,
                                                                          order='id desc')

                review_list = []
                total_scores = []

                rating1_count = rating2_count = rating3_count = rating4_count = rating5_count = 0
                rating1_percent = rating2_percent = rating3_percent = rating4_percent = rating5_percent = 0
                last_review = None
                total_review_count = total_scores = average_score = 0

                if reviews:
                    # rev = reviews[-1]
                    # if rev:
                    #     last_review = {
                    #         'customer_id': rev['partner_id'][0],
                    #         'customer': rev['partner_id'][1],
                    #         'rating': rev['rating'],
                    #         'create_date': rev['create_date'].strftime('%m/%d/%Y'),
                    #         'msg': rev['msg'],
                    #         'email': rev['email'],
                    #     }
                    # review_list.append(val)

                    for review in reviews:
                        val = {
                            'customer_id': review['partner_id'][0],
                            'customer': review['partner_id'][1],
                            'rating': review['rating'],
                            'create_date': review['create_date'].strftime('%m/%d/%Y'),
                            'msg': review['msg'],
                            'email': review['email'],
                        }
                        review_list.append(val)

                        if review['rating'] == 1:
                            rating1_count += 1
                        elif review['rating'] == 2:
                            rating2_count += 1
                        elif review['rating'] == 3:
                            rating3_count += 1
                        elif review['rating'] == 4:
                            rating4_count += 1
                        elif review['rating'] == 5:
                            rating5_count += 1

                    total_review_count = len(reviews) if len(reviews) > 0 else 1
                    total_scores = round((1 * rating1_count) + (2 * rating2_count) + (3 * rating3_count) + (4 * rating4_count) + (5 * rating5_count),2)

                    if total_review_count > 0:
                        average_score = round(total_scores/total_review_count, 2)

                    rating1_divider = rating2_divider = rating3_divider = rating4_divider = rating5_divider = 1
                    # scores = [1, 2, 3, 4, 5]
                    if rating1_count > 0:
                        rating1_divider = rating1_count * 1
                    if rating2_count > 0:
                        rating2_divider = rating2_count * 2
                    if rating3_count > 0:
                        rating3_divider = rating3_count * 3
                    if rating4_count > 0:
                        rating4_divider = rating4_count * 4
                    if rating5_count > 0:
                        rating5_divider = rating5_count * 5

                    rating1_percent = round((rating1_count / total_review_count) * 100,2)#round(((5 * total_review_count) / rating1_divider), 2)
                    rating2_percent = round((rating2_count / total_review_count) * 100,2)#round(((5 * total_review_count) / rating2_divider), 2)
                    rating3_percent = round((rating3_count / total_review_count) * 100,2)#round(((5 * total_review_count) / rating3_divider), 2)
                    rating4_percent = round((rating4_count / total_review_count) * 100,2)#round(((5 * total_review_count) / rating4_divider), 2)
                    rating5_percent = round((rating5_count / total_review_count) * 100,2)#round(((5 * total_review_count) / rating5_divider), 2)

                total_items = len(branches)
                image_url = '/api/image?model=' + model_name + '&id='

                #get shop logo/banner url
                shop_logo_url = shop_banner_url = sub_plan_logo_url = ""

                if seller_shop.active_plan.logo:
                    sub_plan_logo_url = get_images_url(seller_shop.active_plan.id, webclient_subscription_image[0], webclient_subscription_image[1])


                if seller_shop.shop_logo:
                    logo_url = get_images_url(seller_shop.id, seller_shop_image[0],seller_shop_image[1])
                else:
                    logo_url = default_url

                if seller_shop.shop_banner:
                    banner_url = get_images_url(seller_shop.id,seller_shop_image[0], seller_shop_image[2])
                else:
                    banner_url = default_url

                # logo_url, banner_url = _get_shop_images_url(seller_shop)

                #terms & conditions
                # terms_conditions = seller_shop.shop_t_c
                terms_conditions = cleanhtml(seller_shop.shop_t_c) if seller_shop.shop_t_c else ''

                #product template of shop
                product_group_list = _get_product_group_by_shop(seller_shop_id,categ_id)

                shop_address = _get_shop_address(seller_shop)

                #follower count
                follower = request.env['shop.follower'].sudo().search([('shop_id','=',seller_shop.id),('follow','=',True)])
                follower_count = len(follower) if follower else 0

                items = {
                        'shop_info': {
                            'id': seller_shop.id,
                            'name': seller_shop.name,
                            'email': seller_shop.email,
                            'phone': seller_shop.phone,
                            'description': seller_shop.description,
                            # 'mobile':seller_shop.shop_mobile,
                            'shop_informations':seller_shop.description,
                            'logo_url': logo_url,
                            'banner_url': banner_url,
                            'fb_url': seller_shop.fb_url,
                            'tt_url': seller_shop.tt_url,
                            'inst_url': seller_shop.inst_url,
                            'terms_conditions': terms_conditions,
                            'address': shop_address,
                            'follower': follower_count,

                            'sub_plan_level': seller_shop.active_plan.level if seller_shop.active_plan else 0,
                            'sub_plan_type': seller_shop.active_plan.name if seller_shop.active_plan else "",
                            'sub_plan_logo_url': sub_plan_logo_url,
                        },
                        'product_group_list': product_group_list,
                        'branch_info_ids': branch_list,
                        'feedbacks': {
                            'total_scores': [
                                        {
                                            'short_code': 'vb',
                                            'total_review': rating1_count,
                                            'display_name': 'Very Bad',
                                            'percent': rating1_percent,
                                        },
                                        {
                                            'short_code': 'b',
                                            'total_review': rating2_count,
                                            'display_name': 'Bad',
                                            'percent': rating2_percent,
                                        },
                                        {
                                            'short_code': 'n',
                                            'total_review': rating3_count,
                                            'display_name': 'Normal',
                                            'percent': rating3_percent,
                                        },
                                        {
                                            'short_code': 'g',
                                            'total_review': rating4_count,
                                            'display_name': 'Good',
                                            'percent': rating4_percent,
                                        },
                                        {
                                            'short_code': 'vg',
                                            'total_review': rating5_count,
                                            'display_name': 'Very Good',
                                            'percent': rating5_percent,
                                        }
                                        ],
                            'average_score': average_score,
                            'total_reviews': total_review_count,
                            'review_list': review_list
                            # 'last_review': last_review,#review_list,
                        }
                    }

                message = 'Shop Detail'
                success = True
            else:
                message = 'NO Shop'
                success = False
        except MissingError as err:
            message = str(err)
            success = False


        result = {
            'success': success,
            'message': message,
            'data': items
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#

        # return json.dumps(result)

    @public_route(['/shop/follower'], type='http', auth='public', methods=['POST'], csrf=False)
    def create_shop_follower(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        user_id = kwargs['user_id'] if kwargs.get('user_id') else None
        shop_id = kwargs['shop_id'] if kwargs.get('shop_id') else None
        message = success = result = None
        follow_shop = request.env['shop.follower'].sudo().search(
            [('shop_id', '=', shop_id), ('user_id', '=', user_id)], limit=1)
        # try:
        #     follow_shop = request.env['shop.follower'].sudo().search(
        #         [('shop_id', '=', shop_id), ('user_id', '=', user_id)], limit=1)
        #
        # except MissingError as err:
        #     message = str(err)
        #     success = 'FAIL'

        if not follow_shop:
            request.env['shop.follower'].sudo().create({
                'user_id': user_id,
                'shop_id': shop_id,
                'follow': True,
            })

            message = 'Shop Follow Successful!!!'
            success = True
            # result = {
            #     'message':'Successful!!!'
            # }
        else:
            follow_shop.sudo().write({
                'follow': False if follow_shop.follow == True else True,
            })
            message = 'Update Successful!!!'
            success = True

        result = {
            'message': message,
            'success': success
        }

        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)  # json.dumps(result)#
        # return json.dumps(result)

    @login_required(['/list/shop_acquirers'], type='http', auth='public', methods=['POST'], csrf=False)
    def get_shop_acquirer_list(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        shop_id = kwargs['shop_id'] if kwargs.get('shop_id') else None

        filters = [('state', 'in', ('enabled', 'test'))]
        if shop_id:
            filters.append(('seller_shop_id', 'in', shop_id))
        fields = ['id', 'name', 'address', 'branch_latitude', 'branch_longitude', 'seller_shop_id']
        # fields = ['id', 'name', 'shop_id', 'image_128'],
        acquirers = request.env['payment.acquirer'].sudo().search(filters, limit=limit, offset=offset, order=order)
        message = "Acquirer List"
        success = False

        acquirer_list = []
        if acquirers:
            for acquirer in acquirers:
                acquirer_image_url = get_images_url(acquirer.id, acquirer_image[0], acquirer_image[1])
                val = {
                    'id': acquirer.id,
                    'name': acquirer.name,
                    # 'shop_id': acquirer.seller_shop_id.name,
                    'image_url': acquirer_image_url
                }
                acquirer_list.append(val)
                success = True

        result = {
            'message': message,
            'success': success,
            'data': acquirer_list if acquirers else None
        }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)









def _get_product_group_by_shop(shop_id,categ_id):
    model_name = 'product.group'
    filters = [('active', '=', True)]

    if shop_id:
        filters.append(('shop_id', '=', shop_id))
    if categ_id:
        filters.append(('public_categ_ids','in',categ_id))

    fields = ['id', 'name', 'display_product_tmpl_id', 'priority', 'occurance']

    # order
    default_sort = "priority asc,occurance asc,list_price desc"

    items = request.env[model_name].sudo().search(filters, order=default_sort)
    # print('group list=>',shop_id,items)

    item_list = []

    remove_host_url = request.httprequest.host_url

    for group in items:
        priority = 0
        if group.sub_plan_id != None and group.priority != 0:
            priority = group.priority

        # detail info
        # calculate total qty kyats
        total_qty_kyat = _calculate_gold_weight(group.display_product_tmpl_id)


        # calculate deals & offer of product group
        # deal_offer = _calculate_deals_offer(group)

        sale_price, discounted_price, discount_type, \
        discount_value, deals_offer_name,\
        total_qty_kyat,total_qty_gram, sale_price_unit, total_qty_petha, total_qty_yway = calculate_kpy(
            group.display_product_tmpl_id,1,group,None)

        display_product_image_url = None
        if group.display_product_tmpl_id.image_1920:
            display_product_image_url = get_images_url(group.display_product_tmpl_id.id,product_template_image[0],product_template_image[1])
        else:
            display_product_image_url = default_url

        val = {
            'id': group.id,
            'name': group.name,
            'priority': priority,
            'occurance': group.occurance,
            'display_product_id': group.display_product_tmpl_id.id,
            'display_product_name': group.display_product_tmpl_id.name,
            'sale_price': sale_price,#group.display_product_tmpl_id.list_price,
            'cost_price': 0,#group.display_product_tmpl_id.standard_price,
            'discount_type': discount_type,#deal_offer.get('discount_type') if deal_offer.get('discount_type') else None,
            'discount_value': discount_value,#deal_offer.get('discount_value') if deal_offer.get('discount_value') else 0.00,
            'discounted_price': discounted_price,#deal_offer.get('discounted_price') if deal_offer.get('discount_value') else 0.00,
            'display_product_image_url': display_product_image_url,
        }
        item_list.append(val)

    sorted_item_list = item_list.sort(key=lambda a: (a['priority'], a['occurance']))

    total_items = len(item_list)

    return item_list

def _get_shop_address(seller_shop):
    shop_address = ''
    if seller_shop.street:
        shop_address = shop_address + str(seller_shop.street)
    if seller_shop.street2:
        if shop_address:
            shop_address = shop_address + ',' + str(seller_shop.street2)
        else:
            shop_address = str(seller_shop.street2)
    if seller_shop.city:
        if shop_address:
            shop_address = shop_address + ',' + str(seller_shop.city)
        else:
            shop_address = str(seller_shop.city)
    if seller_shop.state_id:
        if shop_address:
            shop_address = shop_address + ',' + str(seller_shop.state_id.name)
        else:
            shop_address = str(seller_shop.state_id.name)
    if seller_shop.country_id:
        if shop_address:
            shop_address = shop_address + ',' + str(seller_shop.country_id.name)
        else:
            shop_address = str(seller_shop.country_id.name)


    return shop_address

def calculate_total_scores(reviews):
    review_list = []
    total_scores = []
    rating1_count = rating2_count = rating3_count = rating4_count = rating5_count = 0
    rating1_percent = rating2_percent = rating3_percent = rating4_percent = rating5_percent = 0
    last_review = None
    if reviews:
        rev = reviews[-1]
        if rev:
            last_review = {
                'customer_id': rev['partner_id'][0],
                'customer': rev['partner_id'][1],
                'rating': rev['rating'],
                'create_date': rev['create_date'].strftime('%m/%d/%Y'),
                'msg': rev['msg'],
                'email': rev['email'],
            }
        # review_list.append(val)
        for review in reviews:
            if review['rating'] == 1:
                rating1_count += 1
            if review['rating'] == 2:
                rating2_count += 1
            if review['rating'] == 3:
                rating3_count += 1
            if review['rating'] == 4:
                rating4_count += 1
            if review['rating'] == 5:
                rating5_count += 1

        review_count = len(reviews) if len(reviews) > 0 else 1
        total_scores = (1 * rating1_count) + (2 * rating2_count) + (3 * rating3_count) + (4 * rating4_count) + (5 * rating5_count)
        average_score = total_scores / review_count

        rating1_percent = ((5 * review_count) / (1 * rating1_count)) * 100
        rating2_percent = ((5 * review_count) / (2 * rating1_count)) * 100
        rating3_percent = ((5 * review_count) / (3 * rating2_count)) * 100
        rating4_percent = ((5 * review_count) / (4 * rating3_count)) * 100
        rating5_percent = ((5 * review_count) / (5 * rating4_count)) * 100