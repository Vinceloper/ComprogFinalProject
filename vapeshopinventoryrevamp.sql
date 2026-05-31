CREATE DATABASE IF NOT EXISTS VapeShop;
USE VapeShop;

-- ========== TABLES ==========

-- BRANDS
CREATE TABLE IF NOT EXISTS Brand (
  BrandID INT AUTO_INCREMENT PRIMARY KEY,
  BrandName VARCHAR(100) NOT NULL
);

-- Ensure brand names are unique (prevents duplicates)
ALTER TABLE Brand
  ADD UNIQUE KEY uq_brand_name (BrandName);

-- CATEGORIES
CREATE TABLE IF NOT EXISTS Category (
  CategoryID INT AUTO_INCREMENT PRIMARY KEY,
  CategoryName VARCHAR(100) NOT NULL
);

-- PRODUCTS
CREATE TABLE IF NOT EXISTS Product (
  ProductID INT AUTO_INCREMENT PRIMARY KEY,
  BrandID INT NOT NULL,
  CategoryID INT NOT NULL,
  ProductName VARCHAR(150) NOT NULL,
  Flavor VARCHAR(100),
  Quantity INT NOT NULL DEFAULT 0,
  Price DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_brand FOREIGN KEY (BrandID) REFERENCES Brand(BrandID),
  CONSTRAINT fk_category FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);

-- SALES
CREATE TABLE IF NOT EXISTS Sales (
  SaleID INT AUTO_INCREMENT PRIMARY KEY,
  ProductID INT NOT NULL,
  QuantitySold INT NOT NULL,
  TotalAmount DECIMAL(12,2) NOT NULL,
  SaleDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

-- USERS (for login/roles)
CREATE TABLE IF NOT EXISTS Users (
  UserID INT AUTO_INCREMENT PRIMARY KEY,
  Username VARCHAR(50) NOT NULL UNIQUE,
  PasswordHash CHAR(64) NOT NULL,
  Role ENUM('ADMIN','EMPLOYEE') NOT NULL
);

-- ========== OPTIONAL: CLEAR AND RESEED (comment out if you have data) ==========
-- Disable FK checks to reset tables
SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE Sales;
TRUNCATE TABLE Product;
TRUNCATE TABLE Brand;
TRUNCATE TABLE Category;
TRUNCATE TABLE Users;

SET FOREIGN_KEY_CHECKS = 1;

-- Seed categories
INSERT INTO Category (CategoryName)
VALUES ('Disposable Vape'), ('Vape Cartridge'), ('Vape Juice');

-- Seed default admin (password: admin123)
-- Stored as SHA2-256 to match the Python hashing
INSERT INTO Users (Username, PasswordHash, Role)
VALUES ('admin', SHA2('admin123', 256), 'ADMIN');

-- ========== VIEWS ==========
DROP VIEW IF EXISTS View_TotalInventory;
CREATE VIEW View_TotalInventory AS
SELECT 
  p.CategoryID,
  c.CategoryName,
  SUM(p.Quantity) AS TotalQuantity,
  SUM(p.Quantity * p.Price) AS TotalStockValue
FROM Product p
JOIN Category c ON p.CategoryID = c.CategoryID
GROUP BY p.CategoryID;

DROP VIEW IF EXISTS View_SalesSummary;
CREATE VIEW View_SalesSummary AS
SELECT 
  DATE(SaleDate) AS SaleDay,
  SUM(TotalAmount) AS DailySales,
  COUNT(*) AS Transactions
FROM Sales
GROUP BY DATE(SaleDate);














-- WARNING: This deletes all data in VapeShop.
DROP DATABASE IF EXISTS VapeShop;

-- Recreate everything fresh
CREATE DATABASE IF NOT EXISTS VapeShop;
USE VapeShop;

-- ========== TABLES ==========

-- BRANDS
CREATE TABLE IF NOT EXISTS Brand (
  BrandID INT AUTO_INCREMENT PRIMARY KEY,
  BrandName VARCHAR(100) NOT NULL
);

-- Ensure brand names are unique (prevents duplicates)
ALTER TABLE Brand
  ADD UNIQUE KEY uq_brand_name (BrandName);

-- CATEGORIES
CREATE TABLE IF NOT EXISTS Category (
  CategoryID INT AUTO_INCREMENT PRIMARY KEY,
  CategoryName VARCHAR(100) NOT NULL
);

-- PRODUCTS
CREATE TABLE IF NOT EXISTS Product (
  ProductID INT AUTO_INCREMENT PRIMARY KEY,
  BrandID INT NOT NULL,
  CategoryID INT NOT NULL,
  ProductName VARCHAR(150) NOT NULL,
  Flavor VARCHAR(100),
  Quantity INT NOT NULL DEFAULT 0,
  Price DECIMAL(10,2) NOT NULL,
  CONSTRAINT fk_brand FOREIGN KEY (BrandID) REFERENCES Brand(BrandID),
  CONSTRAINT fk_category FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
);

-- SALES
CREATE TABLE IF NOT EXISTS Sales (
  SaleID INT AUTO_INCREMENT PRIMARY KEY,
  ProductID INT NOT NULL,
  QuantitySold INT NOT NULL,
  TotalAmount DECIMAL(12,2) NOT NULL,
  SaleDate DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

-- USERS (for login/roles)
CREATE TABLE IF NOT EXISTS Users (
  UserID INT AUTO_INCREMENT PRIMARY KEY,
  Username VARCHAR(50) NOT NULL UNIQUE,
  PasswordHash CHAR(64) NOT NULL,
  Role ENUM('ADMIN','EMPLOYEE') NOT NULL
);

-- ========== SEED DATA ==========
INSERT INTO Category (CategoryName)
VALUES ('Disposable Vape'), ('Vape Cartridge'), ('Vape Juice');

-- Seed default admin (password: admin123) hashed with SHA2-256
INSERT INTO Users (Username, PasswordHash, Role)
VALUES ('admin', SHA2('admin123', 256), 'ADMIN');

-- ========== VIEWS ==========
DROP VIEW IF EXISTS View_TotalInventory;
CREATE VIEW View_TotalInventory AS
SELECT 
  p.CategoryID,
  c.CategoryName,
  SUM(p.Quantity) AS TotalQuantity,
  SUM(p.Quantity * p.Price) AS TotalStockValue
FROM Product p
JOIN Category c ON p.CategoryID = c.CategoryID
GROUP BY p.CategoryID;

DROP VIEW IF EXISTS View_SalesSummary;
CREATE VIEW View_SalesSummary AS
SELECT 
  DATE(SaleDate) AS SaleDay,
  SUM(TotalAmount) AS DailySales,
  COUNT(*) AS Transactions
FROM Sales
GROUP BY DATE(SaleDate);
