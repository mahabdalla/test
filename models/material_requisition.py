# -*- coding: utf-8 -*-
from flectra import fields, api, models
from flectra.exceptions import ValidationError
from datetime import datetime


class MaterialRequisition(models.Model):
    _name = 'construction.material.requisition'
    _description = 'Material Requisition'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, default='New', readonly=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    phase_id = fields.Many2one('construction.project.phase', string='Phase', domain="[('project_id', '=', project_id)]")
    work_order_id = fields.Many2one('construction.work.order', string='Work Order', domain="[('phase_id', '=', phase_id)]")
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True)
    
    date = fields.Date(string='Date', default=fields.Date.context_today)
    line_ids = fields.One2many('construction.material.requisition.line', 'requisition_id', string='Lines')
    
    # Operations
    purchase_order_ids = fields.One2many('purchase.order', 'material_requisition_id', string='Purchase Orders')
    internal_transfer_ids = fields.One2many('stock.picking', 'material_requisition_id', string='Internal Transfers')
    back_order_ids = fields.Many2many('purchase.order', string='Back Orders', compute='_compute_back_orders')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('department_approved', 'Department Approved'),
        ('po_created', 'PO Created'),
        ('transferred', 'Transferred'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.material.requisition') or 'New'
        return super().create(vals_list)

    @api.depends('purchase_order_ids', 'internal_transfer_ids', 'line_ids')
    def _compute_back_orders(self):
        for rec in self:
            back_orders = self.env['purchase.order']
            # Find POs that have back orders (partially received)
            for po in rec.purchase_order_ids:
                if po.state in ('purchase', 'done'):
                    # Check if any line has received quantity less than ordered quantity
                    for line in po.order_line:
                        if line.product_uom_qty > line.qty_received:
                            back_orders |= po
                            break
            
            # Also check lines that need back order
            for line in rec.line_ids:
                if line.operation_type == 'back_order':
                    # If available quantity + transferred quantity is less than required quantity
                    remaining_qty = line.quantity - line.transferred_qty - line.available_qty
                    if remaining_qty > 0 and line.purchase_line_id:
                        if line.purchase_line_id.order_id not in back_orders:
                            back_orders |= line.purchase_line_id.order_id
            
            rec.back_order_ids = back_orders
    
    def action_create_back_order(self):
        """Create back orders for lines that cannot be fulfilled from stock or existing POs"""
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add lines before creating back order.")
            
            # Find lines that need back order
            back_order_lines = []
            for line in rec.line_ids.filtered(lambda l: l.operation_type == 'back_order'):
                remaining_qty = line.quantity - line.transferred_qty - line.available_qty
                if remaining_qty > 0:
                    back_order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_qty': remaining_qty,
                        'product_uom': line.product_id.uom_po_id.id,
                        'price_unit': line.unit_price or line.product_id.standard_price,
                    }))
            
            if back_order_lines:
                # Find supplier or use default
                supplier_id = rec.project_id.construction_id.customer_company_id.id if rec.project_id.construction_id else False
                
                po = self.env['purchase.order'].create({
                    'partner_id': supplier_id,
                    'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                    'material_requisition_id': rec.id,
                    'order_line': back_order_lines,
                })
                # Update lines with purchase line reference
                for line in rec.line_ids.filtered(lambda l: l.operation_type == 'back_order' and not l.purchase_line_id):
                    if line.product_id in po.order_line.mapped('product_id'):
                        line.purchase_line_id = po.order_line.filtered(lambda l: l.product_id == line.product_id)[0].id

    def action_department_approve(self):
        self.write({'state': 'department_approved'})

    def action_create_purchase_order(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add lines before creating purchase order.")
            
            # Filter only approved lines
            approved_lines = rec.line_ids.filtered(lambda l: l.approved)
            if not approved_lines:
                raise ValidationError("Please approve at least one line before creating purchase order.")
            
            # Find supplier or use default
            supplier_id = rec.project_id.construction_id.customer_company_id.id if rec.project_id.construction_id else False
            if not supplier_id:
                raise ValidationError("Please set a customer company in the construction project.")
            
            po_lines = []
            for line in approved_lines.filtered(lambda l: l.operation_type == 'purchase' and not l.purchase_line_id):
                # Only create PO for quantity not available in stock
                qty_to_order = line.quantity - line.transferred_qty
                if qty_to_order > line.available_qty:
                    qty_to_order = qty_to_order - line.available_qty
                    po_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_qty': qty_to_order,
                        'product_uom': line.product_id.uom_po_id.id,
                        'price_unit': line.unit_price or line.product_id.standard_price,
                    }))
            
            if po_lines:
                po = self.env['purchase.order'].create({
                    'partner_id': supplier_id,
                    'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                    'material_requisition_id': rec.id,
                    'order_line': po_lines,
                })
                # Update lines with purchase line reference
                for line in approved_lines.filtered(lambda l: l.operation_type == 'purchase' and not l.purchase_line_id):
                    if line.product_id in po.order_line.mapped('product_id'):
                        line.purchase_line_id = po.order_line.filtered(lambda l: l.product_id == line.product_id)[0].id
                rec.write({'state': 'po_created'})
            else:
                raise ValidationError("No approved lines need purchase orders. Check available quantities and transferred quantities.")

    def action_add_approved_requisitions(self):
        """Smart button to add only approved requisitions to PO"""
        self.ensure_one()
        approved_lines = self.line_ids.filtered(lambda l: l.approved and l.operation_type == 'purchase' and not l.purchase_line_id)
        if not approved_lines:
            raise ValidationError("No approved lines available to add to purchase order.")
        # This method will be called from PO view to add approved requisitions
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Approved Requisitions',
            'res_model': 'construction.material.requisition.line',
            'view_mode': 'tree',
            'domain': [('id', 'in', approved_lines.ids), ('approved', '=', True)],
            'target': 'new',
            'context': {'default_requisition_id': self.id}
        }
    
    def action_create_internal_transfer(self):
        for rec in self:
            if not rec.warehouse_id:
                raise ValidationError("Please select a warehouse.")
            
            picking_lines = []
            for line in rec.line_ids.filtered(lambda l: l.operation_type == 'transfer' and not line.transferred):
                # Only transfer available quantity
                qty_to_transfer = min(line.quantity - line.transferred_qty, line.available_qty)
                if qty_to_transfer > 0:
                    picking_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty_to_transfer,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': rec.warehouse_id.lot_stock_id.id,
                        'location_dest_id': rec.warehouse_id.lot_stock_id.id,
                    }))
            
            if picking_lines:
                picking = self.env['stock.picking'].create({
                    'location_id': rec.warehouse_id.lot_stock_id.id,
                    'location_dest_id': rec.warehouse_id.lot_stock_id.id,
                    'picking_type_id': rec.warehouse_id.int_type_id.id,
                    'material_requisition_id': rec.id,
                    'move_ids_without_package': picking_lines,
                })
                # Update lines with transfer move reference
                for line in rec.line_ids.filtered(lambda l: l.operation_type == 'transfer' and not l.transfer_move_id):
                    if line.product_id in picking.move_ids_without_package.mapped('product_id'):
                        line.transfer_move_id = picking.move_ids_without_package.filtered(lambda m: m.product_id == line.product_id)[0].id
                rec.write({'state': 'transferred'})
            else:
                raise ValidationError("No lines available for internal transfer. Check available quantities.")
    
    def action_send_for_qc(self):
        """Send material requisition line for quality check"""
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add lines before sending for QC check.")
            # Create QC for each line that needs it
            for line in rec.line_ids.filtered(lambda l: not l.qc_check_id and not l.qc_passed):
                qc = self.env['construction.quality.check'].create({
                    'material_requisition_id': rec.id,
                    'material_line_id': line.id,
                    'product_id': line.product_id.id,
                    'project_id': rec.project_id.id,
                    'work_order_id': rec.work_order_id.id if rec.work_order_id else False,
                    'check_type': 'material',
                })
                line.qc_check_id = qc.id
    
    def action_complete(self):
        """Mark requisition as completed when all lines are fulfilled"""
        for rec in self:
            # Check if all lines are fulfilled
            all_fulfilled = True
            for line in rec.line_ids:
                if (line.transferred_qty + (line.purchase_line_id.qty_received if line.purchase_line_id else 0)) < line.quantity:
                    all_fulfilled = False
                    break
            
            if all_fulfilled:
                rec.write({'state': 'completed'})
            else:
                raise ValidationError("Not all lines are fulfilled. Please complete all purchases and transfers.")
    
    def action_fetch_from_wbs(self):
        """Auto-fetch materials from WBS Phase"""
        for rec in self:
            if not rec.phase_id:
                raise ValidationError("Please select a Phase to fetch materials from WBS.")
            
            # Create lines from phase material entries
            for entry in rec.phase_id.material_entry_ids:
                # Check if line already exists for this product
                existing_line = rec.line_ids.filtered(lambda l: l.product_id.id == entry.product_id.id)
                if existing_line:
                    # Update quantity if needed
                    if existing_line.quantity < entry.quantity:
                        existing_line.quantity = entry.quantity
                        existing_line.unit_price = entry.unit_price
                else:
                    # Create new line
                    self.env['construction.material.requisition.line'].create({
                        'requisition_id': rec.id,
                        'product_id': entry.product_id.id,
                        'quantity': entry.quantity,
                        'unit_price': entry.unit_price,
                    })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Materials fetched from WBS successfully.',
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


