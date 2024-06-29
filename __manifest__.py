# Copyright 2022 OpenSynergy Indonesia
# Copyright 2022 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "E-Materai Mekari",
    "version": "11.0.1.3.0",
    "category": "Administration",
    "website": "https://github.com/muhrizky",
    "author": "Muhammad Rizqi",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        "ssi_ematerai_mixin",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ematerai_provider_data.xml",
        "views/ematerai_document_views.xml",
        "views/ematerai_mekari_views.xml",
        "views/res_config_settings_views.xml",
        "views/ematerai_document_templates.xml",
    ],
}
