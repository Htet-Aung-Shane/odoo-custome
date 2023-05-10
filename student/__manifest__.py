{
    'name' : 'Student',
    'description' : 'HAS_Custom_description',
    'depends' : ['customer_extension','contacts','report_xlsx', 'mail', 'base'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/student.xml',
        'views/menu.xml',
        'views/user_extension.xml',
        'wizard/family.xml',
        'report/report.xml',
        'report/report_student.xml',
        'report/report_student_xlsx.xml',
        
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}