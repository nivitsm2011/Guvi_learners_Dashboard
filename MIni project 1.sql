-- Branches
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(100),
    branch_admin_name VARCHAR(100)
);

-- Enum types
CREATE TYPE rol AS ENUM ('Super Admin','Admin');



-- Customer Sales
CREATE TABLE customer_sales (
    sale_id SERIAL PRIMARY KEY,
    branch_id INT ,
    sale_date DATE,
    customer_name VARCHAR(100) ,
    mobile_number VARCHAR(15) UNIQUE ,
    product_name VARCHAR(30) ,
    gross_sales DECIMAL(12,2) ,
    received_amount DECIMAL(12,2) DEFAULT 0.00,
    status VARCHAR(10) DEFAULT 'Open',
	
        
    CONSTRAINT fk_customer_sales_branch
        FOREIGN KEY (branch_id)
        REFERENCES branches(branch_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- Users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(25),
    branch_id INT,
    role rol,
    email VARCHAR(255) UNIQUE
);

ALTER TABLE customer_sales
ADD COLUMN pending_amount DECIMAL(12,2)
GENERATED ALWAYS AS (gross_sales - received_amount) STORED;


-- Payment Splits
CREATE TABLE payment_splits (
    payment_id serial PRIMARY KEY,
    sale_id INT,
    payment_date DATE,
    amount_paid DECIMAL(12,2),
    payment_method VARCHAR(50),
    CONSTRAINT fk_payment_split
        FOREIGN KEY (sale_id)
        REFERENCES customer_sales(sale_id)
);


CREATE OR REPLACE FUNCTION update_sales_amounts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update received_amount and status
    UPDATE customer_sales
    SET received_amount = received_amount + NEW.amount_paid,
        status = CASE
            WHEN received_amount + NEW.amount_paid >= gross_sales THEN 'Close'
            ELSE 'Open'
        END
    WHERE sale_id = NEW.sale_id;

    RETURN NEW;
END; 
$$ LANGUAGE plpgsql;

-- Trigger
CREATE TRIGGER trg_update_sales_amounts
AFTER INSERT ON payment_splits
FOR EACH ROW

EXECUTE FUNCTION update_sales_amounts();


select * from payment_splits;
select * from customer_sales order by sale_id ASC limit 10;

drop table if exists branches cascade;
drop table if exists customer_sales cascade;
drop table if exists users cascade;
drop table if exists payment_splits cascade;
DROP TYPE rol;

DROP TRIGGER trg_update_sales_amounts ON payment_splits;


SELECT setval('payment_splits_payment_id_seq', (SELECT MAX(payment_id) FROM payment_splits));


INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
VALUES (10, '2024-06-01', 12000.00, 'Cash');

INSERT INTO payment_splits (sale_id, payment_date, amount_paid, payment_method)
VALUES (5, '2024-06-01', 20000.00, 'Cash');

SELECT sale_id, gross_sales, received_amount, pending_amount, status
FROM customer_sales
WHERE sale_id = 6;

SELECT setval('customer_sales_sale_id_seq', (SELECT MAX(sale_id) FROM customer_sales) + 1);

SELECT DISTINCT branch_id FROM customer_sales;





