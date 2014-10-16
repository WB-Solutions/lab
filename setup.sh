#!/bin/bash

sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install -y htop
sudo apt-get install -y zip

sudo apt-get install -y python-pip

sudo apt-get install -y nginx
sudo apt-get install -y uwsgi
sudo apt-get install -y uwsgi-plugin-python

sudo apt-get install -y git

sudo apt-get install -y postgresql
sudo apt-get install -y postgresql-contrib
sudo apt-get install -y python-psycopg2

sudo apt-get update
sudo apt-get upgrade -y


sudo echo '
server {
        client_max_body_size 10M;
        listen  80;
        server_name  $hostname  lab.gonubex.com  medical.bicloud.com.mx;
        location   /static  {
                alias  /home/django/lab/mysite/static/;
        }
        location  /  {
                uwsgi_pass  127.0.0.1:9003;
                include  uwsgi_params;
        }
}
' > /etc/nginx/sites-available/lab
sudo ln -s /etc/nginx/sites-available/lab /etc/nginx/sites-enabled/lab
sudo rm /etc/nginx/sites-enabled/default


sudo echo '
<uwsgi>
    <chdir>/home/django/lab/mysite/</chdir>
    <module>mysite.wsgi:application</module>
    <env>DJANGO_SETTINGS_MODULE=mysite.settings</env>
    <socket>127.0.0.1:9003</socket>
    <master/>
    <processes>4</processes>
</uwsgi>
' > /etc/uwsgi/apps-available/lab.xml
sudo ln -s /etc/uwsgi/apps-available/lab.xml /etc/uwsgi/apps-enabled/lab.xml


cd /home
sudo mkdir django
cd django
sudo git clone https://github.com/WB-Solutions/lab.git
cd lab/mysite

sudo pip install Django==1.7
sudo pip install django-suit
sudo pip install django-extensions
sudo pip install djangorestframework
sudo pip install djangorestframework-jwt
sudo pip install django-filter
# sudo pip install django-oauth2-provider
sudo pip install django-mptt
sudo pip install django-allauth
sudo pip install django-bootstrap3

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'lab'"
sudo -u postgres createdb lab
sudo -u postgres psql -l

sudo python manage.py migrate # syncdb --noinput
sudo python manage.py setup_db


sudo service postgresql restart
sudo service uwsgi restart
sudo service nginx restart
