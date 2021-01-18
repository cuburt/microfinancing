# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class MemberForm(http.Controller):
    @http.route(['/member/form'], type='http', auth='public', website=True)
    def member_form(self, **post):
        return request.render("credit_website.tmp_member_form", {})

    @http.route(['/member/form/submit'], type='http', auth='public', website=True)
    def member_form_submit(self, **post):
        partner = request.env.user.partner_id.write({
            'user_id':request.env.user.id,
            'street2':post.get('street2'),
            'city':post.get('city'),
            'phone':post.get('phone'),
            'is_company':False,
            'employee':False,
        })
        vals = {
            'partner':partner
        }
        return request.render('credit_website.tmp_member_form_success', vals)

    # @http.route(['/loan'], type='http', auth='public', website=True)
    # def loans(self, **post):
    #     loans = request.env['product.template'].search([('categ_id.name','=','Loan Products')])
    #     return request.render("credit_website.tmp_loan_gallery", {'loans':loans})

    # @http.route(['/loan/apply'], type='http', auth='public', website=True)
    # def loan_form(self, **post):
    #     return request.render("credit_website.tmp_loan_form", {})
