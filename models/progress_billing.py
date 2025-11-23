# -*- coding: utf-8 -*-
from flectra import fields, api, models


class ConstructionProgressBilling(models.Model):
    _name = 'construction.progress.billing'
    _description = 'Construction Progress Billing'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, default='New', readonly=True)
    project_id = fields.Many2one('project.project', string='Sub Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    line_ids = fields.One2many('construction.progress.billing.line', 'billing_id', string='Lines')
    amount_untaxed = fields.Monetary(string='Untaxed', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Tax', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Total', compute='_compute_amounts', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('invoiced', 'Invoiced'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') in (False, 'New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('construction.progress.billing') or 'New'
            if not vals.get('partner_id') and vals.get('project_id'):
                project = self.env['project.project'].browse(vals['project_id'])
                if project.construction_id and project.construction_id.customer_company_id:
                    vals['partner_id'] = project.construction_id.customer_company_id.id
        return super().create(vals_list)

    @api.depends('line_ids.price_subtotal')
    def _compute_amounts(self):
        for rec in self:
            untaxed = sum(rec.line_ids.mapped('price_subtotal'))
            rec.amount_untaxed = untaxed
            rec.amount_tax = 0.0
            rec.amount_total = untaxed

    def action_create_invoice(self):
        for rec in self:
            if not rec.line_ids:
                continue
            move_vals = {
                'partner_id': rec.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(self),
                'invoice_line_ids': [],
                'construction_id': rec.project_id.construction_id.id if rec.project_id.construction_id else False,
                'order_type': 'expense',
            }
            lines = []
            for line in rec.line_ids:
                lvals = {
                    'name': line.name,
                    'quantity': line.quantity or 1,
                    'price_unit': line.price_unit,
                }
                if line.product_id:
                    lvals['product_id'] = line.product_id.id
                lines.append((0, 0, lvals))
            move_vals['invoice_line_ids'] = lines
            move = self.env['account.move'].create(move_vals)
            move.action_post()
            rec.invoice_id = move.id
            rec.state = 'invoiced'
        return True


class ConstructionProgressBillingLine(models.Model):
    _name = 'construction.progress.billing.line'
    _description = 'Progress Billing Line'

    billing_id = fields.Many2one('construction.progress.billing', string='Billing', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Monetary(string='Unit Price')
    company_id = fields.Many2one(related='billing_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='billing_id.currency_id', store=True, readonly=True)
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    phase = fields.Char(string='Phase')
    work_order = fields.Char(string='Work Order')

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = (rec.quantity or 0.0) * (rec.price_unit or 0.0)

