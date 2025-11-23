# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ConstructionDetails(models.Model):
    _name = 'construction.details'
    _description = "Construction Details"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'site_id'

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: ('New'))
    date = fields.Date(string="Date", default=fields.Date.today())
    site_id = fields.Many2one('construction.site', string="Project")
    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    stage = fields.Selection(
        [('confirm', 'Job Order'),
         ('a_costing', 'Document Verified'),
         ('in_progress', 'In Progress'),
         ('done', 'Complete'),
         ('close', 'Close'),
         ('cancel', 'Cancel')],
        default='confirm')
    zip = fields.Char(related="site_id.zip", string='Pin Code', size=6)
    street = fields.Char(related="site_id.street", string='Street1')
    street2 = fields.Char(related="site_id.street2", string='Street2')
    city = fields.Char(related="site_id.city", string='City')
    country_id = fields.Many2one(related="site_id.country_id")
    state_id = fields.Many2one(related="site_id.state_id", string='State')
    longitude = fields.Char(string="Longitude")
    latitude = fields.Char(string="Latitude")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    area_plot = fields.Float(string='Area of Plot')
    construction_rate = fields.Monetary(string='Construction Rate')
    cost_of_construction = fields.Monetary(string="Cost of Construction", compute="_compute_cost_of_construction")
    is_approved_document = fields.Boolean(string="Approved", compute="_compute_is_approved")
    customer_company_id = fields.Many2one('res.partner', domain=[('is_construction_company', '=', True)],
                                          string="Company ")
    project_id = fields.Many2one('project.project', string="Project ")
    scrap_id = fields.Many2one('scrap.order', string="Scrap Order", compute="_compute_scrap_order", store=True, index=True)
    estimate_cost = fields.Monetary(string="Estimate Budget")
    desc = fields.Html(string="Description")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    document_template_id = fields.Many2one('document.template', string="Document Template")
    delivery_order_id = fields.Many2one('stock.picking')
    sub_project_count = fields.Integer(string="Sub Projects", compute="_compute_sub_project_count")

    # One2Many
    equipment_ids = fields.One2many('construction.equipment', 'construction_id', string="Equipments")
    material_ids = fields.One2many('construction.material', 'construction_id', string="Material")
    construction_engineer_ids = fields.One2many('construction.engineer.line', 'construction_id', string="Engineers")
    total_engineer_charges = fields.Monetary(string="Total Charges", compute="_compute_engineer_charges")
    document_ids = fields.One2many('construction.document.line', 'construction_id')
    construction_labours_ids = fields.One2many('construction.labour.line', 'construction_id', string="Labours")
    construction_expense_ids = fields.One2many('construction.expense', 'construction_id', string="Expense")
    risk_ids = fields.One2many('construction.risk', 'construction_id', string="Risk")
    construction_inspection_ids = fields.One2many('site.inspection', 'construction_id',
                                                  string="Construction Inspection")
    construction_meeting_ids = fields.One2many('calendar.event', 'construction_id', string="Construction Meeting")

    # Profit & Loss
    profit_margin = fields.Monetary(string="Profit/Loss", compute="_compute_profit_margin")

    # Count
    equip_po_count = fields.Integer(compute='_compute_po_count')
    material_po_count = fields.Integer(compute='_compute_po_count')
    equip_bill_count = fields.Integer(compute='_compute_po_count')
    material_bill_count = fields.Integer(compute='_compute_po_count')
    task_count = fields.Integer(related="project_id.task_count", string="Task Count")
    labour_bill_count = fields.Integer(compute='_compute_po_count')
    eng_arc_bill_count = fields.Integer(compute="_compute_po_count")
    expense_bill_count = fields.Integer(compute="_compute_po_count")
    meeting_count = fields.Integer(compute="_compute_po_count")
    equipment_delivery_order_count = fields.Integer(compute="_compute_po_count")
    material_delivery_order_count = fields.Integer(compute="_compute_po_count")

    # Accountancy
    accountancy_type = fields.Selection([('paid', 'Paid'), ('all_bill', 'All Bills')], string="Accountancy")
    total_material_po_amount = fields.Monetary(string="Total Material Purchase Order", compute="_compute_accountancy")
    total_equipment_po_amount = fields.Monetary(string="Total Equipment Purchase Order", compute="_compute_accountancy")
    total_labour_bill_amount = fields.Monetary(string="Total Labour Bill", compute="_compute_accountancy")
    total_engineer_bill_amount = fields.Monetary(string="Total Engineer Bill", compute="_compute_accountancy")
    total_extra_expense_amount = fields.Monetary(string="Total Expense Bill", compute="_compute_accountancy")
    total_insurance_amount = fields.Monetary(string="Total Insurance Bill", compute="_compute_accountancy")
    total_scrap_order_amount = fields.Monetary(string="Total Scrap Order", compute="_compute_accountancy")
    remaining_budget_amount = fields.Monetary(string="Remaining Budget Amount", compute="_compute_accountancy")
    is_negative_remaining = fields.Boolean(compute="_compute_accountancy")
    remaining_material_po_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_equipment_po_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_labour_bill_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_engineer_bill_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_extra_expense_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_insurance_amount = fields.Monetary(compute="_compute_accountancy")
    remaining_to_pay = fields.Monetary(compute="_compute_accountancy")
    total_to_pay = fields.Monetary(compute="_compute_accountancy")

    # Sequence Create
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'construction.details') or ('New')
        return super(ConstructionDetails, self).create(vals_list)

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.site_id.name, rec.name)))
        return data

    def _compute_scrap_order(self):
        if not self:
            return
        scrap_map = {}
        scraps = self.env['scrap.order'].search([('construction_id', 'in', self.ids)])
        for scrap in scraps:
            scrap_map[scrap.construction_id.id] = scrap.id
        for rec in self:
            rec.scrap_id = scrap_map.get(rec.id, False)

    @api.depends('estimate_cost', 'scrap_id.total', 'accountancy_type')
    def _compute_accountancy(self):
        orders = ['equipment', 'material', 'labour', 'eng_arc', 'expense', 'insurance']
        AccountMove = self.env['account.move'].sudo()
        construction_ids = self.ids
        amounts_all = defaultdict(float)
        amounts_paid = defaultdict(float)

        if construction_ids:
            grouped_fields = ['construction_id', 'order_type']
            aggregated_fields = ['amount_total:sum']

            all_moves = AccountMove.read_group(
                [('construction_id', 'in', construction_ids)],
                aggregated_fields,
                grouped_fields
            )
            for entry in all_moves:
                construction = entry.get('construction_id')
                if not construction:
                    continue
                amount = entry.get('amount_total_sum', entry.get('amount_total', 0.0))
                amounts_all[(construction[0], entry.get('order_type'))] = amount

            paid_moves = AccountMove.read_group(
                [('construction_id', 'in', construction_ids), ('payment_state', '=', 'paid')],
                aggregated_fields,
                grouped_fields
            )
            for entry in paid_moves:
                construction = entry.get('construction_id')
                if not construction:
                    continue
                amount = entry.get('amount_total_sum', entry.get('amount_total', 0.0))
                amounts_paid[(construction[0], entry.get('order_type'))] = amount

        for rec in self:
            scrap_amount = rec.scrap_id.total if rec.scrap_id else 0.0
            totals_all = {order: amounts_all[(rec.id, order)] for order in orders}
            totals_paid = {order: amounts_paid[(rec.id, order)] for order in orders}

            total_all_amount = sum(totals_all.values())
            total_paid_amount = sum(totals_paid.values())

            rec.total_scrap_order_amount = scrap_amount

            if rec.accountancy_type == "all_bill":
                rec.total_equipment_po_amount = totals_all['equipment']
                rec.total_material_po_amount = totals_all['material']
                rec.total_labour_bill_amount = totals_all['labour']
                rec.total_engineer_bill_amount = totals_all['eng_arc']
                rec.total_extra_expense_amount = totals_all['expense']
                rec.total_insurance_amount = totals_all['insurance']

                rec.remaining_budget_amount = (rec.estimate_cost or 0.0) - total_all_amount + scrap_amount
                rec.remaining_equipment_po_amount = 0.0
                rec.remaining_material_po_amount = 0.0
                rec.remaining_labour_bill_amount = 0.0
                rec.remaining_engineer_bill_amount = 0.0
                rec.remaining_extra_expense_amount = 0.0
                rec.remaining_insurance_amount = 0.0
                rec.remaining_to_pay = 0.0
                rec.total_to_pay = total_all_amount
                rec.is_negative_remaining = rec.remaining_budget_amount < 0.0

            elif rec.accountancy_type == "paid":
                rec.total_equipment_po_amount = totals_paid['equipment']
                rec.total_material_po_amount = totals_paid['material']
                rec.total_labour_bill_amount = totals_paid['labour']
                rec.total_engineer_bill_amount = totals_paid['eng_arc']
                rec.total_extra_expense_amount = totals_paid['expense']
                rec.total_insurance_amount = totals_paid['insurance']

                rec.remaining_budget_amount = (rec.estimate_cost or 0.0) - total_paid_amount + scrap_amount
                rec.remaining_equipment_po_amount = max(totals_all['equipment'] - totals_paid['equipment'], 0.0)
                rec.remaining_material_po_amount = max(totals_all['material'] - totals_paid['material'], 0.0)
                rec.remaining_labour_bill_amount = max(totals_all['labour'] - totals_paid['labour'], 0.0)
                rec.remaining_engineer_bill_amount = max(totals_all['eng_arc'] - totals_paid['eng_arc'], 0.0)
                rec.remaining_extra_expense_amount = max(totals_all['expense'] - totals_paid['expense'], 0.0)
                rec.remaining_insurance_amount = max(totals_all['insurance'] - totals_paid['insurance'], 0.0)
                rec.total_to_pay = total_all_amount
                rec.remaining_to_pay = max(total_all_amount - total_paid_amount, 0.0)
                rec.is_negative_remaining = rec.remaining_budget_amount < 0.0
            else:
                rec.total_equipment_po_amount = 0.0
                rec.total_material_po_amount = 0.0
                rec.total_labour_bill_amount = 0.0
                rec.total_engineer_bill_amount = 0.0
                rec.total_extra_expense_amount = 0.0
                rec.total_insurance_amount = 0.0
                rec.remaining_budget_amount = 0.0
                rec.remaining_equipment_po_amount = 0.0
                rec.remaining_material_po_amount = 0.0
                rec.remaining_labour_bill_amount = 0.0
                rec.remaining_engineer_bill_amount = 0.0
                rec.remaining_extra_expense_amount = 0.0
                rec.remaining_insurance_amount = 0.0
                rec.remaining_to_pay = 0.0
                rec.total_to_pay = 0.0
                rec.is_negative_remaining = False

    def _compute_sub_project_count(self):
        for rec in self:
            if rec.project_id:
                domain = [('parent_id', '=', rec.project_id.id)]
                if rec.site_id:
                    domain.append(('site_id', '=', rec.site_id.id))
                else:
                    domain.append(('site_id', '!=', False))
                rec.sub_project_count = self.env['project.project'].search_count(domain)
            else:
                rec.sub_project_count = 0

    def _compute_po_count(self):
        PurchaseOrder = self.env['purchase.order'].sudo()
        AccountMove = self.env['account.move'].sudo()
        CalendarEvent = self.env['calendar.event'].sudo()
        StockPicking = self.env['stock.picking'].sudo()

        construction_ids = self.ids
        purchase_counts = defaultdict(int)
        invoice_counts = defaultdict(int)
        meeting_counts = defaultdict(int)

        equipment_po_map = {}
        material_po_map = {}
        all_purchase_ids = set()

        for rec in self:
            equipment_po_ids = set(rec.equipment_ids.mapped('equipment_po_id').ids)
            material_po_ids = set(rec.material_ids.mapped('material_po_id').ids)
            equipment_po_map[rec.id] = equipment_po_ids
            material_po_map[rec.id] = material_po_ids
            all_purchase_ids.update(equipment_po_ids)
            all_purchase_ids.update(material_po_ids)

        if construction_ids:
            purchase_data = PurchaseOrder.read_group(
                [('construction_id', 'in', construction_ids)],
                ['__count'],
                ['construction_id', 'order_type']
            )
            for entry in purchase_data:
                construction = entry.get('construction_id')
                if not construction:
                    continue
                purchase_counts[(construction[0], entry.get('order_type'))] = entry.get('__count', 0)

            invoice_data = AccountMove.read_group(
                [('construction_id', 'in', construction_ids)],
                ['__count'],
                ['construction_id', 'order_type']
            )
            for entry in invoice_data:
                construction = entry.get('construction_id')
                if not construction:
                    continue
                invoice_counts[(construction[0], entry.get('order_type'))] = entry.get('__count', 0)

            meeting_data = CalendarEvent.read_group(
                [('construction_id', 'in', construction_ids), ('is_construction_meeting', '=', True)],
                ['__count'],
                ['construction_id']
            )
            for entry in meeting_data:
                construction = entry.get('construction_id')
                if not construction:
                    continue
                meeting_counts[construction[0]] = entry.get('__count', 0)

        delivered_purchase_ids = set()
        if all_purchase_ids:
            picking_data = StockPicking.read_group(
                [('purchase_id', 'in', list(all_purchase_ids))],
                ['__count'],
                ['purchase_id']
            )
            for entry in picking_data:
                purchase = entry.get('purchase_id')
                if purchase:
                    delivered_purchase_ids.add(purchase[0])

        for rec in self:
            rec.equip_po_count = purchase_counts[(rec.id, 'equipment')]
            rec.material_po_count = purchase_counts[(rec.id, 'material')]
            rec.equip_bill_count = invoice_counts[(rec.id, 'equipment')]
            rec.material_bill_count = invoice_counts[(rec.id, 'material')]
            rec.labour_bill_count = invoice_counts[(rec.id, 'labour')]
            rec.eng_arc_bill_count = invoice_counts[(rec.id, 'eng_arc')]
            rec.expense_bill_count = invoice_counts[(rec.id, 'expense')]
            rec.meeting_count = meeting_counts.get(rec.id, 0)

            equipment_pos = equipment_po_map.get(rec.id, set())
            material_pos = material_po_map.get(rec.id, set())
            rec.equipment_delivery_order_count = len(equipment_pos & delivered_purchase_ids)
            rec.material_delivery_order_count = len(material_pos & delivered_purchase_ids)

    @api.onchange('document_template_id')
    def _onchange_document_template(self):
        for rec in self:
            if rec.document_template_id:
                rec.document_ids = [(5, 0, 0)]
                lines = []
                for line in rec.document_template_id.document_template_line_ids:
                    lines.append((0, 0, {
                        'document_type': line.document_type_id,
                        'role_id': line.role_id,
                    }))
                rec.document_ids = lines

    @api.depends('document_ids')
    def _compute_is_approved(self):
        for rec in self:
            documents = rec.document_ids
            rec.is_approved_document = bool(documents) and all(doc.state == "approved" for doc in documents)

    @api.depends('construction_engineer_ids')
    def _compute_engineer_charges(self):
        for rec in self:
            rec.total_engineer_charges = sum(rec.construction_engineer_ids.mapped('charges'))

    @api.depends('construction_rate', 'area_plot')
    def _compute_cost_of_construction(self):
        for rec in self:
            if rec.construction_rate and rec.area_plot:
                rec.cost_of_construction = rec.construction_rate * rec.area_plot
            else:
                rec.cost_of_construction = 0.0

    @api.depends(
        'estimate_cost',
        'total_equipment_po_amount',
        'total_material_po_amount',
        'total_labour_bill_amount',
        'total_engineer_bill_amount',
        'total_extra_expense_amount',
        'total_insurance_amount',
    )
    def _compute_profit_margin(self):
        for rec in self:
            total_cost = sum([
                rec.total_equipment_po_amount or 0.0,
                rec.total_material_po_amount or 0.0,
                rec.total_labour_bill_amount or 0.0,
                rec.total_engineer_bill_amount or 0.0,
                rec.total_extra_expense_amount or 0.0,
                rec.total_insurance_amount or 0.0,
            ])
            rec.profit_margin = (rec.estimate_cost or 0.0) - total_cost

    def action_confirm(self):
        for rec in self:
            rec.stage = 'confirm'

    def action_cancel(self):
        for rec in self:
            rec.stage = 'cancel'

    def action_complete(self):
        for rec in self:
            rec.stage = "done"

    def action_close_project(self):
        for rec in self:
            rec.stage = "close"

    def action_gmap_location(self):
        self.ensure_one()
        if self.longitude and self.latitude:
            longitude = self.longitude
            latitude = self.latitude
            http_url = 'https://maps.google.com/maps?q=loc:' + latitude + ',' + longitude
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': http_url,
            }
        else:
            raise ValidationError("! Enter Proper Longitude and Latitude Values")

    def action_start_construction(self):
        self.ensure_one()
        if self.project_id:
            return
        if not self.site_id:
            raise ValidationError("Please set a construction site before starting the project.")
        self.stage = 'in_progress'
        data = {
            'name': self.site_id.name + " - " + self.name,
            'construction_id': self.id,
            'partner_id': self.customer_company_id.id
        }
        project_id = self.env['project.project'].create(data)
        self.project_id = project_id.id

    def action_approved(self):
        for rec in self:
            if not rec.is_approved_document:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': 'Document Not Approved !',
                        'message': "Some documents are not approved. Please review them and try again.",
                        'sticky': False,
                    }
                }
        self.write({'stage': 'a_costing'})
        return True

    # Equipment Purchase Order
    def action_equipment_po(self):
        for rec in self:
            if rec.equipment_ids:
                for data in rec.equipment_ids:
                    if not data.equipment_po_id:
                        if data.total_equipment_cost > 0:
                            lines = []
                            for product in data.construction_equipment_ids:
                                record = {
                                    'product_id': product.equipment_id.id,
                                    'name': dict(product._fields['cost_type'].selection).get(product.cost_type),
                                    'product_qty': product.qty,
                                    'product_uom': product.equipment_id.uom_po_id.id,
                                    'price_unit': product.cost,
                                }
                                lines.append((0, 0, record))
                            record = {
                                'partner_id': rec.customer_company_id.id,
                                'order_line': lines,
                                'construction_id': rec.id,
                                'order_type': 'equipment'
                            }
                            purchase_order_id = self.env['purchase.order'].create(record)
                            purchase_order_id.equipment_id = data.id
                            data.equipment_po_id = purchase_order_id.id

    def action_view_equipment_po(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment Purchase Order',
            'res_model': 'purchase.order',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'equipment')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'equipment'},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_equipment_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment Purchase Bills',
            'res_model': 'account.move',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'equipment')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'equipment'},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_delivery_order(self):
        self.ensure_one()
        purchase_ids = self.equipment_ids.mapped('equipment_po_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Equipment Delivery Orders',
            'res_model': 'stock.picking',
            'domain': [('purchase_id', 'in', purchase_ids)],
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    # Material Purchase Order
    def action_material_po(self):
        for rec in self:
            if rec.material_ids:
                for data in rec.material_ids:
                    if not data.material_po_id:
                        if data.total_material_cost > 0:
                            lines = []
                            for product in data.construction_material_ids:
                                record = {
                                    'product_id': product.material_id.id,
                                    'name': "Material",
                                    'product_qty': product.qty,
                                    'product_uom': product.uom_id.id,
                                    'price_unit': product.cost,
                                }
                                lines.append((0, 0, record))
                            record = {
                                'partner_id': rec.customer_company_id.id,
                                'order_line': lines,
                                'construction_id': rec.id,
                                'order_type': 'material'
                            }
                            purchase_order_id = self.env['purchase.order'].create(record)
                            purchase_order_id.material_id = data.id
                            data.material_po_id = purchase_order_id.id

    def action_view_material_po(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Purchase Order',
            'res_model': 'purchase.order',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'material')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'material'},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_material_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Purchase Bill',
            'res_model': 'account.move',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'material')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'material'},
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    def action_view_delivery_order_material(self):
        self.ensure_one()
        purchase_ids = self.material_ids.mapped('material_po_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Delivery Orders',
            'res_model': 'stock.picking',
            'domain': [('purchase_id', 'in', purchase_ids)],
            'view_mode': 'tree,form,kanban',
            'target': 'current'
        }

    # Construction Task
    def action_view_construction_task(self):
        self.ensure_one()
        if not self.project_id:
            raise ValidationError("No project is linked to this construction.")

        task_stages = self.env['project.task.type'].search([('is_construction_stages', '=', True)])
        for stage in task_stages:
            if self.project_id.id not in stage.project_ids.ids:
                stage.write({'project_ids': [(4, self.project_id.id)]})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'kanban,form,tree,calendar,pivot',
            'domain': [('construction_id', '=', self.id), ('project_id', '=', self.project_id.id)],
            'context': {'default_construction_id': self.id, 'default_project_id': self.project_id.id},
            'target': 'current'
        }

    # Sub Projects
    def action_view_sub_projects(self):
        self.ensure_one()
        if not self.project_id:
            raise ValidationError("No project is linked to this construction.")
        
        # Ensure the main project is not a sub-project itself
        if self.project_id.parent_id:
            raise ValidationError("Cannot view sub-projects from a sub-project. Please open the main project first.")

        context = {
            'default_parent_id': self.project_id.id,
            'default_construction_id': self.id,
            'default_site_id': self.site_id.id if self.site_id else False,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Projects',
            'res_model': 'project.project',
            'view_mode': 'kanban,tree,form',
            'domain': [('parent_id', '=', self.project_id.id), ('construction_id', '!=', False), ('site_id', '!=', False)],
            'context': context,
            'target': 'current'
        }

    # Labour Bill
    def action_labours_bill(self):
        for rec in self:
            if rec.construction_labours_ids:
                for data in rec.construction_labours_ids:
                    if not data.labour_bill_id:
                        labours = ""
                        for lab in data.labours_ids:
                            labours = labours + "{}, ".format(lab.name)
                        record = {
                            'product_id': self.env.ref('construction_management.construction_product_1').id,
                            'name': "Labours : \n" + labours,
                            'quantity': 1,
                            'price_unit': data.total_labour_cost
                        }
                        line = [(0, 0, record)]
                        main_data = {
                            'partner_id': data.labour_responsible_id.id,
                            'move_type': 'in_invoice',
                            'invoice_date': fields.date.today(),
                            'construction_id': rec.id,
                            'invoice_line_ids': line,
                            'order_type': 'labour'
                        }
                        bill_id = self.env['account.move'].create(main_data)
                        bill_id.action_post()
                        data.labour_bill_id = bill_id.id

    def action_view_labour_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Labour Bill',
            'res_model': 'account.move',
            'view_mode': 'tree,form,kanban',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'labour')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'labour'},
            'target': 'current'
        }

    # Engineer & Architect Bill
    def action_eng_arc_bill(self):
        for rec in self:
            if rec.construction_engineer_ids:
                for record in rec.construction_engineer_ids:
                    if record.eng_invoice_line_ids:
                        for data in record.eng_invoice_line_ids:
                            if not data.eng_arc_bill_id:
                                record = {
                                    'product_id': self.env.ref('construction_management.construction_product_2').id,
                                    'name': data.name + " Bill",
                                    'quantity': 1,
                                    'price_unit': data.charges
                                }
                                line = [(0, 0, record)]
                                main_data = {
                                    'partner_id': data.construction_engineer_id.employee_id.id,
                                    'move_type': 'in_invoice',
                                    'invoice_date': fields.date.today(),
                                    'construction_id': rec.id,
                                    'invoice_line_ids': line,
                                    'order_type': 'eng_arc'
                                }
                                bill_id = self.env['account.move'].create(main_data)
                                bill_id.action_post()
                                data.eng_arc_bill_id = bill_id.id

    def action_view_eng_arc_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Engineer & Architect Bill',
            'res_model': 'account.move',
            'view_mode': 'tree,form,kanban',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'eng_arc')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'eng_arc'},
            'target': 'current'
        }

    # Construction Expense
    def action_view_expense_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Bill',
            'res_model': 'account.move',
            'view_mode': 'tree,form,kanban',
            'domain': [('construction_id', '=', self.id), ('order_type', '=', 'expense')],
            'context': {'default_construction_id': self.id, 'default_order_type': 'expense'},
            'target': 'current'
        }

    def action_view_meeting(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Meetings',
            'res_model': 'calendar.event',
            'domain': [('construction_id', '=', self.id), ('is_construction_meeting', '=', True)],
            'context': {'default_construction_id': self.id, 'default_is_construction_meeting': True},
            'view_mode': 'tree,form,calendar',
            'target': 'current'
        }


