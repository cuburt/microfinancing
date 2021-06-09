# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import time

class Invoice(models.Model):
    _inherit = 'account.invoice'

    installment_ids = fields.One2many(related='collection_id.collection_line_ids')

# class Payment(models.Model):
