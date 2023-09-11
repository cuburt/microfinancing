FROM odoo:12
USER root
RUN chown -R odoo:odoo /var/lib/odoo
RUN mkdir var/lib/odoo/sessions
RUN chmod +w /var/lib/odoo/sessions
COPY . mnt/extra-addons

RUN alias python=python3
RUN pip3 install -r mnt/extra-addons/requirements.txt