# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models


class ConstructionPo(models.Model):
    _inherit = 'purchase.order'

    construction_id = fields.Many2one('construction.details', string='Construction', check_company=True)
    order_type = fields.Selection([('equipment', 'Equipment'), ('material', 'Material')], string="Order Type")
    material_id = fields.Many2one('construction.material', string='Material', check_company=True)
    equipment_id = fields.Many2one('construction.equipment', string='Equipment', check_company=True)
    material_requisition_id = fields.Many2one('construction.material.requisition', string='Material Requisition')
    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract')

    def _prepare_invoice(self):
        res = super(ConstructionPo, self)._prepare_invoice()
        if self.construction_id:
            res['construction_id'] = self.construction_id.id
            res['order_type'] = self.order_type
        if self.subcontract_id:
            res['subcontract_id'] = self.subcontract_id.id
        return res
    
    def action_add_approved_requisitions(self):
        """Smart button to add only approved requisitions to PO"""
        from flectra.exceptions import ValidationError
        self.ensure_one()
        if not self.material_requisition_id:
            raise ValidationError("Please link a Material Requisition first.")
        
        requisition = self.material_requisition_id
        approved_lines = requisition.line_ids.filtered(
            lambda l: l.approved and l.operation_type == 'purchase' and not l.purchase_line_id
        )
        
        if not approved_lines:
            raise ValidationError("No approved lines available to add to purchase order.")
        
        po_lines = []
        for line in approved_lines:
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
            self.write({'order_line': po_lines})
            # Update lines with purchase line reference
            for line in approved_lines:
                matching_line = self.order_line.filtered(lambda l: l.product_id.id == line.product_id.id)
                if matching_line:
                    line.purchase_line_id = matching_line[0].id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'{len(po_lines)} approved requisition lines added to purchase order.',
                'type': 'success',
                'sticky': False,
            }
        }


class ConstructionBills(models.Model):
    _inherit = 'account.move'

    construction_id = fields.Many2one('construction.details', string="Construction", check_company=True)
    order_type = fields.Selection([('equipment', 'Equipment'), ('material', 'Material'), ('labour', 'Labour Bill'),
                                   ('eng_arc', 'Engineer & Architect'), ('expense', 'Expense'),
                                   ('insurance', 'Risk & Insurance')],
                                  string="Bill")
    subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract')
