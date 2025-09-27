CREATE TABLE division (
        "divisionId" INTEGER NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        "minRating" INTEGER,
        "maxRating" INTEGER,
        price NUMERIC(10, 2) NOT NULL,
        "dateCreated" DATETIME,
        "lastUpdated" DATETIME,
        PRIMARY KEY ("divisionId")
);
CREATE TABLE player (
        "playerId" INTEGER NOT NULL,
        "playerName" VARCHAR(255) NOT NULL,
        "playerRating" INTEGER NOT NULL,
  --      "playerEmail" VARCHAR(255),
        PRIMARY KEY ("playerId")
);
CREATE TABLE payment (
        "paymentId" INTEGER NOT NULL,
        "customerName" VARCHAR(255) NOT NULL,
        "phoneNumber" VARCHAR(20) NOT NULL,
        "totalAmount" NUMERIC(10, 2) NOT NULL,
        "paymentStatus" VARCHAR(7) NOT NULL,
        "mpesaReceiptNumber" VARCHAR(100),
        "transactionDate" DATETIME,
        "dateCreated" DATETIME,
        "lastUpdated" DATETIME,
        PRIMARY KEY ("paymentId")
);
CREATE TABLE ticket (
        "ticketId" INTEGER NOT NULL,
        "ticketPrice" NUMERIC(10, 2) NOT NULL,
        "divisionId" INTEGER NOT NULL,
        "playerId" INTEGER NOT NULL,
        "paymentId" INTEGER NOT NULL,
        "dateCreated" DATETIME,
        "lastUpdated" DATETIME,
        PRIMARY KEY ("ticketId"),
        FOREIGN KEY("divisionId") REFERENCES division ("divisionId") ON DELETE CASCADE,
        UNIQUE ("playerId"),
        FOREIGN KEY("playerId") REFERENCES player ("playerId") ON DELETE CASCADE,
        FOREIGN KEY("paymentId") REFERENCES payment ("paymentId") ON DELETE CASCADE
);
CREATE TABLE pushrequest (
        "pushRequestId" INTEGER NOT NULL,
        "paymentId" INTEGER NOT NULL,
        "checkoutRequestId" VARCHAR(255) NOT NULL,
        "dateCreated" DATETIME,
        "lastUpdated" DATETIME,
        PRIMARY KEY ("pushRequestId"),
        FOREIGN KEY("paymentId") REFERENCES payment ("paymentId") ON DELETE CASCADE
);
CREATE TABLE pesapal_interim_payment (
        "pesapalInterimPaymentId" INTEGER NOT NULL,
        "paymentId" INTEGER NOT NULL,
        amount NUMERIC(10, 2) NOT NULL,
        status VARCHAR(30),
        "iframeSrc" VARCHAR(255) NOT NULL,
        "orderTrackingId" VARCHAR(255) NOT NULL,
        "merchantReference" VARCHAR(255) NOT NULL,
        "dateCreated" DATETIME,
        "lastUpdated" DATETIME,
        PRIMARY KEY ("pesapalInterimPaymentId"),
        FOREIGN KEY("paymentId") REFERENCES payment ("paymentId") ON DELETE CASCADE
);
