# -*- coding: utf-8 -*-
from flectra import fields, api, models


class ToolsCatalog(models.Model):
    _name = 'construction.tools.catalog'
    _description = 'Tools Catalog'
    _order = 'name'

    name = fields.Char(string='Tool Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    category_id = fields.Many2one('construction.tools.category', string='Category')
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    unit_price = fields.Monetary(string='Unit Price')
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    image = fields.Image(string='Image')
    active = fields.Boolean(string='Active', default=True)


class ToolsCategory(models.Model):
    _name = 'construction.tools.category'
    _description = 'Tools Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    tool_ids = fields.One2many('construction.tools.catalog', 'category_id', string='Tools')


class ConstructionConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Email Settings
    email_notification_enabled = fields.Boolean(string='Enable Email Notifications', config_parameter='construction_management.email_notification_enabled')
    email_on_work_order_approval = fields.Boolean(string='Email on Work Order Approval', config_parameter='construction_management.email_on_work_order_approval')
    email_on_qc_approval = fields.Boolean(string='Email on QC Approval', config_parameter='construction_management.email_on_qc_approval')
    email_on_material_requisition = fields.Boolean(string='Email on Material Requisition', config_parameter='construction_management.email_on_material_requisition')
    email_on_subcontract_approval = fields.Boolean(string='Email on Subcontract Approval', config_parameter='construction_management.email_on_subcontract_approval')

