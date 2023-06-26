{
    'name' : 'Library',
    'description' : 'HAS_Custom_description',
    'depends' : ['student', 'product'],
    'category': 'Education',
    'author': 'Htet Aung Shane',
    'data': [
        'security/ir.model.access.csv',
        'views/library.xml',
        'views/book_website_view.xml',
        'report/isbn_badge.xml',
        ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}