class EquipmentDetails(models.Model):
    _inherit = 'product.product'

    is_equipment = fields.Boolean(string="Is Equipment")
    is_material = fields.Boolean(string="Is Material")
    is_expense_product = fields.Boolean(string="Is Expense")


class ConstructionEquipment(models.Model):
    _name = "construction.equipment"
    _description = "Construction Equipment"

    name = fields.Char(string="Title")
    date = fields.Date(string="Date", default=fields.Date.today())
    construction_id = fields.Many2one('construction.details', string="Construction")
    construction_equipment_ids = fields.One2many('construction.equipment.line', 'construction_equip_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_equipment_cost = fields.Monetary(string="Total Cost", compute="_compute_equipment_cost")
    equipment_po_id = fields.Many2one('purchase.order', string="Purchase Order")
    state = fields.Selection(related="equipment_po_id.state", string="State")
    job_type_id = fields.Many2one('construction.job', string="Job Type")

    @api.depends('construction_equipment_ids')
    def _compute_equipment_cost(self):
        for rec in self:
            amount = 0.0
            if rec.construction_equipment_ids:
                for data in rec.construction_equipment_ids:
                    amount = amount + data.cost
                rec.total_equipment_cost = amount
            else:
                rec.total_equipment_cost = 0.0


class ConstructionEquipmentLine(models.Model):
    _name = 'construction.equipment.line'
    _description = 'Construction Equipment Line'

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
    construction_equip_id = fields.Many2one('construction.equipment', string="Construction")


class ConstructionMaterial(models.Model):
    _name = 'construction.material'
    _description = 'Construction Material'

    name = fields.Char(string="Title")
    date = fields.Date(string="Date", default=fields.Date.today())
    construction_id = fields.Many2one('construction.details', string="Construction")
    construction_material_ids = fields.One2many('construction.material.line', 'construction_material_id',
                                                string="Material")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    material_po_id = fields.Many2one('purchase.order', string="Purchase Order")
    total_material_cost = fields.Monetary(string="Total Cost", compute="_compute_material_cost")
    state = fields.Selection(related="material_po_id.state", string="State")
    job_type_id = fields.Many2one('construction.job', string="Job Type")

    @api.depends('construction_material_ids')
    def _compute_material_cost(self):
        for rec in self:
            amount = 0.0
            if rec.construction_material_ids:
                for data in rec.construction_material_ids:
                    amount = amount + data.total_cost
                rec.total_material_cost = amount
            else:
                rec.total_material_cost = 0.0


class ConstructionMaterialLine(models.Model):
    _name = "construction.material.line"
    _description = "Construction Material Line"

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
    construction_material_id = fields.Many2one('construction.material', string="Construction")
    uom_id = fields.Many2one(related="material_id.uom_po_id", string="Unit of Measure")

    @api.depends('material_id', 'qty', 'cost')
    def _compute_total_cost(self):
        for rec in self:
            if rec.material_id:
                rec.total_cost = rec.qty * rec.cost
            else:
                rec.total_cost = 0.0


class ConstructionEngineerLine(models.Model):
    _name = "construction.engineer.line"
    _description = "Construction Engineer Line"
    _rec_name = 'role_id'

    role_id = fields.Many2one('construction.employee', string="Role")
    employee_id = fields.Many2one('res.partner', string="Employee", domain="[('role_id', '=', role_id)]")
    image_1920 = fields.Image(related="employee_id.image_1920")
    note = fields.Html(string="Note", default="Construction Employee Bill")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string="Charges")
    construction_id = fields.Many2one('construction.details', string="Construction")
    eng_invoice_line_ids = fields.One2many('engineer.invoice.line', 'construction_engineer_id')
    invoice_paid_status = fields.Selection([('paid', 'Paid'), ('not_paid', 'Not Paid')], compute="_compute_count")

    @api.depends('eng_invoice_line_ids')
    def _compute_count(self):
        for rec in self:
            if rec.eng_invoice_line_ids:
                for data in rec.eng_invoice_line_ids:
                    if not data.payment_state == "paid":
                        rec.invoice_paid_status = "not_paid"
                    else:
                        rec.invoice_paid_status = "paid"
            else:
                rec.invoice_paid_status = ""


