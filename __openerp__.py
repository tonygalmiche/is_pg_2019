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
        "product",
        "is_mold",
    ], 
    "data" : [
        "data/sequence.xml",
        "security/ir_model_access_is_fiche_tampographie.xml",
        "security/ot_security_view.xml",
        "security/res_groups.xml",
        "views/is_fiche_tampographie_constituant_view.xml",
        "report/is_encres_utilisees_view.xml",
        "views/report_is_fiche_tampographie.xml",
        "views/is_theia_view.xml",
        "views/is_capteur_view.xml",
        "views/is_equipement_view.xml",
        'views/is_head_model_view.xml',
        "views/is_ot_workflow.xml",
        "views/is_ot_view.xml",
        "views/is_ctrl100_view.xml",
        "views/menu.xml",
        "security/ir.model.access.csv",
        "views/report_gamme_defautheque.xml",
        "views/report_gamme_qualite.xml",


        "views/report_paperformat.xml",
        "views/bilan_fin_of_report.xml",
        "views/report.xml",

    ], 
    "qweb": [
    ],
    "installable": True,
    "active": False,
    #"auto_install": True,
}

