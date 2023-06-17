from odoo import models, fields, api

class Library(models.Model):
    _name = 'ha.library'
    _description = 'Library'

    name = fields.Char ('Name')