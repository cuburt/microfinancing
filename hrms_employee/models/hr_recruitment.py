from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
from dateutil.relativedelta import relativedelta
import calendar

SUFFIX = [
    ('jr','JR'),
    ('sr','SR'),
    ('iii','III'),
    ('iv','IV'),
    ('v','V'),
    ('vi','VI'),
    ('vii','VII')
]
GENDER = [
    ('male','Male'),
    ('female','Female'),
    ('other','Others')
]
MonthDate = [(1, 'January'),
             (2, 'February'),
             (3, 'March'),
             (4, 'April'),
             (5, 'May'),
             (6, 'June'),
             (7, 'July'),
             (8, 'August'),
             (9, 'September'),
             (10, 'October'),
             (11, 'November'),
             (12, 'December'),
             ]


class HrApplicant(models.Model):
    _inherit = "hr.applicant"

    @api.depends('recruitment_expense_id')
    def _compute_no_of_recruitmentexpense(self):
        for rec in self:
            rec.no_of_recruitmentexpense = len(rec.recruitment_expense_id.ids)

    first_name = fields.Char(string="First Name")
    middle_name = fields.Char(string="Middle Name")
    last_name = fields.Char(string="Last Name")
    suffix = fields.Selection(SUFFIX, string="Suffix")
    prefix = fields.Many2one('res.partner.title',string="Prefix")
    gender = fields.Selection(GENDER,string="Gender")
    birth_date = fields.Date(string="Date of Birth")
    marital = fields.Selection(string="Marital Status", selection=[('single', 'Single'),
                                              ('married', 'Married'),
                                              ('widower', 'Widower'),
                                              ('divorced', 'Divorced'),
                                              ('singleparent', "Single Parent"),
                                              ('separated', 'Separated')])
    age = fields.Char(compute='_get_age',store=True, string='Age')
    date_hired = fields.Date(string="Date Hired", required=False, )
    date_applied = fields.Date(string="Date Applied", required=False, default=fields.Date.context_today,)

    app_history_id = fields.One2many('hr.applicant.history', 'name',string='Applicant Recruitment History')
    stage_check = fields.Char(related='stage_id.name') #hr recruitment validation
    employee_status_id = fields.Many2one('hr.contract.type', string="Employment Status")
    # mail_template_id = fields.Many2one('mail.template', string="Email Template for Applicant")
    message = fields.Text(string="Message", required=False, )
    remarks = fields.Text(string="Remarks")
    no_of_recruitmentexpense = fields.Integer('No of Recruitment Expense',
                                     compute='_compute_no_of_recruitmentexpense',
                                     readonly=True)
    recruitment_expense_id = fields.One2many('hr.recruitment.expense', 'applicant_id', string='Recruitment Expense')
    is_hired = fields.Boolean(string="Hired", default=False)
    user_id = fields.Many2one('res.users', "Responsible", track_visibility="onchange",
                              default=lambda self: self.env['res.users'].browse(self.env.user.id))
    recruitment_request_id = fields.Many2one(comodel_name="hr.recruitment.request", string="PRF Reference", required=False, domain="[('state', '=', 'validate')]")
    street = fields.Char(string="Street...", required=False, )
    region_id = fields.Many2one('config.region', string="Region", related="province_id.region_id", store=True)
    province_id = fields.Many2one('config.province', string="Province", related="municipality_id.province_id",
                                  store=True)
    municipality_id = fields.Many2one('config.municipality', string="City / Municipality",
                                      related="barangay_id.municipality_id", store=True)
    barangay_id = fields.Many2one('config.barangay', string="Barangay")
    is_initial_hired = fields.Boolean(string="Initial Hired")
    emp_applicant_id = fields.Many2one(comodel_name="hr.employee", string="Employee Applicant", required=False, )
    applicant_type = fields.Selection(string="Applicant Type", selection=[('external', 'External'),
                                                                          ('internal', 'Internal')],
                                      required=False, default='external')
    requester_id = fields.Many2one(comodel_name="hr.employee", string="Responsible", required=False,
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))

    @api.multi
    def send_email_to_applicant(self):
        mail_mail = self.env['mail.mail']
        for applicant in self:
            if applicant.partner_id:
                sender_email = applicant.job_id.user_id.partner_id.email if applicant.job_id.user_id.partner_id.email else applicant.company_id.partner_id.email
                author = applicant.job_id.user_id.partner_id if applicant.job_id.user_id.partner_id else applicant.company_id.partner_id

                if applicant.gender == 'female':
                    if applicant.marital == 'married':
                        header = "<p>Hi <b>Mrs. " + applicant.first_name + " " + applicant.middle_name + " " + applicant.last_name + "</b>, </p><br/>"
                    else:
                        header = "<p>Hi <b>Ms. " + applicant.first_name + " " + applicant.middle_name + " " + applicant.last_name + "</b>, </p><br/>"
                else:
                    header = "<p>Hi <b>Mr. " + applicant.first_name + " " + applicant.middle_name + " " + applicant.last_name + "</b>, </p><br/>"

                body_html = header
                lines = applicant.message.split('\n')
                for line in lines:
                    body_html += "<p>" + line + "</p>"

                body_html += "<br/><p>Best regards, </p><p><b> " + author.name + "</b></p><p>HR Recruitment Officer</p><p>" + applicant.company_id.name + "</p><br/>"

                vals = {
                    'subject': applicant.title_action,
                    'date': datetime.now(),
                    'email_from': '\"' + author.name + '\"<' + sender_email + '>',
                    'author_id': author.id,
                    'recipient_ids': [(4, applicant.partner_id.id)],
                    'reply_to': '\"' + author.name + '\"<' + sender_email + '>',
                    'body_html': body_html,
                    'auto_delete': False,
                    'message_type': 'email',
                    'notification': True,
                    'mail_server_id': self.env.ref('mgc_base.config_email_server_gmail_noreply').id,
                    'model': applicant._name,
                    'res_id': applicant.id,
                }
                result = mail_mail.create(vals)
                result.send()
                return result

    @api.onchange('emp_applicant_id')
    def _onchange_emp_applicant_id(self):
        if self.emp_applicant_id:
            self.first_name = self.emp_applicant_id.first_name
            self.last_name = self.emp_applicant_id.last_name
            self.middle_name = self.emp_applicant_id.middle_name
            self.suffix = self.emp_applicant_id.suffix
            self.partner_id = self.emp_applicant_id.user_id.partner_id.id
            self.email_from = self.emp_applicant_id.work_email
            self.barangay_id = self.emp_applicant_id.barangay_id.id
            self.gender = self.emp_applicant_id.gender
            self.birth_date = self.emp_applicant_id.birthday
            self.marital = self.emp_applicant_id.marital
            self.partner_mobile = self.emp_applicant_id.mobile_phone
            self.prefix = self.emp_applicant_id.prefix.id

    @api.onchange('barangay_id')
    def _onchange_barangay_id(self):
        if self.barangay_id:
            self.municipality_id = self.barangay_id.municipality_id.id
            self.province_id = self.municipality_id.province_id.id
            self.region_id = self.province_id.region_id.id

    @api.multi
    def action_initial_hired(self):
        self.is_initial_hired = True
        request = self.env['hr.recruitment.request'].browse(self.recruitment_request_id.id)
        request.write({'no_of_hired_employee': request.no_of_hired_employee + 1})

    # @api.constrains('department_id', 'job_id')
    # def check_recruitment_requests(self):
    #     request = self.env['hr.recruitment.request'].search([('job_id', '=', self.job_id.id),
    #                                                          ('department_id', '=', self.department_id.id),
    #                                                          ('state', '=', 'validate')], limit=1)
    #     if not request:
    #         raise ValidationError(_('Please check the recruitment request upon the application of this job.'))

    @api.multi
    @api.depends('app_history_id')
    def _put_app_history_id(self):
        state = self.stage_id.id
        # for xxx in self:

        if self.first_name != '' and self.middle_name != '' and self.last_name != '':
            applicant_history = self.env['hr.applicant.history'].create({'name': self.id or self.name or False or '',
                                                                         'stage_date': datetime.today() or False,
                                                                         'stage_state': self.stage_id.id or False})

            print '>>>',applicant_history

    @api.onchange('job_id', 'department_id')
    def check_recruitment_request(self):
        if self.job_id and self.department_id:
            request = self.env['hr.recruitment.request'].search([('job_id', '=', self.job_id.id),
                                                                 ('department_id', '=', self.department_id.id),
                                                                 ('state', '=', 'validate')], limit=1)
            if request.no_of_recruitment > request.no_of_hired_employee:
                self.recruitment_request_id = request.id
            else:
                self.recruitment_request_id = None

    @api.depends('birth_date')
    def _get_age(self):
        for r in self:
            if r.birth_date:
                bdate = datetime.strptime(r.birth_date, "%Y-%m-%d").date()
                today = date.today()
                diffdate = today - bdate

                years = diffdate.days / 365
                formonth = diffdate.days - (years * 365.25)
                months = (formonth / 31)

                bday = bdate.day
                tody = date.today().day

                if tody >= bday:
                    day = tody - bday
                else:
                    day = 31 - (bday - tody)

                # r.age_complete = str(years) + ' Year/s ' + str(int(months)) + ' Month/s ' + str(day) + ' Day/s'
                r.age = str(years)

    @api.onchange('first_name', 'middle_name', 'last_name', 'suffix')
    def onchange_name(self):

        name = ''
        sep = ', '
        if self.last_name:
            lname = self.last_name.title().strip()
        else:
            lname = ''

        if lname:
            name = '%s%s' % (lname, sep)

        if self.first_name:
            fname = self.first_name.title().strip()
        else:
            fname = ''

        if fname:
            name = '%s%s%s' % (name, ' ', fname)

        if self.suffix:
            suffix = self._get_suffix(self.suffix)
        else:
            suffix = ''

        if suffix:
            name = '%s%s%s' % (name, ' ', suffix)

        if self.middle_name:
            mname = self.middle_name.title().strip()
        else:
            mname = ''

        if mname:
            name = '%s%s%s' % (name, ' ', mname)

        # if self.name == '':
        #     self.name = ''
        # else:
        #     self.name = "%s%s %s %s %s" % (lname.title().strip(), fname.title().strip(),, mname.title().strip())

        self.name = name

        self.first_name = fname.title().strip()
        self.middle_name = mname.title().strip()
        self.last_name = lname.title().strip()

    @api.multi
    def _get_suffix(self, values):
        if values == 'jr':
            suffix = 'Jr'

        elif values == 'sr':
            suffix = 'Sr'

        elif values == 'ii':
            suffix = 'II'

        elif values == 'iii':
            suffix = 'III'

        elif values == 'iv':
            suffix = 'IV'

        elif values == 'v':
            suffix = 'V'

        elif values == 'vi':
            suffix = 'VI'

        elif values == 'vii':
            suffix = 'VII'

        else:
            suffix = ''

        return suffix

    @api.model
    def create(self, values):
        if 'first_name' in values and 'middle_name' in values and 'last_name' in values:
            fname = values['first_name'].title().strip()
            mname = values['middle_name'].title().strip()
            lname = values['last_name'].title().strip()

            suffix_ids = values['suffix']
            prefix_id = values['prefix']
            prefix_ids = self.env['res.partner.title'].browse(prefix_id)

            values['name'] = lname + ', ' + fname + ' ' + mname

            values['prefix'] = prefix_ids.id
            values['first_name'] = fname
            values['middle_name'] = mname
            values['last_name'] = lname
            values['suffix'] = suffix_ids

        res = super(HrApplicant, self).create(values)
        if res and 'job_id' in values and 'department_id' in values and 'recruitment_request_id' in values:
                self._cr.execute("""insert into hr_applicant_hr_recruitment_request_rel
                (hr_recruitment_request_id,hr_applicant_id)values(%s,%s)""" % (res.recruitment_request_id.id, res.id))
                self._cr.commit()
                request = self.env['hr.recruitment.request'].browse(res.recruitment_request_id.id)
                request.count_applications()
                res._put_app_history_id()
        return res

    @api.multi
    def write(self, values):

        if 'first_name' in values and values['first_name']:
            fname = values['first_name'].title().strip()
        elif 'first_name' not in values and self.first_name:
            fname = self.first_name.title().strip()
        else:
            fname = ''

        if 'middle_name' in values and values['middle_name']:
            mname = values['middle_name'].title().strip()
        elif 'middle_name' not in values and self.middle_name:
            mname = self.middle_name.title().strip()
        else:
            mname = ''

        if 'last_name' in values and values['last_name']:
            lname = values['last_name'].title().strip()
        elif 'last_name' not in values and self.last_name:
            lname = self.last_name.title().strip()
        else:
            lname = ''

        if self.suffix:
            suffix = self.suffix
        else:
            suffix = ''

        if suffix:
            suffix = self._get_suffix(suffix)

        # if 'first_name' in values and values['first_name'] or 'middle_name' in values and values[
        #     'middle_name'] or 'last_name' in values and values['last_name'] or 'suffix' in values and values['suffix']:
            # if values['first_name'] or values['middle_name'] or values['last_name']:
        values['name'] = "%s, %s %s %s" % (lname, fname, suffix, mname)
        # else:
        #     values['name'] = self.name
        values['first_name'] = fname
        values['middle_name'] = mname
        values['last_name'] = lname
        if 'user_id' not in values or values['user_id'] == None:
            user = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
            values['user_id'] = user.user_id.id
        if 'recruitment_request_id' in values:
            if self.recruitment_request_id:
                request = self.env['hr.recruitment.request'].browse(self.recruitment_request_id.id)
                print request
                applicants = []
                for applicant in request.applicant_ids:
                    applicants.append(applicant.id)
                if len(applicants) == 0:
                    self._cr.execute("""insert into hr_applicant_hr_recruitment_request_rel
                                                                        (hr_recruitment_request_id,hr_applicant_id)values(%s,%s)""" % (
                    request.id, self.id))
                    self._cr.commit()
                    request.count_applications()
                else:
                    if self.id not in applicants:
                        self._cr.execute("""insert into hr_applicant_hr_recruitment_request_rel
                                                        (hr_recruitment_request_id,hr_applicant_id)values(%s,%s)""" % (request.id, self.id))
                        self._cr.commit()
                        request.count_applications()
        rec = super(HrApplicant, self).write(values)
        if rec and ('job_id' in values or 'department_id' in values or 'stage_id' in values):
            self._put_app_history_id()
            self.title_action = "For " + str(self.stage_id.name)
            self.message = ''


        # hr recruitment validation
        # 01-29-2018 pinakuha ng tga hr
        # if 'stage_id' in values and 'last_stage_id' in values:
        #     if values['stage_id'] and values['last_stage_id']:
        #         if values['last_stage_id'] > values['stage_id']:
        #             raise UserError(_("Invalid movement!!!"))
        # end of hr recruitment validation

        return rec

    @api.onchange('job_id')
    def onchange_job_id(self):
        vals = self._onchange_job_id_internal(self.job_id.id)
        # self.department_id = vals['value']['department_id']
        self.user_id = self.env['res.users'].browse(self.env.user.id).id
        self.stage_id = vals['value']['stage_id']
        company = self.env['res.company'].search([('partner_id', '=', self.job_id.address_id.id)], limit=1)
        result = {}
        if company:
            self.company_id = company.id
            requests = self.env['hr.recruitment.request'].search([('job_id', '=', self.job_id.id),
                                                                      ('company_id', '=', company.id),
                                                                      ('state', '=', 'validate'),
                                                                      ('no_of_recruitment', '>=', 1)])
            dept = []
            if requests:
                for req in requests:
                    dept.append(req.department_id.id)
            if dept:
                result['domain'] = {'department_id': [('id', 'in', dept)]}
                return result

    def _onchange_job_id_internal(self, job_id):
        department_id = False
        user_id = False
        stage_id = self.stage_id.id
        if job_id:
            job = self.env['hr.job'].browse(job_id)
            department_id = job.department_id.id
            user_id = job.user_id.id
            if not self.stage_id:
                stage_ids = self.env['hr.recruitment.stage'].search([
                    '|',
                    ('job_id', '=', False),
                    ('job_id', '=', job.id),
                    ('fold', '=', False)
                ], order='sequence asc', limit=1).ids
                stage_id = stage_ids[0] if stage_ids else False

        return {'value': {
            'department_id': department_id,
            'user_id': user_id,
            'stage_id': stage_id
        }}

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        vals = self._onchange_stage_id_internal(self.stage_id.id)
        if vals['value'].get('date_closed'):
            self.date_closed = vals['value']['date_closed']

    def _onchange_stage_id_internal(self, stage_id):
        if self.first_name != '' and self.middle_name != '' and self.last_name != '':
            if not stage_id:
                return {'value': {}}
            stage = self.env['hr.recruitment.stage'].browse(stage_id)
            # self._put_app_history_id()
            if stage.fold:
                return {'value': {'date_closed': fields.datetime.now()}}
        else:
            raise UserError(_('The name of applicant must not be empty!'))

        return {'value': {'date_closed': False}}

    @api.multi
    def get_mail_channel(self, sender, receiver):
        mail_channels = self.env['mail.channel']
        if sender and receiver:
            employee = self.env['hr.employee']
            receiver_partner_browse = employee.sudo().browse(receiver.id)
            sender_partner = sender.partner_id
            receiver_partner = receiver_partner_browse.user_id.partner_id
            if sender_partner and receiver_partner:
                mail_channels_res = mail_channels.sudo().search(
                    [('public', '=', 'private'), ('channel_type', '=', 'chat'),
                     ('channel_partner_ids', 'in', [sender_partner.id, receiver_partner.id]),
                     '|', ('name', 'ilike', sender_partner.name + ', ' + receiver_partner.name),
                     ('name', 'ilike', receiver_partner.name + ', ' + sender_partner.name)], limit=1,
                    order='create_date desc')
                if mail_channels_res:
                    result = mail_channels_res
                else:
                    partners = [(4, sender_partner.id, None), (4, receiver_partner.id, None)]
                    mail_channel_create = mail_channels.sudo().create(
                        {'name': receiver_partner.name + ', ' + sender_partner.name,
                         'public': 'private',
                         'channel_type': 'chat',
                         'channel_partner_ids': partners})
                    result = mail_channel_create
                return result

    def create_mail_message(self, channel, sender, receiver, employee_id):
        if channel and sender and receiver and employee_id:
            mail_message = self.env['mail.message']
            employee = self.env['hr.employee']
            receiver_partner_browse = employee.sudo().browse(receiver.id)
            sender_partner = sender.partner_id
            receiver_partner = receiver_partner_browse.user_id.partner_id
            body = "<p>Congratulations! Your PRF #:%s has been filled by %s! This is an automated notification. Please do not reply to it. </p>" % (self.recruitment_request_id.name, self.name)
            if sender_partner and receiver_partner:
                vals = {
                    'subject': 'PRF Request',
                    'date': datetime.now(),
                    'email_from': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'author_id': sender_partner.id,
                    'record_name': channel.name,
                    'model': 'mail.channel',
                    'res_id': int(channel.id),
                    'message_type': 'comment',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'reply_to': '\"' + sender_partner.name + '\"<' + sender_partner.email + '>',
                    'channel_ids': [(4, channel.id, None)],
                    'body': body
                }
                result = mail_message.sudo().create(vals)
                return result

    # original
    # 'work_email': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.email or False,
    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            address_id = contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            if applicant.job_id and (applicant.partner_name or contact_name):
                request = self.env['hr.recruitment.request'].search([('job_id', '=', applicant.job_id.id),
                                                                     ('department_id', '=', applicant.department_id.id),
                                                                     ('state', '=', 'validate')], limit=1)
                if request:
                    if not applicant.is_initial_hired:
                        request.write({'no_of_hired_employee': request.no_of_hired_employee + 1})
                    if request.no_of_hired_employee == request.no_of_recruitment:
                        request.action_close()
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                if applicant.applicant_type == 'external':
                    employee = self.env['hr.employee'].sudo().create({'name': applicant.name or contact_name,
                                                                      'first_name': applicant.first_name,
                                                                      'middle_name': applicant.middle_name,
                                                                      'last_name': applicant.last_name,
                                                                      'suffix': applicant.suffix,
                                                                      'prefix': applicant.prefix.id,
                                                                      'job_id': applicant.job_id.id,
                                                                      'company_id': applicant.company_id.id,
                                                                      'address_home_id': address_id,
                                                                      'mobile_phone': applicant.partner_mobile,
                                                                      'date_hired': date.today(),
                                                                      'employee_status_id': applicant.employee_status_id.id,
                                                                      'pyrl_date_hired': date(date.today().year, date.today().month, 01) + relativedelta(months=1),
                                                                      'gender': applicant.gender,
                                                                      'marital': applicant.marital,
                                                                      'birthday': applicant.birth_date,
                                                                      'barangay_id': applicant.barangay_id.id,
                                                                      'status': 'joined',
                                                                      'department_id': applicant.department_id.id or False,
                                                                      'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                                                                      'work_email': applicant.email_from,
                                                                      'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False})
                    applicant.write({'emp_id': employee.id, 'is_hired': True, 'is_initial_hired': False, 'date_hired': date.today()})
                    applicant.job_id.message_post(
                        body=_(
                            'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                        subtype="hr_recruitment.mt_job_applicant_hired")
                    employee._broadcast_welcome()
                    print "HHH"
                if applicant.applicant_type == 'internal':
                    employee = self.env['hr.employee'].browse(applicant.emp_applicant_id.id)
                    if employee:
                        employee.write({
                            'name': applicant.name or contact_name,
                            'first_name': applicant.first_name,
                            'middle_name': applicant.middle_name,
                            'last_name': applicant.last_name,
                            'suffix': applicant.suffix,
                            'prefix': applicant.prefix.id,
                            'job_id': applicant.job_id.id,
                            'company_id': applicant.company_id.id,
                            'address_home_id': address_id,
                            'mobile_phone': applicant.partner_mobile,
                            'gender': applicant.gender,
                            'marital': applicant.marital,
                            'birthday': applicant.birth_date,
                            'barangay_id': applicant.barangay_id.id,
                            'department_id': applicant.department_id.id or False,
                            'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
                            'work_email': applicant.email_from,
                            'state': 'probationary'

                        })
                        contract = self.env['hr.contract'].browse(employee.contract_id.id)
                        contract.action_expired()
                    applicant.write({'emp_id': employee.id, 'is_hired': True, 'is_initial_hired': False,
                                     'date_hired': date.today()})
                sender = self.env['res.users'].sudo().browse(
                    self.env.ref('hrms_employee.res_users_notifier').id)
                channel = self.get_mail_channel(sender, self.recruitment_request_id.requester_id)
                self.create_mail_message(channel, sender, self.recruitment_request_id.requester_id,
                                         self.recruitment_request_id.requester_id)
            else:
                raise UserError(_('You must define an Applied Job or Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window


class HrApplicantHistory(models.Model):
    _name = 'hr.applicant.history'

    name = fields.Many2one('hr.applicant',string='Applicant History')
    stage_date = fields.Datetime(string='Date')
    stage_state = fields.Many2one('hr.recruitment.stage',string='Stage')
    remarks = fields.Text('Remarks')


class HrApplicantExpense(models.Model):
    _name = 'hr.recruitment.expense'
    _description = 'This model is reimburse applicant expense from other areas'

    amount = fields.Float(string="Amount")
    doc_date = fields.Date(string="Document Date", default=datetime.today())
    travel_particular = fields.Char(string="Travel Particulars")
    purpose = fields.Char(string="Purpose")
    applicant_id = fields.Many2one('hr.applicant', 'Applicant Ref',
                                   ondelete='cascade')
    attachment_number = fields.Integer(compute='_get_attachment_number', string="Number of Attachments")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'hr.recruitment.expense')],
                                     string='Attachment')

    @api.multi
    def _get_attachment_number(self):
        read_group_res = self.env['ir.attachment'].read_group(
            [('res_model', '=', 'hr.recruitment.expense'), ('res_id', 'in', self.ids)],
            ['res_id'], ['res_id'])
        attach_data = dict((res['res_id'], res['res_id_count']) for res in read_group_res)
        for record in self:
            record.attachment_number = attach_data.get(record.id, 0)

    @api.multi
    def action_get_attachment_tree_view(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {'default_res_model': self._name, 'default_res_id': self.ids[0]}
        action['domain'] = str(['&', ('res_model', '=', self._name), ('res_id', 'in', self.ids)])
        action['search_view_id'] = (self.env.ref('hrms_employee.ir_attachment_view_search_hrrecruitmentexpense').id, )
        return action


class HrRecruitmentRequest(models.Model):
    _name = 'hr.recruitment.request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'date_request desc, name'

    @api.multi
    @api.depends('job_id', 'department_id', 'date_request', 'no_of_recruitment')
    def compute_applicants_variance(self):
        for record in self:
            if record.date_request:
                date_request = datetime.strptime(record.date_request, '%Y-%m-%d').date()
                department_id = record.department_id.parent_id.id if record.department_id.parent_id.id else record.department_id.id
                manpower = self.env['hr.manpower.plan'].search([('department_id', '=', department_id),
                                                                ('month_date', '<=', date_request.month),
                                                                ('year_date', '=', str(date_request.year)),
                                                                ('state', '=', 'posted')], limit=1, order='month_date desc')
                if manpower:
                    for line in manpower.line_ids:
                        if line.job_id.id == record.job_id.id:
                            record.update({
                                'actual': line.no_of_employee,
                                'budget': line.total,
                                'variance': line.total - (line.no_of_employee + record.no_of_recruitment)
                            })
                else:
                    employees_count = self.env['hr.employee'].search_count([('job_id', '=', record.job_id.id),
                                                                ('state', 'not in', ['relieved', 'terminate']),
                                                                ('date_hired', '<=', date_request),
                                                                ('department_id', '=', record.department_id.id)])
                    record.update({
                        'actual': employees_count,
                        'budget': employees_count,
                        'variance': employees_count - (employees_count + record.no_of_recruitment)
                    })

    name = fields.Char(string="Recruitment Reference", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False)
    department_id = fields.Many2one(comodel_name="hr.department", string="Branch / Department", required=False, )
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position Requested", required=True, )
    requester_id = fields.Many2one(comodel_name="hr.employee", string="Requestor", required=True,
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))
    date_request = fields.Date(string="Date Requested", required=False, default=fields.Date.context_today,)
    no_of_recruitment = fields.Integer(string="No. of Expected Employees")
    no_of_applications = fields.Integer(string="No. of Applicants")
    no_of_hired_employee = fields.Integer(string="No. of Hired Applicants")
    type = fields.Selection(string="Type", selection=[('new', 'Additions'), ('replacement', 'Replacement'),
                                                      ('temporary_replacement', 'Temporary Replacement')],
                            required=False, default="new")
    replace_employee_id = fields.Many2one(comodel_name="hr.employee", string="In Replacement of", required=False, )
    remarks = fields.Text(string="Remarks", required=False)
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'),
                                                         ('confirm', 'Confirm'),
                                                         ('managers_approval', 'Managers Approved'),
                                                         ('bod_approval', 'BOD Approved'),
                                                         ('validate', 'HR Approved'),
                                                         ('refuse', 'Refuse'),
                                                         ('cancel', 'Cancelled'),
                                                         ('close', 'Close')],
                             required=False, default=False, track_visibility='onchange')
    gender = fields.Selection(string="Gender", selection=[('male', 'Male'), ('female', 'Female'), ('male/female', 'Male / Female')], required=False, default='male/female')
    age_from = fields.Integer(string="Age From", required=False, default=18)
    age_to = fields.Integer(string="Age To", required=False, default=60)
    education = fields.Text(string="Education", required=False, )
    work_experience = fields.Text(string="Work Experience", required=False, )
    skills = fields.Text(string="Technical Knowledge and Skills Required", required=False, )
    personal_qualification = fields.Text(string="Desired Personal Qualifications", required=False, )
    recommend_id = fields.Many2one(comodel_name="hr.employee", string="Recommended By", required=False, )
    recommend_date = fields.Datetime(string="Date Recommended", required=False, )
    evaluate_id = fields.Many2one(comodel_name="hr.employee", string="Evaluated By", required=False, )
    evaluate_date = fields.Datetime(string="Date Evaluated", required=False, )
    approve_id = fields.Many2one(comodel_name="hr.employee", string="Approved By", required=False, )
    approve_date = fields.Datetime(string="Date Approved", required=False, )
    applicant_ids = fields.Many2many(comodel_name="hr.applicant", string="Applicants")
    hired_applicant_line = fields.One2many(comodel_name="hr.applicant", inverse_name="recruitment_request_id", string="Hired Employees",
                                           required=False, domain=lambda self: ['|', ('is_hired', '=', True), ('is_initial_hired', '=', True)])
    budget = fields.Integer(string="Approve Manpower (Budget)",  required=False, compute='compute_applicants_variance', store=True)
    actual = fields.Integer(string="Actual",  required=False, compute='compute_applicants_variance', store=True)
    variance = fields.Integer(string="Variance",  required=False, compute='compute_applicants_variance', store=True)
    unbudget_justification = fields.Text(string="Justification for Unbudgeted Requisition", required=False, )

    @api.constrains('state', 'job_id', 'department_id', 'company_id')
    def _check_request_existence(self):
        for request in self:
            domain = [('state', 'not in', ['draft', 'close']),
                      ('job_id', '=', request.job_id.id),
                      ('department_id', '=', request.department_id.id),
                      ('company_id', '=', request.company_id.id),
                      ('id', '!=', request.id)]
            requests = self.search_count(domain)
            if requests:
                raise ValidationError(_('You can not have 2 personnel requests on the same running!'))

    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        if vals.get('number', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('recruitment.ref')
        if 'no_of_recruitment' in vals:
            if vals['no_of_recruitment'] <= 0:
                raise ValidationError(_("Please check the expected employees on your request."))
        return super(HrRecruitmentRequest, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'applicant_ids' in vals:
            self.count_applications()
        return super(HrRecruitmentRequest, self).write(vals)

    @api.onchange('requester_id')
    def _onchange_request_id(self):
        if self.requester_id:
            if self.requester_id.parent_id:
                self.recommend_id = self.requester_id.parent_id.id

    @api.onchange('job_id')
    def _onchange_job_id(self):
        if self.job_id:
            company = self.env['res.company'].search([('partner_id', '=', self.job_id.address_id.id)], limit=1)
            if company:
                self.company_id = company.id

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            if self.company_id.id != self.department_id.company_id.id:
                raise ValidationError(_("Please specified the department according to the company."))

    # @api.onchange('job_id', 'department_id')
    # def get_no_of_employee(self):
    #     if self.job_id and self.department_id:
    #         no_of_employee = self.env['hr.employee'].search_count([('job_id', '=', self.job_id.id),
    #                                                                ('department_id', '=', self.department_id.id),
    #                                                                ('active', '=', True)])
    #         print no_of_employee
    #         self.actual = no_of_employee
            # company = self.env['res.company'].search([('partner_id', '=', self.job_id.address_id.id)], limit=1)
            # if company:
            #     self.company_id = company.id

    @api.onchange('company_id')
    def _onchange_company_id(self):
        result = {}
        if self.company_id:
            result['domain'] = {'department_id': [
                ('company_id', '=', self.company_id.id)]}
            return result

    @api.multi
    @api.depends('no_of_hired_employee')
    def _check_no_of_hired_employee(self):
        if self.no_of_hired_employee:
            if self.no_of_hired_employee >= self.no_of_recruitment:
                self.action_close()

    @api.constrains('job_id')
    def check_request_existence(self):
        if self.job_id:
            request = self.search([('job_id', '=', self.job_id.id),
                                   ('state', '=', 'open')])
            if request:
                raise ValidationError(_('Request already existed! Please Verify your request!'))

    @api.multi
    @api.depends('applicant_ids')
    def count_applications(self):
        for record in self:
            count = len(record.applicant_ids)
            record.no_of_applications = count

    @api.multi
    def action_open(self):
        if self.requester_id.user_id.id == self.env.user.id or self.env.user.has_group('hr_recruitment.group_hr_recruitment_user'):
            if self.recommend_id and self.approve_id and self.evaluate_id:
                self.state = 'confirm'
            if not self.recommend_id and self.approve_id and self.evaluate_id:
                self.state = 'managers_approval'
            if not self.recommend_id and not self.approve_id and self.evaluate_id:
                self.state = 'bod_approval'
        else:
            raise ValidationError(_('You cannot confirm other request(s)'))
        if not self.recommend_id and not self.approve_id and not self.evaluate_id:
            raise ValidationError(_("Please fill the approvals of the request."))

    @api.multi
    def action_cancelled(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
                self.requester_id.user_id.id == self.env.user.id or \
                self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            self.state = 'cancel'
            self.active = False
            date_request = datetime.strptime(self.date_request, '%Y-%m-%d').date()
            department_id = self.department_id.parent_id.id if self.department_id.parent_id.id else self.department_id.id
            manpower = self.env['hr.manpower.plan'].search([('department_id', '=', department_id),
                                                            ('month_date', '=', date_request.month),
                                                            ('year_date', '=', str(date_request.year)),
                                                            ('state', '=', 'posted')], limit=1)
            if manpower:
                for line in manpower.line_ids:
                    if line.job_id.id == self.job_id.id:
                        previous_no_of_recruitment = self.budget - self.no_of_recruitment
                        line.write({'no_of_recruitment': self.variance, 'total': previous_no_of_recruitment if previous_no_of_recruitment > 0 else 0})
            next_manpower = self.env['hr.manpower.plan'].search([('department_id', '=', department_id),
                                                                ('month_date', '>', date_request.month),
                                                                ('year_date', '=', str(date_request.year)),
                                                                ('state', '=', 'posted')])
            if next_manpower:
                for mp in next_manpower:
                    for line in mp.line_ids:
                        if line.job_id.id == self.job_id.id and line.no_of_employee == self.budget:
                            previous_no_of_recruitment = self.budget - self.no_of_recruitment
                            line.write({'no_of_recruitment': self.variance, 'total': previous_no_of_recruitment if previous_no_of_recruitment > 0 else 0})

        else:
            raise ValidationError(_('You cannot cancel other request(s)'))

    @api.multi
    def action_close(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            self.state = 'close'
            job = self.env['hr.job'].browse(self.job_id.id)
            job.set_open()
        else:
            raise ValidationError(_('Only Recruitment personnel can confirm the request!'))

    @api.multi
    def action_reset_draft(self):
        if self.state == 'refuse':
            user = self.env.user.id
            if self.requester_id.user_id.id == user or self.recommend_id.user_id.id == user or \
                    self.approve_id.user_id.id == user or self.evaluate_id.user_id.id == user or \
                    self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
                    self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                self.state = 'draft'
            else:
                raise ValidationError(_("You are not allowed for this request. Please contact you administrator."))
        else:
            raise ValidationError(_("Please refuse the request before setting to draft."))

    @api.multi
    def action_refuse(self):
        if self.state not in ('refuse', 'draft', False, 'close', 'cancel'):
            user = self.env.user.id
            if self.requester_id.user_id.id == user or self.recommend_id.user_id.id == user or \
                    self.approve_id.user_id.id == user or self.evaluate_id.user_id.id == user or \
                    self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
                    self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                self.state = 'refuse'
            else:
                raise ValidationError(_("You are not allowed for this request. Please contact you administrator."))
        else:
            raise ValidationError(_("Please refuse the request before setting to draft."))

    @api.multi
    def action_managers_approval(self):
        user = self.env.user
        if self.state == 'confirm':
            if self.recommend_id.user_id.id == user.id or self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') \
                    or self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                self.state = 'managers_approval'
                # self.recommend_id = self.requester_id.parent_id.id
                self.recommend_date = datetime.now()
            else:
                raise ValidationError(_('Only allowed validator can confirm the request!'))
        else:
            raise ValidationError(_('Please follow the procedure or request!'))

    @api.multi
    def action_bod_approval(self):
        user = self.env.user
        if self.state == 'managers_approval':
            if self.approve_id.user_id.id == user.id or self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') \
                    or self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                self.state = 'bod_approval'
                # self.approve_id = self.requester_id.parent_id.parent_id.id
                self.approve_date = datetime.now()
            else:
                raise ValidationError(_('Only allowed validator can confirm the request!'))
        else:
            raise ValidationError(_('Please follow the procedure or request!'))

    @api.multi
    def action_confirm(self):
        if self.state == 'bod_approval':
            user = self.env.user
            if self.evaluate_id.user_id.id == user.id or self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') \
                    or self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
                self.state = 'validate'
                # evaluate = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
                # self.evaluate_id = evaluate.id
                self.evaluate_date = datetime.now()
                job = self.env['hr.job'].browse(self.job_id.id)
                job.set_recruit()
                job.compute_no_of_recruitment()

                if self.variance < 0:
                    date_request = datetime.strptime(self.date_request, '%Y-%m-%d').date()
                    department = self.department_id.parent_id if self.department_id.parent_id else self.department_id
                    manpower = self.env['hr.manpower.plan']
                    manpower_line = self.env['hr.manpower.plan.line']
                    manpower_plan_res = manpower.search([('department_id', '=', department.id),
                                                         ('year_date', '=', str(date_request.year)),
                                                         ('month_date', '=', date_request.month)], limit=1,
                                                        order="month_date desc")
                    if not manpower_plan_res:
                        requester_id = department.supervisor_id.id if department.supervisor_id.id else department.manager_id.id
                        if not requester_id:
                            raise ValidationError(_("Please fill-out the supervisor or manager of the branch / department."))
                        values = {
                            'department_id': department.id,
                            'company_id': department.company_id.id,
                            'year_date': str(date_request.year),
                            'month_date': int(date_request.month),
                            'requester_id': department.supervisor_id.id if department.supervisor_id.id else department.manager_id.id,
                            'date_filed': date.today(),
                            'state': 'posted',
                            'posted': True
                        }
                        res = manpower.create(values)
                        manpower_plan_previous = manpower.search([('id', '!=', res.id), ('department_id', '=', department.id),
                                                                  ('year_date', '=', str(date_request.year)),
                                                                  ('month_date', '<=', date_request.month)], limit=1,
                                                                 order="month_date desc")
                        if manpower_plan_previous:
                            for line in manpower_plan_previous.line_ids:
                                if line.job_id.id == self.job_id.id:
                                    additions = abs(self.variance)
                                else:
                                    additions = 0
                                vals = {
                                    'manpower_id': res.id,
                                    'job_id': line.job_id.id,
                                    'department_id': line.department_id.id,
                                    'no_of_employee': line.total,
                                    'no_of_recruitment': additions,
                                    'total': line.total + additions
                                }
                                manpower_line.create(vals)
                        else:
                            department_list = [self.department_id.id]
                            departments = self.env['hr.department'].search([('parent_id', '=', self.department_id.id)])
                            if departments:
                                for dept in departments:
                                    department_list.append(dept.id)
                            job_list = [self.job_id.id, self.job_id.name]
                            employees = self.env['hr.employee'].search([('department_id', 'in', department_list),
                                                                        ('state', 'not in', ['relieved', 'terminate'])])
                            if employees:
                                for employee in employees:
                                    job_list.append((employee.job_id.id, employee.job_id.name))

                            if job_list:

                                for job in sorted(list(set(job_list)), key=lambda j: j[1]):
                                    date_joined = date(int(date_request.year), int(date_request.month),
                                                       calendar.monthrange(int(date_request.year), int(date_request.month))[1])
                                    employees_count = self.env['hr.employee'].search_count([('job_id', '=', job[0]),
                                                                                            ('department_id', 'in', department_list),
                                                                                            ('state', 'not in',['relieved','terminate']),
                                                                                            ('date_hired', '<=', date_joined)])
                                    if job[0] == self.job_id.id:
                                        additions = abs(self.variance)
                                    else:
                                        additions = 0
                                    vals = {
                                        'manpower_id': res.id,
                                        'job_id': job[0],
                                        'department_id': department.id,
                                        'no_of_employee': employees_count,
                                        'no_of_recruitment': additions,
                                        'total': employees_count + additions
                                    }
                                    manpower_line.create(vals)
                    else:
                        for line in manpower_plan_res.line_ids:
                            if line.job_id.id == self.job_id.id:
                                additions = abs(self.variance)
                                vals = {'no_of_recruitment': additions, 'total': line.total + additions}
                                manpower_plan_res.write(vals)

                    manpower_plan_next_line = manpower.search([('department_id', '=', department.id),
                                                               ('year_date', '=', str(date_request.year)),
                                                               ('month_date', '>', date_request.month)],
                                                               order="month_date")
                    if manpower_plan_next_line:
                        for mp in manpower_plan_next_line:
                            for mp_line in mp.line_ids:
                                if mp_line.job_id.id == self.job_id.id:
                                    no_of_employee = mp_line.no_of_employee + abs(self.variance)
                                    total = no_of_employee + mp_line.no_of_recruitment
                                    mp_line.write({'no_of_employee': no_of_employee,
                                                   'no_of_recruitment': mp_line.no_of_recruitment,
                                                   'total': total})

            else:
                raise ValidationError(_('Only Recruitment validator can confirm the request!'))
        else:
            raise ValidationError(_('Please follow the procedure or request!'))

    @api.multi
    def get_approvers_name(self, values):
        if values:
            employee = self.env['hr.employee'].browse(values)
            if employee:
                last_name = employee.last_name
                first_name = employee.first_name
                if employee.middle_name:
                    middle_name = str(employee.middle_name)[:1]
                else:
                    middle_name = ''
                name = '%s %s. %s' % (first_name, middle_name, last_name)
                return name


class HrManPowerPlan(models.Model):
    _name = 'hr.manpower.plan'
    _order = 'name'

    @api.multi
    @api.depends('month_date', 'year_date')
    def compute_date_applied(self):
        for record in self:
            if record.month_date and record.year_date:
                record.update({'date_applied': date(int(record.year_date), int(record.month_date), 01)})

    name = fields.Char(string="Description", required=False, )
    department_id = fields.Many2one(comodel_name="hr.department", string="Branch / Department", required=False, )
    company_id = fields.Many2one(comodel_name="res.company", string="Company", required=False, )
    requester_id = fields.Many2one(comodel_name="hr.employee", string="Requester", required=True,
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1))
    month_date = fields.Selection(selection=MonthDate, required=False, string="Month")
    year_date = fields.Selection([(str(num), str(num)) for num in range(datetime.now().year - 1, datetime.now().year + 4)],
                                 string="Year")
    date_applied = fields.Date(string="Date Applied", required=False, compute="compute_date_applied", store=True)
    date_filed = fields.Date(string="Date Filed", required=False, default=fields.Date.context_today)
    posted = fields.Boolean(string="Posted")
    state = fields.Selection(string="Status", selection=[('draft', 'Draft'), ('posted', 'Posted'), ], required=False, default='draft')
    line_ids = fields.One2many(comodel_name="hr.manpower.plan.line", inverse_name="manpower_id",
                               string="Job Positions", required=False, )

    @api.onchange('date_filed')
    def check_date_filed(self):
        result = {}
        if self.date_filed:
            records = []
            # if self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
            #         self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            departments = self.env['hr.department'].search([('active', '=', True)])
            if departments:
                for department in departments:
                    if not department.parent_id and department.id not in records:
                        records.append(department.id)
            # if self.requester_id.user_id.id == self.env.user.id and (not self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or
            #                                                          not self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager')):
            #     employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            #     if employee:
            #         if not employee.department_id.parent_id and employee.department_id.id not in records:
            #             records.append(employee.department_id.id)
            result['domain'] = {'department_id': [('id', 'in', records)]}
            return result

    @api.multi
    def cron_sending_personnel_requisition(self):
        date_today = date.today() + relativedelta(months=1)
        start = date(date_today.year, date_today.month, 01)
        end = date(date_today.year, date_today.month, calendar.monthrange(date_today.year, date_today.month)[1])
        manpower = self.search([('month_date', '=', date_today.month), ('year_date', '=', date_today.year),
                                ('state', '=', 'posted')])
        for mp in manpower:
            for line in mp.line_ids:
                if line.no_of_recruitment > 0:
                    personnel_requisition = self.env['hr.recruitment.request'].search([('date_request', '>=', start),
                                                                                       ('date_request', '<=', end),
                                                                                       ('job_id', '=', line.job_id.id), '|',
                                                                                       ('department_id', '=', mp.department_id.id),
                                                                                       ('department_id.parent_id', '=', mp.department_id.id)])
                    if not personnel_requisition:
                        mail_mail = self.env['mail.mail']
                        if mp.requester_id.user_id.partner_id:
                            sender_email = mp.requester_id.user_id.partner_id.email
                            author = mp.company_id.partner_id

                            if mp.requester_id.gender == 'female':
                                if mp.requester_id.marital == 'married':
                                    header = "<p>Hi <b>Mrs. " + mp.requester_id.first_name + " " + mp.requester_id.middle_name + " " + mp.requester_id.last_name + "</b>, </p><br/>"
                                else:
                                    header = "<p>Hi <b>Ms. " + mp.requester_id.first_name + " " + mp.requester_id.middle_name + " " + mp.requester_id.last_name + "</b>, </p><br/>"
                            else:
                                header = "<p>Hi <b>Mr. " + mp.requester_id.first_name + " " + mp.requester_id.middle_name + " " + mp.requester_id.last_name + "</b>, </p><br/>"

                            body_html = header
                            lines = "Good Day! Your department might have a job vacancy on a month of <b>" + calendar.month_name[date_today.month] + "</b> for the position of <b>" + line.job_id.name + "(" + str(line.no_of_recruitment) + ")</b>.<br/> Please fill-out a personnel requisition form and submit it immediately. Thank you!"
                            body_html += "<p>" + lines + "</p>"

                            body_html += "<br/><p>Best regards, </p><p><b> " + author.name + "</p><br/>"

                            vals = {
                                'subject': 'Personnel Requisition Request',
                                'date': datetime.now(),
                                'email_from': '\"' + author.name + '\"<' + sender_email + '>',
                                'author_id': author.id,
                                'recipient_ids': [(4, mp.requester_id.user_id.partner_id.id)],
                                'reply_to': '\"' + author.name + '\"<' + sender_email + '>',
                                'body_html': body_html,
                                'auto_delete': False,
                                'message_type': 'email',
                                'notification': True,
                                'mail_server_id': self.env.ref('mgc_base.config_email_server_gmail_noreply').id,
                                'model': line._name,
                                'res_id': line.id,
                            }
                            result = mail_mail.create(vals)
                            result.send()
                            return result

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.company_id = self.department_id.company_id.id
            if self.department_id.supervisor_id:
                self.requester_id = self.department_id.supervisor_id.id
            else:
                self.requester_id = self.department_id.manager_id.id

    @api.constrains('department_id', 'month_date', 'year_date')
    def check_manpower_plan(self):
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('department_id', '=', record.department_id.id),
                ('year_date', '=', record.year_date),
                ('month_date', '=', record.month_date)
            ]
            exist = self.search_count(domain)
            if exist:
                raise ValidationError(_('You can not have same months in your manpower plan!'))

    @api.onchange('department_id', 'month_date', 'year_date')
    def _onchange_department_ids(self):
        if self.department_id and self.month_date and self.year_date:

            lines = []
            self.company_id = self.department_id.company_id
            if self.department_id.supervisor_id:
                self.requester_id = self.department_id.supervisor_id.id
            else:
                self.requester_id = self.department_id.manager_id.id
            # month_date = int(self.month_date) - 1
            manpower_plan_res = self.sudo().search([('department_id', '=', self.department_id.id),
                                                    ('year_date', '=', self.year_date),
                                                    ('month_date', '<=', self.month_date)], limit=1, order="month_date desc")
            if manpower_plan_res:
                for line in manpower_plan_res.line_ids:
                    values = {
                        'job_id': line.job_id.id,
                        'department_id': line.department_id.id,
                        'no_of_employee': line.total,
                        'no_of_recruitment': 0,
                        'total': line.total
                    }
                    lines.append((0, 0, values))
            else:
                department_list = [self.department_id.id]
                departments = self.env['hr.department'].search([('parent_id', '=', self.department_id.id)])
                if departments:
                    for department in departments:
                        department_list.append(department.id)
                job_list = []
                employees = self.env['hr.employee'].search([('department_id', 'in', department_list),
                                                            ('state', 'not in',['relieved', 'terminate'])])
                if employees:
                    for employee in employees:
                        job_list.append((employee.job_id.id, employee.job_id.name))

                if job_list:

                    for job in sorted(list(set(job_list)), key=lambda j: j[1]):
                        date_joined = date(int(self.year_date), int(self.month_date), calendar.monthrange(int(self.year_date), int(self.month_date))[1])
                        employees_count = self.env['hr.employee'].search_count([('job_id', '=', job[0]),
                                                                                ('department_id', 'in', department_list),
                                                                                ('state', 'not in', ['relieved', 'terminate']),
                                                                                ('date_hired', '<=', date_joined)])
                        if not employees_count:
                            count = 0
                        else:
                            count = employees_count
                        values = {
                            'job_id': job[0],
                            'department_id': self.department_id.id,
                            'no_of_employee': count,
                            'no_of_recruitment': 0,
                            'total': count
                        }
                        lines.append((0, 0, values))
            self.line_ids = lines

    @api.model
    def create(self, values):
        if 'department_id' in values and 'requester_id' in values and 'month_date' in values and 'year_date' in values:
            requester_id = self.env['hr.employee'].browse(values['requester_id'])
            department_id = self.env['hr.department'].browse(values['department_id'])
            values['name'] = department_id.name + " " + str(requester_id.identification_id) + "-[" + str(values['month_date']) + "/" + str(values['year_date']) + ']'
        return super(HrManPowerPlan, self).create(values)

    @api.multi
    def write(self, values):
        values['name'] = self.department_id.name + " " + str(self.requester_id.identification_id) + "-[" + str(self.month_date) + "/" + str(self.year_date) + ']'
        res = super(HrManPowerPlan, self).write(values)
        # if res:
        #     if self.no_of_recruitment <= 0:
        #         raise ValidationError(_("Please verify your number of expected employees needed. Thank you!"))
        return res

    @api.multi
    def action_posted(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
                self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager') or\
                self.requester_id.user_id.id == self.env.user.id:
            self.state = 'posted'
            self.posted = True
        else:
            raise ValidationError(_("You are not allowed for this process. Please contact the administrator."))

    def action_unposted(self):
        if self.env.user.has_group('hr_recruitment.group_hr_recruitment_user') or \
                self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager'):
            self.state = 'draft'
        else:
            raise ValidationError(_("You are not allowed for this process. Please contact the administrator."))


class HrManpowerPlanLine(models.Model):
    _name = 'hr.manpower.plan.line'

    @api.multi
    @api.depends('no_of_employee', 'no_of_recruitment')
    def compute_total(self):
        for record in self:
            if record.no_of_employee or record.no_of_recruitment:
                record.total = record.no_of_employee + record.no_of_recruitment

    manpower_id = fields.Many2one(comodel_name="hr.manpower.plan", string="Manpower Plan", required=False, )
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    department_id = fields.Many2one(comodel_name="hr.department", string="Branch / Department", required=False,)
    no_of_employee = fields.Integer(string="Actual # of Employee(s)", required=False, )
    no_of_recruitment = fields.Integer(string="Expected Employees Needed", required=False, )
    total = fields.Integer(string="Total # of Employee(s)", required=False, compute="compute_total", store=True)

    @api.model
    def create(self, values):
        res = super(HrManpowerPlanLine, self).create(values)
        if res and ('no_of_employee' in values or 'no_of_recruitment' in values):
            res.compute_total()
        return res

    @api.multi
    def write(self, values):
        res = super(HrManpowerPlanLine, self).write(values)
        if res and ('no_of_employee' in values or 'no_of_recruitment' in values):
            self.compute_total()
        return res

    # @api.onchange('no_of_employee', 'no_of_recruitment')
    # def compute_total(self):
    #     # for record in self:
    #     if self.no_of_employee and self.no_of_recruitment:
    #         self.total = self.no_of_employee + self.no_of_recruitment
