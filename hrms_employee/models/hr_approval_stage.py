# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrApprovalStage(models.Model):
    _name = 'hr.approval.stage'
    _order = 'sequence'

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Stage Name already exists!')
    ]

    name = fields.Char(string="Stage Name", required=True, )
    sequence = fields.Integer(string="Sequence", required=False, )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'To Approve'),
                              ('approve_supervisor', "Supervisor's Approved"),
                              ('managers_approval', "Manager's Approval"),
                              ('approve_manager', "Manager's Approved"),
                              ('validate', "Validated"),
                              ('review', "Reviewed"),
                              ('refuse', 'Refused'),
                              ('done', 'Done'),
                              ('done_wpay', 'Done With Pay'),
                              ], string="Status", default=None)
    # parent_id = fields.Many2one(comodel_name="hr.approval.stage", string="Parent", required=False, default=None)
    # child_id = fields.Many2one(comodel_name="hr.approval.stage", string="child", required=False, defalut=None)