class EngineerInvoiceLine(models.Model):
    _name = 'engineer.invoice.line'
    _description = "Engineer Invoices"

    name = fields.Char(string="Title")
    construction_engineer_id = fields.Many2one('construction.engineer.line')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string="Charges")
    date = fields.Date(string="Date", default=fields.Date.today())
    eng_arc_bill_id = fields.Many2one('account.move', string="Bill")
    payment_state = fields.Selection(related='eng_arc_bill_id.payment_state', string="Payment Status", store=True)

    @api.model
    def default_get(self, fields):
        res = super(EngineerInvoiceLine, self).default_get(fields)
        charges = self._context.get('charges')
        res['charges'] = charges
        return res


class DocumentType(models.Model):
    _name = 'document.type'
    _description = "Document Type"

    name = fields.Char(string="Title", required=True)
    type = fields.Selection([('project', 'Project'), ('job_order', 'Job Order')], string="Document for")


class DocumentTemplate(models.Model):
    _name = "document.template"
    _description = "Document Template"

    name = fields.Char(string="Title")
    document_template_line_ids = fields.One2many('document.template.line', 'template_id', string="Template")


class DocumentTemplateLine(models.Model):
    _name = "document.template.line"
    _description = "Document Template Line"

    document_type_id = fields.Many2one('document.type', string="Document Type")
    role_id = fields.Many2one('construction.employee', string="Submitted By")
    template_id = fields.Many2one('document.template', string="Template")


