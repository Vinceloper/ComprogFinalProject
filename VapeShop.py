import mysql.connector
from mysql.connector import Error   
from datetime import datetime
import getpass
import hashlib
import sys

# ==================================================
# MODULE 1: IMPORTS AND CONFIGURATION
# ==================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "VapeShop"
}

CRITICAL_STOCK_THRESHOLD = 5  # Qty <= threshold is critical

# ==================================================
# MODULE 2: UTILITY FUNCTIONS
# ==================================================
def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def validate_positive_int(text: str, allow_zero: bool = False) -> int:
    try:
        val = int(text)
        if allow_zero and val >= 0:
            return val
        if not allow_zero and val > 0:
            return val
        raise ValueError
    except ValueError:
        raise ValueError("Please enter a valid positive integer{}."
                         .format(" (zero allowed)" if allow_zero else ""))

def validate_positive_float(text: str, allow_zero: bool = False) -> float:
    try:
        val = float(text)
        if allow_zero and val >= 0.0:
            return val
        if not allow_zero and val > 0.0:
            return val
        raise ValueError
    except ValueError:
        raise ValueError("Please enter a valid positive number{}."
                         .format(" (zero allowed)" if allow_zero else ""))

def safe_upper(s: str):
    return s.strip().upper()

# ==================================================
# MODULE 3: DATABASE CONNECTION MODULE
# ==================================================
def create_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("\nConnected to VapeShop database.\n")
        return conn
    except Error as e:
        print(f"Connection Error: {e}")
        return None

# ==================================================
# MODULE 4: USER AUTHENTICATION MODULE
# ==================================================
def ensure_minimum_data(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Category")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO Category (CategoryName) VALUES (%s)",
                [("Disposable Vape",), ("Vape Cartridge",), ("Vape Juice",)]
            )
            conn.commit()
            print("Initialized default categories.")
    except Error:
        pass

    try:
        cursor.execute("SELECT COUNT(*) FROM Users")
        u_count = cursor.fetchone()[0]
        if u_count == 0:
            cursor.execute(
                "INSERT INTO Users (Username, PasswordHash, Role) VALUES (%s, %s, %s)",
                ("admin", hash_password("admin123"), "ADMIN")
            )
            conn.commit()
            print("Created default admin 'admin' with password 'admin123'. Please change it.")
    except Error:
        pass

def login(conn):
    print("========= LOGIN =========")
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT UserID, Username, PasswordHash, Role FROM Users WHERE Username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            print("Invalid username or password.\n")
            return None
        _, uname, pwd_hash, role = row
        if hash_password(password) != pwd_hash:
            print("Invalid username or password.\n")
            return None
        print(f"Welcome, {uname} ({role}).\n")
        return {"username": uname, "role": role}
    except Error as e:
        print(f"Login error: {e}\n")
        return None

def change_password(conn, user):
    print("========= CHANGE PASSWORD =========")
    current = getpass.getpass("Current password: ")
    cursor = conn.cursor()
    cursor.execute("SELECT PasswordHash FROM Users WHERE Username = %s", (user["username"],))
    row = cursor.fetchone()
    if not row:
        print("User not found.\n")
        return
    if hash_password(current) != row[0]:
        print("Current password is incorrect.\n")
        return
    new1 = getpass.getpass("New password: ")
    new2 = getpass.getpass("Confirm new password: ")
    if not new1.strip() or new1 != new2:
        print("Passwords do not match or blank.\n")
        return
    cursor.execute("UPDATE Users SET PasswordHash = %s WHERE Username = %s",
                   (hash_password(new1), user["username"]))
    conn.commit()
    print("Password updated successfully.\n")

def create_user(conn, user):
    if user["role"] != "ADMIN":
        print("Only ADMIN can create users.\n")
        return
    print("========= CREATE USER =========")
    username = input("New username: ").strip()
    role = input("Role (ADMIN/EMPLOYEE): ").strip().upper()
    if role not in ("ADMIN", "EMPLOYEE"):
        print("Invalid role.\n")
        return
    password = getpass.getpass("Temporary password: ")
    if not password.strip():
        print("Password cannot be blank.\n")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Users (Username, PasswordHash, Role) VALUES (%s, %s, %s)",
                       (username, hash_password(password), role))
        conn.commit()
        print(f"User '{username}' with role '{role}' created.\n")
    except Error as e:
        print(f"Create user failed: {e}\n")

