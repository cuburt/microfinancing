# -*- coding: utf-8 -*-
from odoo import http

# class CreditReports(http.Controller):
#     @http.route('/credit_reports/credit_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/credit_reports/credit_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('credit_reports.listing', {
#             'root': '/credit_reports/credit_reports',
#             'objects': http.request.env['credit_reports.credit_reports'].search([]),
#         })

#     @http.route('/credit_reports/credit_reports/objects/<model("credit_reports.credit_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('credit_reports.object', {
#             'object': obj
#         })