class ConstructionDocumentLine(models.Model):
    _name = 'construction.document.line'
    _description = "Construction Document Line"
    _rec_name = "document_type"

    document_type = fields.Many2one("document.type", string="Type")
    role_id = fields.Many2one("construction.employee", string="Role")
    submit_employee_id = fields.Many2one('res.partner', string="Submitted By",
                                         domain="[('role_id', '=', role_id)]")
    date = fields.Date(string="Date", default=fields.Date.today())
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('approved', 'Approved'), ('failed', 'Fail')],
        string="Status", default='draft', readonly=True, store=True)
    document = fields.Binary(string='Document')
    file_name = fields.Char(string='File Name')
    construction_id = fields.Many2one('construction.details')

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_failed(self):
        for rec in self:
            rec.state = 'failed'


class ConstructionLabourLine(models.Model):
    _name = 'construction.labour.line'
    _description = 'Construction Labour Line'

    title = fields.Char(string="Title")
    date = fields.Date(string="Date", default=fields.Date.today())
    labour_responsible_id = fields.Many2one('res.partner', string="Labour Responsible",
                                            domain=[('employee_type', '=', 'manager')])
    labours_ids = fields.Many2many('hr.employee', string="Labours")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total_labour_cost = fields.Monetary(string="Total Cost")
    construction_id = fields.Many2one('construction.details')
    labour_bill_id = fields.Many2one('account.move', string="Bill")
    payment_state = fields.Selection(related='labour_bill_id.payment_state', string="Payment Status")

    @api.onchange('labours_ids')
    def _onchange_labour_cost(self):
        for rec in self:
            amount = 0.0
            if rec.labours_ids:
                for data in rec.labours_ids:
                    amount = amount + data.charges
                rec.total_labour_cost = amount
            else:
                rec.total_labour_cost = 0.0


