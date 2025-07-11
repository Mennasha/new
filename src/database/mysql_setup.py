#!/usr/bin/env python3
"""
MySQL Database Setup Script for Bilsan Jewelry Project
This script creates the MySQL database and user if they don't exist.
"""

import mysql.connector
from mysql.connector import Error
import os
import sys

def create_database_and_user():
    """Create MySQL database and user for the application."""
    
    # MySQL connection parameters
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = os.environ.get('MYSQL_PORT', '3306')
    root_user = os.environ.get('MYSQL_ROOT_USER', 'root')
    root_password = os.environ.get('MYSQL_ROOT_PASSWORD', '')
    
    # Application database parameters
    db_name = os.environ.get('MYSQL_DATABASE', 'bilsan_jewelry')
    db_user = os.environ.get('MYSQL_USER', 'bilsan_user')
    db_password = os.environ.get('MYSQL_PASSWORD', 'bilsan_password')
    
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=root_user,
            password=root_password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Database '{db_name}' created or already exists.")
            
            # Create user if it doesn't exist
            cursor.execute(f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_password}'")
            print(f"User '{db_user}' created or already exists.")
            
            # Grant privileges
            cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            print(f"Privileges granted to user '{db_user}' on database '{db_name}'.")
            
            cursor.close()
            connection.close()
            print("MySQL setup completed successfully!")
            
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return False
    
    return True

def test_connection():
    """Test the database connection with application credentials."""
    
    host = os.environ.get('MYSQL_HOST', 'localhost')
    port = os.environ.get('MYSQL_PORT', '3306')
    db_name = os.environ.get('MYSQL_DATABASE', 'bilsan_jewelry')
    db_user = os.environ.get('MYSQL_USER', 'bilsan_user')
    db_password = os.environ.get('MYSQL_PASSWORD', 'bilsan_password')
    
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        if connection.is_connected():
            print("✅ Database connection test successful!")
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("Setting up MySQL database for Bilsan Jewelry Project...")
    print("=" * 50)
    
    if create_database_and_user():
        print("\nTesting database connection...")
        test_connection()
    else:
        print("❌ Database setup failed!")
        sys.exit(1)

