{
    'name' : 'Course',
    'description' : 'HAS_Custom_description',
    'depends' : ['student','contacts'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/course.xml',
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}