# -*- coding: utf-8 -*-
from flectra import fields, api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    material_requisition_id = fields.Many2one('construction.material.requisition', string='Material Requisition')


class StockMove(models.Model):
    _inherit = 'stock.move'

    consume_order_id = fields.Many2one('construction.consume.order', string='Consume Order')

