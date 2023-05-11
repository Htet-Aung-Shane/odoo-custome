from odoo import models, fields, api

class Faculty(models.Model):
    _name = 'ha.faculty'
    _description = 'Faculty'

    name = fields.Char('Name')
    phone = fields.Integer('Phone')
    email = fields.Char('Email')
    dob = fields.Date('Birth Date')    
    partner = fields.Many2one('res.partner','Partner')
    tag_ids = fields.Many2many('res.partner.category', string='Tags')
    
    