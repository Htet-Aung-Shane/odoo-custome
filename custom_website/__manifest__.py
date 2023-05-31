{
    "name" : "Custom Theme",
    "author" : "Htet Aung Shane",
    "website": "mtchannel.tech",
    "support":"https://mtchannel.tech/",
    "version": "16.0.1",
    "category":"kings website theme",
    "license":"LGPL-3",
    "category": 'Theme/Creative',
    "summary": "KINGS Internationl School",
    "application": True,
    "auto_install": False,
    "depends":['base','website','web'],
    "data":[
        'views/custom_footer.xml',
    ],
    "assets":{
        'web.assets_frontend': [
            '/custom_website/static/src/scss/custom.scss',
        ]
    }
}
