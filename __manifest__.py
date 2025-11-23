# -*- coding: utf-8 -*-
# Copyright 2020-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
{
    'name': "Construction Management | Job Costing | Job Cost Sheet | Job Order | Construction Project | Project Planning | Job Contract | Construction Waste Management",
    'description': """
        - Construction Management
        - Job Costing 
        - Job Cost Sheet
        - Job Contract
        - Project Site
        - Construction Project Management
        - Job Budget Management
        - Construction Scrape Management
        - Construction Waste Management
    """,
    'summary': """Construction Management - Job Costing, Job Order, Job Cost Sheet, Project Site, & Scrape Order Management""",
    'version': "3.0.1.0.0",
    'author': 'TechKhedut Inc.',
    'company': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'support': "info@techkhedut.co",
    'category': 'Industry',
    'depends': ['base', 'contacts', 'account', 'sale_management', 'purchase', 'hr', 'project', 'calendar', 'stock',
                'mail', 'hr_timesheet', 'web'],
    'data': [
        # security
        'security/ir.model.access.csv',
        # Data
        'data/sequence.xml',
        'data/construction_data.xml',
        # Wizard Views
        'wizard/construction_inspection_view.xml',
        'wizard/import_task_library_view.xml',
        # Views
        'views/assets.xml',
        'views/construction_details_view.xml',
        'views/construction_site_details.xml',
        'views/construction_equipment.xml',
        'views/construction_labour_inherit.xml',
        'views/construction_employee_role.xml',
        'views/construction_employee_inherit.xml',
        'views/document_type.xml',
        'views/construction_purchase_order.xml',
        'views/construction_project_inherit_view.xml',
        'views/construction_insurance_risk.xml',
        'views/scrap_order_view.xml',
        'views/construction_configuration.xml',
        'views/job_costing_view.xml',
        'views/job_type_view.xml',
        'views/progress_billing_view.xml',
        'views/work_type_view.xml',
        'views/boq_view.xml',
        'views/rate_analysis_view.xml',
        'views/wbs_view.xml',
        'views/material_requisition_view.xml',
        'views/subcontracting_view.xml',
        'views/consume_order_view.xml',
        'views/tools_catalog_view.xml',
        'views/dashboard_view.xml',
        'views/task_library_view.xml',
        # menus
        'views/menus.xml',
        # Report views
        'report/construction_details_report.xml',
        'report/job_costing_report.xml',
        'report/boq_report.xml',
        'report/work_order_report.xml',
        'report/material_requisition_report.xml',
        'report/subcontract_report.xml',
        'report/purchase_reports.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'construction_management/static/src/css/lib/dashboard.css',
            'construction_management/static/src/css/lib/style.css',
            'construction_management/static/src/css/style.scss',
        ],
    },
    'images': ['static/description/cover.gif'],
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 299,
    'currency': 'USD',
}
