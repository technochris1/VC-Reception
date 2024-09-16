BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "credit_transaction_log" (
	"id"	INTEGER NOT NULL,
	"timestamp"	DATETIME DEFAULT (CURRENT_TIMESTAMP),
	"guest"	INTEGER NOT NULL,
	"authorizedSource"	VARCHAR(100) NOT NULL,
	"authorizedBy"	INTEGER,
	"generalAmountChange"	INTEGER NOT NULL,
	"specialEventAmountChange"	INTEGER NOT NULL,
	"privateSessionAmountChange"	INTEGER NOT NULL,
	"description"	VARCHAR(200) NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("authorizedBy") REFERENCES "guest"("id"),
	FOREIGN KEY("guest") REFERENCES "guest"("id")
);
CREATE TABLE IF NOT EXISTS "event" (
	"id"	INTEGER NOT NULL,
	"eventName"	VARCHAR(100),
	"eventDescription"	VARCHAR(200),
	"eventStartDate"	INTEGER,
	"eventEndDate"	INTEGER,
	"eventLocation"	VARCHAR(100),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "guest" (
	"id"	INTEGER NOT NULL,
	"uuid"	VARCHAR,
	"fetUsername"	VARCHAR(100),
	"name"	VARCHAR(100) NOT NULL,
	"email"	VARCHAR(200) NOT NULL,
	"phone"	VARCHAR(20),
	"password"	VARCHAR(255),
	"termsCheck"	BOOLEAN,
	"termsDate"	DATETIME,
	"lastVisit"	DATETIME,
	"created_at"	DATETIME DEFAULT (CURRENT_TIMESTAMP),
	UNIQUE("email"),
	PRIMARY KEY("id"),
	UNIQUE("uuid")
);
CREATE TABLE IF NOT EXISTS "guest_credit" (
	"id"	INTEGER NOT NULL,
	"lastUpdate"	DATETIME,
	"guest_id"	INTEGER NOT NULL,
	"generalAmount"	INTEGER NOT NULL,
	"specialEventAmount"	INTEGER NOT NULL,
	"privateSessionAmount"	INTEGER NOT NULL,
	PRIMARY KEY("id"),
	FOREIGN KEY("guest_id") REFERENCES "guest"("id")
);
CREATE TABLE IF NOT EXISTS "guest_roles" (
	"guest_id"	INTEGER,
	"role_id"	INTEGER,
	FOREIGN KEY("guest_id") REFERENCES "guest"("id"),
	FOREIGN KEY("role_id") REFERENCES "role"("id")
);
CREATE TABLE IF NOT EXISTS "guestlog" (
	"id"	INTEGER NOT NULL,
	"checked_in_at"	DATETIME DEFAULT (CURRENT_TIMESTAMP),
	"userID"	INTEGER,
	PRIMARY KEY("id"),
	FOREIGN KEY("userID") REFERENCES "guest"("id")
);
CREATE TABLE IF NOT EXISTS "role" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(100),
	"description"	VARCHAR(200),
	"permissions"	VARCHAR(200),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "setting" (
	"id"	INTEGER NOT NULL,
	"tos"	VARCHAR,
	"tos_updated"	VARCHAR(100),
	"checkInCooldownSeconds"	INTEGER,
	"show_cashapp"	BOOLEAN,
	"show_paypal"	BOOLEAN,
	"show_venmo"	BOOLEAN,
	"show_cash"	BOOLEAN,
	"show_credit"	BOOLEAN,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "tag" (
	"id"	INTEGER NOT NULL,
	"tagName"	VARCHAR(100),
	"tagDescription"	VARCHAR(200),
	PRIMARY KEY("id")
);
COMMIT;
