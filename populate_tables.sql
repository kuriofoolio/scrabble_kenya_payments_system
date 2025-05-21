-- NOTE: You most likely don't need this since we are using ORM for Flask
-- Create database
CREATE DATABASE IF NOT EXISTS movie_tickets;
USE movie_tickets;

-- Movie table
CREATE TABLE IF NOT EXISTS movie (
    movieId INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    showTime DATETIME NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    maximumTickets INT NOT NULL DEFAULT 100,
    imageUrl VARCHAR(255),
    dateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Ticket table
CREATE TABLE IF NOT EXISTS ticket (
    ticketId INT AUTO_INCREMENT PRIMARY KEY,
    movieId INT NOT NULL,
    customerName VARCHAR(255) NOT NULL,
    phoneNumber VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    totalAmount DECIMAL(10, 2) NOT NULL,
    paymentStatus ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Pending',
    mpesaReceiptNumber VARCHAR(100),
    transactionDate DATETIME,
    dateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_Ticket_Movie FOREIGN KEY (movieId) REFERENCES movie(movieId) ON DELETE CASCADE
);

-- PushRequest table
CREATE TABLE IF NOT EXISTS pushrequest (
    pushRequestId INT AUTO_INCREMENT PRIMARY KEY,
    ticketId INT NOT NULL,
    checkoutRequestId VARCHAR(255) NOT NULL,
    dateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_PushRequest_Ticket FOREIGN KEY (ticketId) REFERENCES ticket(ticketId) ON DELETE CASCADE
);
