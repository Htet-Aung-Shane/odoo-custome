{
    'name' : 'Admission',
    'description' : 'HAS_Custom_description',
    'depends' : ['student','course'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/admission.xml',
        'views/ha_sequence.xml',
        # 'views/subject.xml',
        'wizard/additional.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}