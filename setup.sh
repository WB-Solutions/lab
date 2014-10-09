#!/bin/bash

sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install -y htop
sudo apt-get install -y curl

# sudo apt-get install -y python
# sudo apt-get install -y ipython

# sudo apt-get install -y python-setuptools
# sudo easy_install pip
sudo apt-get install -y python-pip

sudo apt-get install -y nginx
# pip install uwsgi
sudo apt-get install -y uwsgi
sudo apt-get install -y uwsgi-plugin-python

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
    <processes>2</processes>
</uwsgi>
' > /etc/uwsgi/apps-available/lab.xml
sudo ln -s /etc/uwsgi/apps-available/lab.xml /etc/uwsgi/apps-enabled/lab.xml

sudo apt-get install -y git

sudo apt-get update
sudo apt-get upgrade -y



cd /home
sudo mkdir django
cd django
sudo mkdir lab_db
sudo git clone https://github.com/WB-Solutions/lab.git
cd lab/mysite

sudo pip install Django==1.6.5
sudo pip install django-suit
sudo pip install django-extensions
sudo pip install djangorestframework
sudo pip install djangorestframework-jwt
# sudo pip install django-oauth2-provider
sudo pip install django-mptt
sudo pip install django-allauth
sudo pip install django-bootstrap3

sudo python manage.py syncdb --noinput

sudo chmod 777 /home/django/lab_db
sudo chmod 777 /home/django/lab_db/db.sqlite3

sudo python manage.py setup_db



sudo service uwsgi restart
sudo service nginx restart
