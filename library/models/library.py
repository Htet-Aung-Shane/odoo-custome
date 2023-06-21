from odoo import models, fields, api

class Library(models.Model):
    _name = 'ha.library'
    _description = 'Library'

    name = fields.Char ('Name')
    book_id = fields.Many2one('ha.book', string='Student')