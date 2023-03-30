from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ContactId(models.Model):
    _inherit= 'res.partner'
    contact_id = fields.Integer('Contact ID')
    cv_form = fields.Text('CV Form')
    cv_name = fields.Char('CV Name')
    cv_email = fields.Char('CV Email')
    cv_phone = fields.Char('CV Phone')
 
    _sql_constraints=[('unique_contact_id','unique(contact_id)','Contact ID Duplicate, Please input another id')]