class ConstructionExpense(models.Model):
    _name = "construction.expense"
    _description = "Construction Expense"
    _rec_name = "expense_product_id"

    expense_product_id = fields.Many2one(
        'product.product',
        string="Expense",
        domain="[('is_expense_product','=',True),('type','=','service')]",
    )
    date = fields.Date(string="Date", default=fields.Date.today())
    note = fields.Char(string="Note")
    expense_bill_id = fields.Many2one('account.move', string="Bill")
    construction_id = fields.Many2one('construction.details')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    cost = fields.Monetary(string="Cost")
    payment_state = fields.Selection(related='expense_bill_id.payment_state', string="Payment Status")

    @api.onchange('expense_product_id')
    def _onchange_expense_price(self):
        for rec in self:
            if rec.expense_product_id:
                rec.cost = rec.expense_product_id.lst_price
            else:
                rec.cost = 0.0

    def action_expense_bill(self):
        for rec in self:
            if rec.construction_id.stage != "in_progress":
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': 'Start Construction to Create Bill and Invoice',
                        'sticky': False,
                    }
                }

        for rec in self:
            if not rec.expense_product_id:
                continue
            record = {
                'product_id': rec.expense_product_id.id,
                'name': rec.note,
                'quantity': 1,
                'price_unit': rec.cost
            }
            line = [(0, 0, record)]
            main_data = {
                'partner_id': rec.construction_id.customer_company_id.id,
                'move_type': 'in_invoice',
                'invoice_date': fields.date.today(),
                'construction_id': rec.construction_id.id,
                'invoice_line_ids': line,
                'order_type': 'expense'
            }
            bill_id = self.env['account.move'].create(main_data)
            bill_id.action_post()
            rec.expense_bill_id = bill_id.id
        return True


