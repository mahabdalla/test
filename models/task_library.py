# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class TaskLibrary(models.Model):
    _name = 'construction.task.library'
    _description = 'Task Library'
    _order = 'name'

    name = fields.Char(string='Task Name', required=True)
    description = fields.Text(string='Description')
    work_type_id = fields.Many2one('construction.work.type', string='Work Type')
    work_subtype_id = fields.Many2one('construction.work.subtype', string='Work Sub Type')
    
    # Material Entries
    material_line_ids = fields.One2many('construction.task.library.material.line', 'task_library_id', string='Materials')
    material_total = fields.Monetary(string='Material Total', compute='_compute_totals', store=True)
    
    # Equipment Entries
    equipment_line_ids = fields.One2many('construction.task.library.equipment.line', 'task_library_id', string='Equipment')
    equipment_total = fields.Monetary(string='Equipment Total', compute='_compute_totals', store=True)
    
    # Labor Entries
    labor_line_ids = fields.One2many('construction.task.library.labor.line', 'task_library_id', string='Labor')
    labor_total = fields.Monetary(string='Labor Total', compute='_compute_totals', store=True)
    
    # Overhead Entries
    overhead_line_ids = fields.One2many('construction.task.library.overhead.line', 'task_library_id', string='Overhead')
    overhead_total = fields.Monetary(string='Overhead Total', compute='_compute_totals', store=True)
    
    # Subcontractor Entries
    subcontractor_line_ids = fields.One2many('construction.task.library.subcontractor.line', 'task_library_id', string='Subcontractors')
    subcontractor_total = fields.Monetary(string='Subcontractor Total', compute='_compute_totals', store=True)
    
    # Total Cost
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_totals', store=True)
    
    # Active
    active = fields.Boolean(string='Active', default=True)
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)

    @api.depends('material_line_ids', 'equipment_line_ids', 'labor_line_ids', 'overhead_line_ids', 'subcontractor_line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.material_total = sum(rec.material_line_ids.mapped('total'))
            rec.equipment_total = sum(rec.equipment_line_ids.mapped('total'))
            rec.labor_total = sum(rec.labor_line_ids.mapped('total'))
            rec.overhead_total = sum(rec.overhead_line_ids.mapped('total'))
            rec.subcontractor_total = sum(rec.subcontractor_line_ids.mapped('total'))
            rec.total_cost = rec.material_total + rec.equipment_total + rec.labor_total + rec.overhead_total + rec.subcontractor_total

    @api.onchange('work_type_id')
    def _onchange_work_type(self):
        if self.work_type_id:
            return {'domain': {'work_subtype_id': [('work_type_id', '=', self.work_type_id.id)]}}
        return {'domain': {'work_subtype_id': []}}

    def action_import_to_phase(self):
        """Import task library entries to a WBS phase"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import to Phase',
            'res_model': 'construction.import.task.library.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_library_id': self.id}
        }


class TaskLibraryMaterialLine(models.Model):
    _name = 'construction.task.library.material.line'
    _description = 'Task Library Material Line'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='task_library_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='task_library_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class TaskLibraryEquipmentLine(models.Model):
    _name = 'construction.task.library.equipment.line'
    _description = 'Task Library Equipment Line'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Equipment', required=True, domain=[('is_equipment', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='task_library_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='task_library_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class TaskLibraryLaborLine(models.Model):
    _name = 'construction.task.library.labor.line'
    _description = 'Task Library Labor Line'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True, ondelete='cascade')
    name = fields.Char(string='Labor Description', required=True)
    hours = fields.Float(string='Hours', required=True, default=1.0)
    rate = fields.Monetary(string='Rate per Hour', required=True)
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='task_library_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='task_library_id.currency_id', store=True, readonly=True)

    @api.depends('hours', 'rate')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.hours or 0.0) * (rec.rate or 0.0)


class TaskLibraryOverheadLine(models.Model):
    _name = 'construction.task.library.overhead.line'
    _description = 'Task Library Overhead Line'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True, ondelete='cascade')
    name = fields.Char(string='Overhead Description', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='task_library_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='task_library_id.currency_id', store=True, readonly=True)

    @api.depends('amount')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.amount or 0.0


class TaskLibrarySubcontractorLine(models.Model):
    _name = 'construction.task.library.subcontractor.line'
    _description = 'Task Library Subcontractor Line'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True, ondelete='cascade')
    name = fields.Char(string='Subcontractor Description', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='task_library_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='task_library_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)

