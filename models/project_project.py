# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ConstructionProject(models.Model):
    _inherit = 'project.project'

    construction_id = fields.Many2one('construction.details', string="Construction", check_company=True)
    site_id = fields.Many2one('construction.site', string="Site Project", check_company=True, 
                              help="Site Project that this project belongs to")
    image = fields.Image(string='Company Logo')
    parent_id = fields.Many2one('project.project', string='Parent Project', index=True, check_company=True,
                                help="Select a parent project to make this a sub-project. Sub-projects must be linked to a Site Project.")
    child_ids = fields.One2many('project.project', 'parent_id', string='Sub Projects')
    child_count = fields.Integer(string='Sub Projects', compute='_compute_child_count')
    phase_ids = fields.One2many('construction.project.phase', 'project_id', string='Phases')
    phase_count = fields.Integer(string='Phases', compute='_compute_phase_count')
    
    # Approval Workflow
    project_state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Project Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If parent_id is set, inherit construction_id and site_id from parent
            if vals.get('parent_id'):
                parent = self.env['project.project'].browse(vals['parent_id'])
                if not parent.exists():
                    raise ValidationError("Selected parent project does not exist.")
                # Prevent circular reference - sub-project cannot be parent of its parent
                if parent.parent_id:
                    raise ValidationError("Cannot create a sub-project under another sub-project. Please select a main project.")
                # Inherit construction_id and site_id from parent
                if parent.construction_id:
                    vals['construction_id'] = parent.construction_id.id
                if parent.site_id:
                    vals['site_id'] = parent.site_id.id
            # If site_id is set but construction_id is not, try to get it from construction.details
            elif vals.get('site_id') and not vals.get('construction_id'):
                site = self.env['construction.site'].browse(vals['site_id'])
                if site.exists():
                    # Try to find construction.details for this site
                    construction = self.env['construction.details'].search([('site_id', '=', site.id)], limit=1)
                    if construction:
                        vals['construction_id'] = construction.id
        return super().create(vals_list)
    
    @api.constrains('parent_id', 'site_id')
    def _check_parent_id(self):
        """Ensure sub-projects must have a parent project, site_id, and construction_id"""
        for rec in self:
            if rec.parent_id:
                # Sub-project must have site_id (inherited from parent)
                if not rec.site_id:
                    raise ValidationError("Sub-project must be linked to a Site Project. It will be inherited from parent project.")
                # Sub-project must have construction_id (inherited from parent)
                if not rec.construction_id:
                    raise ValidationError("Sub-project must be linked to a Construction. It will be inherited from parent project.")
                # Prevent sub-project from being its own parent
                if rec.parent_id.id == rec.id:
                    raise ValidationError("A project cannot be its own parent.")
                # Prevent circular reference
                if rec.parent_id.parent_id:
                    raise ValidationError("Cannot create a sub-project under another sub-project. Please select a main project.")
            # Main projects (without parent) should have site_id if they have construction_id
            elif rec.construction_id and not rec.site_id:
                # Try to get site_id from construction.details
                if rec.construction_id.site_id:
                    rec.site_id = rec.construction_id.site_id

    @api.onchange('parent_id')
    def _onchange_parent_id(self):
        """Set construction_id and site_id from parent project when parent is selected"""
        if self.parent_id:
            if self.parent_id.construction_id:
                self.construction_id = self.parent_id.construction_id
            if self.parent_id.site_id:
                self.site_id = self.parent_id.site_id
    
    @api.onchange('construction_id')
    def _onchange_construction_id(self):
        """Set site_id from construction when construction is selected"""
        if self.construction_id and self.construction_id.site_id and not self.site_id:
            self.site_id = self.construction_id.site_id

    def _compute_child_count(self):
        for rec in self:
            domain = [('parent_id', '=', rec.id)]
            if rec.site_id:
                domain.append(('site_id', '=', rec.site_id.id))
            else:
                domain.append(('site_id', '!=', False))
            rec.child_count = self.env['project.project'].search_count(domain)

    def _compute_phase_count(self):
        for rec in self:
            rec.phase_count = self.env['construction.project.phase'].search_count([('project_id', '=', rec.id)])

    def action_view_sub_projects(self):
        self.ensure_one()
        # Only show sub-projects if this is a main project (not a sub-project itself)
        if self.parent_id:
            raise ValidationError("Cannot view sub-projects from a sub-project. Please open the main project first.")
        
        # Build domain based on site_id - only show sub-projects if parent is approved
        domain = [('parent_id', '=', self.id), ('construction_id', '!=', False)]
        if self.site_id:
            domain.append(('site_id', '=', self.site_id.id))
        else:
            domain.append(('site_id', '!=', False))
        # Only show sub-projects if parent project is approved
        if self.project_state != 'approved':
            domain.append(('id', '=', False))  # No results if parent not approved
        
        context = {
            'default_parent_id': self.id,
            'default_construction_id': self.construction_id.id if self.construction_id else False,
            'default_site_id': self.site_id.id if self.site_id else False,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Projects',
            'res_model': 'project.project',
            'view_mode': 'kanban,tree,form',
            'domain': domain,
            'context': context,
            'target': 'current'
        }

    def action_view_phases_from_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Phases',
            'res_model': 'construction.project.phase',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
            'target': 'current'
        }

    def action_view_progress_billing(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Progress Billing',
            'res_model': 'construction.progress.billing',
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id, 'default_sub_project_id': self.id},
            'target': 'current'
        }
    
    def action_approve_project(self):
        """Approve project - change state from Draft to Approved"""
        for rec in self:
            if rec.project_state != 'draft':
                raise ValidationError("Only draft projects can be approved.")
            if rec.parent_id and rec.parent_id.project_state != 'approved':
                raise ValidationError("Parent project must be approved before approving sub-project.")
            rec.write({'project_state': 'approved'})
            # Auto-create analytic account if not exists
            if not rec.analytic_account_id:
                rec._create_analytic_account()
        return True
    
    def action_cancel_project(self):
        """Cancel project"""
        for rec in self:
            if rec.child_ids.filtered(lambda c: c.project_state != 'cancel'):
                raise ValidationError("Please cancel all sub-projects before canceling this project.")
            rec.write({'project_state': 'cancel'})
        return True
    
    def action_reset_to_draft(self):
        """Reset project to draft"""
        self.write({'project_state': 'draft'})
        return True


class ConstructionProjectTask(models.Model):
    _inherit = 'project.task'

    construction_id = fields.Many2one(related="project_id.construction_id", string="Construction", store=True)
    labours_ids = fields.Many2many('hr.employee')
    color = fields.Integer(string="Color")
    is_inspection_task = fields.Boolean(string="Inspection Task")

    @api.onchange('construction_id')
    def onchange_construction_id(self):
        for rec in self:
            ids = []
            if rec.construction_id:
                for data in rec.construction_id.construction_labours_ids:
                    for id in data.labours_ids:
                        ids.append(id.id)
            return {'domain': {'labours_ids': [('id', 'in', ids)]}}


class ConstructionTaskStages(models.Model):
    _inherit = 'project.task.type'

    is_construction_stages = fields.Boolean(string="Construction Stage")


class ConstructionMeeting(models.Model):
    _inherit = 'calendar.event'

    construction_id = fields.Many2one('construction.details', string="Construction", check_company=True)
    is_construction_meeting = fields.Boolean(string="Construction Meeting")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
