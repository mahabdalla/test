# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models


class ConstructionWorkers(models.Model):
    _inherit = 'hr.employee'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    charges = fields.Monetary(string="Charge")
    color = fields.Integer()

    def name_get(self):
        data = []
        for rec in self:
            data.append((rec.id, '%s - %s' % (rec.name, rec.charges)))
        return data


class ConstructionEmployee(models.Model):
    _name = 'construction.employee'
    _description = "Construction Employee"

    name = fields.Char(string="Title")


class ConstructionEmployeeRole(models.Model):
    _inherit = 'res.partner'

    employee_type = fields.Selection([('engineer', 'Engineer'), ('architect', 'Architect'), ('manager', 'Manager')],
                                     string="Type")
    role_id = fields.Many2one('construction.employee', string="Role")
    is_construction_company = fields.Boolean(string="Is Construction Company")
    is_builder = fields.Boolean(string="Is Builder")
