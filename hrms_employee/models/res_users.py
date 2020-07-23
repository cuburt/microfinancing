from odoo import models, api, fields
from odoo.exceptions import ValidationError, UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.multi
    def write(self, values):
        res = super(ResUsers, self).write(values)
        if res:
            job = self.env['hr.job'].search([('default_user_id', '=', self.id)])
            employee = self.env['hr.employee']
            if job:
                job_user = job.default_user_id.id
                emp_res = employee.search([('job_id', '=', job.id)])
                for emp in emp_res:
                    if emp.user_id:
                        uid = emp.user_id.id
                        self._cr.execute("""delete from res_groups_users_rel where uid=%s and
                                            gid not in (select gid from res_groups_users_rel
                                            where uid = %s)""" % (uid, job_user))
                        self._cr.commit()
                        self._cr.execute("""select gid from res_groups_users_rel where uid = %s
                                                and gid not in (select gid from res_groups_users_rel
                                                where uid = %s)""" % (job_user, uid))
                        records = self._cr.fetchall()
                        if records:
                            for record in records:
                                gid = record[0]
                                self._cr.execute("""insert into res_groups_users_rel(gid,uid)values(%s,%s)""" % (gid, uid))
                                self._cr.commit()
                        emp.update({'is_check_template': True})

        return res
