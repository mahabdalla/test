# -*- coding: utf-8 -*-
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ProjectPhase(models.Model):
    _name = 'construction.project.phase'
    _description = 'Construction Project Phase (WBS)'
    _order = 'sequence, id'

    name = fields.Char(string='Phase Name', required=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    work_type_id = fields.Many2one('construction.work.type', string='Work Type')
    work_subtype_id = fields.Many2one('construction.work.subtype', string='Work Sub Type')
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    
    # Phase Entries
    material_entry_ids = fields.One2many('construction.phase.material.entry', 'phase_id', string='Material Entries')
    equipment_entry_ids = fields.One2many('construction.phase.equipment.entry', 'phase_id', string='Equipment Entries')
    labor_entry_ids = fields.One2many('construction.phase.labor.entry', 'phase_id', string='Labor Entries')
    overhead_entry_ids = fields.One2many('construction.phase.overhead.entry', 'phase_id', string='Overhead Entries')
    
    # Totals
    total_material = fields.Monetary(string='Total Material', compute='_compute_totals', store=True)
    total_equipment = fields.Monetary(string='Total Equipment', compute='_compute_totals', store=True)
    total_labor = fields.Monetary(string='Total Labor', compute='_compute_totals', store=True)
    total_overhead = fields.Monetary(string='Total Overhead', compute='_compute_totals', store=True)
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_totals', store=True)
    
    # Work Orders
    work_order_ids = fields.One2many('construction.work.order', 'phase_id', string='Work Orders')
    work_order_count = fields.Integer(string='Work Orders', compute='_compute_work_order_count')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')

    @api.depends('material_entry_ids', 'equipment_entry_ids', 'labor_entry_ids', 'overhead_entry_ids')
    def _compute_totals(self):
        for rec in self:
            rec.total_material = sum(rec.material_entry_ids.mapped('total'))
            rec.total_equipment = sum(rec.equipment_entry_ids.mapped('total'))
            rec.total_labor = sum(rec.labor_entry_ids.mapped('total'))
            rec.total_overhead = sum(rec.overhead_entry_ids.mapped('total'))
            rec.total_cost = rec.total_material + rec.total_equipment + rec.total_labor + rec.total_overhead

    @api.depends('work_order_ids')
    def _compute_work_order_count(self):
        for rec in self:
            rec.work_order_count = len(rec.work_order_ids)

    @api.onchange('work_type_id')
    def _onchange_work_type(self):
        if self.work_type_id:
            return {'domain': {'work_subtype_id': [('work_type_id', '=', self.work_type_id.id)]}}
        return {'domain': {'work_subtype_id': []}}

    def action_view_work_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Work Orders',
            'res_model': 'construction.work.order',
            'view_mode': 'tree,form',
            'domain': [('phase_id', '=', self.id)],
            'context': {'default_phase_id': self.id},
            'target': 'current'
        }
    
    def action_import_from_task_library(self):
        """Open wizard to import from task library"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import from Task Library',
            'res_model': 'construction.import.task.library.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_phase_id': self.id}
        }


class PhaseMaterialEntry(models.Model):
    _name = 'construction.phase.material.entry'
    _description = 'Phase Material Entry'

    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    boq_quantity = fields.Float(string='BOQ Quantity')
    quantity = fields.Float(string='Required Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='phase_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='phase_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class PhaseEquipmentEntry(models.Model):
    _name = 'construction.phase.equipment.entry'
    _description = 'Phase Equipment Entry'

    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Equipment', required=True, domain=[('is_equipment', '=', True)])
    boq_quantity = fields.Float(string='BOQ Quantity')
    quantity = fields.Float(string='Required Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_po_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='phase_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='phase_id.currency_id', store=True, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)


class PhaseLaborEntry(models.Model):
    _name = 'construction.phase.labor.entry'
    _description = 'Phase Labor Entry'

    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True, ondelete='cascade')
    name = fields.Char(string='Labor Description', required=True)
    boq_hours = fields.Float(string='BOQ Hours')
    hours = fields.Float(string='Required Hours', required=True, default=1.0)
    rate = fields.Monetary(string='Rate per Hour')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='phase_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='phase_id.currency_id', store=True, readonly=True)

    @api.depends('hours', 'rate')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.hours or 0.0) * (rec.rate or 0.0)


class PhaseOverheadEntry(models.Model):
    _name = 'construction.phase.overhead.entry'
    _description = 'Phase Overhead Entry'

    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True, ondelete='cascade')
    name = fields.Char(string='Overhead Description', required=True)
    amount = fields.Monetary(string='Amount')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_id = fields.Many2one(related='phase_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='phase_id.currency_id', store=True, readonly=True)

    @api.depends('amount')
    def _compute_total(self):
        for rec in self:
            rec.total = rec.amount or 0.0


class WorkOrder(models.Model):
    _name = 'construction.work.order'
    _description = 'Construction Work Order'
    _order = 'id desc'

    name = fields.Char(string='Work Order Reference', required=True, default='New', readonly=True)
    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True)
    project_id = fields.Many2one(related='phase_id.project_id', string='Sub Project', store=True, readonly=True)
    work_type_id = fields.Many2one(related='phase_id.work_type_id', string='Work Type', store=True, readonly=True)
    work_subtype_id = fields.Many2one(related='phase_id.work_subtype_id', string='Work Sub Type', store=True, readonly=True)
    
    description = fields.Text(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    
    # Quantities from Phase
    material_quantity = fields.Float(string='Material Quantity')
    equipment_quantity = fields.Float(string='Equipment Quantity')
    labor_hours = fields.Float(string='Labor Hours')
    overhead_amount = fields.Monetary(string='Overhead Amount')
    
    # Task
    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.work.order') or 'New'
        return super().create(vals_list)

    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        if self.phase_id:
            total_material = sum(self.phase_id.material_entry_ids.mapped('quantity'))
            total_equipment = sum(self.phase_id.equipment_entry_ids.mapped('quantity'))
            total_labor = sum(self.phase_id.labor_entry_ids.mapped('hours'))
            total_overhead = sum(self.phase_id.overhead_entry_ids.mapped('amount'))
            self.material_quantity = total_material
            self.equipment_quantity = total_equipment
            self.labor_hours = total_labor
            self.overhead_amount = total_overhead

    def action_create_task(self):
        for rec in self:
            if not rec.project_id:
                raise ValidationError("Work Order must be linked to a Sub Project to create a task.")
            task = self.env['project.task'].create({
                'name': rec.name + ' - ' + (rec.description or 'Work Order'),
                'project_id': rec.project_id.id,
                'description': rec.description,
                'date_deadline': rec.end_date,
            })
            rec.task_id = task.id
        return True

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'in_progress'})
        if not self.task_id:
            self.action_create_task()

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

