# -*- coding: utf-8 -*-
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class BOQ(models.Model):
    _name = 'construction.boq'
    _description = 'Bill of Quantity'
    _order = 'id desc'

    name = fields.Char(string='BOQ Reference', required=True, default='New', readonly=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    line_ids = fields.One2many('construction.boq.line', 'boq_id', string='BOQ Lines')
    total_material = fields.Monetary(string='Total Material', compute='_compute_totals', store=True)
    total_equipment = fields.Monetary(string='Total Equipment', compute='_compute_totals', store=True)
    total_labor = fields.Monetary(string='Total Labor', compute='_compute_totals', store=True)
    total_overhead = fields.Monetary(string='Total Overhead', compute='_compute_totals', store=True)
    total_budget = fields.Monetary(string='Total Budget', compute='_compute_totals', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.boq') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.total_material = sum(rec.line_ids.mapped('material_total'))
            rec.total_equipment = sum(rec.line_ids.mapped('equipment_total'))
            rec.total_labor = sum(rec.line_ids.mapped('labor_total'))
            rec.total_overhead = sum(rec.line_ids.mapped('overhead_total'))
            rec.total_budget = rec.total_material + rec.total_equipment + rec.total_labor + rec.total_overhead

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_cancel(self):
        self.write({'state': 'cancel'})


class BOQLine(models.Model):
    _name = 'construction.boq.line'
    _description = 'BOQ Line'

    boq_id = fields.Many2one('construction.boq', string='BOQ', required=True, ondelete='cascade')
    work_type_id = fields.Many2one('construction.work.type', string='Work Type', required=True)
    work_subtype_id = fields.Many2one('construction.work.subtype', string='Work Sub Type')
    description = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one('uom.uom', string='Unit of Measure')
    
    # Material
    material_line_ids = fields.One2many('construction.boq.material.line', 'boq_line_id', string='Materials')
    material_total = fields.Monetary(string='Material Total', compute='_compute_totals', store=True)
    
    # Equipment
    equipment_line_ids = fields.One2many('construction.boq.equipment.line', 'boq_line_id', string='Equipment')
    equipment_total = fields.Monetary(string='Equipment Total', compute='_compute_totals', store=True)
    
    # Labor
    labor_line_ids = fields.One2many('construction.boq.labor.line', 'boq_line_id', string='Labor')
    labor_total = fields.Monetary(string='Labor Total', compute='_compute_totals', store=True)
    
    # Overhead
    overhead_line_ids = fields.One2many('construction.boq.overhead.line', 'boq_line_id', string='Overhead')
    overhead_total = fields.Monetary(string='Overhead Total', compute='_compute_totals', store=True)
    
    total = fields.Monetary(string='Line Total', compute='_compute_totals', store=True)
    
    company_id = fields.Many2one(related='boq_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='boq_id.currency_id', store=True, readonly=True)

    @api.depends('material_line_ids', 'equipment_line_ids', 'labor_line_ids', 'overhead_line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.material_total = sum(rec.material_line_ids.mapped('total'))
            rec.equipment_total = sum(rec.equipment_line_ids.mapped('total'))
            rec.labor_total = sum(rec.labor_line_ids.mapped('total'))
            rec.overhead_total = sum(rec.overhead_line_ids.mapped('total'))
            rec.total = rec.material_total + rec.equipment_total + rec.labor_total + rec.overhead_total

    @api.onchange('work_type_id')
    def _onchange_work_type(self):
        if self.work_type_id:
            return {'domain': {'work_subtype_id': [('work_type_id', '=', self.work_type_id.id)]}}
        return {'domain': {'work_subtype_id': []}}


class BOQMaterialLine(models.Model):
    _name = 'construction.boq.material.line'
    _description = 'BOQ Material Line'

    boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Line', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='boq_line_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='boq_line_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class BOQEquipmentLine(models.Model):
    _name = 'construction.boq.equipment.line'
    _description = 'BOQ Equipment Line'

    boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Line', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Equipment', required=True, domain=[('is_equipment', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='boq_line_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='boq_line_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class BOQLaborLine(models.Model):
    _name = 'construction.boq.labor.line'
    _description = 'BOQ Labor Line'

    boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Line', required=True, ondelete='cascade')
    name = fields.Char(string='Labor Description', required=True)
    hours = fields.Float(string='Hours', required=True, default=1.0)
    rate = fields.Monetary(string='Rate per Hour')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='boq_line_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='boq_line_id.currency_id', store=True, readonly=True)

    @api.depends('hours', 'rate')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.hours or 0.0) * (rec.rate or 0.0)


class BOQOverheadLine(models.Model):
    _name = 'construction.boq.overhead.line'
    _description = 'BOQ Overhead Line'

    boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Line', required=True, ondelete='cascade')
    name = fields.Char(string='Overhead Description', required=True)
    amount = fields.Monetary(string='Amount')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='boq_line_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='boq_line_id.currency_id', store=True, readonly=True)

    @api.depends('amount')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.amount or 0.0

