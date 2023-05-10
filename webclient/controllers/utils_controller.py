import base64
from werkzeug.utils import redirect
import io
from odoo import http
import re
from odoo.http import request
import werkzeug
import json

class UtilsController(http.Controller):
    @http.route(['/app-info'], type='json', auth="public",method=['POST'])
    def app_info(self):
        return {
            'status': True,
            'android': {
                'version': '1.1',
                'force_update': True
            },
            'ios': {
                'version': None,
                'force_update': True
            }
        }
        
    @http.route(['/auth/user'], type='json', auth="user",method=['POST'])
    def get_session(self):
        session_id = request.session
        
        result = {
            'message': 'Ok',
            'session_id': session_id
        }
        
        return result
    
    @http.route(['/request-header'], type='json', auth="public",method=['POST'])
    def get_request_header(self, **kwargs):
        result={
            'headers': dict(request.httprequest.headers)
        }
        
        return result

    @http.route(['/api/image/<string:model>/<int:id>/<string:field>'], type='http', auth="public")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):
        # other kwargs are ignored on purpose
        return request.env['ir.http']._content_image(xmlid=xmlid, model=model, res_id=id, field=field,
                                                     filename_field=filename_field, unique=unique, filename=filename,
                                                     mimetype=mimetype,
                                                     download=download, width=width, height=height, crop=crop,
                                                     quality=int(kwargs.get('quality', 0)), access_token=access_token)