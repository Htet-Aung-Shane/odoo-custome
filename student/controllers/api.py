from odoo import http
from odoo.http import request, Response
import json

class MyAPI(http.Controller):

    @http.route('/api/get_data', type='json', auth='none', cors='*')
    def get_data(self, **kwargs):
        data = request.env['ha.student'].search_read([], fields=['name', 'value'])
        return Response(json.dumps(data), content_type='application/json')