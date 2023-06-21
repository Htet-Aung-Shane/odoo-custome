{
    'name' : 'Library',
    'description' : 'HAS_Custom_description',
    'depends' : ['student'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/library.xml',
        'report/isbn_badge.xml',
        ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}