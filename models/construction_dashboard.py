# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models


class ConstructionDashboard(models.TransientModel):
    _name = 'construction.dashboard'
    _description = "Construction Dashboard"

    # Stats Fields
    total_site = fields.Integer(string="Total Sites", compute='_compute_stats', store=False)
    planning_site = fields.Integer(string="Planning Sites", compute='_compute_stats', store=False)
    job_order = fields.Integer(string="Job Orders", compute='_compute_stats', store=False)
    document_verified = fields.Integer(string="Document Verified", compute='_compute_stats', store=False)
    site_in_progress = fields.Integer(string="In Progress", compute='_compute_stats', store=False)
    complete_site = fields.Integer(string="Completed", compute='_compute_stats', store=False)
    close_site = fields.Integer(string="Closed", compute='_compute_stats', store=False)
    cancel_site = fields.Integer(string="Cancelled", compute='_compute_stats', store=False)
    
    # Project Stats
    total_projects = fields.Integer(string="Total Projects", compute='_compute_stats', store=False)
    total_sub_projects = fields.Integer(string="Total Sub Projects", compute='_compute_stats', store=False)
    active_phases = fields.Integer(string="Active Phases", compute='_compute_stats', store=False)
    active_work_orders = fields.Integer(string="Active Work Orders", compute='_compute_stats', store=False)
    
    # Material & Equipment
    total_equipment_po = fields.Integer(string="Equipment POs", compute='_compute_stats', store=False)
    total_material_po = fields.Integer(string="Material POs", compute='_compute_stats', store=False)
    total_requisitions = fields.Integer(string="Material Requisitions", compute='_compute_stats', store=False)
    
    # Financial
    total_budget = fields.Monetary(string="Total Budget", compute='_compute_stats', store=False)
    total_spent = fields.Monetary(string="Total Spent", compute='_compute_stats', store=False)
    remaining_budget = fields.Monetary(string="Remaining Budget", compute='_compute_stats', store=False)
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends()
    def _compute_stats(self):
        """Compute all dashboard statistics"""
        for rec in self:
            # Site Statistics
            rec.total_site = self.env['construction.site'].search_count([])
            rec.planning_site = self.env['job.costing'].search_count([('state', '=', 'planning')])
            rec.job_order = self.env['construction.details'].search_count([('stage', '=', 'confirm')])
            rec.document_verified = self.env['construction.details'].search_count([('stage', '=', 'a_costing')])
            rec.site_in_progress = self.env['construction.details'].search_count([('stage', '=', 'in_progress')])
            rec.complete_site = self.env['construction.details'].search_count([('stage', '=', 'done')])
            rec.close_site = self.env['construction.details'].search_count([('stage', '=', 'close')])
            rec.cancel_site = self.env['construction.details'].search_count([('stage', '=', 'cancel')])
            
            # Project Statistics
            rec.total_projects = self.env['project.project'].search_count([('construction_id', '!=', False), ('parent_id', '=', False)])
            rec.total_sub_projects = self.env['project.project'].search_count([('parent_id', '!=', False), ('construction_id', '!=', False)])
            rec.active_phases = self.env['construction.project.phase'].search_count([('state', 'in', ['draft', 'in_progress'])])
            rec.active_work_orders = self.env['construction.work.order'].search_count([('state', 'in', ['approved', 'in_progress'])])
            
            # Material & Equipment
            rec.total_equipment_po = self.env['purchase.order'].search_count([('construction_id', '!=', False), ('order_type', '=', 'equipment')])
            rec.total_material_po = self.env['purchase.order'].search_count([('construction_id', '!=', False), ('order_type', '=', 'material')])
            rec.total_requisitions = self.env['construction.material.requisition'].search_count([])
            
            # Financial Statistics
            constructions = self.env['construction.details'].search([])
            rec.total_budget = sum(constructions.mapped('estimate_cost') or [0])
            rec.total_spent = sum(constructions.mapped('total_to_pay') or [0])
            rec.remaining_budget = rec.total_budget - rec.total_spent

    @api.model
    def default_get(self, fields_list):
        """Return default values for dashboard"""
        res = super().default_get(fields_list)
        # Compute stats directly without creating a record to avoid recursion
        # Site Statistics
        if 'total_site' in fields_list:
            res['total_site'] = self.env['construction.site'].search_count([])
        if 'planning_site' in fields_list:
            res['planning_site'] = self.env['job.costing'].search_count([('state', '=', 'planning')])
        if 'job_order' in fields_list:
            res['job_order'] = self.env['construction.details'].search_count([('stage', '=', 'confirm')])
        if 'document_verified' in fields_list:
            res['document_verified'] = self.env['construction.details'].search_count([('stage', '=', 'a_costing')])
        if 'site_in_progress' in fields_list:
            res['site_in_progress'] = self.env['construction.details'].search_count([('stage', '=', 'in_progress')])
        if 'complete_site' in fields_list:
            res['complete_site'] = self.env['construction.details'].search_count([('stage', '=', 'done')])
        if 'close_site' in fields_list:
            res['close_site'] = self.env['construction.details'].search_count([('stage', '=', 'close')])
        if 'cancel_site' in fields_list:
            res['cancel_site'] = self.env['construction.details'].search_count([('stage', '=', 'cancel')])
        
        # Project Statistics
        if 'total_projects' in fields_list:
            res['total_projects'] = self.env['project.project'].search_count([('construction_id', '!=', False), ('parent_id', '=', False)])
        if 'total_sub_projects' in fields_list:
            res['total_sub_projects'] = self.env['project.project'].search_count([('parent_id', '!=', False), ('construction_id', '!=', False)])
        if 'active_phases' in fields_list:
            res['active_phases'] = self.env['construction.project.phase'].search_count([('state', 'in', ['draft', 'in_progress'])])
        if 'active_work_orders' in fields_list:
            res['active_work_orders'] = self.env['construction.work.order'].search_count([('state', 'in', ['approved', 'in_progress'])])
        
        # Material & Equipment
        if 'total_equipment_po' in fields_list:
            res['total_equipment_po'] = self.env['purchase.order'].search_count([('construction_id', '!=', False), ('order_type', '=', 'equipment')])
        if 'total_material_po' in fields_list:
            res['total_material_po'] = self.env['purchase.order'].search_count([('construction_id', '!=', False), ('order_type', '=', 'material')])
        if 'total_requisitions' in fields_list:
            res['total_requisitions'] = self.env['construction.material.requisition'].search_count([])
        
        # Financial Statistics
        if any(f in fields_list for f in ['total_budget', 'total_spent', 'remaining_budget']):
            constructions = self.env['construction.details'].search([])
            budget = sum(constructions.mapped('estimate_cost') or [0])
            spent = sum(constructions.mapped('total_to_pay') or [0])
            if 'total_budget' in fields_list:
                res['total_budget'] = budget
            if 'total_spent' in fields_list:
                res['total_spent'] = spent
            if 'remaining_budget' in fields_list:
                res['remaining_budget'] = budget - spent
        
        return res

    def action_view_sites(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Construction Sites',
            'res_model': 'construction.site',
            'view_mode': 'tree,form',
            'target': 'current'
        }

    def action_view_job_costing(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job Costing',
            'res_model': 'job.costing',
            'view_mode': 'tree,form',
            'domain': [('state', '=', 'planning')],
            'target': 'current'
        }

    def action_view_construction_details(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Construction Details',
            'res_model': 'construction.details',
            'view_mode': 'tree,form',
            'domain': [('stage', '=', 'confirm')],
            'target': 'current'
        }

    def action_view_in_progress(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'In Progress Sites',
            'res_model': 'construction.details',
            'view_mode': 'tree,form',
            'domain': [('stage', '=', 'in_progress')],
            'target': 'current'
        }

    def action_view_completed(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Completed Sites',
            'res_model': 'construction.details',
            'view_mode': 'tree,form',
            'domain': [('stage', '=', 'done')],
            'target': 'current'
        }

    @api.model
    def get_construction_stats(self):
        construction_obj = self.env['construction.details'].sudo()
        total_site = self.env['construction.site'].search_count([])
        planning_site = self.env['job.costing'].search_count([('state', '=', 'planning')])
        job_order = construction_obj.search_count([('stage', '=', 'confirm')])
        document_verified = construction_obj.search_count([('stage', '=', 'a_costing')])
        site_in_progress = construction_obj.search_count([('stage', '=', 'in_progress')])
        complete_site = construction_obj.search_count([('stage', '=', 'done')])
        close_site = construction_obj.search_count([('stage', '=', 'close')])
        cancel_site = construction_obj.search_count([('stage', '=', 'cancel')])
        site_state = [['Job Order', 'Document Verified', 'In Progress', 'Complete', 'Close', 'Cancel'],
                      [job_order, document_verified, site_in_progress, complete_site, close_site, cancel_site]]
        data = {
            'total_site': total_site,
            'planning_site': planning_site,
            'job_order': job_order,
            'site_in_progress': site_in_progress,
            'complete_site': complete_site + close_site,
            'site_state': site_state,
            'construction_time_line': self.construction_time_line(),
            'material_equipment_po': self.material_equipment_po()
        }
        site, site_count = [], []
        site_ids = self.env['site.type'].search([])
        if not site_ids:
            data['site_type'] = [[], []]
        for s in site_ids:
            site_data = self.env['construction.site'].sudo().search_count([('site_type_id', '=', s.id)])
            site_count.append(site_data)
            site.append(s.name)
        data['site_type'] = [site, site_count]

        return data

    def construction_time_line(self):
        site_data = []
        construction_site_data = self.env['construction.details'].search([])
        for site in construction_site_data:
            if site.stage == "in_progress":
                site_data.append({
                    'name': str(site.name) + " " + str(site.site_id.name),
                    'start_date': str(site.start_date),
                    'end_date': str(site.end_date),
                })
        return site_data

    def material_equipment_po(self):
        site_name = []
        equipment_po = []
        material_po = []
        construction_site = self.env['construction.details'].sudo().search([])
        for site in construction_site:
            if site.stage == "in_progress":
                site_name.append(site.site_id.name)
                equipment_po.append(site.equip_po_count)
                material_po.append(site.material_po_count)
        data = [site_name, equipment_po, material_po]
        return data
