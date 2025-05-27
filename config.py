# In config.py
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()  # Looks for .env in current directory

# Access variables

SQLALCHEMY_DATABASE_URI= "sqlite:///sk_tickets.db"
SQLALCHEMY_TRACK_MODIFICATIONS= False 
FLASK_SECRET_KEY="a867431a0ab449d8c967e1c950eba612a289a505a7938c6c"
MPESA_BASE_URL= "https://sandbox.safaricom.co.ke"
MPESA_ACCESS_TOKEN_URL= "oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL= "mpesa/stkpush/v1/processrequest"
MPESA_STK_QUERY_URL="mpesa/stkpushquery/v1/query"
MPESA_CALLBACK_URL="https://d14d-197-232-16-120.ngrok-free.app/api/mpesa-callback"
#  "https://13a6-169-150-218-3.ngrok-free.app/callback"

MPESA_PASSKEY= "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

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