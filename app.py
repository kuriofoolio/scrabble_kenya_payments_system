import os
import base64
import requests
from flask import Flask
from flask import jsonify
from flask import request
from flask import current_app
from datetime import datetime
from sqlalchemy.sql import func
from flask import render_template
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie_tickets.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "VvgAKAKEihS5CIbNfUrrxIBbbiTstpZe1y1IrVwU8WTmMuCv5Z"

# M-Pesa Configuration
app.config["MPESA_BASE_URL"] = "https://sandbox.safaricom.co.ke"
app.config[
    "MPESA_ACCESS_TOKEN_URL"
] = "oauth/v1/generate?grant_type=client_credentials"
app.config["MPESA_STK_PUSH_URL"] = "mpesa/stkpush/v1/processrequest"
app.config["MPESA_STK_QUERY_URL"] = "mpesa/stkpushquery/v1/query"
app.config["MPESA_BUSINESS_SHORT_CODE"] = "174379"
app.config[
    "MPESA_PASSKEY"
] = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
app.config["MPESA_TILL_NUMBER"] = "174379"
app.config["MPESA_CALLBACK_URL"] = "https://13a6-169-150-218-3.ngrok-free.app/callback"
app.config[
    "MPESA_CONSUMER_KEY"
] = "E7RkuNKKVFG3p2nWjEM78RcbFOwH2qb5UHpGvpOhzodFGbHV"
app.config[
    "MPESA_CONSUMER_SECRET"
] = "tQw44mUODFBqUk25oS5NweJBMrlvdWwkYdap6P3895kekW2LmLFcHT4Lvjr4figm"

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models


class Movie(db.Model):
    """
    Movie model representing movies available for booking
    """

    __tablename__ = "movie"

    movieId = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    showTime = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    # Maximum tickets available
    maximumTickets = db.Column(db.Integer, nullable=False, default=100)
    imageUrl = db.Column(db.String(255))  # URL to the movie image
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Ticket model
    tickets = db.relationship(
        "Ticket", back_populates="movie", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert movie object to dictionary"""
        return {
            "movieId": self.movieId,
            "title": self.title,
            "description": self.description,
            "showTime": self.showTime.isoformat() if self.showTime else None,
            "price": float(self.price),
            "maximumTickets": self.maximumTickets,
            "imageUrl": self.imageUrl,
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }


class Ticket(db.Model):
    """
    Ticket model representing purchased tickets
    """

    __tablename__ = "ticket"

    ticketId = db.Column(db.Integer, primary_key=True)
    movieId = db.Column(
        db.Integer,
        db.ForeignKey("movie.movieId", ondelete="CASCADE"),
        nullable=False,
    )
    customerName = db.Column(db.String(255), nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    totalAmount = db.Column(db.Numeric(10, 2), nullable=False)
    paymentStatus = db.Column(
        db.Enum("Pending", "Paid", "Failed"), default="Pending", nullable=False
    )
    mpesaReceiptNumber = db.Column(db.String(100))
    transactionDate = db.Column(db.DateTime)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Movie model
    movie = db.relationship("Movie", back_populates="tickets")

    # Relationship with PushRequest model
    push_requests = db.relationship(
        "PushRequest", back_populates="ticket", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert ticket object to dictionary"""
        return {
            "ticketId": self.ticketId,
            "movieId": self.movieId,
            "customerName": self.customerName,
            "phoneNumber": self.phoneNumber,
            "quantity": self.quantity,
            "totalAmount": float(self.totalAmount),
            "paymentStatus": self.paymentStatus,
            "mpesaReceiptNumber": self.mpesaReceiptNumber,
            "transactionDate": self.transactionDate.isoformat()
            if self.transactionDate
            else None,
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }


class PushRequest(db.Model):
    """
    PushRequest model for tracking M-Pesa STK push requests
    """

    __tablename__ = "pushrequest"

    pushRequestId = db.Column(db.Integer, primary_key=True)
    ticketId = db.Column(
        db.Integer,
        db.ForeignKey("ticket.ticketId", ondelete="CASCADE"),
        nullable=False,
    )
    checkoutRequestId = db.Column(db.String(255), nullable=False)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Ticket model
    ticket = db.relationship("Ticket", back_populates="push_requests")

    def to_dict(self):
        """Convert push request object to dictionary"""
        return {
            "pushRequestId": self.pushRequestId,
            "ticketId": self.ticketId,
            "checkoutRequestId": self.checkoutRequestId,
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }


# Helper functions for M-Pesa integration
def get_access_token():
    """
    Gets an access token from the Safaricom M-Pesa API

    Returns:
        str: Access token if successful, None otherwise
    """
    url = os.path.join(
        current_app.config["MPESA_BASE_URL"],
        current_app.config["MPESA_ACCESS_TOKEN_URL"],
    )
    headers = {"Content-Type": "application/json"}
    auth = (
        current_app.config["MPESA_CONSUMER_KEY"],
        current_app.config["MPESA_CONSUMER_SECRET"],
    )

    try:
        response = requests.get(url, headers=headers, auth=auth)
        response.raise_for_status()
        result = response.json()
        return result.get("access_token")

    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {str(e)}")
        return None


def format_phone_number(phone_number):
    """
    Formats a phone number to the required format for M-Pesa API (2547XXXXXXXX)

    Args:
        phone_number (str): Phone number to format

    Returns:
        str: Formatted phone number
    """
    # Remove any non-digit characters
    phone_number = "".join(filter(str.isdigit, phone_number))

    # Check if the number starts with '0' and replace with '254'
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]

    # Check if the number starts with '+254' and remove the '+'
    elif phone_number.startswith("+254"):
        phone_number = phone_number[1:]

    # Check if the number doesn't have the country code and add it
    elif not phone_number.startswith("254"):
        phone_number = "254" + phone_number

    return phone_number


