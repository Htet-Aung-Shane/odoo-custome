from odoo import models, fields, api

class User(models.Model):
    _inherit = 'res.users'
    student = fields.Many2one('ha.student')