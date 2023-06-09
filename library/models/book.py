from odoo import models, fields, api

class Book(models.Model):
    _name = 'ha.book'
    _description = 'Books'

    name = fields.Char ('Name')
    isbn = fields.Char ('ISBN')
    author = fields.Char ('Author')
    image = fields.Binary()
    genre = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('horror', 'Horror'), ('adventure', 'Adventure'), ('romance', 'Horror')], default='draft')
    review = fields.Text ('Review')
    attachment = fields.Binary()