from odoo import models, fields, api, _


class ResBank(models.Model):
    _inherit = 'res.bank'

    bank_manager = fields.Char(string="Bank Manager", required=False, )
    description = fields.Char(string="Bank Name", required=False, )
    location = fields.Char(string="Location", required=False, )
    abbreviation = fields.Char(string="Abbreviation", required=False, )

    @api.onchange('abbreviation', 'location')
    def _get_bank_name(self):
        if self.abbreviation and self.location:
            self.name = "%s [%s]" % (self.abbreviation, self.location)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    company_use = fields.Boolean(string="For Company Used")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = record.acc_number
            if record.partner_id:
                partner = record.partner_id.name
            else:
                partner = ''
            name = "%s [%s]" % (partner, name)
            result.append((record.id, name))
        return result