# Routes
@app.route("/")
def index():
    """Root endpoint"""
    return render_template("index.html")


@app.route("/api/movies", methods=["GET"])
def get_movies():
    """
    Endpoint to get all movies

    Returns:
        JSON: List of movies
    """
    movies = Movie.query.all()
    return jsonify({"movies": [movie.to_dict() for movie in movies]})


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    """
    Endpoint to get a specific movie by ID

    Args:
        movie_id (int): Movie ID

    Returns:
        JSON: Movie details or error
    """
    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    return jsonify({"movie": movie.to_dict()})


@app.route("/api/movies", methods=["POST"])
def add_movie():
    """
    Endpoint to add a new movie

    Expected JSON payload:
    {
        "title": "Movie Title",
        "description": "Movie Description",
        "showTime": "2025-06-01T18:00:00",
        "price": 500,
        "maximumTickets": 200,
        "imageUrl": "https://example.com/image.jpg"
    }

    Returns:
        JSON: Added movie details or error
    """
    data = request.get_json()

    try:
        # Validate required fields
        required_fields = ["title", "showTime", "price"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}"}),
                    400,
                )

        # Create new movie
        new_movie = Movie(
            title=data["title"],
            description=data.get("description"),
            showTime=datetime.fromisoformat(data["showTime"]),
            price=data["price"],
            maximumTickets=data.get("maximumTickets", 100),
            imageUrl=data.get("imageUrl"),
        )

        db.session.add(new_movie)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Movie added successfully",
                    "movie": new_movie.to_dict(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/purchase-ticket", methods=["GET"])
def purchase_ticket():
    """
    Endpoint to get all movies for ticket purchase

    Returns:
        JSON: List of all movies
    """
    movies = Movie.query.all()
    return jsonify({"movies": [movie.to_dict() for movie in movies]})


@app.route("/api/make-payment", methods=["POST"])
def make_payment():
    """
    Endpoint to initiate M-Pesa payment

    Expected JSON payload:
    {
        "movieId": 1,
        "customerName": "John Doe",
        "phoneNumber": "254712345678",
        "quantity": 2
    }

    Returns:
        JSON: Payment initiation results or error
    """
    data = request.get_json()

    try:
        # Validate required fields
        required_fields = ["movieId", "customerName", "phoneNumber", "quantity"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}"}),
                    400,
                )

        # Get the movie
        movie = Movie.query.get(data["movieId"])
        if not movie:
            return jsonify({"error": "Movie not found"}), 404

        quantity = int(data["quantity"])

        # Check if enough tickets are available
        tickets_sold = (
            db.session.query(db.func.sum(Ticket.quantity))
            .filter(
                Ticket.movieId == movie.movieId, Ticket.paymentStatus == "Paid"
            )
            .scalar()
            or 0
        )

        if tickets_sold + quantity > movie.maximumTickets:
            return (
                jsonify(
                    {
                        "error": f"Not enough tickets available. Only {movie.maximumTickets - tickets_sold} left."
                    }
                ),
                400,
            )

        # Calculate total amount
        total_amount = float(movie.price) * quantity

        # Format phone number
        formatted_phone = format_phone_number(data["phoneNumber"])

        # Create a new ticket record with pending status
        new_ticket = Ticket(
            movieId=movie.movieId,
            customerName=data["customerName"],
            phoneNumber=formatted_phone,
            quantity=quantity,
            totalAmount=total_amount,
            paymentStatus="Pending",
        )

        db.session.add(new_ticket)
        db.session.flush()  # Get the ID without committing

        # Get access token for M-Pesa API
        access_token = get_access_token()
        if not access_token:
            db.session.rollback()
            return jsonify({"error": "Failed to get M-Pesa access token"}), 500

        # Prepare STK push request
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            (
                current_app.config["MPESA_BUSINESS_SHORT_CODE"]
                + current_app.config["MPESA_PASSKEY"]
                + timestamp
            ).encode()
        ).decode()

        stk_push_url = os.path.join(
            current_app.config["MPESA_BASE_URL"],
            current_app.config["MPESA_STK_PUSH_URL"],
        )
        print(f"This is the STK PUSH URL to Safaricom: {stk_push_url}")

        stk_push_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        stk_push_payload = {
            "BusinessShortCode": current_app.config[
                "MPESA_BUSINESS_SHORT_CODE"
            ],
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerBuyGoodsOnline",
            "Amount": int(total_amount),  # Amount must be an integer
            "PartyA": formatted_phone,
            "PartyB": current_app.config["MPESA_TILL_NUMBER"],
            "PhoneNumber": formatted_phone,
            "CallBackURL": current_app.config["MPESA_CALLBACK_URL"],
            "AccountReference": f"Movie Ticket",
            "TransactionDesc": "Movie Tckt",
        }

        # Send STK push request
        response = requests.post(
            stk_push_url, headers=stk_push_headers, json=stk_push_payload
        )

        mpesa_response = response.json()
        print(mpesa_response)

        # Check if STK push was successful
        if (
            "ResponseCode" in mpesa_response
            and mpesa_response["ResponseCode"] == "0"
        ):
            # Create PushRequest record
            checkout_request_id = mpesa_response.get("CheckoutRequestID")
            push_request = PushRequest(
                ticketId=new_ticket.ticketId,
                checkoutRequestId=checkout_request_id,
            )

            db.session.add(push_request)
            db.session.commit()

            return jsonify(
                {
                    "message": "Payment initiated successfully",
                    "ticketId": new_ticket.ticketId,
                    "checkoutRequestId": checkout_request_id,
                    "responseDescription": mpesa_response.get(
                        "ResponseDescription", ""
                    ),
                }
            )

        else:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "error": "Failed to initiate payment",
                        "mpesaResponse": mpesa_response,
                    }
                ),
                500,
            )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/query-payment-status", methods=["POST"])
