from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
    #diff_date = fields.Char(compute='_diff_date', store=True, string='Diff Date')
    student = fields.Many2one('ha.student', string='Student')
    partner = fields.Many2one('res.partner',related='student.partner', string='Partner')
    course =  fields.Many2one('ha.course', string='Course')
    subject =  fields.Many2one('ha.subject', string='Subject')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('done', 'Done')], default='draft', tracking=True)
    #subject = fields.Many2many('ha.subject', string='Subjects')
    
    @api.constrains('start_date', 'end_date')
    def _diff_date(self):
        for rec in self:
            if rec.end_date <= rec.start_date:
                    print(rec.end_date)
                    raise ValidationError(
                        _("End Date Must Greater Than Start Date"))

    def action_done(self):
        self.state = 'done'
        self.student.write({'course':self.course})

    def action_set_to_draft(self):
        self.state = 'draft'
    