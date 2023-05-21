from odoo import fields, models, api

class AdditionalWizard(models.Model):
    _name = 'admission.additional.wizard'
    _description = 'Admission Additional Wizard'

    admission_date = fields.Date('Admission Date')
    comfirmation_date = fields.Date('Comfirm Date')
    parent = fields.Char('Parent Name')
    additional_id = fields.Many2one('ha.admission','Additional To Admission')