# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models


class JobCosting(models.Model):
    _name = "job.costing"
    _description = "Job Costing"

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: ('New'))
    site_id = fields.Many2one('construction.site', string="Construction Site")
    state = fields.Selection([('planning', 'Planning'), ('job_order', 'Job Order'), ('cancel', 'Cancel')],
                             string="Stage", default="planning")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    area_plot = fields.Float(string='Area of Plot')
    construction_rate = fields.Monetary(string='Construction Rate')
    cost_of_construction = fields.Monetary(string="Cost of Construction")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    desc = fields.Html(string="Description")
    material_ids = fields.One2many('cost.material.line', 'job_costing_id')
    equipment_ids = fields.One2many('cost.equipment.line', 'job_costing_id')
    eng_labour_ids = fields.One2many('cost.employee.line', 'job_costing_id')
    material_total = fields.Monetary(string="Material Total")
    equipment_total = fields.Monetary(string="Equipment Total")
    eng_labour_total = fields.Monetary(string="Labour Total")
    estimate_cost = fields.Monetary(string="Estimate Cost", compute="_compute_estimate_cost")
    job_order_id = fields.Many2one('construction.details', string="Job Order")

    # Address
    zip = fields.Char(string='Pin Code', size=6)
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", string='State', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")
    longitude = fields.Char(string="Longitude")
    latitude = fields.Char(string="Latitude")

    @api.onchange('site_id')
    def _onchange_site_id(self):
        for rec in self:
            if rec.site_id:
                rec.zip = rec.site_id.zip
                rec.street = rec.site_id.street
                rec.street2 = rec.site_id.street2
                rec.city = rec.site_id.city
                rec.country_id = rec.site_id.country_id.id
                rec.state_id = rec.site_id.state_id.id
                rec.longitude = rec.site_id.longitude
                rec.latitude = rec.site_id.latitude

    @api.onchange('construction_rate', 'area_plot')
    def _onchange_cost_of_construction(self):
        for rec in self:
            if rec.construction_rate and rec.area_plot:
                rec.cost_of_construction = rec.construction_rate * rec.area_plot
            else:
                rec.cost_of_construction = 0.0

    # Sequence Create
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'job.costing') or ('New')
        return super(JobCosting, self).create(vals_list)

    @api.onchange('material_ids')
    def _onchange_material_total(self):
        for rec in self:
            total = 0.0
            if rec.material_ids:
                for data in rec.material_ids:
                    total = total + data.total_cost
                rec.material_total = total
            else:
                rec.material_total = 0.0

    @api.onchange('equipment_ids')
    def _onchange_equipment_total(self):
        for rec in self:
            total = 0.0
            if rec.equipment_ids:
                for data in rec.equipment_ids:
                    total = total + data.total_cost
                rec.equipment_total = total
            else:
                rec.equipment_total = 0.0

    @api.onchange('eng_labour_ids')
    def _onchange_labours_total(self):
        for rec in self:
            total = 0.0
            if rec.eng_labour_ids:
                for data in rec.eng_labour_ids:
                    total = total + data.total_cost
                rec.eng_labour_total = total
            else:
                rec.eng_labour_total = 0.0

    @api.depends('eng_labour_total', 'equipment_total', 'material_total', 'cost_of_construction')
    def _compute_estimate_cost(self):
        for rec in self:
            rec.estimate_cost = rec.eng_labour_total + rec.equipment_total + rec.material_total + rec.cost_of_construction

    def action_cancel(self):
        self.state = "cancel"

    def action_create_job_order(self):
        self.state = "job_order"
        data = {
            'job_costing_id': self.id,
            'site_id': self.site_id.id,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'area_plot': self.area_plot,
            'construction_rate': self.construction_rate,
            'estimate_cost': self.estimate_cost,
            'desc': self.desc
        }
        job_order_id = self.env['construction.details'].create(data)
        self.job_order_id = job_order_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Construction Site',
            'res_model': 'construction.details',
            'res_id': job_order_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class CostMaterialLine(models.Model):
    _name = "cost.material.line"
    _description = "Job Costing Material Line"

    material_id = fields.Many2one(
        'product.product',
        string="Material",
        domain="[('type','=','product'),('is_material','=',True)]",
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    qty = fields.Integer(string="Qty.", default=1)
    cost = fields.Float(related="material_id.lst_price", string="Cost", store=True)
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    job_costing_id = fields.Many2one('job.costing', string="Costing")
    uom_id = fields.Many2one(related="material_id.uom_po_id", string="Unit of Measure")

    @api.depends('material_id', 'qty', 'cost')
    def _compute_total_cost(self):
        for rec in self:
            if rec.material_id:
                rec.total_cost = rec.qty * rec.cost
            else:
                rec.total_cost = 0.0


class CostEquipmentLine(models.Model):
    _name = "cost.equipment.line"
    _description = "Job Costing Equipment Line"
    _rec_name = 'equipment_id'

    equipment_id = fields.Many2one(
        'product.product',
        string="Equipment",
        domain="[('type','=','product'),('is_equipment','=',True)]",
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost_type = fields.Selection(
        [('depreciation_cost', 'Depreciation Cost'), ('investment_cost', 'Investment/Interest Cost'),
         ('tax', 'Tax'),
         ('rent', 'Rent'), ('other', 'Other')], string="Type", default='rent')
    desc = fields.Text(string='Description')
    qty = fields.Integer(string="Qty.", default=1)
    cost = fields.Monetary(string="Estimation Cost")
    job_costing_id = fields.Many2one('job.costing', string="Equipment Costing")
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)

    @api.depends('cost', 'qty')
    def _compute_total_cost(self):
        for rec in self:
            if rec.cost:
                rec.total_cost = rec.qty * rec.cost
            else:
                rec.total_cost = 0.0


class CostEmployeeLine(models.Model):
    _name = "cost.employee.line"
    _description = "Job Costing Employee Line"

    name = fields.Char(string="Title")
    role_id = fields.Many2one('construction.employee', string="Role")
    no_of_person = fields.Integer(string="No of People")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost = fields.Monetary(string="Charges")
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", store=True)
    job_costing_id = fields.Many2one('job.costing', string="Equipment Costing")

    @api.depends('cost', 'no_of_person')
    def _compute_total_cost(self):
        for rec in self:
            if rec.no_of_person:
                rec.total_cost = rec.no_of_person * rec.cost
            else:
                rec.total_cost = 0.0
