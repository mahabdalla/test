# -*- coding: utf-8 -*-
# Copyright 2020 - Today Techkhedut.
# Part of Techkhedut. See LICENSE file for full copyright and licensing details.
from flectra import fields, api, models
from flectra.exceptions import ValidationError


class ConstructionSite(models.Model):
    _name = 'construction.site'
    _description = 'Construction Site Details'

    name = fields.Char(string="Project")
    desc = fields.Html(string="Description")
    job_costing_id = fields.Many2one('job.costing', string="Job Costing")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # Address
    zip = fields.Char(string='Pin Code', size=6)
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", string='State', readonly=False, store=True,
        domain="[('country_id', '=?', country_id)]")

    longitude = fields.Char(string="Longitude")
    latitude = fields.Char(string="Latitude")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    website = fields.Char(string="Website")
    tax = fields.Char(string="Vat")
    licence = fields.Char(string="Licence No.")
    site_type_id = fields.Many2one('site.type', string="Type")
    owners_ids = fields.Many2many('res.partner', domain="[('is_builder','=',True)]")
    amenities_ids = fields.Many2many('construction.amenities', string="Amenities")
    site_image_ids = fields.One2many('construction.images', 'site_id')
    catalog_ids = fields.One2many('construction.catalog', 'construction_id')
    catalog_count = fields.Integer(string="Catalog Count", compute="_compute_catalog_count")
    certificate_count = fields.Integer(string="Certificate Count", compute="_compute_catalog_count")
    certificate_ids = fields.One2many('construction.certificate', 'construction_id')

    def action_gmap_location(self):
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

    @api.depends('catalog_ids')
    def _compute_catalog_count(self):
        self.catalog_count = self.env['construction.catalog'].search_count([('construction_id', '=', self.id)])
        self.certificate_count = self.env['construction.certificate'].search_count([('construction_id', '=', self.id)])

    def action_construction_catalog(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Catalog',
            'res_model': 'construction.catalog',
            'domain': [('construction_id', '=', self.id)],
            'context': {'default_construction_id': self.id},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_construction_certificate(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Certificate',
            'res_model': 'construction.certificate',
            'domain': [('construction_id', '=', self.id)],
            'context': {'default_construction_id': self.id},
            'view_mode': 'tree',
            'target': 'current'
        }

    def action_create_job_costing(self):
        data = {
            'site_id': self.id,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'longitude': self.longitude,
            'latitude': self.latitude,
        }
        job_costing_id = self.env['job.costing'].create(data)
        self.job_costing_id = job_costing_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Job Costing',
            'res_model': 'job.costing',
            'res_id': job_costing_id.id,
            'view_mode': 'form',
            'target': 'current'
        }


class SiteType(models.Model):
    _name = 'site.type'
    _description = "Site Type"

    name = fields.Char(string="Name")


class ConstructionAmenities(models.Model):
    _name = 'construction.amenities'
    _description = 'Details About Construction Amenities'
    _rec_name = 'title'

    image = fields.Binary(string='Image')
    title = fields.Char(string='Title')


class ConstructionImages(models.Model):
    _name = 'construction.images'
    _description = 'Construction Images'

    site_id = fields.Many2one('construction.site')
    title = fields.Char(string='Title')
    image = fields.Image(string='Images')


class ConstructionCatalog(models.Model):
    _name = 'construction.catalog'
    _description = 'Construction Catalog'
    _rec_name = 'construction_id'

    construction_id = fields.Many2one('construction.site', string='Property Name', readonly=True)
    document_date = fields.Date(string='Date', default=fields.Date.today())
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')


class ConstructionCertificate(models.Model):
    _name = "construction.certificate"
    _description = "Construction Certificate"

    construction_id = fields.Many2one('construction.site', string='Property Name', readonly=True)
    document_type = fields.Many2one('document.type', string="Document Type", domain="[('type','=','project')]")
    document_date = fields.Date(string='Date', default=fields.Date.today())
    document = fields.Binary(string='Documents', required=True)
    file_name = fields.Char(string='File Name')
