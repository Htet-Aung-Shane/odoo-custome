import odoo.http as http
from odoo.http import request
from odoo.http import request, Response
import json
from odoo import models

class BookShow(http.Controller):
    @http.route(['/books'], type='http',
                auth='public', website=True)
    def inquiry(self, **get):
        item = http.request.env['ha.book']
        items = item.search([])
        return http.request.render(
            "library.bookrent_form", {'data': items})