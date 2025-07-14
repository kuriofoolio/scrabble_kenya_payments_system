import os
import base64
import requests
from flask import Flask
from flask import jsonify
from flask import request
from flask import current_app
from datetime import datetime, timezone, timedelta
from sqlalchemy.sql import func
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from flask_mailman import EmailMultiAlternatives
from config import *
from flask import redirect, url_for
from functools import wraps


# Initialize Flask app
app = Flask("Scrabble Kenya Payments System")

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["FLASK_SECRET_KEY"] = FLASK_SECRET_KEY

# M-Pesa Configuration
app.config["MPESA_BASE_URL"] = MPESA_BASE_URL
app.config["MPESA_ACCESS_TOKEN_URL"] = MPESA_ACCESS_TOKEN_URL
app.config["MPESA_STK_PUSH_URL"] = MPESA_STK_PUSH_URL
app.config["MPESA_STK_QUERY_URL"] = MPESA_STK_QUERY_URL
app.config["MPESA_BUSINESS_SHORT_CODE"] = "174379"
app.config["MPESA_PASSKEY"] = MPESA_PASSKEY
app.config["MPESA_TILL_NUMBER"] = "8976288"
app.config["MPESA_CALLBACK_URL"] = MPESA_CALLBACK_URL
app.config[
    "MPESA_CONSUMER_KEY"
] = "E7RkuNKKVFG3p2nWjEM78RcbFOwH2qb5UHpGvpOhzodFGbHV"
app.config[
    "MPESA_CONSUMER_SECRET"
] = "tQw44mUODFBqUk25oS5NweJBMrlvdWwkYdap6P3895kekW2LmLFcHT4Lvjr4figm"

# Initialize SQLAlchemy
db = SQLAlchemy(app)


# Email sending functions
def send_async_email(app, message):
    """
    Asynchronously sends an email using Flask-Mailman within the given Flask
        app context.

    Parameters:
        - app: Flask app object
        - msg: Message object containing email details
    """
    with app.app_context():
        message.send()


def send_email(to, subject, template, cc=None, bcc=None, **kwargs):
    """
    Asynchronously send an email using Flask-Mailman with support for HTML templates only.

    Parameters:
        - to: Email recipient(s) (string or list of strings)
        - subject: Email subject
        - template: Base name of the email template (without the file extension)
        - cc: Carbon copy recipients (optional, string or list of strings)
        - bcc: Blind carbon copy recipients (optional, string or list of strings)
        - **kwargs: Additional keyword arguments to pass to the email template

    Returns:
        - Thread object representing the asynchronous email sending process
    """
    app = current_app._get_current_object()
    rendered_html = render_template(template + ".html", **kwargs)

    # Create the EmailMultiAlternatives message
    message = EmailMultiAlternatives(subject=subject, body=rendered_html, to=to)

    # Attach HTML version of the email
    message.attach_alternative(rendered_html, "text/html")

    # Add CC and BCC if provided
    if cc:
        if isinstance(cc, str):
            cc = [cc]
        message.cc = cc

    if bcc:
        if isinstance(bcc, str):
            bcc = [bcc]
        message.bcc = bcc

    # Send the email asynchronously
    thread = Thread(target=send_async_email, args=[app, message])
    thread.start()
    return thread


def send_ticket_confirmation_emails(payment_id):
    """
    Send ticket confirmation emails to all players associated with a payment
    
    Parameters:
        - payment_id: ID of the payment record
    """
    try:
        # Get payment details
        payment = Payment.query.get(payment_id)
        if not payment:
            print(f"Payment {payment_id} not found")
            return

        # Get all tickets for this payment
        tickets = Ticket.query.filter_by(paymentId=payment_id).all()
        
        for ticket in tickets:
            player = ticket.player
            division = ticket.division
            
            # Only send email if player has an email address
            if player and player.playerEmail:
                try:
                    send_email(
                        to=[player.playerEmail],
                        subject=f"Tournament Registration Confirmation - {division.title}",
                        template="ticket_confirmation",
                        player=player,
                        division=division,
                        ticket=ticket,
                        payment=payment
                    )
                    print(f"Ticket confirmation email sent to {player.playerEmail}")
                except Exception as e:
                    print(f"Failed to send email to {player.playerEmail}: {str(e)}")
            else:
                print(f"No email address for player {player.playerName if player else 'Unknown'}")
                
    except Exception as e:
        print(f"Error sending ticket confirmation emails: {str(e)}")


