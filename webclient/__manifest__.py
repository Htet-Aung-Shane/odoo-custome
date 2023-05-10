{
    'name': "Webclient - Basic Setup",

    'summary': """
        Basic setup for ecommerce web client """,

    'description': """
        Basic setup for ecommerce web client which use rpc to communicate with odoo server.
        Customizations \n
        1. Create a new website to be used as default website. \n
        2. Default website, saleperson and pricelist relations for company \n
        3. Methods with prefix rpc_ to allow some internal methods to be able to call from rpc
        4. Apis for Django ecommerce website
        ** Default website created by this module "Ecommerce Web Client" must be at the top of website list 
        ** Need to enable register, General Settings > CustomerAccount > Free sign up
        ** To send email after confirmation from webclient, you need to setup odoo automation ( base_automation )
        ** Need to enable wishlist 
        ** Need to create membership service product **
        ** Need to create coupon service product **
        ** Need to install product attachment app
        ** Invoicing policy is "Ordered Quantity" **
        ** All product are need to setup published ** 
        to create mail after sale order status is changed**
        ** Need to open "Continue Selling"
        ** Need to add products and services for membership calculate.
        ** Need to install "Product Customization Module". 
    """,

    'author': "Myanmar Software Integrated Solutions",
    'website': "http://www.myansis.com",
    'category': 'WebClient/Ecommerce/Webclient',
    'version': '0.9',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'website',
        'website_sale',
        'sale',
        'purchase',
        'stock',
        'odoo_marketplace',
        'website_blog',
        'gold_update_price'

    ],
    # always loadedres.township
    'data': [
            # "security/ir.model.access.csv",
            "views/website_views.xml",
    ],
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
}