class ConstructionRisk(models.Model):
    _name = "construction.risk"
    _description = "Construction Risk"

    risk_type = fields.Selection(
        [('project', 'Project'), ('labours', 'Labours & Workers'), ('material', 'Material'), ('equipment', 'Equipment'),
         ('other', 'Other')],
        string="Risk for")
    note = fields.Char(string="Note")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    construction_id = fields.Many2one('construction.details', string="Construction")
    date = fields.Date(string='Date', default=fields.Date.today())

    # Insurance Details
    is_insurance = fields.Boolean(string="Is Insurance")
    policy_no = fields.Char(string='Policy No.')
    insurance_date = fields.Date(string='Issue Date')
    issue_by = fields.Char(string='Issued By')
    policy_name = fields.Char(string='Policy Name')
    total_charge = fields.Monetary(string='Total Charge')
    term = fields.Html(string='Insurance Terms')
    risk_ids = fields.Many2many('policy.risk', string='Risk Covered')
    policy_added = fields.Boolean(string='Policy Added')
    insurance_invoice_id = fields.Many2one('account.move', string="Invoice")
    payment_state = fields.Selection(related='insurance_invoice_id.payment_state', string="Payment Status")

    def action_insurance_bill(self):
        self.ensure_one()
        if self.construction_id.stage == "in_progress":
            if self.is_insurance:
                if self.total_charge > 0:
                    record = {
                        'product_id': self.env.ref('construction_management.construction_product_3').id,
                        'name': self.policy_name + " " + self.policy_no,
                        'quantity': 1,
                        'price_unit': self.total_charge
                    }
                    line = [(0, 0, record)]
                    main_data = {
                        'partner_id': self.construction_id.customer_company_id.id,
                        'move_type': 'out_invoice',
                        'invoice_date': fields.date.today(),
                        'construction_id': self.construction_id.id,
                        'invoice_line_ids': line,
                        'order_type': 'insurance'
                    }
                    invoice_id = self.env['account.move'].create(main_data)
                    invoice_id.action_post()
                    self.insurance_invoice_id = invoice_id.id
                    return True
                else:
                    message = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'danger',
                            'title': ('Insurance Charge Cannot be Zero !'),
                            'sticky': False,
                        }
                    }
                    return message
            else:
                message = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'type': 'danger',
                        'title': ('No Insurance Found !'),
                        'sticky': False,
                    }
                }
                return message
        else:
            message = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': ('Start Construction to Create Bill and Invoice'),
                    'sticky': False,
                }
            }
            return message


