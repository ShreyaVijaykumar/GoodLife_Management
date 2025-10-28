-- Visitors Table 
CREATE TABLE visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    aadhar TEXT,
    age INTEGER,
    address TEXT,
    purpose TEXT,
    remarks TEXT,
    visit_date DATE
);

-- Donations Table
CREATE TABLE donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT,
    amount REAL,
    items_donated TEXT,
    payment_mode TEXT,
    payment_detail TEXT,
    donation_date DATE
);