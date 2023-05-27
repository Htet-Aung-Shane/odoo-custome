import odoo.http as http
from odoo.http import request
from odoo.http import request, Response
import json

class Enrollment(http.Controller):
    @http.route(['/enrollment'], type='http',
                auth='public', website=True)
    def inquiry(self, **get):
        return http.request.render(
            "admission.enrollment_form", get)

    @http.route(['/enrollment/submit'], type='http', auth='public', website=True)
    def enrollment_submit(self, **get):
        enrollment_id = False

        #create admission
        print(get['student'])
        student = request.env['ha.student'].search([('name', '=', get['student'])])
        if student:
            admisssion = request.env['ha.admission'].sudo().create({
                'start_date' : get['start-date'],
                'end_date' : get['end-Date'],
                'student' : student.id
            })
        else:
            partner = request.env['ha.student'].sudo().create({
                'name': get['student']
            })
            admisssion = request.env['ha.admission'].sudo().create({
                'start_date' : get['start-date'],
                'end_date' : get['end-Date'],
                'student' : partner.id
            })

        return http.request.render(
            "admission.enrollment_confirmed", get)

    @http.route(['/enrollment/api'], type='http', auth='public', website=True)
    def api(self, **kwargs):

        model_name = 'ha.admission'
        items = request.env[model_name].sudo()
        print('shop items',items)

        result = {
            'success': True,
            'message': 'Ok',
            }
        headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(result), headers=headers)