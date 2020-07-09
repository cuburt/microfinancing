# -*- coding: utf-8 -*-

from odoo import models, fields, api

class LoanAssessment(models.Model):
    _inherit = 'micro.loan.application'

    state = fields.Selection(string="Status", selection_add=[('investigate','Investigation')], required=True,
                             track_visibility='onchange')
    assessment_date = fields.Datetime('Assessment Date', default=fields.Datetime.now(), required_if_state='investigate')
    client_investigations = fields.One2many('micro.client.investigation', 'assessment_id', 'Client Investigations')

class ClientInvestigation(models.Model):
    _name = 'micro.client.investigation'

    assessment_id = fields.Many2one('micro.loan.application','Assessment')
    investigation_date = fields.Datetime('Investigation Date', default=fields.Datetime.now())

class CIQuestionnaire(models.Model):
    _name = 'micro.client.investigation.questionnaire'

class CIScore(models.Model):
    _name = 'micro.client.investigation.score'
