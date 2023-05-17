from odoo import models, fields, api

class Admission(models.Model):
    _name = 'ha.admission'
    _description = 'Admission'

    name = fields.Char ('Name')
    #subject = fields.Many2many('ha.subject', string='Subjects')
    