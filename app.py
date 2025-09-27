from flask_migrate import Migrate
import os
import base64
import json
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


# Initialize Flask app
app = Flask("Scrabble Kenya Payments System")

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["FLASK_SECRET_KEY"] = FLASK_SECRET_KEY

# Pesapal Configuration
app.config["PESAPAL_BASE_URL"] = PESAPAL_BASE_URL
app.config["PESAPAL_CONSUMER_KEY"] = PESAPAL_CONSUMER_KEY
app.config["PESAPAL_CONSUMER_SECRET"] = PESAPAL_CONSUMER_SECRET
#app.config["PESAPAL_CALLBACK_URL"] = PESAPAL_CALLBACK_URL
#app.config["PESAPAL_IPN_URL"] = PESAPAL_IPN_URL

# Initialize SQLAlchemy
db = SQLAlchemy(app)

migrate = Migrate(app, db)


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
                        payment=payment,
                    )
                    print(
                        f"Ticket confirmation email sent to {player.playerEmail}"
                    )
                except Exception as e:
                    print(
                        f"Failed to send email to {player.playerEmail}: {str(e)}"
                    )
            else:
                print(
                    f"No email address for player {player.playerName if player else 'Unknown'}"
                )

    except Exception as e:
        print(f"Error sending ticket confirmation emails: {str(e)}")


# Models
class Division(db.Model):
    """
    Division model representing divisions available to play in
    """

    _tablename_ = "division"

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

    _tablename_ = "player"

    playerId = db.Column(db.Integer, primary_key=True)
    playerName = db.Column(db.String(255), nullable=False)
    playerRating = db.Column(db.Integer, nullable=False)
   # playerEmail = db.Column(db.String(255))

    # Relationship with Ticket model (one-to-one)
    ticket = db.relationship("Ticket", back_populates="player", uselist=False)

    def to_dict(self):
        """Convert player object to dictionary"""
        return {
            "playerId": self.playerId,
            "playerName": self.playerName,
            "playerRating": self.playerRating,
 #           "playerEmail": self.playerEmail,
        }


class Payment(db.Model):
    """
    Payment model representing payment transactions
    """

    _tablename_ = "payment"

    paymentId = db.Column(db.Integer, primary_key=True)
    customerName = db.Column(db.String(255), nullable=False)
   # phoneNumber = db.Column(db.String(20), nullable=False)
    totalAmount = db.Column(db.Numeric(10, 2), nullable=False)
    paymentStatus = db.Column(
        db.Enum("Pending", "Paid", "Failed"), default="Pending", nullable=False
    )
    receiptNumber = db.Column(db.String(100))
    paymentMethod = db.Column(db.String(50), default="Pesapal")
    transactionDate = db.Column(db.DateTime)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Ticket model
    tickets = db.relationship(
        "Ticket", back_populates="payment", cascade="all, delete-orphan"
    )

    # Relationship with PesapalInterimPayment model
    interim_payments = db.relationship(
        "PesapalInterimPayment",
        back_populates="payment",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        """Convert payment object to dictionary"""
        return {
            "paymentId": self.paymentId,
            "customerName": self.customerName,
   #         "phoneNumber": self.phoneNumber,
            "totalAmount": float(self.totalAmount),
            "paymentStatus": self.paymentStatus,
            "receiptNumber": self.receiptNumber,
            "paymentMethod": self.paymentMethod,
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

    _tablename_ = "ticket"

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
  #              "playerEmail": self.player.playerEmail,
            }
            if self.player
            else None,
            "division": {
                "title": self.division.title,
                "description": self.division.description,
            }
            if self.division
            else None,
            "payment": self.payment.to_dict() if self.payment else None,
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }


