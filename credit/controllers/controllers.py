# -*- coding: utf-8 -*-
from odoo import http

# class Credit(http.Controller):
#     @http.route('/credit/credit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit/credit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit.listing', {
#             'root': '/credit/credit',
#             'objects': http.request.env['credit.credit'].search([]),
#         })

#     @http.route('/credit/credit/objects/<model("credit.credit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit.object', {
#             'object': obj
#         })