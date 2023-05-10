# from math import prod
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

prod_basic_fields = [
    'name',
    'default_code',
    'brand_id',
    'image_url_md',
    'public_categ_ids',
    'webclient_list_price_with_currency',
    'webclient_sale_price_with_currency',
    'has_discount',
    'discount_description',
    'discount_description_detail',
    'sale_delay',
    'seller_lead_time',
    'invoice_policy',
    'virtual_available',
    'qty_available',
    'allow_out_of_stock_order',
    'website_description',
    'product_description'

]


remove_host_url = request.httprequest.host_url
CLEANR = re.compile('<.*?>')
default_image_shop = 'default-img-shop.png'
default_url = remove_host_url + "webclient/static/default_img/" + default_image_shop
product_template_image=['product.template','image_1920']
product_set_image=['product.set','image_1920']
seller_shop_image=['seller.shop','shop_logo','shop_banner']
webclient_subscription_image=['webclient.subscription.plan','logo']


class ProductController(http.Controller):
    @http.route(['/list/products'], type='json', auth='public',method=['POST'])
    def get_product_list(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()

        print('limit, offset, page, order',limit, offset, page, order)
        categ_id = int(kwargs['categ_id']) if kwargs.get('categ_id') else None
        type = str(kwargs['type']) if kwargs.get('type') else None
        shop_ids = tuple(kwargs['shop_ids']) if kwargs.get('shop_ids') else None
        sort = str(kwargs['sort']) if kwargs.get('sort') else None

        model_name = 'product.group'
        image_url = '/web/image?model=' + model_name + '&id='

        filters = []
        if shop_ids:
            filters = [('shop_id','in',shop_ids),('active','=',True)]

        fields = ['id', 'name','display_product_tmpl_id','display_product_id','shop_id','group_line','shop_id']

        items = request.env[model_name].sudo().search(filters, order=sort,limit=limit,offset=offset)
        print('items=>',items)
        ##update occurrance count
        request.cr.execute("""
                    update product_group set occurance=occurance+1 
                     where id in %s
                """, [tuple(items.ids)])

        # result = request.cr.fetchall()

        item_list = []
        for group in items:
            #get last pricelist of display product template id
            pricelist_id = None
            if group.display_product_tmpl_id:
                pricelist_id = request.env['product.pricelist.item'].sudo().search([
                    ('product_tmpl_id','=', group.display_product_tmpl_id.id),
                    ('deal_applied_on','=','1_product')
                ], limit=1, order='id desc')

            #get last deal and offer of last pricelist item of display product template id
            discount_value = 0
            if pricelist_id:
                deal_id = request.env['website.deals'].sudo().search([('pricelist_items','in',pricelist_id.id),('state','=','validated')],limit=1,order='id desc')
                if deal_id:
                    for deal in deal_id.pricelist_items:
                            if deal.id == pricelist_id.id:
                                discount_value = deal.compute_price

        categ_id = int(kwargs['categ_id']) if kwargs.get('categ_id') else None
        shop_ids = tuple(kwargs['shop_ids']) if kwargs.get('shop_ids') else None
        sort = str(kwargs['sort']) if kwargs.get('sort') else None
        gender = str(kwargs['gender']) if kwargs.get('gender') else None

        #filter parameters
        filters = [('active','=',True)]

        if categ_id:
            filters.append(('public_categ_ids','in',categ_id))
        if shop_ids:
            filters.append(('shop_id','in',shop_ids))

        search_filters = []
        if gender:
            val={
                'key':'gender',
                'value':gender,
            }
            search_filters.append(val)

        #order
        default_sort = "priority asc,occurance asc,list_price desc"
        # if sort:
        #     default_sort = default_sort + ',' + sort

        items = request.env['product.group'].sudo().search(filters, order=default_sort,limit=limit,offset=offset)

        #update occurrance count
        if items:
            request.cr.execute("""
                        update product_group set occurance=occurance+1
                         where id in %s
                    """, [tuple(items.ids)])

        item_list = []
        for group in items:
            # #get last pricelist of display product template id
            # pricelist_id = None
            # if group.display_product_tmpl_id:
            #     pricelist_id = request.env['product.pricelist.item'].sudo().search([
            #         ('product_group_id','=', group.id),
            #         ('deal_applied_on','=','product_group')
            #     ], order='id desc')

            shop_id = group.shop_id

            #get discounted price of display product template of product group
            discounted_price = sale_price = 0
            discount_type = None
            discount_value = None
            deals_offer_name = None

            sale_price, discounted_price, discount_type, discount_value, deals_offer_name \
                , total_qty_kyat, total_qty_gram, sale_price_unit = calculate_kpy(
                group.display_product_tmpl_id, 1, group, None)


            #get shop information of shop that relate with group
            if group.shop_id:
                shop = request.env['seller.shop'].sudo().search([('id','=',group.shop_id.id)])

                discount_value = 0
                if pricelist_id.compute_price == 'fixed':
                    discount_value = pricelist_id.fixed_price
                if pricelist_id.compute_price == 'percentage':
                    discount_value = pricelist_id.percent_price

                val = {
                    'id': group.id,
                    'name': group.name,
                    'discount_type': pricelist_id.compute_price,
                    'discount_value': discount_value,
                    'plan_priority':group.sub_plan_id.level,
                    'occurance': group.occurance,
                    'currency_id':{
                        'id':request.env.company.currency_id.id,
                        'symbol':request.env.company.currency_id.symbol,#pricelist_id.product_tmpl_id.uom_id.name,
                        'decimal_places':request.env.company.currency_id.decimal_places,
                        'rounding':request.env.company.currency_id.rounding,
                        'position':request.env.company.currency_id.position,
                    },
                    'disply_product_id':{
                        'id':group.display_product_tmpl_id.id,
                        'name':pricelist_id.product_tmpl_id.name,
                        'sale_price':pricelist_id.product_tmpl_id.list_price,#before discount price
                        'cost_price':pricelist_id.product_tmpl_id.standard_price,#after disocunt price
                        'discounted_price':pricelist_id.discounted_price,
                        'product_image_url': "/api/image/product.template/" + str(group.display_product_tmpl_id.id) + "/image_1920/",
                    },
                    'shop_id':{
                        'name':shop.name if shop else None,
                        'logo_url': "/api/image/seller.shop/" + str(shop.id) + "/shop_logo/"
                    },

                }

                item_list.append(val)
                # sorted_item_list = item_list.sort(key=lambda a: a['discount_value'],reverse=True)
            # sorted_item_list = item_list.sort(key=lambda a: (a['disply_product_id']['discounted_price']),reverse=True)

            sorted_item_list = item_list.sort(key=lambda a: (a['plan_priority'],a['occurance']))
            # print(sorted_item_list)



            #get product group's display product template's attributes
            attribute_lines = _get_related_attribute_lines(group.display_product_tmpl_id, search_filters)

            #product image url
            product_image_url = None #_get_product_image_url(group.display_product_tmpl_id)
            if group.display_product_tmpl_id.image_1920:
                product_image_url = get_images_url(group.display_product_tmpl_id,product_template_image[0],product_template_image[1])
            else:
                product_image_url = default_url

            #logo url
            # logo_url = _get_shop_logo_url(shop)
            logo_url = None
            if shop.shop_logo:
                logo_url = get_images_url(shop,seller_shop_image[0],seller_shop_image[1])
            else:
                logo_url = default_url


            # category = _get_category(group.display_product_tmpl_id.public_categ_ids)
            category = None
            if categ_id:
                category = request.env['product.public.category'].sudo().search_read([('id','=',categ_id)], fields=['id','name'], limit=1)
            else:
                category = request.env['product.public.category'].sudo().search_read([('id', '=', group.public_categ_ids.ids)],
                                                                                     fields=['id', 'name'], limit=1)

            val = {
                'id': group.id,
                'name': group.name,
                'plan_priority': group.sub_plan_id.level,
                'occurance': group.occurance,
                 'sale_price':group.list_price,
                'category':category[0] if category else None,
                'display_product_id': {
                    'id': group.display_product_tmpl_id.id,
                    'name': group.display_product_tmpl_id.name,
                    'sale_price': sale_price,#group.display_product_tmpl_id.list_price,  # sale
                    'cost_price': 0,#group.display_product_tmpl_id.standard_price,  # standard price/ cost
                    'deals_offer_name':deals_offer_name,
                    'discount_type': discount_type,
                    'discount_value': discount_value,
                    'discounted_price': discounted_price or 0.00,
                    'product_image_url': product_image_url,
                    'attribute_lines': attribute_lines,
                },
                'currency_id': {
                    'id': request.env.company.currency_id.id,
                    'symbol': request.env.company.currency_id.symbol,# pricelist_id.product_tmpl_id.uom_id.name,
                    'decimal_places': request.env.company.currency_id.decimal_places,
                    'rounding': request.env.company.currency_id.rounding,
                    'position': request.env.company.currency_id.position,
                },
                'shop_id': {
                    'shop_id':shop.id if shop else None,
                    'name': shop.name if shop else None,
                    'logo_url': logo_url
                },
            }
            item_list.append(val)

            sorted_item_list = item_list.sort(key=lambda a: (a['plan_priority'],a['occurance']))


        total_items = len(item_list)
        result = {
            'status': 'SUCCESS',
            'message': 'Product List',
            'paginate_info': {
                'limit': limit,
                'offset': offset,
                'offset': offset,
                'current_page': page,
                'total_items': total_items,
                'total_pages': math.ceil(total_items / limit),
            },
            # 'items': item_list,
            # 'item_info': {
            #     'prod_image_url_base': image_url,
            #     'shop_image_url_base': image_url
            # },
            'items': item_list,#item_list,


        }

        return result

    @http.route(['/detail/product'], type='json', auth='public', method=['POST'])
    def get_product_detail(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        # categ_id = int(kwargs['categ_id']) if kwargs.get('categ_id') else None
        # type = str(kwargs['type']) if kwargs.get('type') else None
        # shop_ids = tuple(kwargs['shop_ids']) if kwargs.get('shop_ids') else None
        # sort = str(kwargs['sort']) if kwargs.get('sort') else None

        model_name = 'product.group'
        remove_host_url = request.httprequest.host_url
        image_url = remove_host_url+"webclient/static/default_img/default-img-shop.png"

        filters = []
        fields = ['id', 'name', 'display_product_tmpl_id','priority']
        items = request.env[model_name].sudo().search(filters,order='priority desc')
        # items = request.env[model_name].sudo().search_read(filters, fields=fields, limit=limit, offset=offset,
        #                                                    order='priority desc')

        item_list = []
        for group in items:
            priority = 0
            if group.sub_plan_id != None and group.priority != 0:
                priority = group.priority

        product_group_id = kwargs['product_group_id'] if kwargs.get('product_group_id') else None

        model_name = 'product.group'
        # remove_host_url = request.httprequest.host_url
        image_url = remove_host_url + "webclient/static/default_img/"+default_image_shop

        filters = [('active','=',True)]

        if product_group_id:
            filters.append(('id','=',product_group_id))

        fields = ['id', 'name', 'display_product_tmpl_id','priority','occurance']

        # order
        default_sort = "priority asc,occurance asc,list_price desc"

        group = request.env[model_name].sudo().search(filters,order=default_sort)

        item_list = []
        val = None

        priority = 0
        if group:
            if group.sub_plan_id != None and group.priority != 0:
                priority = group.priority

            display_product_val = get_detail_product_template(group.display_product_tmpl_id,group,group.display_product_tmpl_id.public_categ_ids.ids)

            product_tmpl_list = []
            product_tmpl_weight_list = []

            if group.group_line:
                #product template list in product group
                for line in group.group_line:

                    product_tmpl_val = get_detail_product_template(line.product_template_id, group,
                                                              line.product_template_id.public_categ_ids.ids)

                    product_tmpl_weight_list.append(
                        {
                            'product_template_id': line.product_template_id.id,
                            'weight': product_tmpl_val['weight']
                        }
                    )

                    val = {
                        'product_template_id':line.product_template_id.id,
                        'product_template_name':line.product_template_id.name,
                        'product_template_available_qty': line.product_template_id.qty_available,
                        'product_template_weight':product_tmpl_val['weight'],
                        'product_template_petha_dec':line.product_template_id.petha_dec,
                        'product_template_yway_dec': line.product_template_id.yway_dec,
                        'product_template_size': line.product_template_id.length,
                        'product_template_description': str(line.product_template_id.product_description) if line.product_template_id.product_description else '',
                        'product_template_jewellery_type':
                            {
                               'id': line.product_template_id.gold_quality.id if line.product_template_id.gold_quality else " ",
                               'name':line.product_template_id.gold_quality.name if line.product_template_id.gold_quality.name else " ",
                            },
                        'product_template_category': product_tmpl_val['category'],
                        'product_template_sale_price': product_tmpl_val['sale_price'],
                        'product_template_cost_price': 0,
                        'product_template_deals_offer_name': product_tmpl_val['deals_offer_name'],#deal_offer.get('deals_offer_name') if deal_offer.get(
                        'product_template_discount_type': product_tmpl_val['discount_type'],#deal_offer.get('discount_type') if deal_offer.get('discount_type') else None,
                        'product_template_discount_value': product_tmpl_val['discount_value'],#deal_offer.get('discount_value') if deal_offer.get('discount_value') else 0.00,
                        'product_template_discounted_price': product_tmpl_val['discounted_price'],
                        'colour':product_tmpl_val['colour'],
                        'gender':product_tmpl_val['gender'],
                        'product_template_bundle_lines':product_tmpl_val['bundle_lines'],
                        'product_template_images': product_tmpl_val['images_url'],
                        'product_template_slider_img_urls':product_tmpl_val['slider_img_urls'],
                    }

                    product_tmpl_list.append(val)

            #shop info
            shop_t_c = cleanhtml(group.shop_id.shop_t_c)

            shop_logo_url = None
            if group.shop_id.shop_logo:
                shop_logo_url = get_images_url(group.shop_id, seller_shop_image[0], seller_shop_image[1])
            else:
                shop_logo_url = default_url

            similar_product_group = request.env['product.group'].sudo().search([('display_product_category_id','=',group.display_product_category_id.id)])
            similar_product_group_list = []
            if similar_product_group:
                for similar_group in similar_product_group:

                    similar_product_val = get_detail_product_template(
                        similar_group.display_product_tmpl_id, similar_group, similar_group.display_product_tmpl_id.public_categ_ids.ids)

                    val = {
                        'group_id': similar_group.id,
                        'group_name': similar_group.name,
                        'product_template_id': similar_group.display_product_tmpl_id.id,
                        'product_template_name': similar_group.display_product_tmpl_id.name,
                        'sale_price': similar_product_val['sale_price'],#similar_sale_price,#similar_group.display_product_tmpl_id.list_price,
                        'cost_price': 0,
                        'deals_offer_name': similar_product_val['deals_offer_name'],#similar_deals_offer_name,#similar_product_group_deal_offer.get('deals_offer_name') if similar_product_group_deal_offer.get(
                        'discount_type': similar_product_val['discount_type'],#similar_discount_type,#similar_product_group_deal_offer.get('discount_type') if similar_product_group_deal_offer.get('discount_type') else None,
                        'discount_value': similar_product_val['discount_value'],#similar_discount_value,#similar_product_group_deal_offer.get('discount_value') if similar_product_group_deal_offer.get(
                        'discounted_price': similar_product_val['discounted_price'],#similar_discounted_price,#similar_product_group_deal_offer.get('discounted_price') if similar_product_group_deal_offer.get(
                        'image':similar_product_val['images_url'],#similar_product_image_url,
                        'shop_id':similar_group.shop_id.id,

                    }
                    similar_product_group_list.append(val)

            # related product(product group with same shop)
            related_product_group = request.env['product.group'].sudo().search([('shop_id', '=', group.shop_id.id)])
            related_product_group_list = []
            if related_product_group:
                for related_group in related_product_group:

                    related_product_val = get_detail_product_template(
                        related_group.display_product_tmpl_id, related_group,
                        related_group.display_product_tmpl_id.public_categ_ids.ids)

                    val = {
                        'group_id': related_group.id,
                        'group_name': related_group.name,
                        'product_template_id': related_group.display_product_tmpl_id.id,
                        'product_template_name': related_group.display_product_tmpl_id.name,
                        'sale_price': related_product_val['sale_price'],
                        'cost_price': 0,
                        'deals_offer_name':related_product_val['deals_offer_name'] ,
                        'discount_type': related_product_val['discount_type'],
                        'discount_value': related_product_val['discount_value'],
                        'discounted_price': related_product_val['discounted_price'],
                        'image': related_product_val['images_url'],
                        'shop_id': related_group.shop_id.id,

                    }
                    related_product_group_list.append(val)

            val = {
                'id': group.id,
                'name': group.name,
                'priority':priority,
                'occurance':group.occurance,
                'display_product_id':group.display_product_tmpl_id.id,

                'images':[{
                    'display_product_image_url':"/api/image/product.template/" + str(group.display_product_tmpl_id.id) + "/image_1920/",
                    'type':"product.template",
                }]

            }
            item_list.append(val)

        sorted_item_list = item_list.sort(key=lambda a: (a['priority'], a['occurance']))


        total_items = len(item_list)
        result = {
            'status': 'SUCCESS',
            'message': 'Product Detail',

                'product_name': group.display_product_tmpl_id.name,
                'available_qty': group.display_product_tmpl_id.qty_available,
                'weight':display_product_val['weight'],
                'petha_dec':group.display_product_tmpl_id.petha_dec,#display_product_petha_dec,
                'yway_dec':group.display_product_tmpl_id.yway_dec,#display_product_yway_dec,
                'size': group.display_product_tmpl_id.length,
                'description':str(group.display_product_tmpl_id.product_description) if group.display_product_tmpl_id.product_description else '',
                'jewellery_type': {
                    'id':group.display_product_tmpl_id.gold_quality.id if group.display_product_tmpl_id.gold_quality else " ",
                    'name': group.display_product_tmpl_id.gold_quality.name if group.display_product_tmpl_id.gold_quality else " "
                },
                'category': display_product_val['category'],#category[0] if category else None,
                'sale_price':display_product_val['sale_price'],#: display_product_sale_price,
                'cost_price': 0,
                'deals_offer_name':display_product_val['deals_offer_name'],#display_product_deals_offer_name, #deal_offer.get('deals_offer_name') if deal_offer.get('deals_offer_name') else None,
                'discount_type': display_product_val['discount_type'],#display_product_discount_type,#deal_offer.get('discount_type') if deal_offer.get('discount_type') else None,
                'discount_value': display_product_val['discount_value'],#display_product_discount_value,#deal_offer.get('discount_value') if deal_offer.get('discount_value') else 0.00,
                'discounted_price': display_product_val['discounted_price'],#display_product_discounted_price,#deal_offer.get('discounted_price') if deal_offer.get('discount_value') else 0.00,
                'gender': display_product_val['gender'],#display_product_attr_gender if display_product_attr_gender else None,
                'colour':display_product_val['colour'],#display_product_attr_colour if display_product_attr_colour else None,
                'bundle_lines':display_product_val['bundle_lines'],#bundle_line,
                'display_product_image_url': display_product_val['images_url'],#display_product_image_url,
                'slider_image_urls':display_product_val['slider_img_urls'],#slider_img_urls,
                'product_tmpls': product_tmpl_list,
                'similar_product_group_list': similar_product_group_list,
                'related_product_group_list': related_product_group_list,
                'product_tmpl_weight_list': product_tmpl_weight_list,
                'shop_info':
                    {
                    'shop_id':group.shop_id.id,
                    'shop_name':group.shop_id.name,
                    'shop_logo':shop_logo_url,
                    'terms_conditions':shop_t_c,
                }

            }

        if val:
            total_items = len(group)
        else:
            total_items = 0

        result = {
            'status': 'SUCCESS',
            'message': 'Product Detail',

            'paginate_info': {
                'limit': limit,
                'current_page': page,
                'total_items': total_items,
                'total_pages': math.ceil(total_items / limit),
            },

            'item_info': {
                'prod_image_url_base': image_url,
                'shop_image_url_base': image_url
            },
            'items': item_list,

            'item_detail': val,

        }

        return result

    @http.route(['/detail/product-template'], type='json', auth='public', method=['POST'])
    def get_product_template_detail(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        product_template_id = kwargs['product_template_id'] if kwargs.get('product_template_id') else None
        group_id = kwargs['group_id'] if kwargs.get('group_id') else None
        shop_id = kwargs['shop_id'] if kwargs.get('shop_id') else None

        product_template = request.env['product.template'].sudo().search([('id','=',product_template_id)])
        # weight = str(product_template.kyat) + " ကျပ် " + str(product_template.petha) + " ပဲ " + str(product_template.yway) + " ရွေး"
        kyats, petha_var, yway_var, petha_dec_var, yway_dec_var = _calculate_gold_weight(product_template)
        weight = str(kyats) + " ကျပ် " + str(petha_var+petha_dec_var) + " ပဲ " + str(yway_var+yway_dec_var) + " ရွေး"

        # calculate deals & offer of product group
        group = request.env['product.group'].sudo().search([('id', '=', group_id)])

        sale_price = discounted_price = 0
        discount_type = discount_value= deals_offer_name = None
        if group:
            sale_price, discounted_price, discount_type, discount_value,\
            deals_offer_name ,total_qty_kyat,total_qty_gram,sale_price_unit= calculate_kpy(product_template,1,group,None)

        # image_url = _get_product_image_url(product_template)
        image_url = None
        if product_template.image_1920:
            image_url = get_images_url(product_template,product_template_image[0],product_template_image[1])
        else:
            image_url = default_url

        result = {
            'message': 'Product Template Detail',
            'items': {
                'id':product_template.id,
                'name':product_template.name,
                'weight':weight,
                'sale_price':sale_price,
                'discounted_price':discounted_price,
                'image_url':image_url,
                'shop_id':shop_id,
            },
        }

        return result

    @http.route(['/list/product-set'], type='json', auth='public',method=['POST'])
    def get_product_set_list(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()

        # filter parameters
        filters = [('active', '=', True)]

        default_sort = "priority asc,occurance asc"
        items = request.env['product.set'].sudo().search(filters, order=default_sort, limit=limit, offset=offset)
        # print('items',items)
        # update occurrance count
        if items:
            request.cr.execute("""
                                update product_set set occurance=occurance+1
                                 where id in %s
                            """, [tuple(items.ids)])

        item_list = []
        for product_set in items:
            #product set image url
            # product_set_image_url = _get_product_set_image_url(product_set)
            product_set_image_url = get_images_url(product_set,product_set_image[0],product_template_image[1])

            # category = _get_category(product_set.public_categ_ids)

            category = request.env['product.public.category'].sudo().search_read([('id', 'in', product_set.public_categ_ids.ids)],
                                                                                 fields=['id', 'name'], limit=1)

            # product_group_list=[]
            # for set_line in product_set.set_line:
            #     #product group line
            #     # product template line
            #     product_tmpl_list = []
            #
            #     if set_line.product_group_id.group_line:
            #         # product template list in product group
            #         for group_line in set_line.product_group_id.group_line:
            #             # category
            #             # line_category = _get_category(line.product_template_id.public_categ_ids)
            #             line_category = request.env['product.public.category'].sudo().search_read(
            #                 [('id', 'in', group_line.product_template_id.public_categ_ids.ids)],
            #                 fields=['id', 'name'], limit=1)
            #
            #             group_line_product_image_url = _get_product_image_url(group_line.product_template_id)
            #
            #             # calculate gorup's product template's weight(kyats,petha, yawy) and add to weight list to show in weight selection box in front end view
            #             weight = str(group_line.product_template_id.kyat) + " ကျပ် " + \
            #                      str(group_line.product_template_id.petha) + " ပဲ " + \
            #                      str(group_line.product_template_id.yway) + " ရွေး"
            #             image_url = _get_product_image_url(group_line.product_template_id)
            #
            #             sale_price, discounted_price, discount_type, discount_value, deals_offer_name = calculate_kpy(
            #                 set_line.product_group_id, group_line.product_template_id)
            #
            #             val = {
            #                 'product_template_id': group_line.product_template_id.id,
            #                 'product_template_name': group_line.product_template_id.name,
            #                 'product_template_sale_price': sale_price,#line.product_template_id.list_price,
            #                 'product_template_cost_price': 0,#line.product_template_id.standard_price,
            #                 'product_template_available_qty': group_line.product_template_id.qty_available,
            #                 'product_template_weight': weight,
            #                 'product_template_size': group_line.product_template_id.length,
            #                 'product_template_description': str(
            #                     group_line.product_template_id.product_description) if group_line.product_template_id.product_description else '',
            #                 'product_template_jewellery_type':
            #                     {
            #                         'id': group_line.product_template_id.gold_quality if group_line.product_template_id.gold_quality else " ",
            #                         'name': group_line.product_template_id.gold_quality.name if group_line.product_template_id.gold_quality.name else " ",
            #                     },
            #                 'product_template_category': line_category,
            #                 'product_template_image_url': group_line_product_image_url,
            #                 'product_template_image_url':image_url,
            #             }
            #             product_tmpl_list.append(val)
            #
            #     product_image_url=_get_product_image_url(set_line.product_group_id.display_product_tmpl_id)
            #
            #
            #     group_val = {
            #         'id': set_line.product_group_id.id,
            #         'name': set_line.product_group_id.name,
            #         'plan_priority': set_line.product_group_id.sub_plan_id.level,
            #         'occurance': set_line.product_group_id.occurance,
            #         'sale_price': set_line.product_group_id.list_price,
            #         'display_product_id': {
            #             'id': set_line.product_group_id.display_product_tmpl_id.id,
            #             'name': set_line.product_group_id.display_product_tmpl_id.name,
            #             'sale_price': set_line.product_group_id.display_product_tmpl_id.list_price,  # sale
            #             'cost_price': set_line.product_group_id.display_product_tmpl_id.standard_price,  # standard price/ cost
            #             'image_url': product_image_url,
            #         },
            #         'product_tmpl_list':product_tmpl_list,
            #
            #     }
            #     product_group_list.append(group_val)

            val={
                'id':product_set.id,
                'name':product_set.name,
                'description':product_set.description,
                'sale_price':product_set.sale_price,
                'discounted_price': product_set.discounted_price,
                'category':category[0] if category else None,
                'image':product_set_image_url,
                'currency_id': {
                    'id': request.env.company.currency_id.id,
                    'symbol': request.env.company.currency_id.symbol,  # pricelist_id.product_tmpl_id.uom_id.name,
                    'decimal_places': request.env.company.currency_id.decimal_places,
                    'rounding': request.env.company.currency_id.rounding,
                    'position': request.env.company.currency_id.position,
                },
                # 'product_group_list':product_group_list
            }
            item_list.append(val)

        return item_list

    @http.route(['/detail/product-set'], type='json', auth='public',method=['POST'])
    def get_product_set_detail(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        product_set_id = kwargs['product_set_id'] if kwargs.get('product_set_id') else None
        # filter parameters
        filters = [('active', '=', True)]

        if product_set_id:
            filters.append(('id','=',product_set_id))


        default_sort = "priority asc,occurance asc"
        product_set = request.env['product.set'].sudo().search(filters, order=default_sort, limit=1, offset=offset)


        item_list = []
        val = None
        # logo url
        # image_url = _get_product_set_image_url(product_set)
        image_url = get_images_url(product_set,product_set_image[0],product_set_image[1])

        product_group_list=[]
        if product_set:
            for set_line in product_set.set_line:
                #product template of a group
                # product template line
                product_tmpl_list = []
                product_tmpl_weight_list = []
                if set_line.product_group_id.group_line:
                    # product template list in product group
                    for group_line in set_line.product_group_id.group_line:
                        # category
                        # line_category = _get_category(group_line.product_template_id.public_categ_ids)
                        # line_category = request.env['product.public.category'].sudo().search_read(
                        #     [('id', 'in', product_set.public_categ_ids.ids)],
                        #     fields=['id', 'name'], limit=1)
                        #
                        # # attribute line value
                        # # line_attribute = _get_attribute_lines(group_line.product_template_id)
                        # gender = _get_attribute_lines(group_line.product_template_id,'Gender')
                        # colour = _get_attribute_lines(group_line.product_template_id, 'Colour')
                        #
                        # # bundle info
                        # line_bundle = _get_bundle_line(group_line.product_template_id)
                        #
                        # # group_line_product_image_url = _get_product_image_url(group_line.product_template_id)
                        # group_line_product_image_url = None
                        # if group_line.product_template_id.image_1920:
                        #     group_line_product_image_url = get_images_url(group_line.product_template_id,product_template_image[0],product_set_image[1])
                        # else:
                        #     group_line_product_image_url = default_url
                        #
                        # # calculate gorup's product template's weight(kyats,petha, yawy) and add to weight list to show in weight selection box in front end view
                        # # weight = str(group_line.product_template_id.kyat) + " ကျပ် " + str(
                        # #     group_line.product_template_id.petha) + " ပဲ " + \
                        # #          str(group_line.product_template_id.yway) + " ရွေး"
                        # kyats, petha_var, yway_var, petha_dec_var, yway_dec_var = _calculate_gold_weight(group_line.product_template_id)
                        # weight = str(kyats) + " ကျပ် " + str(petha_var+petha_dec_var) + " ပဲ " + str(yway_var+yway_dec_var) + " ရွေး"
                        #
                        # product_tmpl_weight_list.append(
                        #     {
                        #         'product_template_id': group_line.product_template_id.id,
                        #         'weight': weight
                        #     }
                        # )

                        product_tmpl_val = get_detail_product_template(group_line.product_template_id, group_line.group_id,
                                                          group_line.product_template_id.public_categ_ids.ids)

                        val = {
                            'product_template_id': group_line.product_template_id.id,
                            'product_template_name': group_line.product_template_id.name,
                            'product_template_sale_price': product_tmpl_val['sale_price'],
                            'product_template_cost_price': 0,
                            'product_template_available_qty': group_line.product_template_id.qty_available,
                            'product_template_weight': product_tmpl_val['weight'],
                            'product_template_petha_dec': group_line.product_template_id.petha_dec,
                            'product_template_yway_dec': group_line.product_template_id.yway_dec,
                            'product_template_size': group_line.product_template_id.length,
                            'product_template_description': str(
                                group_line.product_template_id.product_description) if group_line.product_template_id.product_description else '',
                            'product_template_jewellery_type':
                                {
                                    'id': group_line.product_template_id.gold_quality.id if group_line.product_template_id.gold_quality else " ",
                                    'name': group_line.product_template_id.gold_quality.name if group_line.product_template_id.gold_quality.name else " ",
                                },
                            # 'product_template_attribute_lines': line_attribute,
                            'gender':product_tmpl_val['gender'],
                            'colour':product_tmpl_val['colour'],
                            'product_template_bundle_lines': product_tmpl_val['bundle_lines'],
                            'product_template_images': [
                                {
                                    # 'product_template_product_image_url': group_line_product_image_url,
                                    'image_url': product_tmpl_val['images_url'],
                                    'type': "product.template",
                                }
                            ]
                        }

                        product_tmpl_list.append(val)

                # weight of product
                # display_product_weight = str(set_line.product_group_id.display_product_tmpl_id.kyat) + " ကျပ် " + str(
                #     set_line.product_group_id.display_product_tmpl_id.petha) + " ပဲ " + str(set_line.product_group_id.display_product_tmpl_id.yway) + " ရွေး"
                kyats, petha_var, yway_var, petha_dec_var, yway_dec_var = _calculate_gold_weight(set_line.product_group_id.display_product_tmpl_id)
                display_product_weight = str(kyats) + " ကျပ် " + str(petha_var+petha_dec_var) + " ပဲ " + str(yway_var+yway_dec_var) + " ရွေး"

                group_display_product_val = get_detail_product_template(set_line.product_group_id.display_product_tmpl_id, set_line.product_group_id,
                                                               set_line.product_group_id.display_product_tmpl_id.public_categ_ids.ids)

                group_val = {
                    'id': set_line.product_group_id.id,
                    'name': set_line.product_group_id.name,
                    'plan_priority': set_line.product_group_id.sub_plan_id.level,
                    'occurance': set_line.product_group_id.occurance,
                    'sale_price': group_display_product_val['sale_price'],
                    'discounted_price': group_display_product_val['sale_price'],
                    'display_product_id': {
                        'id': set_line.product_group_id.display_product_tmpl_id.id,
                        'name': set_line.product_group_id.display_product_tmpl_id.name,
                        'sale_price': group_display_product_val['sale_price'],  # sale
                        'cost_price': 0,#set_line.product_group_id.display_product_tmpl_id.standard_price,  # standard price/ cost
                        'weight': group_display_product_val['weight'],
                        'petha_dec':set_line.product_group_id.display_product_tmpl_id.petha_dec,
                        'yway_dec':set_line.product_group_id.display_product_tmpl_id.yway_dec,
                        'size': set_line.product_group_id.display_product_tmpl_id.length,
                    },
                    'product_tmpl_list':product_tmpl_list,
                    'currency_id': {
                        'id': request.env.company.currency_id.id,
                        'symbol': request.env.company.currency_id.symbol,  # pricelist_id.product_tmpl_id.uom_id.name,
                        'decimal_places': request.env.company.currency_id.decimal_places,
                        'rounding': request.env.company.currency_id.rounding,
                        'position': request.env.company.currency_id.position,
                    },

                }
                product_group_list.append(group_val)


            # shop information
            # logo url
            # shop_logo_url = _get_shop_logo_url(product_set.shop_id)
            # shop_logo_url = get_images_url(product_set.shop_id,'seller.shop','shop_logo')

            shop_logo_url = None
            if product_set.shop_id.shop_logo:
                shop_logo_url = get_images_url(product_set.shop_id, seller_shop_image[0], seller_shop_image[1])
            else:
                shop_logo_url = default_url


            #shop terms & condition
            shop_t_c = cleanhtml(product_set.shop_id.shop_t_c)

            #category
            # set_category = _get_category(product_set.public_categ_ids)
            set_category = request.env['product.public.category'].sudo().search_read(
                [('id', 'in', product_set.public_categ_ids.ids)],
                fields=['id', 'name'], limit=1)

            #related product set(filter product set by shop id)
            related_product_set = request.env['product.set'].sudo().search(
                [('active', '=', True), ('shop_id', '=', product_set.shop_id.id)],
                order=default_sort, limit=limit, offset=offset)

            # related_product_group = request.env['product.group'].sudo().search([('shop_id', '=', group.shop_id.id)])
            related_product_set_list = []
            if related_product_set:
                for related_set in related_product_set:
                    # related_product_set_image_url = _get_product_set_image_url(related_set)
                    related_product_set_image_url = get_images_url(related_set,product_set_image[0],product_set_image[1])


                    discounted_value = 0
                    if related_set.compute_price == 'percentate':
                        discounted_value = related_set.percent_price
                    elif related_set.compute_price == 'fixed':
                        discounted_value = related_set.fixed_price


                    val = {
                        'id': related_set.id,
                        'name': related_set.name,
                        # 'product_template_id': related_group.display_product_tmpl_id.id,
                        # 'product_template_name': related_group.display_product_tmpl_id.name,
                        'sale_price': related_set.sale_price,
                        'cost_price': related_set.cost_price,
                        # 'deals_offer_name': related_set.compute_price,
                        'discount_type': related_set.compute_price,
                        'discount_value': discounted_value,
                        'discounted_price': related_set.discounted_price if related_set.discounted_price else 0.00,
                        'image': related_product_set_image_url,

                    }
                    related_product_set_list.append(val)

            # similar product set(filter product set by shop id)
            similar_product_set = request.env['product.set'].sudo().search([('active', '=', True),('public_categ_ids', 'in', product_set.public_categ_ids.ids)],order=default_sort, limit=limit, offset=offset)

            # print('similar_product_set',similar_product_set)
            # related_product_group = request.env['product.group'].sudo().search([('shop_id', '=', group.shop_id.id)])
            similar_product_set_list = []
            if similar_product_set:
                for similar_set in similar_product_set:
                    # similar_product_set_image_url = _get_product_set_image_url(similar_set)
                    similar_product_set_image_url = get_images_url(similar_set, product_set_image[0],product_set_image[1])

                    discounted_value = 0
                    if similar_set.compute_price == 'percentate':
                        discounted_value = similar_set.percent_price
                    elif similar_set.compute_price == 'fixed':
                        discounted_value = similar_set.fixed_price

                    val = {
                        'id': similar_set.id,
                        'name': similar_set.name,
                        # 'product_template_id': related_group.display_product_tmpl_id.id,
                        # 'product_template_name': related_group.display_product_tmpl_id.name,
                        'sale_price': similar_set.sale_price,
                        'cost_price': similar_set.cost_price,
                        # 'deals_offer_name': related_set.compute_price,
                        'discount_type': similar_set.compute_price,
                        'discount_value': discounted_value,
                        'discounted_price': similar_set.discounted_price if similar_set.discounted_price else 0.00,
                        'image': similar_product_set_image_url,

                    }
                    similar_product_set_list.append(val)

            # print('similar_product_set_list',similar_product_set_list)

            val={
                'id':product_set.id,
                'name':product_set.name,
                'description':product_set.description,
                'sale_price':product_set.sale_price,
                'discounted_price': product_set.discounted_price,
                'category':set_category[0] if set_category else None,
                'image':image_url,
                'product_group_list':product_group_list,
                'similar_product_set': similar_product_set_list,
                'related_product_set': related_product_set_list,
                'shop_info': {
                    'shop_id': product_set.shop_id.id,
                    'shop_name': product_set.shop_id.name,
                    'shop_logo': shop_logo_url,
                    'terms_conditions': shop_t_c,
                },
                'currency_id': {
                    'id': request.env.company.currency_id.id,
                    'symbol': request.env.company.currency_id.symbol,  # pricelist_id.product_tmpl_id.uom_id.name,
                    'decimal_places': request.env.company.currency_id.decimal_places,
                    'rounding': request.env.company.currency_id.rounding,
                    'position': request.env.company.currency_id.position,
                },
            }

        if val:
            total_items = len(val)
        else:
            total_items = 0

        result = {
            'status': 'SUCCESS',
            'message': 'Product Set Detail',
            'paginate_info': {
                'limit': limit,
                'current_page': page,
                'total_items': total_items,
                'total_pages': math.ceil(total_items / limit),
            },
            'item_detail': val,


        }

        return result

    @http.route(['/list/deals'], type='json', auth='public', method=['POST'])
    def get_website_deals(self, **kwargs):
        # limit = int(kwargs['limit']) if 'limit' in kwargs else 12
        # page = int(kwargs['page']) if 'page' in kwargs else 1
        # order = kwargs['order'] if 'order' in kwargs else 'name ASC'
        # offset = (page - 1) * limit

        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()
        date = kwargs['date'] if 'date' in kwargs else None
        model_name = 'website.deals'
        image_url = '/web/image?model=' + model_name + '&id='

        website = request.env['website'].get_default_website()

        filters = []
        filters = [('state','=','validated')]
        filters = [('state','=','validated')]
        if date:
            filters.append(('start_date','<=',date))
            filters.append(('end_date','>=',date))
        if website:
            filters.append(('deal_pricelist','=',website.webclient_pricelist_id.id))

        fields = ['id','name', 'marketplace_seller_id']
        website_deals = request.env[model_name].search(filters, order='level desc,occurance asc')
        # website_deals = request.env[model_name].sudo().search_read(filters, fields=fields,limit=limit, offset=offset, order='')


        deals_list = []
        if website_deals:
            for deal in website_deals:
                partner = shop = None
                seller_shop_id = None
                if deal.marketplace_seller_id:
                    partner = request.env['res.partner'].sudo().search([('id','=',deal.marketplace_seller_id.id)])
                    if partner.seller_shop_id:
                        shop = partner.seller_shop_id.name
                        seller_shop_id = partner.seller_shop_id
                    else:
                        shop = None
                        seller_shop_id = None
                val ={
                    'id':deal.id,
                    'title': deal.name,
                    'deal_shop_sub_plan_priority': seller_shop_id.level if seller_shop_id else 0,
                    'deal_shop_sub_plan_occurance':deal.occurance if deal.occurance else 0,
                    'shop':shop if shop else None,
                }
                deals_list.append(val)

        total_website_deals = len(deals_list)
        sorted_item_list = deals_list.sort(key=lambda a: (a['deal_shop_sub_plan_priority'], a['deal_shop_sub_plan_occurance']), reverse=True)
        paginations = set_paginations(page, limit, total_website_deals)

        result = {
            'status': 'SUCCESS',
            'message': 'Deals & Offer List',

            'paginate_info': {
                'limit': limit,
                'current_page': page,
                'total_items': total_website_deals,
                'total_pages': math.ceil(total_website_deals / limit),
            },
            'item_info': {
                'deal_banner_url': "/api/image/website.deals/{id}/banner/",
                'deal_banner_url': "/web/image/website.deals/{id}/banner/",
                'deal_banner_url': "/web/image/website.deals/{id}/banner/",
            },
            'items': deals_list,
        }

        return result


    @http.route(['/sst_product/create'], type='json', auth='public', methods=['GET'])
    def get_shops_basic(self, **kwargs):
        limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()

        order = kwargs['order'] if 'order' in kwargs else 'name ASC'


        return limit

    # @http.route(['/list/product-collections'], type='json', auth='public',method=['POST'])
    # def get_product_collection(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     offset = (page - 1) * limit
    #
    #     filter = [('is_active', '=', True)]
    #     # if slug == 'hot-items':
    #     #     filter += [('slug', '=', 'hot-items')]
    #     # if slug == 'new-products':
    #     #     filter += [('slug', '=', 'new-products')]
    #     # if slug == 'most-viewed':
    #     #     filter += [('slug', '=', 'most-viewed')]
    #     # if slug == 'best-sellers':
    #     #     filter += [('slug', '=', 'best-sellers')]
    #
    #     product_collections = request.env['product.public.collection'].sudo().search_read(filter)
    #     if not product_collections:
    #         return {"status": False, "message": "Product collection does not exists."}
    #     else:
    #         for collection in product_collections:
    #             products = request.env['product.template'].sudo().search_read(
    #                 [('id', 'in', collection['product_tmpl_ids']), ('is_published', '=', True)],
    #                 fields=prod_basic_fields)
    #
    #             total_products = len(products)
    #             paginations = set_paginations(page, limit, total_products)
    #             products = products = request.env['product.template'].sudo().search_read(
    #                 [('id', 'in', collection['product_tmpl_ids']), ('is_published', '=', True)],
    #                 fields=prod_basic_fields, limit=limit, offset=offset, order=order)
    #
    #             response_context = {'items': products, 'paginations': paginations}
    #             return response_context

    # @http.route(['/list/categories'], type='json', auth='public',methods=['GET'])
    # def get_categories(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     offset = (page - 1) * limit
    #     product_categories = request.env['product.public.category'].sudo().search_read([], limit=limit)

    #     return {'items': product_categories}

    # @http.route(['/list/shops'], type='json', auth='public',methods=['GET'])
    # def get_seller_shops(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     offset = (page - 1) * limit

    #     shops = request.env['seller.shop'].sudo().search_read([])
    #     total_shops = len(shops)
    #     paginations = set_paginations(page, limit, total_shops)

    #     return {'items': shops, 'paginations': paginations}


    #seller controller
    # @http.route(['/shop/basic'], type='json', auth='public', methods=['GET'])
    # def get_shops_basic(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     shop_id = kwargs['shop_id'] if 'shop_id' in kwargs else 0
    #     offset = (page - 1) * limit
    #
    #     shops = request.env['seller.shop'].sudo().search_read([('id', '=', shop_id)])
    #     total_shops = len(shops)
    #     paginations = set_paginations(page, limit, total_shops)
    #     state = request.env['res.country.state'].sudo().search([('id', '=', shops[0]['state_id'])])
    #     country = request.env['res.country'].sudo().search([('id', '=', shops[0]['country_id'])])
    #
    #     return {
    #         'name': shops[0]['name'],
    #         'url': shops[0]['url'],
    #         'fb_url': shops[0]['fb_url'],
    #         'tt_url': shops[0]['tt_url'],
    #         'inst_url': shops[0]['inst_url'],
    #         'shop_banner': shops[0]['shop_banner'],
    #         'street': shops[0]['street'],
    #         'street2': shops[0]['street2'],
    #         'city': shops[0]['city'],
    #         'state': state.name if state else None,
    #         'country': country.name if country else None,
    #         'phone': shops[0]['phone'],
    #         'shop_mobile': shops[0]['shop_mobile'],
    #         'email': shops[0]['email'],
    #     }

    # @http.route(['/shop/detail'], type='json', auth='public', methods=['GET'])
    # def get_shops_detail(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     shop_id = kwargs['shop_id'] if 'shop_id' in kwargs else 0
    #     offset = (page - 1) * limit
    #
    #     shop = request.env['seller.shop'].sudo().search([('id', '=', shop_id)])
    #     branches = request.env['seller.shop.branch'].sudo().search_read([('seller_shop_id', '=', shop_id)])
    #     total_shops = len(shop)
    #     paginations = set_paginations(page, limit, total_shops)
    #
    #     return {
    #         'description': shop.name,
    #         'branches': branches,
    #     }
    #
    # @http.route(['/shop/terms-condition'], type='json', auth='public', methods=['GET'])
    # def get_shops_terms(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     shop_id = kwargs['shop_id'] if 'shop_id' in kwargs else 0
    #     offset = (page - 1) * limit
    #
    #     shop = request.env['seller.shop'].sudo().search([('id', '=', shop_id)])
    #     branches = request.env['seller.shop.branch'].sudo().search([('seller_shop_id', '=', shop_id)])
    #     terms_condition = request.env['terms.condition'].sudo().search_read(
    #         [('seller_shop_id', '=', shop_id),'|', ('branch_id', 'in', branches.ids),('branch_id', '=', None)])
    #     total_shops = len(shop)
    #     paginations = set_paginations(page, limit, total_shops)
    #
    #     return {
    #         'description': shop.name,
    #         'terms_condition': terms_condition,
    #     }
    #
    # @http.route(['/shop/reviews'], type='json', auth='public', methods=['GET'])
    # def get_shops_reviews(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     shop_id = kwargs['shop_id'] if 'shop_id' in kwargs else 0
    #     offset = (page - 1) * limit
    #
    #     shop = request.env['seller.shop'].sudo().search([('id', '=', shop_id)])
    #     review = request.env['seller.review'].sudo().search_read([('marketplace_seller_id', '=', shop.seller_id.id)])
    #     total_reviews = len(review)
    #     paginations = set_paginations(page, limit, total_reviews)
    #
    #     return {
    #         'items': review,
    #         'paginations': paginations,
    #     }
    #
    # @http.route(['/deals'], type='json', auth='public', methods=['GET'])
    # def get_deals(self, **kwargs):
    #     limit = int(kwargs['limit']) if 'limit' in kwargs else 12
    #     page = int(kwargs['page']) if 'page' in kwargs else 1
    #     order = kwargs['order'] if 'order' in kwargs else 'name ASC'
    #     shop_id = kwargs['shop_id'] if 'shop_id' in kwargs else 0
    #     # start_date = kwargs['start_date'] if 'start_date' in kwargs else None
    #     # end_date = kwargs['end_date'] if 'end_date' in kwargs else None
    #     offset = (page - 1) * limit
    #
    #     # user_tz = request.env.user.tz or pytz.utc
    #     # local = pytz.timezone(user_tz)
    #
    #     # from_date = datetime.strftime(
    #     #     pytz.utc.localize(datetime.strptime(kwargs['start_date'], DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
    #     #         local), "%Y-%m-%d %H:%M%S")
    #     # to_date = datetime.strftime(
    #     #     pytz.utc.localize(datetime.strptime(kwargs['end_date'], DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(
    #     #         local), "%Y-%m-%d %H:%M%S")
    #     start_date = datetime.strptime(kwargs['start_date'],"%Y-%m-%d %H:%M%S")
    #     end_date = datetime.strptime(kwargs['end_date'], "%Y-%m-%d %H:%M%S")
    #     print('start_date,end_date',start_date,end_date)
    #
    #     shop = request.env['seller.shop'].sudo().search([('id', '=', shop_id)])
    #     deals = None
    #     paginations = None
    #     if shop and start_date and end_date:
    #         deals = request.env['website.deals'].sudo().search([
    #             ('marketplace_seller_id', '=', shop.seller_id.id),
    #             ('start_date', '>=', start_date), ('end_date', '<=', end_date)
    #         ])
    #         if deals:
    #             total_deals = len(deals.pricelist_items.ids)
    #             paginations = set_paginations(page, limit, total_deals)
    #     pricelist_items = None
    #     if deals:
    #         pricelist_items = deals.pricelist_items
    #     return {
    #         'items': pricelist_items,
    #         'paginations': paginations,
    #     }


    @http.route(['/product/create'], type='json', auth='public', methods=['GET'])
    def create_agbs_product(self, **kwargs):
        # limit, offset, page, order = request.env['ir.api.helper'].setup_limit_offset_page_order(kwargs).values()

        product = kwargs['name'] if 'name' in kwargs else None
        if product:
            val={
                'name':product['name'],
                # 'detailed_type':product['detailed_type'],
                # 'uom_id':product['uom_id'],
                # 'uom_po_id': product['uom_po_id'],
                # 'gold_quality':product['gold_quality'],
                # 'length':product['length'],
                # 'gold_smith_name':product['gold_smith_name'],
            }
            agbs_product = request.env['product.template'].create(val)

        # result = {
        #     'status': 'Product Creation SUCCESS',
        #     'message': 'Product Createion Success',
        #     }
        print('agbs_product=>',agbs_product)
        # return agbs_product


def _prepare_search_filter(kw):
    filter_criterias = ['|', '|']
    filters = []

    if kw:
        categ_id = request.env['product.public.category'].search([('name', 'ilike', kw)])
        if categ_id:
            filter_criterias.append('|')
            filters += [('public_categ_ids', 'child_of', categ_id.ids)]

        brand_id = request.env['product.brand'].sudo().search([('name', '=ilike', kw)])
        if brand_id:
            filter_criterias.append('|')
            filters += [('brand_id', 'in', brand_id.ids)]
            # print("filters", filters)

        webclient_keyword_id = request.env['product.webclient.keyword'].search([('name', '=ilike', kw)])
        if webclient_keyword_id:
            filter_criterias.append('|')
            filters += [('webclient_keyword_ids', 'in', webclient_keyword_id.ids)]

    return filter_criterias + filters

def _calculate_deals_offer(product_group):
    product_group.ensure_one()
    # get last pricelist of display product template id
    pricelist_id = None
    if product_group:
        pricelist_id = request.env['product.pricelist.item'].sudo().search([
            ('product_group_id', '=', product_group.id),
            ('deal_applied_on', '=', 'product_group')
        ], order='id desc')

    # get discounted price of display product template of product group

    discounted_price = 0
    discount_type = None
    discount_value = None
    deals_offer_name = None

    if pricelist_id:
        website_deals = request.env['website.deals'].sudo().search(
            [('pricelist_items', 'in', pricelist_id.ids), ('state', '=', 'validated')], order='id desc')
        if website_deals:
            for deal in website_deals:
                if deal.state != 'expired':
                    for item in deal.pricelist_items:
                        if item.product_group_id.id == product_group.id:
                            if item.compute_price == 'percentage':
                                # (actual_price - (actual_price * (percent_price / 100))) or 0.0
                                # discounted_price = (item.product_group_id.display_product_tmpl_id.list_price - (
                                #                     item.product_group_id.display_product_tmpl_id.list_price * (
                                #                     item.percent_price / 100))) or 0.00
                                discount_type = item.compute_price
                                discount_value = item.percent_price
                            if item.compute_price == 'fixed':
                                # discounted_price = (item.product_group_id.display_product_tmpl_id.list_price - item.fixed_price) or 0.00
                                discount_type = item.compute_price
                                discount_value = item.fixed_price
                            # print('group,discount_type,discount_value=>', item.id, product_group.name,
                            #       discount_type, discount_value)
                        deals_offer_name = deal.name

    result={
        'deals_offer_name':deals_offer_name,
        'discount_type':discount_type,
        'discount_value':discount_value,
        'discounted_price':discounted_price,
    }
    return result#discount_type,discount_value

def _calculate_gold_weight(prod_tmpl_id):
    kyat_var = petha_var = yway_var = petha_dec_var = yway_dec_var =  kyats = 0

    if prod_tmpl_id:
        kyat = prod_tmpl_id.kyat
        petha = prod_tmpl_id.petha
        yway = prod_tmpl_id.yway
        petha_dec = prod_tmpl_id.petha_dec
        yway_dec = prod_tmpl_id.yway_dec

        if yway > 7:
            petha_var += int(yway / 8)
            yway_var += yway % 8
        if yway < 8:
            yway_var += yway
        if petha > 15:
            kyat_var += int(petha / 16)
            petha_var += petha % 16
        if petha < 16:
            petha_var += petha

        if yway_dec > 7:
            petha_dec_var += int(yway_dec / 8)
            yway_dec_var += yway_dec % 8
        if yway_dec < 8:
            yway_dec_var += yway_dec
        if petha_dec > 15:
            petha_dec_var += petha_dec % 16
        if petha_dec < 16:
            petha_dec_var += petha_dec

        kyats = kyat_var + kyat

    return kyats, petha_var, yway_var, petha_dec_var, yway_dec_var

    # total_qty_kyats = 0
    # if prod_tmpl_id:
    #     total_petha = prod_tmpl_id.petha
    #     total_yway = prod_tmpl_id.yway
    #
    #     if prod_tmpl_id.kyat:
    #         total_qty_kyats += prod_tmpl_id.kyat
    #     if prod_tmpl_id.petha:
    #         total_qty_kyats += total_petha / 16
    #     if prod_tmpl_id.yway:
    #         total_qty_kyats += total_yway / 128
    #
    # return total_qty_kyats

def _get_category(public_categ_ids):
    category = None
    if public_categ_ids:
        for categ in public_categ_ids:
            if not category:
                category = categ.name
            else:
                category = category +','+ categ.name

    return category

def _get_attribute_lines(prod_tmpl_id,attribute_name):
    attr_lines = []
    attr_val = None
    for line in prod_tmpl_id.attribute_line_ids:
        if attribute_name in line.attribute_id.display_name:
            for val in line.product_template_value_ids:
                if not attr_val:
                    attr_val = {
                        'id': val.id,
                        'name': val.name,
                    }
    return attr_val

def _get_bundle_line(prod_tmpl_id):
    bundle_lines = []
    for line in prod_tmpl_id.sh_bundle_product_ids:
        bundle_lines.append({
            'bundle_product_id': line.sh_product_id.id,
            'bundle_product_name': line.sh_product_id.name,
            'bundle_proudct_kyats': line.kyats,
            'bundle_proudct_petha': line.petha,
            'bundle_proudct_yway': line.yway,
            'bundle_proudct_total_gram': line.total_gram,
        })

    return bundle_lines

def _get_related_attribute_lines(prod_tmpl_id,search_filters):
    attr_lines = []
    for line in prod_tmpl_id.attribute_line_ids:
        attr_vals = []
        for val in line.product_template_value_ids:
            if search_filters:
                for filter in search_filters:
                    if filter['key']=='gender':
                        if filter['value'] == val.name:
                            attr_vals.append({
                                'id': val.id,
                                'name': val.name,
                                'html_color': val.html_color if val.html_color else None,
                                'price_extra': val.price_extra,
                                'display_name': line.attribute_id.display_name,
                                'display_type': line.attribute_id.display_type,
                            })
            else:
                attr_vals.append({
                    'id': val.id,
                    'name': val.name,
                    'html_color': val.html_color if val.html_color else None,
                    'price_extra': val.price_extra,
                    'display_name': line.attribute_id.display_name,
                    'display_type': line.attribute_id.display_type,
                })

        if attr_vals:
            attr_lines.append({
                'id': line.id,
                'display_name': line.attribute_id.display_name,
                'display_type': line.attribute_id.display_type,
                'variant_count': line.value_count,
                'values': attr_vals
            })
    return attr_lines


def set_paginations(page, limit, total):
    total_items = total
    related_range = 1
    current_page = page if page > 0 else 1
    total_pages = ceil(float(total_items / limit))
    first_page = 1
    last_page = total_pages if total_pages > 0 else 1
    related_first_page = current_page - related_range if current_page - related_range >= first_page else first_page
    related_last_page = current_page + related_range if current_page + related_range <= last_page else last_page
    pages_to_show = list(range(related_first_page, related_last_page + 1))

    paginations = {
        'total_items': total_items,
        'related_range': related_range,
        'current_page': current_page,
        'total_pages': total_pages,
        'first_page': first_page,
        'last_page': last_page,
        'related_first_page': related_first_page,
        'related_last_page': related_last_page,
        'prev_page': current_page - 1 if current_page > 1 else 1,
        'next_page': current_page + 1 if current_page < last_page else last_page,
        'pages_to_show': pages_to_show
    }

    return paginations


def _get_product_slider_image_url(product_template):
    slider_img_lst = []
    if product_template.product_template_image_ids:
        for product_image in product_template.product_template_image_ids:
            if product_image.image_1920:
                image_url = remove_host_url + "web/image/product.image/" + str(
                    product_image.id) + "/image_1920/"
            else:
                image_url = remove_host_url + "webclient/static/default_img/"+default_image_shop

            slider_img_lst.append(image_url)
    return slider_img_lst



    product_set_image_url = None
    if product_template.image_1920:
        product_set_image_url = remove_host_url + "web/image/product.template/" + str(
            product_template.id) + "/image_1920/"
    else:
        product_set_image_url = remove_host_url + "webclient/static/default_img/"+default_image_shop

    return product_set_image_url

def cleanhtml(raw_html):
  # print('raw_html',raw_html)
  cleantext = re.sub(CLEANR, '', raw_html)
  return cleantext

def get_images_url(model,model_name,image_field_name):
    url = None
    url = remove_host_url + "web/image/"+ model_name+"/"+ str(model.id) +"/"+ image_field_name+"/"

    return url

def calculate_kpy(product_template,qty,group,product_set):
    kyat_var = petha_var = yway_var = petha_dec_var = yway_dec_var = 0
    total_qty_kyat = 0
    price_unit = product_qty = 0
    total_petha = product_template.petha + product_template.petha_dec
    total_yway = product_template.yway + product_template.yway_dec
    discount_percent = discount_fix = discounted_price = sale_unit = 0
    # print('product.kyat,product.petha,product.yway=>',product.kyat,product.petha,product.yway)
    if product_template.kyat:
        total_qty_kyat += product_template.kyat
    if total_petha:
        total_qty_kyat += total_petha / 16
    if total_yway:
        total_qty_kyat += total_yway / 128

    ratio = list(filter(lambda uom: uom.id == product_template.uom_id.id, product_template.uom_id.category_id.uom_ids))
    # total_qty_gram = round(total_qty_kyat/16.606,6)
    total_qty_gram = qty * round(total_qty_kyat * list(
        filter(lambda uom: uom.id == product_template.uom_id.id,
               product_template.uom_id.category_id.uom_ids))[0].ratio, 6)

    # gold sale price gram by shop
    gold_price = request.env['gold.update.price'].sudo().search(
        [('gold_quality', '=', product_template.gold_quality.id),
         ('date', '<=', datetime.today()),
         ('date', '>=', datetime.today()),
         ('seller_shop_id', '=', group.shop_id.id)], order="date DESC", limit=1)
    if not gold_price:
        gold_price = request.env['gold.update.price'].sudo().search(
            [('gold_quality', '=', product_template.gold_quality.id),
             ('seller_shop_id', '=', group.shop_id.id)],
            order="date DESC", limit=1)

    sale_price_unit = discounted_price = sale_price =  0
    discount_type = discount_value = deal_offer_name = None
    if not product_set:
        deal_offer = _calculate_deals_offer(group)
        discount_type = deal_offer.get('discount_type') if deal_offer else None
        discount_value = deal_offer.get('discount_value') if deal_offer else 0
        deal_offer_name = deal_offer.get('deals_offer_name') if deal_offer else 0
    else:
        discount_type = product_set.compute_price if product_set else None
        discount_value = product_set.percent_price if product_set.compute_price == 'percentage' else product_set.fixed_price
        deal_offer_name = product_set.compute_price+'('+str(discounted_value)+')'

    if product_template.detailed_type == 'service':
        sale_price_unit = total_qty_kyat = total_qty_gram = product_qty = 1
    else:
        if discount_type == 'percentage':
            discount_percent = discount_value
        elif discount_type == 'fixed':
            discount_fix = discount_value

        if product_template.use_price =='gold_update_price':
            sale_price_unit = round(gold_price.sale_price_gram, 6)
            sale_price = round(gold_price.sale_price_gram * total_qty_gram,6)
        elif product_template.use_price =='list_price':
            sale_price_unit = product_template.list_price
            sale_price = product_template.list_price

    if discount_percent:
        discounted_price = round(sale_price - (sale_price * (discount_percent or 0.0) / 100.0),6)
        #round(total_qty_gram * (sale_price - (sale_price * (discount_percent or 0.0) / 100.0)), 6)
    if discount_fix:
        discounted_price = round(sale_price - discount_fix,6)

    # print('total_qty_gram###',total_qty_gram,sale_price_unit,discounted_price)
    total_qty_kyat = round(total_qty_kyat * qty,6)

    return sale_price,discounted_price,discount_type,discount_value,deal_offer_name,total_qty_kyat,total_qty_gram,sale_price_unit

def get_detail_product_template(product_template,group,public_categ_ids):
    line_category=request.env['product.public.category'].sudo().search_read(
        [('id', 'in', public_categ_ids)],
        fields=['id', 'name'], limit=1)

    # gender
    attr_gender = _get_attribute_lines(product_template, 'Gender')

    # colour
    attr_colour = _get_attribute_lines(product_template, 'Colour')

    # bundle info
    bundle_line = _get_bundle_line(product_template)

    product_image_url = None
    if product_template.image_1920:
        product_image_url = get_images_url(product_template,product_template_image[0],product_template_image[1])#_get_product_image_url(line.product_template_id)
    else:
        product_image_url = default_url

    kyats, petha_var, yway_var, petha_dec_var, yway_dec_var = _calculate_gold_weight(product_template)

    weight = str(kyats) + " ကျပ် " + str(petha_var+petha_dec_var) + " ပဲ " + str(yway_var+yway_dec_var) + " ရွေး"


    slider_img_urls = _get_product_slider_image_url(product_template)


    # get discounted price of display product template of product group
    discounted_price = sale_price = 0
    discount_type = None
    discount_value = None
    deals_offer_name = None

    sale_price, discounted_price, discount_type, \
    discount_value, deals_offer_name, total_qty_kyat, \
    total_qty_gram, sale_price_unit = calculate_kpy(product_template, 1, group, None)


    val = {
        'id':product_template.id,
        'name':product_template.name,
        'available_qty': product_template.qty_available,
        'weight':weight,
        'petha_dec':petha_dec_var,
        'yway_dec': yway_dec_var,
        'size': product_template.length,
        'description': str(product_template.product_description) if product_template.product_description else '',
        'jewellery_type':
            {
               'id': product_template.gold_quality.id if product_template.gold_quality else " ",
               'name':product_template.gold_quality.name if product_template.gold_quality.name else " ",
            },
        'category': line_category[0] if line_category else None,
        'sale_price': sale_price,
        'cost_price': 0,
        'deals_offer_name': deals_offer_name,
        'discount_type': discount_type,
        'discount_value': discount_value,
        'discounted_price': discounted_price if discounted_price else 0.00,
        'colour':attr_colour if attr_colour else None,
        'gender':attr_gender if attr_colour else None,
        'bundle_lines': bundle_line,
        'images_url': product_image_url,
        'slider_img_urls':slider_img_urls,
    }
    return val

