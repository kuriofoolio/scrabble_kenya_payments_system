# In config.py
from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()  # Looks for .env in current directory

# Access variables
PORT=os.getenv('PORT')
SQLALCHEMY_DATABASE_URI= "sqlite:///sk_tickets.db"
SQLALCHEMY_TRACK_MODIFICATIONS= False 
MPESA_BASE_URL= "https://api.safaricom.co.ke"
MPESA_ACCESS_TOKEN_URL= "oauth/v1/generate?grant_type=client_credentials"
MPESA_STK_PUSH_URL= "mpesa/stkpush/v1/processrequest"
MPESA_STK_QUERY_URL="mpesa/stkpushquery/v1/query"
MPESA_PASSKEY= os.getenv('MPESA_PASSKEY')
MPESA_CONSUMER_KEY=  os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET=  os.getenv('MPESA_CONSUMER_SECRET')
MPESA_TILL_NUMBER=  os.getenv('MPESA_TILL_NUMBER')
MPESA_BUSINESS_SHORT_CODE=  os.getenv('MPESA_BUSINESS_SHORT_CODE')
FLASK_SECRET_KEY=  os.getenv('FLASK_SECRET_KEY')
# MPESA_CALLBACK_URL="https://cf8061fe3e78.ngrok-free.app/api/mpesa-callback"
MPESA_CALLBACK_URL="https://register.scrabblekenya.com/api/mpesa-callback"

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
