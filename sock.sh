# These are the commands used to update the Gunicorn instance to the current stamp of changes done within the app
app='reg'

sudo systemctl stop $app
sudo systemctl start $app
sudo systemctl daemon-reload
sudo systemctl enable $app
sudo systemctl status $app