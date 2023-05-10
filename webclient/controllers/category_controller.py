import json
from dataclasses import field
from odoo import http
from odoo.http import request
from odoo import models
import math
from odoo_rest_framework import login_required, response_json,jwt_http,public_route
from odoo.exceptions import UserError, MissingError, QWebException
from werkzeug.wrappers import Request, Response
from ..controllers.product_controller import get_images_url
remove_host_url = request.httprequest.host_url
default_image_shop = 'default-img-shop.png'
default_url = remove_host_url + "webclient/static/default_img/" + default_image_shop
product_category_image = ['product.public.category', 'image_1920']

class CategoryController(http.Controller):
    @public_route(['/list/categories'], type='http', auth='public', method=['POST'], csrf=False)
    def get_categories(self, **kwargs):
        headers = request.httprequest.headers
        print('header=>',headers)
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        model_name = 'product.public.category'
        filters = []
        shop_id = kwargs['shop_id'] if kwargs.get('shop_id') else None
        # public_categ_ids
        if shop_id:
            public_categ_ids = request.env['product.template'].sudo().search([('shop_id', '=', shop_id)], limit=limit, offset=offset, order=order).public_categ_ids
            # print('public_categ_ids')
            if public_categ_ids:
                filters.append(('id', '=', public_categ_ids.ids))
        # shop_ids = kwargs.get('shop_ids')
        
        # fields = ['id', 'name', 'image_1920']
        # items = request.env[model_name].sudo().search_read(filters, fields=fields, limit=limit, offset=offset, order=order)
        items = request.env[model_name].sudo().search(filters, limit=limit, offset=offset, order=order)
        total_items = len(items)

        category_list = []
        # remove_host_url = request.httprequest.host_url
        category_image_url = None
        message = success = None
        if items:
            for category in items:
                if category.image_1920:
                    category_image_url = get_images_url(category.id, product_category_image[0], product_category_image[1])
                else:
                    category_image_url = default_url

                val = {
                    'id': category['id'],
                    'name': category['name'],
                    'image_url': category_image_url,
                }
                category_list.append(val)

        if len(category_list) >= 1:
            success = True
            message = 'Category List'
        else:
            success = False
            message = 'No Category List'

        result = {
            'message': message,
            'success': success,
            'paginate_info': {
                'limit': limit,
                'current_page': page,
                'total_items': total_items,
                'total_pages': math.ceil(total_items/limit),
            },
            'data': category_list,
        }
        headers = {'Content-Type': 'application/json'}

        return Response(json.dumps(result), headers=headers)#json.dumps(result)#
        # return json.
        # return response_json(success=success,message=message,data=result)
        # return jwt_http.response(data=result,succes=success,message=message)#json.dumps(result)