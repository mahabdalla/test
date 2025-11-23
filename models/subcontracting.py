# -*- coding: utf-8 -*-
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class Subcontract(models.Model):
    _name = 'construction.subcontract'
    _description = 'Construction Subcontract'
    _order = 'id desc'

    name = fields.Char(string='Subcontract Reference', required=True, default='New', readonly=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    phase_id = fields.Many2one('construction.project.phase', string='Phase', domain="[('project_id', '=', project_id)]")
    work_order_id = fields.Many2one('construction.work.order', string='Work Order', domain="[('phase_id', '=', phase_id)]")
    partner_id = fields.Many2one('res.partner', string='Subcontractor', required=True)
    
    subcontract_type = fields.Selection([
        ('equipment', 'Equipment'),
        ('labor', 'Labor'),
        ('overhead', 'Overhead'),
    ], string='Subcontract Type', required=True)
    
    description = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    unit_price = fields.Monetary(string='Unit Price', required=True)
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    retention_percent = fields.Float(string='Retention %', default=0.0)
    retention_amount = fields.Monetary(string='Retention Amount', compute='_compute_retention', store=True)
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_retention', store=True)
    
    # Payment Schedule
    payment_schedule_ids = fields.One2many('construction.subcontract.payment.schedule', 'subcontract_id', string='Payment Schedule')
    
    # Purchase Orders & Bills
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    bill_ids = fields.One2many('account.move', 'subcontract_id', string='Bills')
    bill_count = fields.Integer(string='Bills', compute='_compute_bill_count')
    
    # RA Billing
    ra_billing_ids = fields.One2many('construction.ra.billing', 'subcontract_id', string='RA Billings')
    ra_billing_count = fields.Integer(string='RA Billings', compute='_compute_ra_billing_count')
    
    # Quality Check
    qc_check_ids = fields.One2many('construction.quality.check', 'subcontract_id', string='Quality Checks')
    qc_approved = fields.Boolean(string='QC Approved', default=False)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('qc_pending', 'QC Pending'),
        ('department_approved', 'Department Approved'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.subcontract') or 'New'
        return super().create(vals_list)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = (rec.quantity or 0.0) * (rec.unit_price or 0.0)

    @api.depends('subtotal', 'retention_percent')
    def _compute_retention(self):
        for rec in self:
            rec.retention_amount = rec.subtotal * (rec.retention_percent / 100.0)
            rec.amount_total = rec.subtotal - rec.retention_amount

    @api.depends('bill_ids')
    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = len(rec.bill_ids)

    @api.depends('ra_billing_ids')
    def _compute_ra_billing_count(self):
        for rec in self:
            rec.ra_billing_count = len(rec.ra_billing_ids)

    def action_send_for_qc(self):
        """Send subcontract for quality check"""
        for rec in self:
            if not rec.project_id:
                raise ValidationError("Please link this subcontract to a Sub Project.")
            qc = self.env['construction.quality.check'].create({
                'subcontract_id': rec.id,
                'project_id': rec.project_id.id,
                'work_order_id': rec.work_order_id.id if rec.work_order_id else False,
                'check_type': 'subcontract',
            })
            rec.write({'state': 'qc_pending'})
        return True

    def action_create_purchase_order(self):
        for rec in self:
            if rec.state != 'approved':
                raise ValidationError("Subcontract must be approved before creating Purchase Order.")
            po_lines = [(0, 0, {
                'product_id': self.env.ref('construction_management.construction_product_1').id if rec.subcontract_type == 'labor' else False,
                'name': rec.description,
                'product_qty': rec.quantity,
                'product_uom': 1,
                'price_unit': rec.unit_price,
            })]
            
            po = self.env['purchase.order'].create({
                'partner_id': rec.partner_id.id,
                'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                'order_line': po_lines,
            })
            rec.purchase_order_id = po.id
            rec.write({'state': 'in_progress'})

    def action_create_bill(self):
        for rec in self:
            invoice_lines = [(0, 0, {
                'product_id': self.env.ref('construction_management.construction_product_1').id if rec.subcontract_type == 'labor' else False,
                'name': rec.description,
                'quantity': rec.quantity,
                'price_unit': rec.unit_price,
            })]
            
            bill = self.env['account.move'].create({
                'partner_id': rec.partner_id.id,
                'move_type': 'in_invoice',
                'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                'order_type': rec.subcontract_type,
                'subcontract_id': rec.id,
                'invoice_line_ids': invoice_lines,
            })
            bill.action_post()

    def action_view_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bills',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('subcontract_id', '=', self.id)],
            'target': 'current'
        }

    def action_view_ra_billings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'RA Billings',
            'res_model': 'construction.ra.billing',
            'view_mode': 'tree,form',
            'domain': [('subcontract_id', '=', self.id)],
            'target': 'current'
        }
    
    def action_fetch_from_wbs(self):
        """Auto-fetch labor from WBS Phase"""
        for rec in self:
            if not rec.phase_id:
                raise ValidationError("Please select a Phase to fetch labor from WBS.")
            
            if rec.subcontract_type != 'labor':
                raise ValidationError("Auto-fetch from WBS is only available for Labor subcontracts.")
            
            # Get labor entries from phase
            labor_entries = rec.phase_id.labor_entry_ids
            if not labor_entries:
                raise ValidationError("No labor entries found in the selected phase.")
            
            # Update quantity and unit_price from phase labor entries
            total_hours = sum(labor_entries.mapped('hours'))
            total_cost = sum(labor_entries.mapped('total'))
            
            if total_hours > 0:
                rec.quantity = total_hours
                rec.unit_price = total_cost / total_hours
                rec.description = f"Labor from Phase: {rec.phase_id.name}\n" + "\n".join([f"- {entry.name}: {entry.hours} hours @ {entry.rate}" for entry in labor_entries])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Labor fetched from WBS successfully.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        """Update work_order_id domain when phase changes"""
        if self.phase_id:
            return {'domain': {'work_order_id': [('phase_id', '=', self.phase_id.id)]}}
        return {'domain': {'work_order_id': []}}


