# -*- coding: utf-8 -*-
from flectra import fields, api, models


class RateAnalysis(models.Model):
    _name = 'construction.rate.analysis'
    _description = 'Rate Analysis'
    _order = 'work_type_id, work_subtype_id'

    work_type_id = fields.Many2one('construction.work.type', string='Work Type', required=True)
    work_subtype_id = fields.Many2one('construction.work.subtype', string='Work Sub Type')
    unit_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    
    # Costs
    material_line_ids = fields.One2many('construction.rate.analysis.material', 'rate_analysis_id', string='Materials')
    material_cost = fields.Monetary(string='Material Cost', compute='_compute_costs', store=True)
    
    equipment_line_ids = fields.One2many('construction.rate.analysis.equipment', 'rate_analysis_id', string='Equipment')
    equipment_cost = fields.Monetary(string='Equipment Cost', compute='_compute_costs', store=True)
    
    labor_line_ids = fields.One2many('construction.rate.analysis.labor', 'rate_analysis_id', string='Labor')
    labor_cost = fields.Monetary(string='Labor Cost', compute='_compute_costs', store=True)
    
    overhead_line_ids = fields.One2many('construction.rate.analysis.overhead', 'rate_analysis_id', string='Overhead')
    overhead_cost = fields.Monetary(string='Overhead Cost', compute='_compute_costs', store=True)
    
    total_rate = fields.Monetary(string='Total Rate', compute='_compute_costs', store=True)
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)

    @api.depends('material_line_ids', 'equipment_line_ids', 'labor_line_ids', 'overhead_line_ids')
    def _compute_costs(self):
        for rec in self:
            rec.material_cost = sum(rec.material_line_ids.mapped('total'))
            rec.equipment_cost = sum(rec.equipment_line_ids.mapped('total'))
            rec.labor_cost = sum(rec.labor_line_ids.mapped('total'))
            rec.overhead_cost = sum(rec.overhead_line_ids.mapped('total'))
            rec.total_rate = rec.material_cost + rec.equipment_cost + rec.labor_cost + rec.overhead_cost

    @api.onchange('work_type_id')
    def _onchange_work_type(self):
        if self.work_type_id:
            return {'domain': {'work_subtype_id': [('work_type_id', '=', self.work_type_id.id)]}}
        return {'domain': {'work_subtype_id': []}}


class RateAnalysisMaterial(models.Model):
    _name = 'construction.rate.analysis.material'
    _description = 'Rate Analysis Material'

    rate_analysis_id = fields.Many2one('construction.rate.analysis', string='Rate Analysis', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='rate_analysis_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='rate_analysis_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class RateAnalysisEquipment(models.Model):
    _name = 'construction.rate.analysis.equipment'
    _description = 'Rate Analysis Equipment'

    rate_analysis_id = fields.Many2one('construction.rate.analysis', string='Rate Analysis', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Equipment', required=True, domain=[('is_equipment', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='rate_analysis_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='rate_analysis_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class RateAnalysisLabor(models.Model):
    _name = 'construction.rate.analysis.labor'
    _description = 'Rate Analysis Labor'

    rate_analysis_id = fields.Many2one('construction.rate.analysis', string='Rate Analysis', required=True, ondelete='cascade')
    name = fields.Char(string='Labor Description', required=True)
    hours = fields.Float(string='Hours', required=True, default=1.0)
    rate = fields.Monetary(string='Rate per Hour')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='rate_analysis_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='rate_analysis_id.currency_id', store=True, readonly=True)

    @api.depends('hours', 'rate')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.hours or 0.0) * (rec.rate or 0.0)


class RateAnalysisOverhead(models.Model):
    _name = 'construction.rate.analysis.overhead'
    _description = 'Rate Analysis Overhead'

    rate_analysis_id = fields.Many2one('construction.rate.analysis', string='Rate Analysis', required=True, ondelete='cascade')
    name = fields.Char(string='Overhead Description', required=True)
    amount = fields.Monetary(string='Amount')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='rate_analysis_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='rate_analysis_id.currency_id', store=True, readonly=True)

    @api.depends('amount')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.amount or 0.0

