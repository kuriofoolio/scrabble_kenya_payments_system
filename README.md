
<img src="static/img/sk_logo.png" alt="Scrabble Kenya Logo" width="180" height="180"></img>

# Scrabble Kenya Tournament Registration System API Documentation

## Introduction

The Scrabble Kenya Tournament Registration System is a Flask-based backend application that enables players to register for tournament divisions and process payments via M-Pesa. This system is designed to provide a seamless registration experience for tournament organizers, specifically tailored for competitive Scrabble tournaments in Kenya.

This API handles the complete workflow from division listing to payment processing and ticket generation, with integrated email confirmations. With M-Pesa payment functionality and automated email notifications, it provides a comprehensive solution for tournament registration management.

Key features include:
- Division management (add, retrieve divisions with rating bands)
- Player management and registration
- Multi-player ticket purchasing
- M-Pesa payment integration with STK Push
- Payment status tracking
- Automated email confirmations
- Rating-based division eligibility
- Professional tournament administration

## Getting Started

### Prerequisites

- Python 3.6+
- Flask and Flask-SQLAlchemy
- Flask-Mailman (for email functionality)
- Requests library
- SQLite (for development) or another database of your choice
- M-Pesa developer account (for Safaricom API access)
- Email account for sending confirmations (Gmail recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/scrabble-kenya-tournament-system.git
   cd scrabble-kenya-tournament-system
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the application:
   - Update the M-Pesa configuration in the `config.py` file with your Safaricom credentials
   - Update the `MPESA_CALLBACK_URL` to your actual callback URL
   - Configure email settings with your SMTP credentials

5. Create the templates directory and add email templates:
   ```bash
   mkdir templates
   # Place ticket_confirmation.html in the templates folder
   ```

6. Run the application:
   ```bash
   python app.py
   ```

The server will start at `http://localhost:5000` or `http://127.0.0.1:5000`.

## Database Schema

The system uses five main models:

### Division
- `divisionId`: Primary key (integer)
- `title`: Division title (string, required)
- `description`: Division description (text)
- `minimumRating`: Minimum player rating for division (integer, required)
- `maximumRating`: Maximum player rating for division (integer, required)
- `price`: Registration price (decimal, required)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

### Player
- `playerId`: Primary key (integer)
- `playerName`: Player's full name (string, required)
- `playerRating`: Player's tournament rating (integer, required)
- `playerEmail`: Player's email address (string, optional)

### Payment
- `paymentId`: Primary key (integer)
- `customerName`: Name of the person making payment (string, required)
- `phoneNumber`: Customer phone number (string, required)
- `totalAmount`: Total amount paid (decimal, required)
- `paymentStatus`: Status of payment ('Pending', 'Paid', 'Failed')
- `mpesaReceiptNumber`: M-Pesa receipt number (string)
- `transactionDate`: Date and time of the transaction (datetime)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

### Ticket
- `ticketId`: Primary key (integer)
- `ticketPrice`: Individual ticket price (decimal, required)
- `divisionId`: Foreign key to Division (integer, required)
- `playerId`: Foreign key to Player (integer, required, unique)
- `paymentId`: Foreign key to Payment (integer, required)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

### PushRequest
- `pushRequestId`: Primary key (integer)
- `paymentId`: Foreign key to Payment (integer, required)
- `checkoutRequestId`: M-Pesa checkout request ID (string, required)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

## API Endpoints

### Root Endpoint
- **URL**: `/`
- **Method**: `GET`
- **Description**: Display tournament registration page
- **Response**: HTML page with registration interface

### Division Management

#### Get All Divisions
- **URL**: `/api/divisions`
- **Method**: `GET`
- **Description**: Retrieve all tournament divisions
- **Response**: JSON object containing an array of divisions
  ```json
  {
    "divisions": [
      {
        "divisionId": 1,
        "title": "Premier Division",
        "description": "Top-tier competition for experienced players",
        "minimumRating": 1800,
        "maximumRating": 2500,
        "price": 1500.0,
        "dateCreated": "2025-05-21T12:00:00",
        "lastUpdated": "2025-05-21T12:00:00"
      },
      ...
    ]
  }
  ```

#### Get Division by ID
- **URL**: `/api/divisions/<division_id>`
- **Method**: `GET`
- **Description**: Retrieve a specific division by ID
- **URL Parameters**: `division_id` - ID of the division to retrieve
- **Response**: JSON object containing the division details

#### Add New Division
- **URL**: `/api/divisions`
- **Method**: `POST`
- **Description**: Add a new tournament division
- **Request Body**:
  ```json
  {
    "title": "Intermediate Division",
    "description": "For players with developing skills",
    "minimumRating": 1200,
    "maximumRating": 1799,
    "price": 1000
  }
  ```
- **Required Fields**: `title`, `minimumRating`, `maximumRating`, `price`
- **Response**: JSON object containing the added division details

### Registration Management

#### Get Available Players and Divisions
- **URL**: `/api/purchase-ticket`
- **Method**: `GET`
- **Description**: Retrieve all available players (without existing tickets) and divisions
- **Response**: JSON object containing players and divisions
  ```json
  {
    "players": [
      {
        "playerId": 1,
        "playerName": "John Doe",
        "playerRating": 1650,
        "playerEmail": "john.doe@email.com"
      },
      ...
    ],
    "divisions": [
      {
        "divisionId": 1,
        "title": "Premier Division",
        "minimumRating": 1800,
        "maximumRating": 2500,
        "price": 1500.0
      },
      ...
    ]
  }
  ```

#### Register Players (Initiate M-Pesa Payment)
- **URL**: `/api/make-payment`
- **Method**: `POST`
- **Description**: Register multiple players and initiate M-Pesa payment
- **Request Body**:
  ```json
  {
    "players": [
      {"playerId": 1, "divisionId": 2},
      {"playerId": 3, "divisionId": 1}
    ],
    "customerName": "Tournament Organizer",
    "phoneNumber": "254712345678"
  }
  ```
- **Required Fields**: `players`, `customerName`, `phoneNumber`
- **Response**: JSON object containing payment initiation details
  ```json
  {
    "message": "Payment initiated successfully",
    "totalAmount": 2500.0,
    "playersRegistered": 2,
    "players": ["John Doe", "Jane Smith"],
    "paymentId": 1,
    "ticketIds": [1, 2],
    "checkoutRequestId": "ws_CO_DMZ_12345678901234567",
    "responseDescription": "Success. Request accepted for processing"
  }
  ```

#### Query Payment Status
- **URL**: `/api/query-payment-status`
- **Method**: `POST`
- **Description**: Query the status of an M-Pesa STK push transaction
- **Request Body**:
  ```json
  {
    "checkoutRequestId": "ws_CO_DMZ_12345678901234567"
  }
  ```
- **Required Fields**: `checkoutRequestId`
- **Response**: JSON object containing the payment status

#### M-Pesa Callback
- **URL**: `/api/mpesa-callback`
- **Method**: `POST`
- **Description**: Callback endpoint for M-Pesa payment notifications
- **Notes**:
  - This endpoint is called by Safaricom's M-Pesa API
  - Should be exposed via a publicly accessible URL
  - Updates payment status and triggers email confirmations

#### Get Ticket Details
- **URL**: `/api/tickets/<ticket_id>`
- **Method**: `GET`
- **Description**: Retrieve details of a specific ticket
- **Response**: JSON object containing ticket details including player and payment information

#### Get Payment Details
- **URL**: `/api/payments/<payment_id>`
- **Method**: `GET`
- **Description**: Retrieve details of a specific payment including associated tickets
- **Response**: JSON object containing payment details and associated tickets

## Email Functionality

The system includes automated email confirmations sent to players after successful payment:

### Email Features:
- **Professional HTML Templates**: Responsive, branded email design
- **Comprehensive Information**: Ticket details, payment confirmation, tournament instructions
- **Asynchronous Sending**: Emails sent in background threads
- **Smart Handling**: Only sent to players with email addresses
- **Error Handling**: Graceful handling of email sending failures

### Email Configuration:
```python
# In config.py
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
MAIL_DEFAULT_SENDER = 'your-email@gmail.com'
```

### Email Template Location:
Place `ticket_confirmation.html` in the `templates/` directory.

## Registration Flow

The system implements a comprehensive registration flow:

1. **Player Selection**:
   - Display available players and divisions
   - Show rating-based eligibility
   - Allow multiple player selection

2. **Division Matching**:
   - Validate player ratings against division requirements
   - Prevent duplicate registrations
   - Calculate total costs

3. **Payment Initiation**:
   - Create payment and ticket records
   - Send STK Push request to Safaricom
   - User receives M-Pesa prompt

4. **Payment Processing**:
   - User enters PIN on their phone
   - Safaricom processes the payment

5. **Confirmation**:
   - System receives payment callback
   - Updates payment status
   - Sends email confirmations to players
   - Provides confirmation to organizer

## Tournament Management Features

### Division Management:
- **Rating Bands**: Divisions with minimum and maximum rating requirements
- **Flexible Pricing**: Different prices for different divisions
- **Eligibility Checking**: Automatic validation of player eligibility

### Player Management:
- **Rating System**: Players have tournament ratings
- **Email Integration**: Optional email addresses for confirmations
- **One Registration Per Player**: Prevents duplicate registrations

### Payment Management:
- **Multi-Player Payments**: Single payment can cover multiple players
- **Receipt Tracking**: M-Pesa receipt numbers stored
- **Status Monitoring**: Real-time payment status tracking

## Error Handling

The API implements comprehensive error handling, including:

- Missing required fields
- Invalid player or division IDs
- Rating eligibility violations
- Duplicate player registrations
- Failed M-Pesa API calls
- Email sending failures
- Invalid callback data

All error responses include appropriate HTTP status codes and descriptive error messages.

## Configuration Requirements

### M-Pesa Configuration:
- `MPESA_BASE_URL`: Safaricom API base URL
- `MPESA_CONSUMER_KEY`: Your M-Pesa API consumer key
- `MPESA_CONSUMER_SECRET`: Your M-Pesa API consumer secret
- `MPESA_BUSINESS_SHORT_CODE`: Your business short code
- `MPESA_PASSKEY`: Your M-Pesa passkey
- `MPESA_CALLBACK_URL`: Your callback URL (publicly accessible)

### Email Configuration:
- `MAIL_SERVER`: SMTP server (e.g., smtp.gmail.com)
- `MAIL_USERNAME`: Email account username
- `MAIL_PASSWORD`: Email account password (use App Password for Gmail)
- `MAIL_DEFAULT_SENDER`: Default sender email address

## Security Considerations

For production deployment:

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **HTTPS**: Ensure all endpoints are served over HTTPS
3. **Input Validation**: Comprehensive input validation and sanitization
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Authentication**: Add admin authentication for management endpoints
6. **Audit Logging**: Detailed logging for all transactions
7. **Email Security**: Use App Passwords and 2FA for email accounts

## Extending the System

The system can be extended with:

1. **Admin Dashboard**: Web interface for tournament management
2. **Player Portal**: Player registration and profile management
3. **Tournament Scheduling**: Schedule and bracket management
4. **Reporting**: Financial and registration reports
5. **Multiple Tournaments**: Support for multiple concurrent tournaments
6. **SMS Notifications**: Additional notification channels
7. **Check-in System**: Tournament day check-in functionality

## Troubleshooting

### Common Issues

1. **M-Pesa Integration**:
   - Verify credentials and callback URL accessibility
   - Check phone number format (254XXXXXXXXX)
   - Ensure business short code is correctly configured

2. **Email Issues**:
   - Verify SMTP credentials
   - Use App Passwords for Gmail
   - Check spam folders for test emails

3. **Rating Validation**:
   - Ensure player ratings are within division ranges
   - Check for data type consistency

4. **Database Issues**:
   - Verify foreign key relationships
   - Check for unique constraint violations

### Debugging

Enable debug mode for development and implement proper logging for production. Monitor email sending status and M-Pesa callback responses for troubleshooting.

## File Structure

```
tournament-registration-system/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── templates/
│   ├── index.html                  # Main registration interface
│   └── ticket_confirmation.html    # Email template
├── static/                         # Static files (CSS, JS, images)
└── README.md                      # This documentation
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support, feature requests, or bug reports:
- Email: jisortublow@gmail.com
- Create an issue on the GitHub repository

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Scrabble Kenya community for requirements and feedback
- Safaricom for M-Pesa API integration
- Flask community for the excellent framework

---

**Scrabble Kenya Tournament Registration System** - Streamlining tournament registration with modern payment solutions and professional communication.