def perform_stk_query():
    """
    Endpoint to query the status of an STK push transaction

    Expected JSON payload:
    {
        "checkoutRequestId": "ws_CO_DMZ_12345678901234567"
    }

    Returns:
        JSON: STK query result or error
    """
    data = request.get_json()
    checkout_request_id = data.get("checkoutRequestId")

    if not checkout_request_id:
        return jsonify({"error": "Checkout Request ID not provided"}), 400

    try:
        # Get access token for M-Pesa API
        access_token = get_access_token()
        if not access_token:
            return jsonify({"error": "Failed to get M-Pesa access token"}), 500

        # Prepare STK query request
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            (
                current_app.config["MPESA_BUSINESS_SHORT_CODE"]
                + current_app.config["MPESA_PASSKEY"]
                + timestamp
            ).encode()
        ).decode()

        query_url = os.path.join(
            current_app.config["MPESA_BASE_URL"],
            current_app.config["MPESA_STK_QUERY_URL"],
        )

        query_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        query_payload = {
            "BusinessShortCode": current_app.config[
                "MPESA_BUSINESS_SHORT_CODE"
            ],
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id,
        }

        # Send STK query request
        response = requests.post(
            query_url, headers=query_headers, json=query_payload
        )

        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/mpesa-callback", methods=["POST"])
