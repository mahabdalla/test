# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ImportTaskLibraryWizard(models.TransientModel):
    _name = 'construction.import.task.library.wizard'
    _description = 'Import Task Library to Phase Wizard'

    task_library_id = fields.Many2one('construction.task.library', string='Task Library', required=True)
    phase_id = fields.Many2one('construction.project.phase', string='Phase', required=True)
    
    import_materials = fields.Boolean(string='Import Materials', default=True)
    import_equipment = fields.Boolean(string='Import Equipment', default=True)
    import_labor = fields.Boolean(string='Import Labor', default=True)
    import_overhead = fields.Boolean(string='Import Overhead', default=True)
    import_subcontractor = fields.Boolean(string='Import Subcontractor', default=True)

    def action_import(self):
        """Import task library entries to the selected phase"""
        self.ensure_one()
        if not self.phase_id:
            raise ValidationError("Please select a phase to import to.")
        
        # Import Materials
        if self.import_materials:
            for line in self.task_library_id.material_line_ids:
                self.env['construction.phase.material.entry'].create({
                    'phase_id': self.phase_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                })
        
        # Import Equipment
        if self.import_equipment:
            for line in self.task_library_id.equipment_line_ids:
                self.env['construction.phase.equipment.entry'].create({
                    'phase_id': self.phase_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                })
        
        # Import Labor
        if self.import_labor:
            for line in self.task_library_id.labor_line_ids:
                self.env['construction.phase.labor.entry'].create({
                    'phase_id': self.phase_id.id,
                    'name': line.name,
                    'hours': line.hours,
                    'rate': line.rate,
                })
        
        # Import Overhead
        if self.import_overhead:
            for line in self.task_library_id.overhead_line_ids:
                self.env['construction.phase.overhead.entry'].create({
                    'phase_id': self.phase_id.id,
                    'name': line.name,
                    'amount': line.amount,
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Task library imported successfully to phase.',
                'type': 'success',
                'sticky': False,
            }
        }