class RABilling(models.Model):
    _name = 'construction.ra.billing'
    _description = 'RA (Running Account) Billing'
    _order = 'id desc'

    name = fields.Char(string='RA Billing Reference', required=True, default='New', readonly=True)
    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract', required=True)
    project_id = fields.Many2one(related='subcontract_id.project_id', string='Sub Project', store=True, readonly=True)
    partner_id = fields.Many2one(related='subcontract_id.partner_id', string='Subcontractor', store=True, readonly=True)
    
    date = fields.Date(string='Date', default=fields.Date.context_today)
    completed_quantity = fields.Float(string='Completed Quantity', required=True)
    unit_price = fields.Monetary(related='subcontract_id.unit_price', string='Unit Price', readonly=True)
    subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    retention_percent = fields.Float(related='subcontract_id.retention_percent', string='Retention %', readonly=True)
    retention_amount = fields.Monetary(string='Retention Amount', compute='_compute_retention', store=True)
    amount_total = fields.Monetary(string='Total Amount', compute='_compute_retention', store=True)
    
    # Purchase Order & Bill
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', readonly=True)
    bill_id = fields.Many2one('account.move', string='Bill', readonly=True)
    
    # Work Completion Certificate
    certificate_id = fields.Many2one('construction.work.completion.certificate', string='Certificate', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('po_created', 'PO Created'),
        ('billed', 'Billed'),
        ('certified', 'Certified'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.ra.billing') or 'New'
        return super().create(vals_list)

    @api.depends('completed_quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = (rec.completed_quantity or 0.0) * (rec.unit_price or 0.0)

    @api.depends('subtotal', 'retention_percent')
    def _compute_retention(self):
        for rec in self:
            rec.retention_amount = rec.subtotal * (rec.retention_percent / 100.0)
            rec.amount_total = rec.subtotal - rec.retention_amount

    def action_create_purchase_order(self):
        for rec in self:
            po_lines = [(0, 0, {
                'product_id': self.env.ref('construction_management.construction_product_1').id if rec.subcontract_id.subcontract_type == 'labor' else False,
                'name': f'RA Billing: {rec.name}',
                'product_qty': rec.completed_quantity,
                'product_uom': 1,
                'price_unit': rec.unit_price,
            })]
            
            po = self.env['purchase.order'].create({
                'partner_id': rec.partner_id.id,
                'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                'order_line': po_lines,
            })
            rec.purchase_order_id = po.id
            rec.write({'state': 'po_created'})

    def action_create_bill(self):
        for rec in self:
            invoice_lines = [(0, 0, {
                'product_id': self.env.ref('construction_management.construction_product_1').id if rec.subcontract_id.subcontract_type == 'labor' else False,
                'name': f'RA Billing: {rec.name}',
                'quantity': rec.completed_quantity,
                'price_unit': rec.unit_price,
            })]
            
            bill = self.env['account.move'].create({
                'partner_id': rec.partner_id.id,
                'move_type': 'in_invoice',
                'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                'order_type': rec.subcontract_id.subcontract_type,
                'invoice_line_ids': invoice_lines,
            })
            bill.action_post()
            rec.bill_id = bill.id
            rec.write({'state': 'billed'})

    def action_create_certificate(self):
        for rec in self:
            cert = self.env['construction.work.completion.certificate'].create({
                'ra_billing_id': rec.id,
                'subcontract_id': rec.subcontract_id.id,
                'project_id': rec.project_id.id,
                'partner_id': rec.partner_id.id,
                'completed_quantity': rec.completed_quantity,
                'amount_total': rec.amount_total,
            })
            rec.certificate_id = cert.id
            rec.write({'state': 'certified'})


class SubcontractPaymentSchedule(models.Model):
    _name = 'construction.subcontract.payment.schedule'
    _description = 'Subcontract Payment Schedule'
    _order = 'sequence, id'

    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    percentage = fields.Float(string='Percentage (%)', required=True, default=100.0)
    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=True)
    date = fields.Date(string='Payment Date')
    paid = fields.Boolean(string='Paid', default=False)
    payment_date = fields.Date(string='Payment Date', readonly=True)
    
    company_id = fields.Many2one(related='subcontract_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='subcontract_id.currency_id', store=True, readonly=True)

    @api.depends('percentage', 'subcontract_id.amount_total')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.subcontract_id.amount_total * (rec.percentage / 100.0)
    
    def action_mark_paid(self):
        """Mark payment schedule line as paid"""
        for rec in self:
            rec.write({
                'paid': True,
                'payment_date': fields.Date.context_today(self),
            })
        return True


class WorkCompletionCertificate(models.Model):
    _name = 'construction.work.completion.certificate'
    _description = 'Work Completion Certificate'

    name = fields.Char(string='Certificate Number', required=True, default='New', readonly=True)
    ra_billing_id = fields.Many2one('construction.ra.billing', string='RA Billing', required=True)
    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract', required=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Subcontractor', required=True)
    
    date = fields.Date(string='Date', default=fields.Date.context_today)
    completed_quantity = fields.Float(string='Completed Quantity')
    amount_total = fields.Monetary(string='Total Amount')
    description = fields.Text(string='Description')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.work.completion.certificate') or 'New'
        return super().create(vals_list)

