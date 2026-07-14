-- Aurora PostgreSQL DDL for Customer 360 (Operational Data)
-- Database: customer360_db
-- Column types matched to actual CSV data

DROP TABLE IF EXISTS rewards_account CASCADE;
DROP TABLE IF EXISTS credit_card CASCADE;
DROP TABLE IF EXISTS address CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

-- Customer table
-- CSV: cid,first_name,last_name,email,ssn,picture,phone,location,full_name
CREATE TABLE customer (
    cid INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    ssn VARCHAR(20),
    picture VARCHAR(500),
    phone VARCHAR(20),
    location VARCHAR(50),          -- UUID linking to address.id
    full_name VARCHAR(200)
);

-- Address table
-- CSV: id,street_number,street_name,street_suffix,state,zip,city
CREATE TABLE address (
    id VARCHAR(50) PRIMARY KEY,    -- UUID
    street_number VARCHAR(20),
    street_name VARCHAR(200),
    street_suffix VARCHAR(50),
    state VARCHAR(50),
    zip VARCHAR(10),
    city VARCHAR(100)
);

-- Credit card table
-- CSV: id,cid,card_num,card_type
CREATE TABLE credit_card (
    id VARCHAR(50) PRIMARY KEY,    -- UUID
    cid INTEGER REFERENCES customer(cid),
    card_num VARCHAR(20),
    card_type VARCHAR(50)
);

-- Rewards account table
-- CSV: id,cid,account_id,create_date
CREATE TABLE rewards_account (
    id VARCHAR(50) PRIMARY KEY,    -- UUID
    cid INTEGER REFERENCES customer(cid),
    account_id VARCHAR(50),
    create_date DATE
);

-- Indexes
CREATE INDEX idx_credit_card_cid ON credit_card(cid);
CREATE INDEX idx_rewards_cid ON rewards_account(cid);
CREATE INDEX idx_customer_location ON customer(location);
CREATE INDEX idx_address_state ON address(state);
