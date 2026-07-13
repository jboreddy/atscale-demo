-- Aurora PostgreSQL DDL for Customer 360 (Operational Data)
-- Database: customer360_db
-- Source: https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data

-- Drop tables if exist (idempotent)
DROP TABLE IF EXISTS rewards_account CASCADE;
DROP TABLE IF EXISTS credit_card CASCADE;
DROP TABLE IF EXISTS address CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

-- Customer table
CREATE TABLE customer (
    cid INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(200),
    ssn VARCHAR(11),
    phone VARCHAR(20),
    location INTEGER
);

-- Address table
CREATE TABLE address (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    street_name VARCHAR(200)
);

-- Credit card table
CREATE TABLE credit_card (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    card_num VARCHAR(20),
    card_type VARCHAR(50)
);

-- Rewards account table
CREATE TABLE rewards_account (
    id INTEGER PRIMARY KEY,
    cid INTEGER REFERENCES customer(cid),
    account_id VARCHAR(50),
    create_date DATE
);

-- Performance indexes on join keys
CREATE INDEX idx_address_cid ON address(cid);
CREATE INDEX idx_credit_card_cid ON credit_card(cid);
CREATE INDEX idx_rewards_cid ON rewards_account(cid);
CREATE INDEX idx_customer_location ON customer(location);
