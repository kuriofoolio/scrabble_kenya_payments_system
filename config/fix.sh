cd ..

#give user sudo priv
usermod -aG sudo <user>
#after installing requirements, do this for things to work
#gunicorn --bind 0.0.0.0:5000 wsgi:app

sudo nano /etc/ssh/sshd_config
systemctl restart sshd

venv
py app.py
gunicorn --bind 0.0.0.0:5000 wsgi:app

# this is much safer, in case it brings flask cant be found
python -m gunicorn --bind 0.0.0.0:5000 wsgi:app
deactivate

# create the service to serve the app
sudo nano /etc/systemd/system/sk.service 

# bring up the service
sudo systemctl daemon-reload
sudo systemctl start sk
sudo systemctl enable sk
sudo systemctl status sk

# set up nginx to point to your domain
sudo nano /etc/nginx/sites-available/sk.conf
# sudo unlink /etc/nginx/sites-enabled/app.conf
sudo ln -s /etc/nginx/sites-available/sk.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo ufw enable
sudo ufw delete allow 5000
sudo ufw allow "Nginx Full"
sudo ufw status
sudo tail /var/log/nginx/error.log 
# sudo chmod 775 /home/kuria

# reload the server
bash sock.sh