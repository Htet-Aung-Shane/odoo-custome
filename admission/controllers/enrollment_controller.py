import odoo.http as http
from odoo.http import request
from odoo.http import request, Response

class Enrollment(http.Controller):
    @http.route(['/enrollment'], type='http',
                auth='public', website=True)
    def inquiry(self, **post):
        return http.request.render(
            "admission.enrollment_form", post)

    @http.route(['/enrollment/submit'], type='http', auth='public', website=True)
    def enrollment_submit(self, **post):
        enrollment_id = False
        return http.request.render(
            "admission.enrollment_confirmed", post)

    @http.route(['/enrollment/api'], type='http', auth='public', website=True)
    def api(self, **kwargs):

        model_name = 'ha.admission'
        result = {
            'success': True,
            'message': 'Ok',
            }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)