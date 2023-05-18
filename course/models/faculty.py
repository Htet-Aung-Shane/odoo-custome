from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime,date
from odoo.exceptions import ValidationError

class Faculty(models.Model):
    _name = 'ha.faculty'
    _description = 'Faculty'

    name = fields.Char('Name')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    dob = fields.Date('Birth Date')
    age = fields.Char(compute='_onchange_dob', store=True, string='Age')    
    partner = fields.Many2one('res.partner', string='Partner')
    tag_ids = fields.Many2many('res.partner.category', string='Tags')
    
    _sql_constraints=[('unique_name','unique(name)','Faculty Name Duplicate, Please input another faculty name')]
    @api.depends('dob')
    def _onchange_dob(self):
        for rec in self:
            if rec.dob:
                dt = rec.dob
                d1 = datetime.strptime(str(dt), "%Y-%m-%d").date()
                d2 = datetime.today()
                rd = relativedelta(d2, d1)
                if rd.years>=18:
                    rec.age = str(rd.years) +' years'+  str(rd.months)+' months' +  str(rd.days)+' days' 
                else:
                    raise ValidationError(
                        _("Faculty Age Must Over 18"))
    # @api.onchange('dob')
    # def set_age(self):
    #     for rec in self:
    #         if rec.dob:
    #             dt = rec.dob
    #             d1 = datetime.strptime(str(dt), "%Y-%m-%d").date()
    #             d2 = datetime.today()
    #             rd = relativedelta(d2, d1)
    #             rec.age = str(rd.years) +' years'+  str(rd.months)+' months' 
        