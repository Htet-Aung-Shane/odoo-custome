from odoo import fields, models, api

class FamilyWizard(models.Model):
    _name = 'family.member.wizard'
    _description = 'Family Member Wizard'

    name = fields.Char('Name')
    age = fields.Integer('Age')
    occupation = fields.Char('Occupation')
    gender = fields.Selection([('male','Male'),('female','Female')])
    family_id = fields.Many2one('ha.student','Family To Student')