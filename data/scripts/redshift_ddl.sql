-- Redshift Serverless DDL for Customer 360 (Analytics Data)
-- Database: analytics_db
-- Column types matched to actual CSV data

DROP TABLE IF EXISTS purchase CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS vendor CASCADE;

-- Category table
-- CSV: id,dept_name,parent,description
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    dept_name VARCHAR(100),
    parent INTEGER,
    description VARCHAR(500)
);

-- Vendor table
-- CSV: id,vendor_name,industry,homepage
CREATE TABLE vendor (
    id INTEGER PRIMARY KEY,
    vendor_name VARCHAR(200),
    industry VARCHAR(100),
    homepage VARCHAR(500)
);

-- Product table
-- CSV: id,name,brand,price,dept,description
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    dept INTEGER,
    description VARCHAR(2000)
);

-- Purchase table (fact)
-- CSV: id,pid,date,time,quantity,price,cid,card,reward_account
CREATE TABLE purchase (
    id VARCHAR(50),              -- UUID
    pid INTEGER,
    purchase_date DATE,
    purchase_time VARCHAR(20),
    quantity INTEGER,
    price DECIMAL(10,2),
    cid INTEGER,
    card VARCHAR(50),            -- UUID
    reward_account VARCHAR(50)   -- UUID (nullable)
)
DISTSTYLE KEY
DISTKEY(cid)
SORTKEY(purchase_date);
