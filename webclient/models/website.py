from odoo import fields, models
from odoo.http import request

class Website(models.Model):
    _inherit = "website"

    webclient_pricelist_id = fields.Many2one('product.pricelist',
                                           string='Default Pricelist for Ecommerce Website',
                                           required=False)
