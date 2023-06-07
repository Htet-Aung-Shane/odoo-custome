from odoo import models, fields, api

class Timetable(models.Model):
    _name = 'ha.timetable'
    _description = 'Timetable'

    name = fields.Char ('Name')
    faculty = fields.Many2one('ha.faculty', string='Faculty')
    course = fields.Many2one('ha.course', string='Course')
    subject = fields.Many2one('ha.subject', string='Subject')
    start_time = fields.Date ('Start Time')
    end_time = fields.Date ('End Time')
    day = fields.Selection([('monday', 'Monday'), ('tuesday', 'Tuesday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('friday', 'Friday')], string='Day')