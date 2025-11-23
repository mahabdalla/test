# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import models, api, fields
from flectra.exceptions import ValidationError


class ConstructionInspection(models.TransientModel):
    _name = "construction.inspection"
    _description = "Construction Inspection "

    name = fields.Char(string="Title")
    user_ids = fields.Many2many('res.users', string="Assignee")
    date = fields.Date(string="Date", default=fields.Date.today())
    deadline = fields.Date(string="Deadline")
    construction_id = fields.Many2one('construction.details', string="Construction", check_company=True)
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    desc = fields.Html(string="Description")

    def action_create_task(self):
        if not self.construction_id or not self.construction_id.project_id:
            raise ValidationError("Construction project is not available for this inspection.")
        assignees = self.user_ids
        primary_user = assignees[:1] or self.env.user
        record = {
            'name': self.name,
            'project_id': self.construction_id.project_id.id,
            'construction_id': self.construction_id.id,
            'is_inspection_task': True,
            'partner_id': self.construction_id.customer_company_id.id,
            'date_deadline': self.deadline,
            'description': self.desc,
            'user_id': primary_user.id if primary_user else False,
        }
        task_id = self.env['project.task'].create(record)
        if assignees:
            allowed_users = (task_id.allowed_user_ids | assignees)
            task_id.allowed_user_ids = [(6, 0, allowed_users.ids)]
            partner_ids = assignees.partner_id.ids
            if partner_ids:
                task_id.message_subscribe(partner_ids=partner_ids)
        inspection_record = {
            'date': self.date,
            'note': self.name,
            'construction_id': self.construction_id.id,
            'date_deadline': self.deadline,
            'task_id': task_id.id
        }
        self.env['site.inspection'].create(inspection_record)
