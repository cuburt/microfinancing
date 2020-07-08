# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CIAssessment(models.Model):
    _inherit = 'micro.loan.application'

    state = fields.Selection(string="Status", selection_add=[('investigate','Investigation')], required=True,
                             track_visibility='onchange')
    investigation_date = fields.Datetime('Investigation Date', default=fields.Datetime.now(), required_if_state='investigate')

class ClientInvestigation(models.Model):
    _name = 'micro.client.investigation'

class CIQuestionnaire(models.Model):
    _name = 'micro.client.investigation.questionnaire'

class CIScore(models.Model):
    _name = 'micro.client.investigation.score'
