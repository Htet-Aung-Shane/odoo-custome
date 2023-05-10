from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
import math

class IrApiHelper(models.Model):
    _name = "ir.api.helper"
    _description = "API Helper"

    def setup_limit_offset_page_order(self, kw):
        limit = int(kw['limit']) if 'limit' in kw else 12
        page = int(kw['page']) if 'page' in kw else 1
        order = kw['order'] if 'order' in kw else 'name ASC'
        offset = (page - 1) * limit if not 'offset' in kw else 0
        
        result = {
            'limit': limit,
            'offset': offset,
            'page': page,
            'order': order
        }
        # print("Result - ",result,"\n\n")
        return result
    
    # def response_result(self, message, item, kw, model_name=False, filters=False):
    #     msg = message
    #     items = item
    #     model = model_name
    #     limit, page, offset, order = self.setup_limit_offset_page_order(kw).values()
    #     total_items = self.record_count(model_name,filters)
    #     total_pages = int(total_items/limit)
    #     current_page = page
        
    #     result = {
    #         'status': 'SUCCESS',
    #         'message': msg,
    #         'paginate_info':{
    #             'limit': limit,
    #             'current_page': current_page,
    #             'total_items': total_items,
    #             'total_pages': total_pages,
    #         },
    #         'item_info':{
    #             'image_url': '/web/image/'+model_name+'/'
    #         },
    #         'items': items
    #     }
        
    #     return result
        
        
    # def record_count(self,model_name,filters):
    #     rec_count = len(self.env[model_name].sudo().search(filters))
        
    #     return rec_count