# ============== FEATURES SUMMARY ==============
#def show_features():
#    print("FEATURES SUMMARY")
#    print("{:<25}{}".format("Feature", "Description"))
#    print("-" * 75)
#    features = [
#        ("Login (Admin/Employee)", "Role-based menus and permissions."),
#        ("Brands / Categories", "Choose existing brand or add new brand."),
#        ("Add Product", "Add product without quantity."),
#        ("Add Stock Quantity", "Separate option to add stock to a product."),
#        ("Update (Limited)", "Only Quantity(add), Price, ProductName, Flavor."),
#        ("Process Sales", "Rejects negative qty; updates stock; logs transactions."),
#        ("Critical Stock", f"Shows products with qty <= {CRITICAL_STOCK_THRESHOLD}."),
#        ("View Inventory", "Lists products with total stock value."),
#        ("View Sales History", "All sales with timestamps and totals."),
#        ("User Management", "Admin: create users; all: change own password.")
#    
#    for f in features:
#        print(f"{f[0]:<25}{f[1]}")
#    print("-" * 75 + "\n")

# ==================================================
# MODULE 5: BRAND MANAGEMENT MODULE
# ==================================================
def ensure_brand(conn, brand_name):
    cursor = conn.cursor()
    cursor.execute("SELECT BrandID FROM Brand WHERE BrandName = %s", (brand_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    try:
        cursor.execute("INSERT INTO Brand (BrandName) VALUES (%s)", (brand_name,))
        conn.commit()
        print(f"Created new brand '{brand_name}'.")
        return cursor.lastrowid
    except Error as e:
        # If duplicate due to simultaneous insert, reselect
        cursor.execute("SELECT BrandID FROM Brand WHERE BrandName = %s", (brand_name,))
        r = cursor.fetchone()
        if r:
            return r[0]
        else:
            print(f"Tanga may gan'yan ng brand!: {e}")
            raise

def pick_category(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT CategoryID, CategoryName FROM Category ORDER BY CategoryID")
    cats = cursor.fetchall()
    if not cats:
        print("No categories found.")
        return None
    print("Select Category:")
    for cid, cname in cats:
        print(f"{cid}. {cname}")
    while True:
        choice = input("Enter category ID: ").strip()
        try:
            val = int(choice)
            if any(val == c[0] for c in cats):
                return val
            else:
                print("Invalid category ID.")
        except ValueError:
            print("Enter a valid number.")

def pick_existing_brand(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT BrandID, BrandName FROM Brand ORDER BY BrandName")
    rows = cursor.fetchall()
    if not rows:
        print("No existing brands yet.")
        return None
    print("Existing Brands:")
    for bid, bname in rows:
        print(f"{bid}. {bname}")
    while True:
        choice = input("Enter brand ID: ").strip()
        if not choice.isdigit():
            print("Enter a valid number.")
            continue
        bid = int(choice)
        if any(bid == r[0] for r in rows):
            return bid
        print("Invalid brand ID.")

def choose_brand_flow(conn):
    print("Brand selection:")
    print("1. Use existing brand")
    print("2. Add new brand")
    while True:
        ch = input("Select option (1/2): ").strip()
        if ch == "1":
            bid = pick_existing_brand(conn)
            if bid is None:
                print("No brand selected.\n")
                return None
            return bid
        elif ch == "2":
            bname = safe_upper(input("Enter NEW Brand Name: "))
            if not bname:
                print("Brand name cannot be empty.")
                continue
            return ensure_brand(conn, bname)
        else:
            print("Invalid choice.")

# ==================================================
# MODULE 6: PRODUCT MANAGEMENT MODULE
# ==================================================
# ADD PRODUCT
def add_product(conn):
    cursor = conn.cursor()

    brand_id = choose_brand_flow(conn)
    if brand_id is None:
        return

    category_id = pick_category(conn)
    if category_id is None:
        return

    product_name = safe_upper(input("Enter Product Name: "))
    if not product_name:
        print("Product name cannot be empty.\n")
        return
    flavor_raw = input("Enter Flavor (optional): ").strip()
    flavor = safe_upper(flavor_raw) if flavor_raw else None

    try:
        price = validate_positive_float(input("Enter Price: "), allow_zero=False)
    except ValueError as e:
        print(str(e) + "\n")
        return

    # Quantity is NOT asked here; defaults to 0.
    query = """
        INSERT INTO Product (BrandID, CategoryID, ProductName, Flavor, Quantity, Price)
        VALUES (%s, %s, %s, %s, 0, %s)
    """
    try:
        cursor.execute(query, (brand_id, category_id, product_name, flavor, price))
        conn.commit()
        print("Product added successfully with initial Quantity = 0.\n")
    except Error as e:
        print(f"Add product failed: {e}\n")

# ==================================================
# MODULE 7: STOCK MANAGEMENT MODULE
# ==================================================
# ADD STOCK QUANTITY
def add_stock_quantity(conn):
    cursor = conn.cursor()
    pid = input("Enter Product ID to add stock: ").strip()
    if not pid.isdigit():
        print("Invalid Product ID.\n")
        return
    try:
        add_qty = validate_positive_int(input("Enter quantity to ADD: "), allow_zero=False)
    except ValueError as e:
        print(str(e) + "\n")
        return

    # Fetch current
    cursor.execute("SELECT Quantity FROM Product WHERE ProductID = %s", (pid,))
    row = cursor.fetchone()
    if not row:
        print("Product not found.\n")
        return
    current_qty = row[0]
    new_qty = current_qty + add_qty
    try:
        cursor.execute("UPDATE Product SET Quantity = %s WHERE ProductID = %s", (new_qty, pid))
        conn.commit()
        print(f"Stock updated. Previous: {current_qty}, Added: {add_qty}, New: {new_qty}\n")
    except Error as e:
        print(f"Add stock failed: {e}\n")

# ==================================================
# MODULE 8: INVENTORY MONITORING MODULE
# ==================================================
def view_products(conn):
    cursor = conn.cursor()
    query = """SELECT p.ProductID, b.BrandName, c.CategoryName, 
                      p.ProductName, p.Flavor, p.Quantity, p.Price, (p.Price * p.Quantity) AS TotalValue
               FROM Product p
               JOIN Brand b ON p.BrandID = b.BrandID
               JOIN Category c ON p.CategoryID = c.CategoryID
               ORDER BY c.CategoryID, b.BrandName, p.ProductName"""
    cursor.execute(query)
    data = cursor.fetchall()

    if not data:
        print("No products available.\n")
        return

    print("\n======== INVENTORY LIST ========")
    print("{:<4} | {:<20} | {:<15} | {:<24} | {:<10} | {:<8} | {:<10}".format(
        "ID", "Brand", "Category", "Product", "Qty", "Price", "Value"
    ))
    print("-" * 100)
    for row in data:
        pid, brand, cat, name, flavor, qty, price, total = row
        pname = f"{name} ({flavor})" if flavor else name
        print(f"{pid:<4} | {brand:<20} | {cat:<15} | {pname:<24} | {qty:<10} | {price:<8.2f} | {total:<10.2f}")
    print("-" * 100 + "\n")

# ==================================================
# MODULE 9: CRITICAL STOCK MONITORING MODULE
# ==================================================
def view_critical_stock(conn):
    cursor = conn.cursor()
    query = """SELECT p.ProductID, b.BrandName, c.CategoryName, p.ProductName, p.Flavor, p.Quantity
               FROM Product p
               JOIN Brand b ON p.BrandID = b.BrandID
               JOIN Category c ON p.CategoryID = c.CategoryID
               WHERE p.Quantity <= %s
               ORDER BY p.Quantity ASC, b.BrandName, p.ProductName"""
    cursor.execute(query, (CRITICAL_STOCK_THRESHOLD,))
    rows = cursor.fetchall()
    if not rows:
        print("No critically stocked products.\n")
        return
    print("\n====== CRITICALLY STOCKED PRODUCTS (<= {}) ======".format(CRITICAL_STOCK_THRESHOLD))
    print("{:<4} | {:<20} | {:<15} | {:<24} | {:<5}".format("ID", "Brand", "Category", "Product", "Qty"))
    print("-" * 90)
    for pid, brand, cat, name, flavor, qty in rows:
        pname = f"{name} ({flavor})" if flavor else name
        print(f"{pid:<4} | {brand:<20} | {cat:<15} | {pname:<24} | {qty:<5}")
    print("-" * 90 + "\n")

# ==================================================
# MODULE 10: PRODUCT UPDATE MODULE
# ==================================================
def update_product(conn):
    cursor = conn.cursor()
    pid = input("Enter Product ID to update: ").strip()
    if not pid.isdigit():
        print("Invalid Product ID.\n")
        return

    print("You can update only: Quantity(add), Price, ProductName, Flavor")
    print("1. Add to Quantity")
    print("2. Update Price")
    print("3. Update ProductName")
    print("4. Update Flavor")
    choice = input("Select option: ").strip()

    try:
        if choice == "1":
            # Additive quantity only
            cursor.execute("SELECT Quantity FROM Product WHERE ProductID = %s", (pid,))
            row = cursor.fetchone()
            if not row:
                print("Product not found.\n")
                return
            current_qty = row[0]
            add_qty = validate_positive_int(input("Enter quantity to ADD: "), allow_zero=False)
            new_qty = current_qty + add_qty
            cursor.execute("UPDATE Product SET Quantity = %s WHERE ProductID = %s", (new_qty, pid))
            conn.commit()
            print(f"Quantity updated. Previous: {current_qty}, Added: {add_qty}, New: {new_qty}\n")

        elif choice == "2":
            new_price = validate_positive_float(input("Enter new Price: "), allow_zero=False)
            cursor.execute("UPDATE Product SET Price = %s WHERE ProductID = %s", (new_price, pid))
            conn.commit()
            print("Price updated.\n")

        elif choice == "3":
            new_name = safe_upper(input("Enter new Product Name: "))
            if not new_name:
                print("Product name cannot be empty.\n")
                return
            cursor.execute("UPDATE Product SET ProductName = %s WHERE ProductID = %s", (new_name, pid))
            conn.commit()
            print("Product name updated.\n")

        elif choice == "4":
            raw = input("Enter new Flavor (blank to set NULL): ").strip()
            new_flavor = safe_upper(raw) if raw else None
            cursor.execute("UPDATE Product SET Flavor = %s WHERE ProductID = %s", (new_flavor, pid))
            conn.commit()
            print("Flavor updated.\n")

        else:
            print("Invalid option.\n")
            return

        if cursor.rowcount == 0:
            print("Product not found or no changes made.\n")

    except ValueError as ve:
        print(str(ve) + "\n")
    except Error as e:
        print(f"Update failed: {e}\n")

# ==================================================
# MODULE 11: PRODUCT DELETION MODULE
# ==================================================
def delete_product(conn):
    cursor = conn.cursor()
    pid = input("Enter Product ID to delete: ").strip()
    if not pid.isdigit():
        print("Invalid Product ID.\n")
        return
    try:
        cursor.execute("DELETE FROM Product WHERE ProductID = %s", (pid,))
        conn.commit()
        if cursor.rowcount > 0:
            print("Product deleted.\n")
        else:
            print("Product not found.\n")
    except Error as e:
        print(f"Delete failed: {e}\n")

# ==================================================
# MODULE 12: SALES PROCESSING MODULE
# ==================================================
def process_sale(conn):
    cursor = conn.cursor()
    try:
        pid = int(input("Enter Product ID: "))
    except ValueError:
        print("Invalid Product ID.\n")
        return
    try:
        qty = validate_positive_int(input("Quantity Sold: "), allow_zero=False)
    except ValueError as e:
        print(str(e) + " Negative numbers are not allowed for sales.\n")
        return

    cursor.execute("SELECT Quantity, Price FROM Product WHERE ProductID = %s", (pid,))
    product = cursor.fetchone()
    if not product:
        print("Product not found.\n")
        return

    stock, price = product
    if qty > stock:
        print(f"Not enough stock in inventory. Available: {stock}\n")
        return

    total = qty * price
    new_stock = stock - qty
    try:
        cursor.execute("UPDATE Product SET Quantity = %s WHERE ProductID = %s", (new_stock, pid))
        cursor.execute(
            "INSERT INTO Sales (ProductID, QuantitySold, TotalAmount, SaleDate) VALUES (%s, %s, %s, %s)",
            (pid, qty, total, datetime.now())
        )
        conn.commit()
        print(f"Sale recorded (₱{total:.2f}). New stock: {new_stock}\n")
    except Error as e:
        print(f"Sale failed: {e}\n")

# ==================================================
# MODULE 13: SALES REPORTING MODULE
# ==================================================
def view_sales(conn):
    cursor = conn.cursor()
    cursor.execute("""SELECT s.SaleID, p.ProductName, s.QuantitySold, s.TotalAmount, s.SaleDate
                      FROM Sales s
                      JOIN Product p ON s.ProductID = p.ProductID
                      ORDER BY s.SaleDate DESC""")
    data = cursor.fetchall()
    if not data:
        print("No sales found.\n")
        return
    print("\n====== SALES HISTORY ======")
    print("{:<5} | {:<24} | {:<10} | {:<12} | {:<20}".format("ID", "Product", "Qty", "Total", "Date"))
    print("-" * 80)
    for row in data:
        sid, pname, qty, total, date = row
        date_str = date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(date, "strftime") else str(date)
        print(f"{sid:<5} | {pname:<24} | {qty:<10} | {total:<12.2f} | {date_str:<20}")
    print("-" * 80 + "\n")

# ==================================================
# MODULE 14: SYSTEM MENU MODULE
# ==================================================
def admin_menu(conn, user):
    while True:
        print("========= VAPE SHOP INVENTORY SYSTEM (ADMIN) =========")
        print("1. Add Product (choose or add brand)")
        print("2. Add Stock Quantity")
        print("3. Update Product (Qty add only, Price, Name, Flavor)")
        print("4. Delete Product")
        print("5. View Inventory")
        print("6. Record Sale")
        print("7. View Sales History")
        print("8. View Critically Stocked Products")
        print("9. Create User")
        print("10. Change My Password")
        print("0. Logout / Exit")
        print("======================================================")
        choice = input("Select option: ").strip()
        print()

        if choice == "1":
            add_product(conn)
        elif choice == "2":
            add_stock_quantity(conn)
        elif choice == "3":
            update_product(conn)
        elif choice == "4":
            delete_product(conn)
        elif choice == "5":
            view_products(conn)
        elif choice == "6":
            process_sale(conn)
        elif choice == "7":
            view_sales(conn)
        elif choice == "8":
            view_critical_stock(conn)
        elif choice == "9":
            create_user(conn, user)
        elif choice == "10":
            change_password(conn, user)
        elif choice == "0":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice.\n")

def employee_menu(conn, user):
    while True:
        print("========= VAPE SHOP INVENTORY SYSTEM (EMPLOYEE) =========")
        print("1. Add Product (choose or add brand)")
        print("2. Add Stock Quantity")
        print("3. Update Product (Qty add only, Price, Name, Flavor)")
        print("4. View Inventory")
        print("5. Record Sale")
        print("6. View Sales History")
        print("7. View Critically Stocked Products")
        print("8. Change My Password")
        print("0. Logout / Exit")
        print("=========================================================")
        choice = input("Select option: ").strip()
        print()

        if choice == "1":
            add_product(conn)
        elif choice == "2":
            add_stock_quantity(conn)
        elif choice == "3":
            update_product(conn)
        elif choice == "4":
            view_products(conn)
        elif choice == "5":
            process_sale(conn)
        elif choice == "6":
            view_sales(conn)
        elif choice == "7":
            view_critical_stock(conn)
        elif choice == "8":
            change_password(conn, user)
        elif choice == "0":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice.\n")

# ==================================================
# MODULE 15: MAIN PROGRAM MODULE
# ==================================================
def main():
    conn = create_connection()
    if not conn:
        sys.exit(1)

    ensure_minimum_data(conn)
    #show_features()

    while True:
        user = login(conn)
        if not user:
            retry = input("Try again? (y/n): ").strip().lower()
            print()
            if retry != "y":
                break
            continue

        if user["role"] == "ADMIN":
            admin_menu(conn, user)
        else:
            employee_menu(conn, user)

        again = input("Exit program? (y/n): ").strip().lower()
        print()
        if again == "y":
            break

    conn.close()
    print("Goodbye!")

if __name__ == "__main__":
    main()
