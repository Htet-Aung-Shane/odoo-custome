{
    'name' : 'Time Table',
    'description' : 'HAS_Custom_description',
    'depends' : ['student','course'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/timetable.xml',
        ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}