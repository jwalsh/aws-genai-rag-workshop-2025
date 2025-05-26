-- Sample data for Text-to-SQL workshop
SET search_path TO workshop, public;

-- Insert sample suppliers
INSERT INTO suppliers (supplier_name, contact_person, email, phone, address, city, country) VALUES
('Tech Components Inc', 'John Smith', 'john@techcomp.com', '555-0101', '123 Tech St', 'San Francisco', 'USA'),
('Global Electronics', 'Maria Garcia', 'maria@globalelec.com', '555-0102', '456 Innovation Ave', 'Austin', 'USA'),
('Premium Parts Ltd', 'David Chen', 'david@premiumparts.com', '555-0103', '789 Quality Rd', 'Seattle', 'USA'),
('Reliable Supplies Co', 'Sarah Johnson', 'sarah@reliable.com', '555-0104', '321 Supply Chain Blvd', 'Denver', 'USA');

-- Insert sample customers
INSERT INTO customers (first_name, last_name, email, phone, address, city, state, zip_code, registration_date, status) VALUES
('Alice', 'Johnson', 'alice.johnson@email.com', '555-1001', '123 Oak St', 'Portland', 'OR', '97201', '2024-01-15', 'active'),
('Bob', 'Smith', 'bob.smith@email.com', '555-1002', '456 Pine Ave', 'Seattle', 'WA', '98101', '2024-02-20', 'active'),
('Carol', 'Davis', 'carol.davis@email.com', '555-1003', '789 Elm Dr', 'San Francisco', 'CA', '94102', '2024-03-10', 'active'),
('David', 'Wilson', 'david.wilson@email.com', '555-1004', '321 Maple Ln', 'Los Angeles', 'CA', '90210', '2024-04-05', 'active'),
('Eva', 'Brown', 'eva.brown@email.com', '555-1005', '654 Cedar Way', 'Phoenix', 'AZ', '85001', '2024-05-12', 'active'),
('Frank', 'Miller', 'frank.miller@email.com', '555-1006', '987 Birch St', 'Denver', 'CO', '80202', '2024-06-08', 'inactive'),
('Grace', 'Taylor', 'grace.taylor@email.com', '555-1007', '147 Spruce Ave', 'Austin', 'TX', '73301', '2024-07-22', 'active'),
('Henry', 'Anderson', 'henry.anderson@email.com', '555-1008', '258 Willow Dr', 'Miami', 'FL', '33101', '2024-08-15', 'active'),
('Iris', 'Thomas', 'iris.thomas@email.com', '555-1009', '369 Poplar Ln', 'Boston', 'MA', '02101', '2024-09-03', 'active'),
('Jack', 'Garcia', 'jack.garcia@email.com', '555-1010', '741 Redwood Way', 'Chicago', 'IL', '60601', '2024-10-18', 'active');

-- Insert sample products
INSERT INTO products (product_name, category, price, cost, stock_quantity, supplier_id, description, created_date, is_active) VALUES
('Wireless Bluetooth Headphones', 'Electronics', 99.99, 60.00, 150, 1, 'High-quality wireless headphones with noise cancellation', '2024-01-01', true),
('Smartphone Case', 'Electronics', 24.99, 12.00, 300, 1, 'Protective case for smartphones', '2024-01-02', true),
('USB-C Cable', 'Electronics', 19.99, 8.00, 500, 2, '6ft USB-C charging cable', '2024-01-03', true),
('Laptop Stand', 'Office', 79.99, 45.00, 75, 3, 'Adjustable aluminum laptop stand', '2024-01-04', true),
('Wireless Mouse', 'Electronics', 39.99, 22.00, 200, 1, 'Ergonomic wireless mouse', '2024-01-05', true),
('Mechanical Keyboard', 'Electronics', 129.99, 75.00, 100, 2, 'RGB mechanical gaming keyboard', '2024-01-06', true),
('Monitor', '27" 4K Monitor', 'Electronics', 299.99, 180.00, 50, 3, 'Ultra HD 4K monitor', '2024-01-07', true),
('Desk Organizer', 'Office', 34.99, 18.00, 120, 4, 'Bamboo desk organizer with compartments', '2024-01-08', true),
('Coffee Mug', 'Kitchen', 14.99, 6.00, 250, 4, 'Ceramic coffee mug with handle', '2024-01-09', true),
('Water Bottle', 'Kitchen', 22.99, 10.00, 180, 4, 'Stainless steel insulated water bottle', '2024-01-10', true),
('Notebook', 'Office', 12.99, 5.00, 400, 4, 'A5 lined notebook', '2024-01-11', true),
('Pen Set', 'Office', 18.99, 8.50, 300, 4, 'Set of 5 ballpoint pens', '2024-01-12', true),
('Tablet Stand', 'Electronics', 49.99, 28.00, 85, 3, 'Adjustable tablet and phone stand', '2024-01-13', true),
('Bluetooth Speaker', 'Electronics', 69.99, 40.00, 90, 1, 'Portable Bluetooth speaker', '2024-01-14', true),
('Power Bank', 'Electronics', 44.99, 25.00, 160, 2, '10000mAh portable power bank', '2024-01-15', true);

