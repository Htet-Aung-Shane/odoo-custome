from odoo import models, fields, api

class Course(models.Model):
    _name = 'ha.course'
    _description = 'Course'

    name = fields.Char ('Name')
    