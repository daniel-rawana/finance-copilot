-- Captura Portfolio Database Schema
-- SQLite database schema for storing portfolio and holdings data

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =============================================
-- PORTFOLIOS TABLE
-- =============================================
-- Stores portfolio metadata for each uploaded CSV file
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for each portfolio
    user_id TEXT NOT NULL,                 -- User identifier (can be email, username, or UUID)
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,  -- When the portfolio was uploaded
    file_name TEXT NOT NULL                -- Original filename of the uploaded CSV
);

-- =============================================
-- HOLDINGS TABLE
-- =============================================
-- Stores individual stock holdings within each portfolio
CREATE TABLE holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for each holding
    portfolio_id INTEGER NOT NULL,         -- Foreign key reference to portfolios table
    ticker TEXT NOT NULL,                  -- Stock symbol (e.g., 'AAPL', 'MSFT')
    shares REAL NOT NULL,                  -- Number of shares owned (allows fractional shares)
    purchase_price REAL NOT NULL,          -- Price per share when purchased
    purchase_date DATE,                    -- Date when the shares were purchased
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,  -- When this holding record was created
    
    -- Foreign key constraint
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Index on user_id for fast portfolio lookups by user
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);

-- Index on upload_date for chronological portfolio queries
CREATE INDEX idx_portfolios_upload_date ON portfolios(upload_date);

-- Index on portfolio_id for fast holdings lookups
CREATE INDEX idx_holdings_portfolio_id ON holdings(portfolio_id);

-- Index on ticker for stock-specific queries
CREATE INDEX idx_holdings_ticker ON holdings(ticker);

-- Index on purchase_date for date-based queries
CREATE INDEX idx_holdings_purchase_date ON holdings(purchase_date);

-- =============================================
-- SAMPLE DATA (OPTIONAL - FOR TESTING)
-- =============================================

-- Insert a sample portfolio
INSERT INTO portfolios (user_id, file_name) VALUES ('user@example.com', 'my_portfolio.csv');

-- Insert sample holdings for the portfolio
INSERT INTO holdings (portfolio_id, ticker, shares, purchase_price, purchase_date) VALUES
(1, 'AAPL', 50, 175.43, '2024-01-15'),
(1, 'MSFT', 30, 378.85, '2024-01-20'),
(1, 'GOOGL', 20, 142.56, '2024-02-01'),
(1, 'TSLA', 15, 248.50, '2024-02-10'),
(1, 'AMZN', 25, 155.30, '2024-02-15'),
(1, 'NVDA', 10, 875.20, '2024-02-20');

-- =============================================
-- USEFUL QUERIES
-- =============================================

-- Get all portfolios for a user
-- SELECT * FROM portfolios WHERE user_id = 'user@example.com' ORDER BY upload_date DESC;

-- Get all holdings for a specific portfolio
-- SELECT h.*, p.file_name, p.upload_date 
-- FROM holdings h 
-- JOIN portfolios p ON h.portfolio_id = p.id 
-- WHERE p.id = 1;

-- Get portfolio summary with total value
-- SELECT 
--     p.id,
--     p.file_name,
--     p.upload_date,
--     COUNT(h.id) as total_holdings,
--     SUM(h.shares * h.purchase_price) as total_invested
-- FROM portfolios p
-- LEFT JOIN holdings h ON p.id = h.portfolio_id
-- WHERE p.user_id = 'user@example.com'
-- GROUP BY p.id, p.file_name, p.upload_date;

-- Get holdings by ticker across all portfolios
-- SELECT ticker, SUM(shares) as total_shares, AVG(purchase_price) as avg_price
-- FROM holdings h
-- JOIN portfolios p ON h.portfolio_id = p.id
-- WHERE p.user_id = 'user@example.com'
-- GROUP BY ticker
-- ORDER BY total_shares DESC;
