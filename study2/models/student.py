from odoo import models, fields, api

class Student(models.Model):
    _name = 'ha.student'
    _description = 'Student'

    name = fields.Char('Name')
    phone = fields.Integer('Phone')
    email = fields.Char('Email')
    dob = fields.Date('Birth Date')    
    partner = fields.Many2one('res.partner','Partner')
    contact_id = fields.Integer(related='partner.contact_id', string='Contact ID', readonly=True)