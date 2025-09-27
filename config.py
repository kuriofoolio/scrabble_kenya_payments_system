# In config.py
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()  # Looks for .env in current directory

# Access variables

SQLALCHEMY_DATABASE_URI= "sqlite:///sk_tickets.db"
SQLALCHEMY_TRACK_MODIFICATIONS= False 
FLASK_SECRET_KEY="a867431a0ab449d8c967e1c950eba612a289a505a7938c6c"
PESAPAL_BASE_URL = "https://pay.pesapal.com/v3"
PESAPAL_CONSUMER_KEY = "CdvEJKiWtYguQqEHfRIJ8vZ8lmlWDa1P"
PESAPAL_CONSUMER_SECRET = "1dKYEWoxb2aiLic4cdNTT6WLDWE="
#PESAPAL_CALLBACK_URL = "pesapal/callback"
#PESAPAL_IPN_URL = "pesapal/ipn"

# Email Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
# MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

# print (type(MAIL_USERNAME))

# Alternative configuration for other email providers:
# For Outlook/Hotmail:
# MAIL_SERVER = 'smtp-mail.outlook.com'
# MAIL_PORT = 587

# For Yahoo:
# MAIL_SERVER = 'smtp.mail.yahoo.com'
# MAIL_PORT = 587

# For custom SMTP (like cPanel hosting):
# MAIL_SERVER = 'mail.yourdomain.com'
# MAIL_PORT = 587
# MAIL_USERNAME = 'noreply@yourdomain.com'
# MAIL_PASSWORD = 'your-email-password'