# Models
class Division(db.Model):
    """
    Division model representing divisions available to play in
    """

    __tablename__ = "division"

    divisionId = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    minRating = db.Column(db.Integer)
    maxRating = db.Column(db.Integer)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Ticket model
    tickets = db.relationship(
        "Ticket", back_populates="division", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert division object to dictionary"""
        return {
            "divisionId": self.divisionId,
            "title": self.title,
            "description": self.description,
            "minRating": self.minRating,
            "maxRating": self.maxRating,
            "price": float(self.price),
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }

class Player(db.Model):
    """
    Player model representing players
    """

    __tablename__ = "player"

    playerId = db.Column(db.Integer, primary_key=True)
    playerName = db.Column(db.String(255), nullable=False)
    playerRating = db.Column(db.Integer, nullable=False)
    playerEmail = db.Column(db.String(255))

    # Relationship with Ticket model (one-to-one)
    ticket = db.relationship("Ticket", back_populates="player", uselist=False)

    def to_dict(self):
        """Convert player object to dictionary"""
        return {
            "playerId": self.playerId,
            "playerName": self.playerName,
            "playerRating": self.playerRating,
            "playerEmail": self.playerEmail,
        }


class Payment(db.Model):
    """
    Payment model representing payment transactions
    """

    __tablename__ = "payment"

    paymentId = db.Column(db.Integer, primary_key=True)
    customerName = db.Column(db.String(255), nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
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

    # Relationship with Ticket model
    tickets = db.relationship(
        "Ticket", back_populates="payment", cascade="all, delete-orphan"
    )

    # Relationship with PushRequest model
    push_requests = db.relationship(
        "PushRequest", back_populates="payment", cascade="all, delete-orphan"
    )

    def to_dict(self):
        """Convert payment object to dictionary"""
        return {
            "paymentId": self.paymentId,
            "customerName": self.customerName,
            "phoneNumber": self.phoneNumber,
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


class Ticket(db.Model):
    """
    Ticket model representing purchased tickets
    """

    __tablename__ = "ticket"

    ticketId = db.Column(db.Integer, primary_key=True)
    ticketPrice = db.Column(db.Numeric(10, 2), nullable=False)
    divisionId = db.Column(
        db.Integer,
        db.ForeignKey("division.divisionId", ondelete="CASCADE"),
        nullable=False,
    )
    playerId = db.Column(
        db.Integer,
        db.ForeignKey("player.playerId", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Ensures only one ticket per player
    )
    paymentId = db.Column(
        db.Integer,
        db.ForeignKey("payment.paymentId", ondelete="CASCADE"),
        nullable=False,
    )
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Division model
    division = db.relationship("Division", back_populates="tickets")

    # Relationship with Player model (one-to-one)
    player = db.relationship("Player", back_populates="ticket")

    # Relationship with Payment model
    payment = db.relationship("Payment", back_populates="tickets")

    def to_dict(self):
        """Convert ticket object to dictionary"""
        return {
            "ticketId": self.ticketId,
            "ticketPrice": float(self.ticketPrice),
            "divisionId": self.divisionId,
            "playerId": self.playerId,
            "paymentId": self.paymentId,
            "player": {
                "playerName": self.player.playerName,
                "playerRating": self.player.playerRating,
                "playerEmail": self.player.playerEmail
            } if self.player else None,
            "division": {
                "title": self.division.title,
                "description": self.division.description
            } if self.division else None,
            "payment": self.payment.to_dict() if self.payment else None,
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
    paymentId = db.Column(
        db.Integer,
        db.ForeignKey("payment.paymentId", ondelete="CASCADE"),
        nullable=False,
    )
    checkoutRequestId = db.Column(db.String(255), nullable=False)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Payment model
    payment = db.relationship("Payment", back_populates="push_requests")

    def to_dict(self):
        """Convert push request object to dictionary"""
        return {
            "pushRequestId": self.pushRequestId,
            "paymentId": self.paymentId,
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
# Set your deadline here
KENYA_TZ = timezone(timedelta(hours=3))
DEADLINE = datetime(2025, 8, 1, 23, 59, 59, tzinfo=KENYA_TZ)

def check_deadline():
    """Check if current time is past the deadline"""
    current_time = datetime.now(KENYA_TZ)
    return current_time > DEADLINE

@app.before_request
def before_request():
    """Check deadline before every request"""
    # Skip deadline check for specific routes
    excluded_routes = ['deadline_passed', 'static']
    
    if request.endpoint not in excluded_routes and check_deadline():
        return redirect(url_for('deadline_passed'))

@app.route("/deadline-passed")
def deadline_passed():
    """Page shown when deadline has passed"""
    deadline_formatted = DEADLINE.strftime("%B %d, %Y at %I:%M %p UTC")
    return render_template("deadline_passed.html", deadline=deadline_formatted)

@app.route("/")
# @deadline_required
def index():
    """Root endpoint"""
    return render_template("index.html")

@app.route("/api/check-deadline")
def api_check_deadline():
    """API endpoint to check deadline status"""
    is_past = check_deadline()
    time_remaining = None
    
    if not is_past:
        current_time = datetime.now(KENYA_TZ)
        time_diff = DEADLINE - current_time
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        time_remaining = {
            "days": days,
            "hours": hours,
            "minutes": minutes
        }
    
    return {
        "deadline_passed": is_past,
        "deadline": DEADLINE.isoformat(),
        "current_time": datetime.now(KENYA_TZ).isoformat(),
        "time_remaining": time_remaining
    }


@app.route("/api/divisions", methods=["GET"])
def get_divisions():
    """
    Endpoint to get all divisions

    Returns:
        JSON: List of divisions
    """
    divisions = Division.query.all()
    return jsonify({"divisions": [division.to_dict() for division in divisions]})


@app.route("/api/divisions/<int:division_id>", methods=["GET"])
def get_division(division_id):
    """
    Endpoint to get a specific division by ID

    Args:
        division_id (int): Division ID

    Returns:
        JSON: Division details or error
    """
    division = Division.query.get(division_id)
    if not division:
        return jsonify({"error": "Division not found"}), 404

    return jsonify({"division": division.to_dict()})


@app.route("/api/divisions", methods=["POST"])
def add_division():
    """
    Endpoint to add a new division

    Expected JSON payload:
    {
        "title": "Division Title",
        "description": "Division Description",
        "minRating": 1000,
        "maxRating": 1500,
        "price": 500
    }

    Returns:
        JSON: Added division details or error
    """
    data = request.get_json()

    try:
        # Validate required fields
        required_fields = ["title", "price", "minRating", "maxRating"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}"}),
                    400,
                )

        # Create new division
        new_division = Division(
            title=data["title"],
            description=data.get("description"),
            minRating=data["minRating"],
            maxRating=data["maxRating"],
            price=data["price"],
        )

        db.session.add(new_division)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Division added successfully",
                    "division": new_division.to_dict(),
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
    Endpoint to get all available players and divisions for ticket purchase

    Returns:
        JSON: List of all players and divisions
    """
    # Get players who don't already have tickets (since it's one-to-one)
    players_with_tickets = db.session.query(Ticket.playerId).subquery()
    available_players = Player.query.filter(
        ~Player.playerId.in_(players_with_tickets)
    ).all()
    
    divisions = Division.query.all()
    
    return jsonify({
        "players": [player.to_dict() for player in available_players],
        "divisions": [division.to_dict() for division in divisions]
    })


@app.route("/api/make-payment", methods=["POST"])
def make_payment():
    """
    Endpoint to initiate M-Pesa payment for multiple players

    Expected JSON payload:
    {
        "players": [
            {"playerId": 1, "divisionId": 1},
            {"playerId": 2, "divisionId": 2}
        ],
        "customerName": "John Doe",
        "phoneNumber": "254712345678"
    }

    Returns:
        JSON: Payment initiation results or error
    """
    data = request.get_json()

    try:
        # Validate required fields
        required_fields = ["players", "customerName", "phoneNumber"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}"}),
                    400,
                )

        if not isinstance(data["players"], list) or len(data["players"]) == 0:
            return jsonify({"error": "At least one player must be selected"}), 400

        # Validate and calculate total amount
        total_amount = 0
        player_registrations = []
        registered_players = []

        for player_data in data["players"]:
            if "playerId" not in player_data or "divisionId" not in player_data:
                return jsonify({"error": "Each player must have playerId and divisionId"}), 400

            # Check if player exists
            player = Player.query.get(player_data["playerId"])
            if not player:
                return jsonify({"error": f"Player with ID {player_data['playerId']} not found"}), 404

            # Check if player already has a ticket
            existing_ticket = Ticket.query.filter_by(playerId=player.playerId).first()
            if existing_ticket:
                return jsonify({"error": f"Player {player.playerName} is already registered"}), 400

            # Check if division exists
            division = Division.query.get(player_data["divisionId"])
            if not division:
                return jsonify({"error": f"Division with ID {player_data['divisionId']} not found"}), 404

            # Check if player's rating is within division's rating band
            if not (division.minRating <= player.playerRating <= division.maxRating):
                return jsonify({
                    "error": f"Player {player.playerName} (rating: {player.playerRating}) cannot play in {division.title} "
                           f"(rating range: {division.minRating}-{division.maxRating})"
                }), 400

            # Add to total amount
            total_amount += float(division.price)
            
            # Store for ticket creation
            player_registrations.append({
                "player": player,
                "division": division,
                "playerId": player.playerId,
                "divisionId": division.divisionId
            })
            
            registered_players.append(player.playerName)

        # Format phone number
        formatted_phone = format_phone_number(data["phoneNumber"])

        # Create payment record first
        new_payment = Payment(
            customerName=data["customerName"],
            phoneNumber=formatted_phone,
            totalAmount=total_amount,
            paymentStatus="Pending",
        )
        db.session.add(new_payment)
        db.session.flush()  # Get the payment ID without committing

        # Create ticket records for each player
        new_tickets = []
        for registration in player_registrations:
            new_ticket = Ticket(
                playerId=registration["playerId"],
                divisionId=registration["divisionId"],
                paymentId=new_payment.paymentId,
                ticketPrice=float(registration["division"].price),
            )
            db.session.add(new_ticket)
            new_tickets.append(new_ticket)

        db.session.flush()  # Get the ticket IDs without committing

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

        # Create description of registered players
        players_description = ", ".join(registered_players[:3])  # Limit for description length
        if len(registered_players) > 3:
            players_description += f" and {len(registered_players) - 3} more"

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
            "AccountReference": f"Player Registration",
            "TransactionDesc": f"Registration for {len(registered_players)} player(s)",
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
                paymentId=new_payment.paymentId,
                checkoutRequestId=checkout_request_id,
            )
            db.session.add(push_request)

            db.session.commit()

            return jsonify(
                {
                    "message": "Payment initiated successfully",
                    "totalAmount": total_amount,
                    "playersRegistered": len(registered_players),
                    "players": registered_players,
                    "paymentId": new_payment.paymentId,
                    "ticketIds": [ticket.ticketId for ticket in new_tickets],
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
        print(response.json())

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

        # Get the associated payment
        payment = Payment.query.get(push_request.paymentId)

        if not payment:
            return jsonify({"error": "No matching payment found"}), 404

        # Process successful payment
        if result_code == 0:
            # Extract payment details
            callback_metadata = callback_data.get("CallbackMetadata", {}).get(
                "Item", []
            )

            # Extract amount, receipt number, and transaction date
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

            # Update payment with payment details
            payment.paymentStatus = "Paid"
            payment.mpesaReceiptNumber = receipt_number
            payment.transactionDate = transaction_date

            db.session.commit()

            # Send ticket confirmation emails to all players
            send_ticket_confirmation_emails(payment.paymentId)

            return jsonify({"message": "Payment completed successfully"})

        # Process failed payment
        else:
            # Update payment status to Failed
            payment.paymentStatus = "Failed"
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
        JSON: Ticket details including player and payment information
    """
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify({"ticket": ticket.to_dict()})


@app.route("/api/payments/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    """
    Endpoint to get details of a specific payment

    Args:
        payment_id (int): Payment ID

    Returns:
        JSON: Payment details including associated tickets
    """
    payment = Payment.query.get(payment_id)

    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # Get associated tickets
    tickets = Ticket.query.filter_by(paymentId=payment_id).all()
    
    payment_data = payment.to_dict()
    payment_data["tickets"] = [ticket.to_dict() for ticket in tickets]

    return jsonify({"payment": payment_data})


if __name__ == "__main__":
    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()

    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=5001)