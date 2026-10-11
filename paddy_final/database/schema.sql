-- Paddy Procurement System - Database Schema (Reference)
-- SQLite compatible

-- Admin (system administrators)
CREATE TABLE IF NOT EXISTS Admin (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Officer (procurement center staff)
CREATE TABLE IF NOT EXISTS Officer (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Farmer
CREATE TABLE IF NOT EXISTS Farmer (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  aadhaar TEXT UNIQUE NOT NULL,
  phone TEXT NOT NULL,
  email TEXT,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- LandDetails (farmer's land)
CREATE TABLE IF NOT EXISTS LandDetails (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farmer_id INTEGER NOT NULL REFERENCES Farmer(id) ON DELETE CASCADE,
  survey_no TEXT NOT NULL,
  village TEXT NOT NULL,
  area_acres REAL NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Crop (MSP rates)
CREATE TABLE IF NOT EXISTS Crop (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  msp_per_kg REAL NOT NULL,
  season TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- SlotBooking
CREATE TABLE IF NOT EXISTS SlotBooking (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farmer_id INTEGER NOT NULL REFERENCES Farmer(id),
  slot_date DATE NOT NULL,
  slot_time TEXT NOT NULL,
  status TEXT DEFAULT 'booked',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Procurement
CREATE TABLE IF NOT EXISTS Procurement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farmer_id INTEGER NOT NULL REFERENCES Farmer(id),
  slot_booking_id INTEGER REFERENCES SlotBooking(id),
  crop_id INTEGER NOT NULL REFERENCES Crop(id),
  weight_kg REAL NOT NULL,
  moisture_pct REAL,
  msp_rate REAL NOT NULL,
  amount REAL NOT NULL,
  officer_id INTEGER REFERENCES Officer(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Bill
CREATE TABLE IF NOT EXISTS Bill (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  procurement_id INTEGER NOT NULL UNIQUE REFERENCES Procurement(id),
  bill_no TEXT UNIQUE NOT NULL,
  total_amount REAL NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Payment
CREATE TABLE IF NOT EXISTS Payment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bill_id INTEGER NOT NULL UNIQUE REFERENCES Bill(id),
  amount REAL NOT NULL,
  mode TEXT NOT NULL,
  reference_no TEXT,
  approved_by INTEGER REFERENCES Officer(id),
  paid_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_farmer_aadhaar ON Farmer(aadhaar);
CREATE INDEX IF NOT EXISTS idx_slot_date ON SlotBooking(slot_date);
CREATE INDEX IF NOT EXISTS idx_procurement_farmer ON Procurement(farmer_id);
CREATE INDEX IF NOT EXISTS idx_bill_status ON Bill(status);
