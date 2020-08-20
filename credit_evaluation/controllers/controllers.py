# -*- coding: utf-8 -*-
from odoo import http

# class CreditOrientation(http.Controller):
#     @http.route('/credit_orientation/credit_orientation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_orientation/credit_orientation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_orientation.listing', {
#             'root': '/credit_orientation/credit_orientation',
#             'objects': http.request.env['credit_orientation.credit_orientation'].search([]),
#         })

#     @http.route('/credit_orientation/credit_orientation/objects/<model("credit_orientation.credit_orientation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_orientation.object', {
#             'object': obj
#         })