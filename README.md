<img src="https://github.com/user-attachments/assets/8cc3904f-582e-4177-8205-e78ccea0500a" alt="Alt Text" width="180" height="180"></img>
# Movie Ticket System API Documentation (Flask Version)

## Introduction

The Movie Ticket System is a Flask-based backend application that enables users to browse movies, purchase tickets, and process payments via M-Pesa. This system is designed to provide a seamless ticket purchasing experience for movie theaters, event organizers, and similar businesses.

This API handles the complete workflow from movie listing to payment processing and ticket generation. With integrated M-Pesa payment functionality, it's specifically tailored for the Kenyan market, but can be adapted for other mobile payment systems.

Key features include:
- Movie management (add, retrieve)
- Ticket purchasing
- M-Pesa payment integration with STK Push
- Payment status tracking
- Ticket availability management

## Getting Started

### Prerequisites

- Python 3.6+
- Flask and Flask-SQLAlchemy
- Requests library
- SQLite (for development) or another database of your choice
- M-Pesa developer account (for Safaricom API access)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/barasamichael/mpesa_movie_system_python_flask.git
   cd mpesa_movie_system_python_flask
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install flask flask-sqlalchemy requests
   ```

4. Configure the application:
   - Update the M-Pesa configuration in the `app.py` file with your Safaricom credentials
   - Update the `MPESA_CALLBACK_URL` to your actual callback URL

5. Run the application:
   ```bash
   python app.py
   ```

The server will start at `http://localhost:5000` or `http:127.0.0.1:5000`.

## Database Schema

The system uses three main models:

### Movie
- `movieId`: Primary key (integer)
- `title`: Movie title (string, required)
- `description`: Movie description (text)
- `showTime`: Date and time of the movie (datetime, required)
- `price`: Ticket price (decimal, required)
- `maximumTickets`: Maximum number of available tickets (integer, default: 100)
- `imageUrl`: URL to the movie poster image (string)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

### Ticket
- `ticketId`: Primary key (integer)
- `movieId`: Foreign key to Movie (integer, required)
- `customerName`: Name of the customer (string, required)
- `phoneNumber`: Customer phone number (string, required)
- `quantity`: Number of tickets purchased (integer, required)
- `totalAmount`: Total amount paid (decimal, required)
- `paymentStatus`: Status of payment ('Pending', 'Paid', 'Failed')
- `mpesaReceiptNumber`: M-Pesa receipt number (string)
- `transactionDate`: Date and time of the transaction (datetime)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

### PushRequest
- `pushRequestId`: Primary key (integer)
- `ticketId`: Foreign key to Ticket (integer, required)
- `checkoutRequestId`: M-Pesa checkout request ID (string, required)
- `dateCreated`: Record creation timestamp (datetime)
- `lastUpdated`: Record last updated timestamp (datetime)

## API Endpoints

### Root Endpoint
- **URL**: `/`
- **Method**: `GET`
- **Description**: Display page
- **Response**: The Flask Response Object
### Movie Management

#### Get All Movies
- **URL**: `/api/movies`
- **Method**: `GET`
- **Description**: Retrieve all movies
- **Response**: JSON object containing an array of movies
  ```json
  {
    "movies": [
      {
        "movieId": 1,
        "title": "The Matrix",
        "description": "A computer hacker learns about the true nature of reality",
        "showTime": "2025-06-15T18:30:00",
        "price": 500.0,
        "maximumTickets": 200,
        "imageUrl": "https://example.com/matrix.jpg",
        "dateCreated": "2025-05-21T12:00:00",
        "lastUpdated": "2025-05-21T12:00:00"
      },
      ...
    ]
  }
  ```

#### Get Movie by ID
- **URL**: `/api/movies/<movie_id>`
- **Method**: `GET`
- **Description**: Retrieve a specific movie by ID
- **URL Parameters**: `movie_id` - ID of the movie to retrieve
- **Response**: JSON object containing the movie details
  ```json
  {
    "movie": {
      "movieId": 1,
      "title": "The Matrix",
      "description": "A computer hacker learns about the true nature of reality",
      "showTime": "2025-06-15T18:30:00",
      "price": 500.0,
      "maximumTickets": 200,
      "imageUrl": "https://example.com/matrix.jpg",
      "dateCreated": "2025-05-21T12:00:00",
      "lastUpdated": "2025-05-21T12:00:00"
    }
  }
  ```

#### Add New Movie
- **URL**: `/api/movies`
- **Method**: `POST`
- **Description**: Add a new movie
- **Request Body**:
  ```json
  {
    "title": "The Matrix Resurrections",
    "description": "The fourth installment in The Matrix franchise",
    "showTime": "2025-07-15T20:00:00",
    "price": 600,
    "maximumTickets": 150,
    "imageUrl": "https://example.com/matrix4.jpg"
  }
  ```
- **Required Fields**: `title`, `showTime`, `price`
- **Response**: JSON object containing the added movie details
  ```json
  {
    "message": "Movie added successfully",
    "movie": {
      "movieId": 2,
      "title": "The Matrix Resurrections",
      "description": "The fourth installment in The Matrix franchise",
      "showTime": "2025-07-15T20:00:00",
      "price": 600.0,
      "maximumTickets": 150,
      "imageUrl": "https://example.com/matrix4.jpg",
      "dateCreated": "2025-05-21T14:30:00",
      "lastUpdated": "2025-05-21T14:30:00"
    }
  }
  ```

### Ticket Management

#### Purchase Ticket (Get Available Movies)
- **URL**: `/api/purchase-ticket`
- **Method**: `GET`
- **Description**: Retrieve all movies for ticket purchase
- **Response**: Same as `GET /api/movies`

