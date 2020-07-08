# -*- coding: utf-8 -*-
from odoo import http

# class MgcCredit(http.Controller):
#     @http.route('/mgc_credit/mgc_credit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mgc_credit/mgc_credit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mgc_credit.listing', {
#             'root': '/mgc_credit/mgc_credit',
#             'objects': http.request.env['mgc_credit.mgc_credit'].search([]),
#         })

#     @http.route('/mgc_credit/mgc_credit/objects/<model("mgc_credit.mgc_credit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mgc_credit.object', {
#             'object': obj
#         })