def callback_function():
    """
    Callback endpoint for M-Pesa payment notifications

    Expected payload from M-Pesa API after payment

    Returns:
        JSON: Acknowledgement message
    """
    try:
        response = request.get_json()
        print("This is a response from Safaricom on our callback url")
        print("Wow it worked. We are happy!")
        print(response)

        callback_data = response.get("Body", {}).get("stkCallback", {})

        # Check if callback data exists
        if not callback_data:
            return jsonify({"error": "Invalid callback data"}), 400

        # Get result code and checkout request ID
        result_code = callback_data.get("ResultCode")
        checkout_request_id = callback_data.get("CheckoutRequestID")

        # Find the associated push request
        push_request = PushRequest.query.filter_by(
            checkoutRequestId=checkout_request_id
        ).first()

        if not push_request:
            return jsonify({"error": "No matching push request found"}), 404

        # Get the associated ticket
        ticket = Ticket.query.get(push_request.ticketId)

        if not ticket:
            return jsonify({"error": "No matching ticket found"}), 404

        # Process successful payment
        if result_code == 0:
            # Extract payment details
            callback_metadata = callback_data.get("CallbackMetadata", {}).get(
                "Item", []
            )

            # Extract amount, receipt number, and transaction date
            next(
                (
                    item.get("Value")
                    for item in callback_metadata
                    if item.get("Name") == "Amount"
                ),
                None,
            )

            receipt_number = next(
                (
                    item.get("Value")
                    for item in callback_metadata
                    if item.get("Name") == "MpesaReceiptNumber"
                ),
                None,
            )

            transaction_date_str = next(
                (
                    item.get("Value")
                    for item in callback_metadata
                    if item.get("Name") == "TransactionDate"
                ),
                None,
            )

            # Convert transaction date string to datetime
            transaction_date = None
            if transaction_date_str:
                try:
                    # Format from Safaricom is typically YYYYMMDDHHmmss
                    transaction_date = datetime.strptime(
                        str(transaction_date_str), "%Y%m%d%H%M%S"
                    )
                except ValueError:
                    # If that fails, store as string
                    transaction_date = datetime.now()

            # Update ticket with payment details
            ticket.paymentStatus = "Paid"
            ticket.mpesaReceiptNumber = receipt_number
            ticket.transactionDate = transaction_date

            db.session.commit()

            return jsonify({"message": "Payment completed successfully"})

        # Process failed payment
        else:
            # Update ticket status to Failed
            ticket.paymentStatus = "Failed"
            db.session.commit()

            return jsonify(
                {"message": "Payment failed", "result_code": result_code}
            )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """
    Endpoint to get details of a specific ticket

    Args:
        ticket_id (int): Ticket ID

    Returns:
        JSON: Ticket details including movie information
    """
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    # Get the associated movie
    movie = Movie.query.get(ticket.movieId)

    if not movie:
        return jsonify({"error": "Associated movie not found"}), 404

    # Combine ticket and movie information
    ticket_data = ticket.to_dict()
    ticket_data["movie"] = movie.to_dict()

    return jsonify({"ticket": ticket_data})


if __name__ == "__main__":
    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()

    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)
