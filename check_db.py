# check_db.py
import sqlite3
import os

def check_categories():
    try:
        # Check if the database file exists
        if not os.path.exists('finance.db'):
            print("Database file 'finance.db' does not exist!")
            return
            
        print(f"Database file exists, size: {os.path.getsize('finance.db')} bytes")
        
        # Connect to the database
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        
        # Check if the categories table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        if not cursor.fetchone():
            print("The 'categories' table does not exist in the database!")
            conn.close()
            return
        
        # Query the categories table
        cursor.execute('SELECT id, name, transaction_type FROM categories')
        rows = cursor.fetchall()
        
        # Print the results
        print("Categories in the database:")
        print("--------------------------")
        if rows:
            for row in rows:
                print(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
        else:
            print("No categories found in the database.")
        
        # Close the connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_categories() 