-- Insert sample orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address, shipping_date, delivery_date) VALUES
(1, '2024-11-01 10:30:00', 119.98, 'delivered', '123 Oak St, Portland, OR 97201', '2024-11-02', '2024-11-05'),
(2, '2024-11-02 14:45:00', 299.99, 'delivered', '456 Pine Ave, Seattle, WA 98101', '2024-11-03', '2024-11-06'),
(3, '2024-11-03 09:15:00', 154.97, 'delivered', '789 Elm Dr, San Francisco, CA 94102', '2024-11-04', '2024-11-07'),
(1, '2024-11-05 16:20:00', 79.99, 'shipped', '123 Oak St, Portland, OR 97201', '2024-11-06', NULL),
(4, '2024-11-07 11:30:00', 249.96, 'delivered', '321 Maple Ln, Los Angeles, CA 90210', '2024-11-08', '2024-11-11'),
(5, '2024-11-08 13:45:00', 67.97, 'delivered', '654 Cedar Way, Phoenix, AZ 85001', '2024-11-09', '2024-11-12'),
(2, '2024-11-10 15:00:00', 199.97, 'processing', '456 Pine Ave, Seattle, WA 98101', NULL, NULL),
(7, '2024-11-12 10:15:00', 89.98, 'shipped', '147 Spruce Ave, Austin, TX 73301', '2024-11-13', NULL),
(8, '2024-11-14 12:30:00', 44.99, 'delivered', '258 Willow Dr, Miami, FL 33101', '2024-11-15', '2024-11-18'),
(9, '2024-11-16 14:45:00', 169.97, 'processing', '369 Poplar Ln, Boston, MA 02101', NULL, NULL),
(10, '2024-11-18 09:00:00', 129.99, 'pending', '741 Redwood Way, Chicago, IL 60601', NULL, NULL),
(3, '2024-11-20 16:30:00', 94.98, 'pending', '789 Elm Dr, San Francisco, CA 94102', NULL, NULL);

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES
-- Order 1 (Alice): Headphones + Smartphone Case
(1, 1, 1, 99.99, 99.99),
(1, 2, 1, 19.99, 19.99),

-- Order 2 (Bob): Monitor
(2, 7, 1, 299.99, 299.99),

-- Order 3 (Carol): Laptop Stand + Mouse + Cable
(3, 4, 1, 79.99, 79.99),
(3, 5, 1, 39.99, 39.99),
(3, 3, 1, 34.99, 34.99),

-- Order 4 (Alice): Laptop Stand
(4, 4, 1, 79.99, 79.99),

-- Order 5 (David): Keyboard + Mouse + Cable
(5, 6, 1, 129.99, 129.99),
(5, 5, 1, 39.99, 39.99),
(5, 3, 4, 19.99, 79.96),

-- Order 6 (Eva): Speaker + Water Bottle
(6, 14, 1, 69.99, 69.99),
(6, 10, 1, 22.99, 22.99),

-- Order 7 (Bob): Bluetooth Speaker + Power Bank + Desk Organizer
(7, 14, 1, 69.99, 69.99),
(7, 15, 1, 44.99, 44.99),
(7, 8, 1, 34.99, 34.99),

-- Order 8 (Grace): Coffee Mug + Notebook
(8, 9, 2, 14.99, 29.98),
(8, 11, 3, 12.99, 38.97),

-- Order 9 (Henry): Power Bank
(9, 15, 1, 44.99, 44.99),

-- Order 10 (Iris): Keyboard + Mouse + Tablet Stand
(10, 6, 1, 129.99, 129.99),
(10, 5, 1, 39.99, 39.99),

-- Order 11 (Jack): Mechanical Keyboard
(11, 6, 1, 129.99, 129.99),

-- Order 12 (Carol): Pen Set + Desk Organizer
(12, 12, 2, 18.99, 37.98),
(12, 8, 1, 34.99, 34.99);