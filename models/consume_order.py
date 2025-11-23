# -*- coding: utf-8 -*-
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ConsumeOrder(models.Model):
    _name = 'construction.consume.order'
    _description = 'Consume Order'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, default='New', readonly=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    work_order_id = fields.Many2one('construction.work.order', string='Work Order', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    
    date = fields.Date(string='Date', default=fields.Date.context_today)
    line_ids = fields.One2many('construction.consume.order.line', 'consume_order_id', string='Lines')
    
    # Quality Check
    qc_check_id = fields.Many2one('construction.quality.check', string='QC Check', readonly=True)
    qc_approved = fields.Boolean(string='QC Approved', default=False)
    
    # Department Approval
    department_approved = fields.Boolean(string='Department Approved', default=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('qc_pending', 'QC Pending'),
        ('qc_approved', 'QC Approved'),
        ('department_pending', 'Department Pending'),
        ('approved', 'Approved'),
        ('consumed', 'Consumed'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.consume.order') or 'New'
        return super().create(vals_list)

    def action_send_for_qc(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add lines before sending for QC check.")
            qc = self.env['construction.quality.check'].create({
                'consume_order_id': rec.id,
                'work_order_id': rec.work_order_id.id,
                'project_id': rec.project_id.id,
                'check_type': 'consume',
            })
            rec.qc_check_id = qc.id
            rec.write({'state': 'qc_pending'})

    def action_department_approve(self):
        for rec in self:
            rec.write({
                'department_approved': True,
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'state': 'approved'
            })

    def action_consume(self):
        for rec in self:
            if not rec.qc_approved or not rec.department_approved:
                raise ValidationError("Consume order must be QC and Department approved before consuming.")
            
            # Create stock moves to consume materials
            for line in rec.line_ids:
                move_vals = {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': rec.warehouse_id.lot_stock_id.id,
                    'location_dest_id': self.env.ref('stock.stock_location_scrapped').id,
                    'picking_type_id': rec.warehouse_id.int_type_id.id,
                    'consume_order_id': rec.id,
                }
                self.env['stock.move'].create(move_vals)
            
            rec.write({'state': 'consumed'})


class ConsumeOrderLine(models.Model):
    _name = 'construction.consume.order.line'
    _description = 'Consume Order Line'

    consume_order_id = fields.Many2one('construction.consume.order', string='Consume Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_id = fields.Many2one(related='product_id.uom_id', string='Unit', readonly=True)
    consumed = fields.Boolean(string='Consumed', default=False)


class QualityCheck(models.Model):
    _name = 'construction.quality.check'
    _description = 'Quality Check'
    _order = 'id desc'

    name = fields.Char(string='QC Reference', required=True, default='New', readonly=True)
    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract')
    consume_order_id = fields.Many2one('construction.consume.order', string='Consume Order')
    work_order_id = fields.Many2one('construction.work.order', string='Work Order')
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    
    check_type = fields.Selection([
        ('subcontract', 'Subcontract'),
        ('consume', 'Consume Order'),
        ('work_order', 'Work Order'),
        ('material', 'Material Quality Check'),
    ], string='Check Type', required=True)
    
    # Material Quality Check fields
    material_requisition_id = fields.Many2one('construction.material.requisition', string='Material Requisition')
    material_line_id = fields.Many2one('construction.material.requisition.line', string='Material Line')
    product_id = fields.Many2one('product.product', string='Material', domain=[('is_material', '=', True)])
    
    date = fields.Date(string='Date', default=fields.Date.context_today)
    inspector_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user)
    
    # Check Results
    passed = fields.Boolean(string='Passed', default=False)
    failed = fields.Boolean(string='Failed', default=False)
    notes = fields.Text(string='Notes')
    
    # Approval
    department_manager_id = fields.Many2one('res.users', string='Department Manager')
    department_approved = fields.Boolean(string='Department Approved', default=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.quality.check') or 'New'
        return super().create(vals_list)

    def action_start_check(self):
        self.write({'state': 'in_progress'})

    def action_pass(self):
        for rec in self:
            rec.write({
                'state': 'passed',
                'passed': True,
                'failed': False,
            })
            # Update related records
            if rec.subcontract_id:
                rec.subcontract_id.qc_approved = True
                rec.subcontract_id.write({'state': 'department_approved'})
            if rec.consume_order_id:
                rec.consume_order_id.qc_approved = True
                rec.consume_order_id.write({'state': 'qc_approved'})
            if rec.material_requisition_id:
                # Update material requisition line QC status
                if rec.material_line_id:
                    rec.material_line_id.qc_passed = True
                    rec.material_line_id.qc_check_id = rec.id

    def action_fail(self):
        for rec in self:
            rec.write({
                'state': 'failed',
                'passed': False,
                'failed': True,
            })

    def action_department_approve(self):
        for rec in self:
            rec.write({
                'department_approved': True,
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'state': 'approved'
            })
            
            # Update related records
            if rec.subcontract_id:
                rec.subcontract_id.write({'state': 'approved'})
            if rec.consume_order_id:
                rec.consume_order_id.action_department_approve()

