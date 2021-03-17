FROM odoo:12
COPY odoo12 ./var/CARE/odoo
COPY CARE ./var/CARE/CARE
WORKDIR ./var/CARE/odoo
RUN alias python=python3
RUN pip3 install -r ./var/CARE/CARE/requirements.txt
CMD ["odoo-bin","-c","odoo-care.conf","-d","CARE","-i","base","--without-demo=WITHOUT_DEMO"]