from odoo import models, fields, api

class Course(models.Model):
    _name = 'ha.course'
    _description = 'Course'

    name = fields.Char ('Name')
    tag_ids = fields.Many2many('res.partner.category', string='Tags')
    #subject = fields.Many2many('ha.subject', string='Subjects')
    