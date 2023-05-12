from odoo import models, fields, api

class Subject(models.Model):
    _name = 'ha.subject'
    _description = 'Subject'

    name = fields.Char ('Name')
    faculty = fields.Many2one ('ha.faculty', string='Faculty')
    tag_ids = fields.Many2many('res.partner.category', string='Tags')