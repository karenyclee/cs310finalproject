CREATE DATABASE IF NOT EXISTS ikeaapp;

USE ikeaapp;

DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS cart;

-- products table to store all products in IKEA inventory
CREATE TABLE products
(
    product_id           INT AUTO_INCREMENT,
    product_title        VARCHAR(255) NOT NULL,
    product_url          VARCHAR(255) NOT NULL,
    sku                  VARCHAR(64) NOT NULL,
    mpn                  VARCHAR(64) NOT NULL,
    currency             VARCHAR(3) NOT NULL,
    product_price        DECIMAL(10, 2) NOT NULL,
    product_condition    VARCHAR(32) NOT NULL,
    available            VARCHAR(32) NOT NULL,
    seller               VARCHAR(64) NOT NULL,
    seller_url           VARCHAR(255),
    brand                VARCHAR(64) NOT NULL,
    PRIMARY KEY (product_id),
    UNIQUE (product_url)
);

ALTER TABLE products AUTO_INCREMENT = 80001;  -- starting value

-- shopping cart table to store client's chosen products
CREATE TABLE cart (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

FLUSH PRIVILEGES;

--
-- done
--