class MaterialRequisitionLine(models.Model):
    _name = 'construction.material.requisition.line'
    _description = 'Material Requisition Line'

    requisition_id = fields.Many2one('construction.material.requisition', string='Requisition', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True, domain=[('is_material', '=', True)])
    quantity = fields.Float(string='Required Quantity', required=True, default=1.0)
    available_qty = fields.Float(string='Available Quantity', compute='_compute_available_qty')
    transferred_qty = fields.Float(string='Transferred Quantity', default=0.0)
    unit_id = fields.Many2one(related='product_id.uom_id', string='Unit', readonly=True)
    unit_price = fields.Monetary(string='Unit Price')
    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    
    operation_type = fields.Selection([
        ('purchase', 'Purchase Order'),
        ('transfer', 'Internal Transfer'),
        ('back_order', 'Back Order'),
    ], string='Operation Type', required=True, default='purchase')
    
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Line', readonly=True)
    transfer_move_id = fields.Many2one('stock.move', string='Transfer Move', readonly=True)
    transferred = fields.Boolean(string='Transferred', default=False)
    fulfilled_qty = fields.Float(string='Fulfilled Quantity', compute='_compute_fulfilled_qty', store=True)
    remaining_qty = fields.Float(string='Remaining Quantity', compute='_compute_fulfilled_qty', store=True)
    
    # Quality Check
    qc_check_id = fields.Many2one('construction.quality.check', string='QC Check', readonly=True)
    qc_passed = fields.Boolean(string='QC Passed', default=False)
    
    # Individual Approval
    approved = fields.Boolean(string='Approved', default=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    
    @api.depends('transferred_qty', 'purchase_line_id.qty_received')
    def _compute_fulfilled_qty(self):
        for rec in self:
            received_qty = rec.purchase_line_id.qty_received if rec.purchase_line_id else 0.0
            rec.fulfilled_qty = rec.transferred_qty + received_qty
            rec.remaining_qty = rec.quantity - rec.fulfilled_qty
    
    company_id = fields.Many2one(related='requisition_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='requisition_id.currency_id', store=True, readonly=True)

    @api.depends('product_id', 'requisition_id.warehouse_id')
    def _compute_available_qty(self):
        for rec in self:
            if rec.product_id and rec.requisition_id.warehouse_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', 'child_of', rec.requisition_id.warehouse_id.lot_stock_id.id),
                ])
                rec.available_qty = sum(quants.mapped('quantity'))
            else:
                rec.available_qty = 0.0

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for rec in self:
            rec.total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)
    
    def action_approve_line(self):
        """Approve individual material line"""
        for rec in self:
            if rec.approved:
                raise ValidationError("This line is already approved.")
            rec.write({
                'approved': True,
                'approved_by': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
        return True
    
    def action_unapprove_line(self):
        """Unapprove individual material line"""
        for rec in self:
            rec.write({
                'approved': False,
                'approved_by': False,
                'approval_date': False,
            })
        return True

