{
    'name' : 'Student',
    'description' : 'HAS_Custom_description',
    'depends' : ['customer_extension','contacts'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/student.xml',
        'views/menu.xml',
        'wizard/family.xml',
        'report/report.xml',
        'report/report_student.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}