class PolicyRisk(models.Model):
    _name = 'policy.risk'
    _description = 'Policy Risk Details'

    name = fields.Char(string='Title')
    desc = fields.Char(string='Description')


class ScrapOrder(models.Model):
    _name = 'scrap.order'
    _description = "Construction Scrap Order"
    _rec_name = 'name'

    name = fields.Char(string='Sequence', required=True, readonly=True, default=lambda self: ('New'))
    construction_id = fields.Many2one('construction.details', string="Construction Site")
    date = fields.Date(string="Date", default=fields.Date.today())
    note = fields.Char(string="Note")
    scrap_order_line_ids = fields.One2many('scrap.order.line', 'scrap_order_id', string="Scrap Order Line")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    total = fields.Monetary(string="Total", compute="_compute_net_total", store=True)

    @api.depends('scrap_order_line_ids')
    def _compute_net_total(self):
        for rec in self:
            amount = 0.0
            if rec.scrap_order_line_ids:
                for data in rec.scrap_order_line_ids:
                    amount = amount + data.net_total
                rec.total = amount
            else:
                rec.total = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', ('New')) == ('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'scrap.order') or ('New')
        return super(ScrapOrder, self).create(vals_list)

    _sql_constraints = [
        ('unique_construction_id', 'unique (construction_id)',
         'Only one Scrape Order is Valid for One Construction Project')
    ]


