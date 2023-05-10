from odoo import models

class StudentXlsx(models.AbstractModel):
    _name = 'report.student.report_student_excel_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, partners):
        sheet = workbook.add_worksheet("student report")