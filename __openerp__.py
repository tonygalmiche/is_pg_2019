# -*- coding: utf-8 -*-
{
    "name" : "InfoSaône - Module Odoo pour Plastigray en 2019",
    "version" : "0.1",
    "author" : "InfoSaône",
    "category" : "InfoSaône\Plastigray",
    "description": """
InfoSaône - Module Odoo pour Plastigray en 2019
===================================================
InfoSaône - Module Odoo pour Plastigray en 2019
    """,
    "maintainer": 'InfoSaône',
    "website": 'http://www.infosaone.com',
    "depends" : [
        "is_plastigray",
    ], 
    "data" : [
        "security/ir_model_access_is_fiche_tampographie.xml",
        "views/is_fiche_tampographie_constituant_view.xml",
        "report/is_encres_utilisees_view.xml",
        "views/report_is_fiche_tampographie.xml",
        "views/is_equipement_view.xml",
        'views/is_head_model_view.xml',
        "views/menu.xml",
        "security/ir.model.access.csv",
    ], 
    "qweb": [
    ],
    "installable": True,
    "active": False
}