class ScrapOrderLine(models.Model):
    _name = 'scrap.order.line'
    _description = "Scrap Order Line"

    scrap_type = fields.Selection([('material', 'Material'), ('equipment', 'Equipment')], string="Scrap of")
    product_id = fields.Many2one("product.product", string="Product")
    qty = fields.Integer(string="Qty.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    dep_cost = fields.Monetary(string="Value")
    scrap_order_id = fields.Many2one('scrap.order', string="Scrap Order")
    net_total = fields.Monetary(string="Total Value", compute="_compute_net_total")

    @api.onchange('scrap_type')
    def filter_materia_equipment(self):
        construction_id = self._context.get('construction_id')
        site_material_record = self.env['construction.material'].search(
            [('construction_id', '=', construction_id)]).mapped('id')
        material_record = self.env['construction.material.line'].search(
            [('construction_material_id', 'in', site_material_record)]).mapped('material_id').mapped('id')
        site_equip_record = self.env['construction.equipment'].search(
            [('construction_id', '=', construction_id)]).mapped('id')
        equip_record = self.env['construction.equipment.line'].search(
            [('construction_equip_id', 'in', site_equip_record)]).mapped('equipment_id').mapped('id')
        for rec in self:
            if rec.scrap_type == "material":
                return {'domain': {'product_id': [('id', 'in', material_record)]}}
            elif rec.scrap_type == "equipment":
                return {'domain': {'product_id': [('id', 'in', equip_record)]}}

    @api.depends('dep_cost', 'qty')
    def _compute_net_total(self):
        for rec in self:
            if rec.product_id:
                rec.net_total = rec.dep_cost * rec.qty
            else:
                rec.net_total = 0


class SiteInspection(models.Model):
    _name = 'site.inspection'
    _description = "Site Inspection of Construction Project"

    construction_id = fields.Many2one('construction.details', string="Construction")
    date = fields.Date(string="Date")
    note = fields.Char(string="Note")
    task_id = fields.Many2one("project.task")
    date_deadline = fields.Date("Deadline")
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user and self.env.user.id or False)

    def action_view_task(self):
        self.ensure_one()
        if not self.task_id:
            raise ValidationError("No inspection task linked to this record.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inspection Task',
            'res_model': 'project.task',
            'res_id': self.task_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class ConstructionJob(models.Model):
    _name = "construction.job"
    _description = "Construction Job Type"

    name = fields.Char(string="Job Type")
