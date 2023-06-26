import odoo.http as http
from odoo.http import request
from odoo.http import request, Response
import json

class BookShow(http.Controller):
    @http.route(['/books'], type='http',
                auth='public', website=True)
    def inquiry(self, **get):
        return http.request.render(
            "library.bookrent_form", get)