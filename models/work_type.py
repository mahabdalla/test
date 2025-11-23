# -*- coding: utf-8 -*-
from flectra import fields, api, models


class WorkType(models.Model):
    _name = 'construction.work.type'
    _description = 'Work Type'
    _order = 'name'

    name = fields.Char(string='Work Type', required=True)
    subtype_ids = fields.One2many('construction.work.subtype', 'work_type_id', string='Sub Types')


class WorkSubType(models.Model):
    _name = 'construction.work.subtype'
    _description = 'Work Sub Type'
    _order = 'name'

    name = fields.Char(string='Sub Type', required=True)
    work_type_id = fields.Many2one('construction.work.type', string='Work Type', required=True, ondelete='cascade')

