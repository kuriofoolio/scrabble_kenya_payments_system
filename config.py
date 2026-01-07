# In config.py
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()  # Looks for .env in current directory

# Access variables

SQLALCHEMY_DATABASE_URI= "sqlite:///sk_tickets.db"
SQLALCHEMY_TRACK_MODIFICATIONS= False 
FLASK_SECRET_KEY="a867431a0ab449d8c967e1c950eba612a289a505a7938c6c"
MPESA_BASE_URL= "https://api.safaricom.co.ke"
MPESA_ACCESS_TOKEN_URL= "oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL= "mpesa/stkpush/v1/processrequest"
MPESA_STK_QUERY_URL="mpesa/stkpushquery/v1/query"
MPESA_CALLBACK_URL="https://66769a289536.ngrok-free.app/api/mpesa-callback"

MPESA_PASSKEY= "27a4ec97fc2e5e9cfd7aea12d1308389bcfaa938bbb8d7f933c72a9a8f14529a"

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
