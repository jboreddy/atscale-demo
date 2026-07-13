-- Redshift Serverless DDL for Customer 360 (Analytics Data)
-- Database: analytics_db
-- Source: https://github.com/stardog-union/knowledge-kits/tree/main/examples/c360/data

-- Drop tables if exist (idempotent)
DROP TABLE IF EXISTS purchase CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS vendor CASCADE;

-- Category table (dimension)
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    dept_name VARCHAR(100),
    parent INTEGER
);

-- Vendor table (dimension)
CREATE TABLE vendor (
    id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(200),
    industry VARCHAR(100)
);

-- Product table (dimension)
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    dept INTEGER
);

-- Purchase table (fact)
CREATE TABLE purchase (
    id INTEGER,
    cid INTEGER,
    pid INTEGER,
    purchase_date DATE,
    quantity INTEGER,
    price DECIMAL(10,2),
    card INTEGER
)
DISTSTYLE KEY
DISTKEY(cid)
SORTKEY(purchase_date);

-- Note: No foreign keys in Redshift (not supported)
-- Relationships enforced at semantic layer level
