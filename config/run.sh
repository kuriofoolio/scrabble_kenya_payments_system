bash sock.sh 
venv
gunicorn --bind 0.0.0.0:5000 wsgi:app
deactivate
sudo nginx -t
sudo systemctl restart nginx
