from odoo import models, fields, api

class Admission(models.Model):
    _name = 'ha.admission'
    _description = 'Admission'

    name = fields.Char (
        'Application Number', size=16, copy=False,
        readonly=True, store=True,
        default=lambda self:
        self.env['ir.sequence'].next_by_code('has.admission'))
    start_date = fields.Date ('Start Date')
    end_date = fields.Date ('End Date')
    student = fields.Many2one('ha.student', string='Student')
    partner = fields.Many2one('res.partner',related='student.partner', string='Partner')
    course =  fields.Many2one('ha.course', string='Course')
    subject =  fields.Many2one('ha.subject', string='Subject')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('done', 'Done')], default='draft', tracking=True)
    #subject = fields.Many2many('ha.subject', string='Subjects')

    @api.model    
    def action_done(self):
        self.state = 'done'

    def action_set_to_draft(self):
        self.state = 'draft'
    