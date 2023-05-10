from odoo import fields, models

class CountryState(models.Model):
    _inherit = 'res.country.state'
    _order = 'code'


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result