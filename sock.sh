# cd ..
sudo systemctl stop sk
sudo systemctl start sk
sudo systemctl daemon-reload
sudo systemctl enable sk
sudo systemctl status sk