class PesapalInterimPayment(db.Model):
    """
    PesapalInterimPayment model for tracking Pesapal payment requests
    """

    _tablename_ = "pesapal_interim_payment"

    pesapalInterimPaymentId = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    paymentId = db.Column(
        db.Integer,
        db.ForeignKey("payment.paymentId", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default="SAVED")
    iframeSrc = db.Column(db.String(255), nullable=False)
    orderTrackingId = db.Column(db.String(255), nullable=False)
    merchantReference = db.Column(db.String(255), nullable=False)
    dateCreated = db.Column(db.DateTime, default=func.now())
    lastUpdated = db.Column(
        db.DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationship with Payment model
    payment = db.relationship("Payment", back_populates="interim_payments")

    def to_dict(self):
        """Convert pesapal interim payment object to dictionary"""
        return {
            "pesapalInterimPaymentId": self.pesapalInterimPaymentId,
            "paymentId": self.paymentId,
            "amount": float(self.amount),
            "status": self.status,
            "iframeSrc": self.iframeSrc,
            "orderTrackingId": self.orderTrackingId,
            "merchantReference": self.merchantReference,
            "dateCreated": self.dateCreated.isoformat()
            if self.dateCreated
            else None,
            "lastUpdated": self.lastUpdated.isoformat()
            if self.lastUpdated
            else None,
        }


# Helper functions for Pesapal integration
def split_full_name(full_name):
    """
    Split a full name into first name, middle name, and last name parts

    Parameters:
        full_name (str): Full name to split

    Returns:
        tuple: (first_name, middle_name, last_name)
    """
    # Split the name by spaces
    name_parts = full_name.split()

    # Check how many parts the name has
    if len(name_parts) == 2:  # First and last name only
        first_name, last_name = name_parts
        middle_name = ""
    elif len(name_parts) > 2:  # First, middle, and last name
        first_name = name_parts[0]
        middle_name = " ".join(name_parts[1:-1])
        last_name = name_parts[-1]
    else:
        first_name = full_name
        middle_name = last_name = ""

    return first_name, middle_name, last_name


def get_access_token():
    """
    Retrieves 5 minute access token from PesaPal.

    Returns:
        dict: Access token response
    """
    headers = {"accept": "text/plain", "content-type": "application/json"}
    post_data = {
        "consumer_key": current_app.config["PESAPAL_CONSUMER_KEY"],
        "consumer_secret": current_app.config["PESAPAL_CONSUMER_SECRET"],
    }
    end_point = os.path.join(
        current_app.config["PESAPAL_BASE_URL"], "api/Auth/RequestToken"
    )

    
	
    return make_request(end_point, headers, post_data)


def get_registered_ipn(access_token):
    """
    Get registered IPN from PesaPal

    Parameters:
        access_token (str): Access token received from get_access_token

    Returns:
        dict: Registered IPN response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    end_point = os.path.join(
        current_app.config["PESAPAL_BASE_URL"], "api/URLSetup/GetIpnList"
    )
    return make_request(end_point, headers)


def get_notification_id(access_token, callback_url):
    """
    Get notification ID for IPN from PesaPal

    Parameters:
        access_token (str): Access token received from get_access_token
        callback_url (str): Callback URL for IPN

    Returns:
        dict: Notification ID response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    post_data = {"ipn_notification_type": "GET", "url": callback_url}
    end_point = os.path.join(
        current_app.config["PESAPAL_BASE_URL"],
        "api/URLSetup/RegisterIPN",
    )
    return make_request(end_point, headers, post_data)


def get_merchant_order_url(details, access_token, subscription_details=None):
    """
    Get merchant order URL from PesaPal

    Parameters:
        details (dict): Dict object containing order details
        access_token (str): Access token received from get_access_token
        subscription_details (dict, optional): Dict object containing subscription details

    Returns:
        dict: Merchant order URL response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    post_data = {
        "language": details.get("language", "EN"),
        "currency": details.get("currency", "KES"),
        "amount": details.get("amount", 1.0),
        "id": details.get("id", datetime.now().strftime("%Y%m%d%H%M%S")),
        "description": details.get("description", ""),
        "billing_address": {
            "country_code": "KE",
            "phone_number": details.get("phone_number", ""),
            #"email_address": details.get("email_address", ""),
            "first_name": details.get("first_name", ""),
            "middle_name": details.get("middle_name", ""),
            "last_name": details.get("last_name", ""),
            "line_1": details.get("line_1", ""),
            "line_2": details.get("line_2", ""),
            "city": details.get("city", ""),
            "state": details.get("state", ""),
            "postal_code": details.get("postal_code", ""),
            "zip_code": details.get("zip_code", ""),
        },
        "callback_url": details.get("callback_url"),
        "notification_id": details.get("notification_id"),
        "terms_and_conditions_id": details.get("terms_and_conditions_id"),
    }

    # Check if subscription is activated
    if subscription_details:
        post_data.update(subscription_details)

    # Send request
    end_point = os.path.join(
        current_app.config["PESAPAL_BASE_URL"],
        "api/Transactions/SubmitOrderRequest",
    )
    return make_request(end_point, headers, post_data)


def get_transaction_status(order_tracking_id, access_token):
    """
    Get transaction status from PesaPal

    Parameters:
        order_tracking_id (str): Order tracking ID from get_merchant_order_url
        access_token (str): Access token received from get_access_token

    Returns:
        dict: Transaction status response
    """
    headers = {
        "accept": "text/plain",
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    end_point = (
        current_app.config["PESAPAL_BASE_URL"]
        + "/api/Transactions/GetTransactionStatus?"
        + f"orderTrackingId={order_tracking_id}"
    )
    return make_request(end_point, headers)


def make_request(url, headers, post_data=None):
    """
    Helper function to make HTTP requests

    Parameters:
        url (str): Endpoint URL
        headers (dict): HTTP headers
        post_data (dict, optional): Data to be posted

    Returns:
        dict: Decoded JSON response
    """
    try:
        if post_data:
            response = requests.post(
                url, headers=headers, data=json.dumps(post_data)
            )
        else:
            response = requests.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# Generate hash for secure payment links
def generate_hash(interim_payment_id):
    """
    Generate a secure hash for interim payment links

    Parameters:
        interim_payment_id (int): Interim payment ID

    Returns:
        str: Secure hash
    """
    hash_string = f"{interim_payment_id}{app.config['FLASK_SECRET_KEY']}"
    return base64.b64encode(hash_string.encode()).decode()


# Routes
# Set your deadline here
KENYA_TZ = timezone(timedelta(hours=3))
DEADLINE = datetime(2025, 12, 31, 23, 59, 59, tzinfo=KENYA_TZ)


def check_deadline():
    """Check if current time is past the deadline"""
    current_time = datetime.now(KENYA_TZ)
    return current_time > DEADLINE


@app.before_request
def before_request():
    """Check deadline before every request"""
    # Skip deadline check for specific routes
    excluded_routes = ["deadline_passed", "static"]

    if request.endpoint not in excluded_routes and check_deadline():
        return redirect(url_for("deadline_passed"))


@app.route("/deadline-passed")
def deadline_passed():
    """Page shown when deadline has passed"""
    deadline_formatted = DEADLINE.strftime("%B %d, %Y at %I:%M %p UTC")
    return render_template("deadline_passed.html", deadline=deadline_formatted)


@app.route("/")
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
        time_remaining = {"days": days, "hours": hours, "minutes": minutes}

    return {
        "deadline_passed": is_past,
        "deadline": DEADLINE.isoformat(),
        "current_time": datetime.now(KENYA_TZ).isoformat(),
        "time_remaining": time_remaining,
    }


@app.route("/api/divisions", methods=["GET"])
def get_divisions():
    """
    Endpoint to get all divisions

    Returns:
        JSON: List of divisions
    """
    divisions = Division.query.all()
    return jsonify(
        {"divisions": [division.to_dict() for division in divisions]}
    )


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

    return jsonify(
        {
            "players": [player.to_dict() for player in available_players],
            "divisions": [division.to_dict() for division in divisions],
        }
    )


@app.route("/api/make-payment", methods=["POST"])
def make_payment():
    """
    Endpoint to initiate Pesapal payment for multiple players

    Expected JSON payload:
    {
        "players": [
            {"playerId": 1, "divisionId": 1},
            {"playerId": 2, "divisionId": 2}
        ],
        "customerName": "John Doe",
        "phoneNumber": "254712345678",
        "email": "john@example.com"  // Added email field for Pesapal
    }

    Returns:
        JSON: Payment initiation results or error
    """
    data = request.get_json()

    try:
        # Validate required fields
        required_fields = ["players", "customerName"] #"phoneNumber" ] #"email"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}"}),
                    400,
                )

        if not isinstance(data["players"], list) or len(data["players"]) == 0:
            return (
                jsonify({"error": "At least one player must be selected"}),
                400,
            )

        # Validate and calculate total amount
        total_amount = 0
        player_registrations = []
        registered_players = []

        for player_data in data["players"]:
            if "playerId" not in player_data or "divisionId" not in player_data:
                return (
                    jsonify(
                        {
                            "error": "Each player must have playerId and divisionId"
                        }
                    ),
                    400,
                )

            # Check if player exists
            player = Player.query.get(player_data["playerId"])
            if not player:
                return (
                    jsonify(
                        {
                            "error": f"Player with ID {player_data['playerId']} not found"
                        }
                    ),
                    404,
                )

            # Check if player already has a ticket
            existing_ticket = Ticket.query.filter_by(
                playerId=player.playerId
            ).first()
            if existing_ticket:
                return (
                    jsonify(
                        {
                            "error": f"Player {player.playerName} is already registered"
                        }
                    ),
                    400,
                )

            # Check if division exists
            division = Division.query.get(player_data["divisionId"])
            if not division:
                return (
                    jsonify(
                        {
                            "error": f"Division with ID {player_data['divisionId']} not found"
                        }
                    ),
                    404,
                )

            # Check if player's rating is within division's rating band
            if not (
                division.minRating <= player.playerRating <= division.maxRating
            ):
                return (
                    jsonify(
                        {
                            "error": f"Player {player.playerName} (rating: {player.playerRating}) cannot play in {division.title} "
                            f"(rating range: {division.minRating}-{division.maxRating})"
                        }
                    ),
                    400,
                )

            # Add to total amount
            total_amount += float(division.price)

            # Store for ticket creation
            player_registrations.append(
                {
                    "player": player,
                    "division": division,
                    "playerId": player.playerId,
                    "divisionId": division.divisionId,
                }
            )

            registered_players.append(player.playerName)

        # Create payment record first
        new_payment = Payment(
            customerName=data["customerName"],
            #phoneNumber=data["phoneNumber"],
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

        # Get access token for Pesapal API
        access_token = get_access_token().get("token")


        if not access_token:
            db.session.rollback()
            return jsonify({"error": "Failed to get Pesapal access token"}), 500


        # Get IPN ID for callbacks
        ipn_url =  url_for("pesapal_ipn", _external=True)
        ipn_response = get_notification_id(access_token, ipn_url)
        if "error" in ipn_response or "ipn_id" not in ipn_response:
            db.session.rollback()
            return jsonify({"error": "Failed to register Pesapal IPN URL"}), 500

        ipn_id = ipn_response["ipn_id"]

        # Create description of registered players
        players_description = ", ".join(
            registered_players[:3]
        )  # Limit for description length
        if len(registered_players) > 3:
            players_description += f" and {len(registered_players) - 3} more"

        # Split customer name for Pesapal
        first_name, middle_name, last_name = split_full_name(
            data["customerName"]
        )

        # Create payment request
        payment_request = {
            "id": f"SCR-{new_payment.paymentId}",
            "amount": total_amount,
            "description": f"Registration for {players_description}",
            "callback_url": url_for("pesapal_callback", _external=True),
            "notification_id": ipn_id,
            #"email_address": data["email"],
#            "phone_number": data["phoneNumber"],
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "currency": "KES",
        }

        # Get order URL from Pesapal
        iframe_response = get_merchant_order_url(payment_request, access_token)

        if not  iframe_response.get("order_tracking_id") :
            db.session.rollback()
            return (
                jsonify(
                    {
                        "error": "Failed to generate Pesapal payment URL",
                       
                        "details": iframe_response,
                    }
                ),
                500,
            )

        # Create PesapalInterimPayment record
        interim_payment = PesapalInterimPayment(
            paymentId=new_payment.paymentId,
            amount=total_amount,
            status="SAVED",
            iframeSrc=iframe_response["redirect_url"],
            orderTrackingId=iframe_response["order_tracking_id"],
            merchantReference=iframe_response.get(
                "merchant_reference", f"SCR-{new_payment.paymentId}"
            ),
        )
        db.session.add(interim_payment)

        # Commit all changes
        db.session.commit()

        # Generate secure hash for redirect
        payment_hash = generate_hash(interim_payment.pesapalInterimPaymentId)

        return jsonify(
            {
                "message": "Payment initiated successfully",
                "totalAmount": total_amount,
                "playersRegistered": len(registered_players),
                "players": registered_players,
                "paymentId": new_payment.paymentId,
                "ticketIds": [ticket.ticketId for ticket in new_tickets],
                "orderTrackingId": iframe_response["order_tracking_id"],
                "paymentUrl": iframe_response["redirect_url"],
                "iframe_redirect_url": url_for(
                    "pesapal_iframe_redirect",
                    interim_payment_id=interim_payment.pesapalInterimPaymentId,
                    payment_hash=payment_hash,
                ),
            }
        )

    except IOError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/pesapal/iframe/<int:interim_payment_id>/redirect/<payment_hash>")
def pesapal_iframe_redirect(interim_payment_id, payment_hash):
    """
    Endpoint to display Pesapal iframe

    Parameters:
        interim_payment_id (int): Interim payment ID
        payment_hash (str): Secure hash to verify access

    Returns:
        HTML: Iframe page
    """
    # Verify hash
    valid_hash = generate_hash(interim_payment_id)
    if payment_hash != valid_hash:
        return (
            render_template("error.html", message="Invalid payment link"),
            403,
        )

    # Get interim payment
    interim_payment = PesapalInterimPayment.query.get_or_404(interim_payment_id)

    # Get payment
    payment = Payment.query.get_or_404(interim_payment.paymentId)

    # Get tickets
    tickets = Ticket.query.filter_by(paymentId=payment.paymentId).all()

    return render_template(
        "pesapal_iframe.html",
        iframe_src=interim_payment.iframeSrc,
        payment=payment,
        tickets=tickets,
    )


@app.route("/api/query-payment-status", methods=["POST"])
def query_payment_status():
    """
    Endpoint to query the status of a Pesapal transaction

    Expected JSON payload:
    {
        "orderTrackingId": "4e9d1490-45a0-4f50-9a1f-b08c0f8e41a0"
    }

    Returns:
        JSON: Transaction status result or error
    """
    data = request.get_json()
    order_tracking_id = data.get("orderTrackingId")

    if not order_tracking_id:
        return jsonify({"error": "Order Tracking ID not provided"}), 400

    try:
        # Get access token for Pesapal API
        access_token_response = get_access_token()
        if (
            "error" in access_token_response
            or "token" not in access_token_response
        ):
            return jsonify({"error": "Failed to get Pesapal access token"}), 500

        access_token = access_token_response["token"]

        # Get transaction status
        status_response = get_transaction_status(
            order_tracking_id, access_token
        )

        # Find the associated interim payment
        interim_payment = PesapalInterimPayment.query.filter_by(
            orderTrackingId=order_tracking_id
        ).first()

        if not interim_payment:
            return (
                jsonify(
                    {
                        "error": "No matching interim payment found",
                        "pesapalResponse": status_response,
                    }
                ),
                404,
            )

        # Get the associated payment
        payment = Payment.query.get(interim_payment.paymentId)
        if not payment:
            return (
                jsonify(
                    {
                        "error": "No matching payment found",
                        "pesapalResponse": status_response,
                    }
                ),
                404,
            )

        # Return the status
        return jsonify(
            {
                "status": status_response.get(
                    "payment_status_description", "Unknown"
                ),
                "payment": payment.to_dict(),
                "pesapalResponse": status_response,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/pesapal/ipn", methods=["GET"])
def pesapal_ipn():
    """
    IPN endpoint for Pesapal payment notifications

    Returns:
        JSON: Acknowledgement message
    """
    try:
        # Get parameters from request
        order_tracking_id = request.args.get("OrderTrackingId")

        if not order_tracking_id:
            return (
                jsonify(
                    {"error": "Invalid IPN data - missing OrderTrackingId"}
                ),
                400,
            )

        # Get access token for Pesapal API
        access_token = get_access_token().get("token")
        if not access_token:
            db.session.rollback()
            return jsonify({"error": "Failed to get Pesapal access token"}), 500

        # Get transaction status
        status = get_transaction_status(order_tracking_id, access_token)
        payment_status = status.get("payment_status_description")

        # Find the associated interim payment
        interim_payment = PesapalInterimPayment.query.filter_by(
            orderTrackingId=order_tracking_id
        ).first()

        if not interim_payment:
            return jsonify({"error": "No matching interim payment found"}), 404

        # Get the associated payment
        payment = Payment.query.get(interim_payment.paymentId)
        if not payment:
            return jsonify({"error": "No matching payment found"}), 404

        # Process based on status
        if payment_status == "Completed":
            # Update payment
            payment.paymentStatus = "Paid"
            payment.receiptNumber = status.get("confirmation_code")
            payment.paymentMethod = (
                f"Pesapal - {status.get('payment_method', 'Unknown')}"
            )
            payment.transactionDate = datetime.strptime(
                status.get("created_date", datetime.now().isoformat()),
                "%Y-%m-%dT%H:%M:%S.%f"
                if "." in status.get("created_date", "")
                else "%Y-%m-%dT%H:%M:%S",
            )

            # Update interim payment
            interim_payment.status = "COMPLETED"

            db.session.commit()

            # Send ticket confirmation emails to all players
           # send_ticket_confirmation_emails(payment.paymentId)

            return jsonify({"message": "Payment processed successfully"}), 200

        elif payment_status == "Failed":
            # Update statuses
            payment.paymentStatus = "Failed"
            interim_payment.status = "FAILED"
            db.session.commit()

            return jsonify({"message": "Failed payment recorded"}), 200

        else:  # Pending or other status
            return (
                jsonify(
                    {
                        "message": "Payment status updated",
                        "status": payment_status,
                    }
                ),
                200,
            )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/pesapal/callback", methods=["GET"])
def pesapal_callback():
    """
    Callback endpoint for Pesapal payment redirect

    Returns:
        HTML: Redirect to payment result page
    """
    # Get parameters from request
    order_tracking_id = request.args.get("OrderTrackingId")

    if not order_tracking_id:
        return (
            render_template(
                "error.html",
                message="Invalid callback data - missing OrderTrackingId",
            ),
            400,
        )

    # Find the associated interim payment
    interim_payment = PesapalInterimPayment.query.filter_by(
        orderTrackingId=order_tracking_id
    ).first()

    if not interim_payment:
        return (
            render_template("error.html", message="Payment record not found"),
            404,
        )

    # Get the associated payment
    payment = Payment.query.get(interim_payment.paymentId)
    if not payment:
        return (
            render_template("error.html", message="Payment record not found"),
            404,
        )

    # Get access token for Pesapal API
    access_token = get_access_token().get("token")
    if not access_token:
        db.session.rollback()
        return jsonify({"error": "Failed to get Pesapal access token"}), 500


    # Get transaction status
    status = get_transaction_status(order_tracking_id, access_token)
    payment_status = status.get("payment_status_description")

    # Get tickets
    tickets = Ticket.query.filter_by(paymentId=payment.paymentId).all()

    # Handle based on status
    if payment_status == "Completed":
        # Update payment if not already updated by IPN
        if payment.paymentStatus != "Paid":
            payment.paymentStatus = "Paid"
            payment.receiptNumber = status.get("confirmation_code")
            payment.paymentMethod = (
                f"Pesapal - {status.get('payment_method', 'Unknown')}"
            )
            payment.transactionDate = datetime.strptime(
                status.get("created_date", datetime.now().isoformat()),
                "%Y-%m-%dT%H:%M:%S.%f"
                if "." in status.get("created_date", "")
                else "%Y-%m-%dT%H:%M:%S",
            )

            # Update interim payment
            interim_payment.status = "COMPLETED"
            db.session.commit()

            # Send ticket confirmation emails to all players
            send_ticket_confirmation_emails(payment.paymentId)

        return render_template(
            "payment_success.html",
            payment=payment,
            tickets=tickets,
            receipt=status.get("confirmation_code"),
            method=status.get("payment_method", "Unknown"),
        )

    elif payment_status == "Failed":
        # Update statuses if not already updated by IPN
        if payment.paymentStatus != "Failed":
            payment.paymentStatus = "Failed"
            interim_payment.status = "FAILED"
            db.session.commit()

        return render_template(
            "payment_failed.html",
            payment=payment,
            message=status.get(
                "status_reason", "Payment failed. Please try again."
            ),
        )

    else:  # Pending or other status
        return render_template(
            "payment_pending.html",
            payment=payment,
            orderTrackingId=order_tracking_id,
        )


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
