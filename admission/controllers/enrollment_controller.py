import odoo.http as http
from odoo.http import request

class Enrollment(http.Controller):
    @http.route(['/enrollment'], type='http',
                auth='public', website=True)
    def inquiry(self, **kw):
        return http.request.render(
            "admission.enrollment_form", post)