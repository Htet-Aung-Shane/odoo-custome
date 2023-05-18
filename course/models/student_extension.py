from odoo import fields, models, api

class ContactId(models.Model):
    _inherit= 'ha.student'
    course = fields.Many2one('ha.course', string='Course')
    faculty = fields.Many2one('ha.faculty', string='Faculty')