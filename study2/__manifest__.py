{
    'name' : 'Student',
    'description' : 'HAS_Custom_description',
    'depends' : ['study1','contacts'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/student.xml',
        'views/menu.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}