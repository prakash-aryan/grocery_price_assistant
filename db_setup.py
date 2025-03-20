import psycopg2
from config import get_db_connection, CURRENCY, CURRENCY_SYMBOL

def setup_database():
    """
    Set up the PostgreSQL database with grocery items and their prices in INR.
    
    This function:
    1. Connects to the PostgreSQL database
    2. Creates the grocery_items table if it doesn't exist
    3. Populates the table with 20 sample grocery items with prices in INR
    """
    # Connect to the database
    conn = psycopg2.connect(**get_db_connection())
    conn.autocommit = True
    cursor = conn.cursor()

    # Create table for grocery items with price in INR
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grocery_items (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        category VARCHAR(50),
        unit VARCHAR(20),
        currency VARCHAR(3) DEFAULT 'INR'
    );
    """)

    # Sample grocery items with prices in INR
    grocery_items = [
        ("Milk", 65.00, "Dairy", "1 liter"),
        ("Bread", 40.00, "Bakery", "1 packet"),
        ("Eggs", 80.00, "Dairy", "12 count"),
        ("Apples", 180.00, "Produce", "1 kg"),
        ("Bananas", 60.00, "Produce", "1 dozen"),
        ("Chicken Breast", 320.00, "Meat", "1 kg"),
        ("Rice", 75.00, "Grains", "1 kg bag"),
        ("Atta (Wheat Flour)", 60.00, "Grains", "1 kg"),
        ("Tomatoes", 40.00, "Produce", "1 kg"),
        ("Potatoes", 30.00, "Produce", "1 kg"),
        ("Onions", 25.00, "Produce", "1 kg"),
        ("Paneer", 80.00, "Dairy", "200 gm"),
        ("Curd", 45.00, "Dairy", "500 gm"),
        ("Tea", 120.00, "Beverages", "250 gm"),
        ("Sugar", 45.00, "Essentials", "1 kg"),
        ("Cooking Oil", 180.00, "Essentials", "1 liter"),
        ("Dal (Lentils)", 110.00, "Pulses", "1 kg"),
        ("Biscuits", 30.00, "Snacks", "1 packet"),
        ("Salt", 20.00, "Essentials", "1 kg"),
        ("Green Chillies", 15.00, "Produce", "100 gm"),
    ]

    # Clear existing data and insert new items
    cursor.execute("TRUNCATE TABLE grocery_items RESTART IDENTITY;")

    for item in grocery_items:
        cursor.execute(
            "INSERT INTO grocery_items (name, price, category, unit, currency) VALUES (%s, %s, %s, %s, %s)",
            (*item, CURRENCY)
        )

    # Verify the data
    cursor.execute("SELECT * FROM grocery_items;")
    items = cursor.fetchall()
    print(f"Inserted {len(items)} grocery items into the database with prices in {CURRENCY}.")
    
    # Display a few sample items for verification
    print("\nSample items:")
    for i in range(min(5, len(items))):
        print(f"{items[i][1]}: {CURRENCY_SYMBOL}{items[i][2]} per {items[i][4]}")

    # Close the connection
    cursor.close()
    conn.close()
    
    return len(items)

if __name__ == "__main__":
    print(f"Setting up database with grocery prices in {CURRENCY}...")
    num_items = setup_database()
    print(f"Database setup complete with {num_items} grocery items.")