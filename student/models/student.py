from odoo import models, fields, api

class Student(models.Model):
    _name = 'ha.student'
    _description = 'Student'

    name = fields.Char('Name')
    phone = fields.Integer('Phone')
    email = fields.Char('Email')
    dob = fields.Date('Birth Date')    
    partner = fields.Many2one('res.partner','Partner')
    image = fields.Binary()
    contact_id = fields.Integer(related='partner.contact_id', string='Contact ID', readonly=True)
    student_ids = fields.One2many('family.member.wizard','family_id',string='Family')
    education_ids = fields.One2many('ha.education','education_id',string='Education')

    #def action_family(self):
     #   return {
      #      'type': 'ir.actions.act_window',
       #     'res_model': 'family.member.wizard',
        #    'name': 'Family Member',
         #   'view_mode': 'form',
          #  'target': 'new',

        #}

class Education(models.Model):
    _name = 'ha.education'
    _description = 'Education of the students'

    degree = fields.Char('Degree')
    award_date = fields.Char('Award Date')
    education_id = fields.Many2one('ha.student',string='Education To Student')