#### Make Payment (Initiate M-Pesa STK Push)
- **URL**: `/api/make-payment`
- **Method**: `POST`
- **Description**: Initiate an M-Pesa payment for ticket purchase
- **Request Body**:
  ```json
  {
    "movieId": 1,
    "customerName": "John Doe",
    "phoneNumber": "254712345678",
    "quantity": 2
  }
  ```
- **Required Fields**: `movieId`, `customerName`, `phoneNumber`, `quantity`
- **Response**: JSON object containing payment initiation details
  ```json
  {
    "message": "Payment initiated successfully",
    "ticketId": 1,
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
  ```json
  {
    "ResponseCode": "0",
    "ResponseDescription": "The service request has been accepted successfully",
    "MerchantRequestID": "12345-67890-1",
    "CheckoutRequestID": "ws_CO_DMZ_12345678901234567",
    "ResultCode": "0",
    "ResultDesc": "The service request is processed successfully"
  }
  ```

#### M-Pesa Callback
- **URL**: `/api/mpesa-callback`
- **Method**: `POST`
- **Description**: Callback endpoint for M-Pesa payment notifications
- **Notes**: 
  - This endpoint is called by Safaricom's M-Pesa API
  - Should be exposed via a publicly accessible URL
  - Updates ticket status based on payment result

#### Get Ticket Details
- **URL**: `/api/tickets/<ticket_id>`
- **Method**: `GET`
- **Description**: Retrieve details of a specific ticket
- **URL Parameters**: `ticket_id` - ID of the ticket to retrieve
- **Response**: JSON object containing ticket details including movie information
  ```json
  {
    "ticket": {
      "ticketId": 1,
      "movieId": 1,
      "customerName": "John Doe",
      "phoneNumber": "254712345678",
      "quantity": 2,
      "totalAmount": 1000.0,
      "paymentStatus": "Paid",
      "mpesaReceiptNumber": "PBH234TYGD",
      "transactionDate": "2025-05-21T15:30:45",
      "dateCreated": "2025-05-21T15:25:10",
      "lastUpdated": "2025-05-21T15:30:50",
      "movie": {
        "movieId": 1,
        "title": "The Matrix",
        "description": "A computer hacker learns about the true nature of reality",
        "showTime": "2025-06-15T18:30:00",
        "price": 500.0,
        "maximumTickets": 200,
        "imageUrl": "https://example.com/matrix.jpg",
        "dateCreated": "2025-05-21T12:00:00",
        "lastUpdated": "2025-05-21T12:00:00"
      }
    }
  }
  ```

## Payment Flow

The system implements M-Pesa's STK Push functionality with the following flow:

1. **Ticket Creation**:
   - User selects a movie and provides details (name, phone number, ticket quantity)
   - System creates a ticket record with 'Pending' status

2. **Payment Initiation**:
   - System calculates the total amount
   - System formats the phone number for M-Pesa
   - System sends an STK Push request to Safaricom

3. **STK Push Request**:
   - System calls Safaricom's STK Push API
   - User receives a prompt on their phone to enter M-Pesa PIN

4. **Payment Processing**:
   - User enters PIN on their phone
   - Safaricom processes the payment

5. **Payment Callback**:
   - Safaricom sends a callback to the system
   - System updates the ticket status based on payment result

6. **Ticket Confirmation**:
   - System provides ticket details to the user if payment is successful

## Error Handling

The API implements comprehensive error handling, including:

- Missing required fields
- Invalid movie ID
- Insufficient available tickets
- Failed M-Pesa API calls
- Invalid callback data

All error responses include an appropriate HTTP status code and an error message.

## M-Pesa Configuration

The system requires the following M-Pesa configuration:

- `MPESA_BASE_URL`: Safaricom API base URL (sandbox or production)
- `MPESA_CONSUMER_KEY`: Your M-Pesa API consumer key
- `MPESA_CONSUMER_SECRET`: Your M-Pesa API consumer secret
- `MPESA_BUSINESS_SHORT_CODE`: Your business short code or paybill number
- `MPESA_PASSKEY`: Your M-Pesa passkey
- `MPESA_CALLBACK_URL`: Your callback URL (must be publicly accessible)

## Security Considerations

For production deployment, consider implementing:

1. **Authentication**: Add JWT or API key authentication for secure API access
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **HTTPS**: Ensure all endpoints are served over HTTPS
4. **Input Validation**: Add more comprehensive input validation
5. **Logs**: Implement detailed logging for audit trails
6. **Environment Variables**: Move sensitive configuration to environment variables

## Extending the System

The system can be extended in several ways:

1. **User Authentication**: Add user registration and login functionality
2. **Admin Dashboard**: Create an admin interface for movie management
3. **Email Notifications**: Send email confirmations for ticket purchases
4. **Multiple Payment Methods**: Integrate additional payment gateways
5. **Seat Selection**: Add seat reservation functionality
6. **Analytics**: Implement reporting and analytics features

## Troubleshooting

### Common Issues

1. **M-Pesa Connection Issues**:
   - Ensure your M-Pesa credentials are correct
   - Verify that your callback URL is publicly accessible
   - Check that your phone number format is correct (254XXXXXXXXX)

2. **Database Issues**:
   - Verify that the database file is writable
   - Check for database migration issues when updating

3. **Callback Not Received**:
   - Ensure your server is publicly accessible
   - Check Safaricom's callback timeout settings
   - Implement callback logging for debugging

### Debugging

The application runs in debug mode by default, which provides detailed error messages. For production, disable debug mode and implement proper logging.

## Conclusion

The Movie Ticket System provides a robust backend for movie ticket sales with M-Pesa integration. By following this documentation, you can set up, customize, and extend the system to meet your specific requirements.

For further assistance or to report issues, please contact Barasa Michael Murunga: jisortublow@gmail.com.
