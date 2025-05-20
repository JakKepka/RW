import os
import sqlite3
import subprocess
import sys

def init_project():
    """Initialize the project environment"""
    print("Initializing Multi-Agent Action Programs Analysis System...")
    
    # Create directory structure
    directories = [
        'ui',
        'engine',
        'db',
        'tests',
        'assets'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Initialize database
    print("\nInitializing database...")
    try:
        with open('db/schema.sql', 'r') as f:
            schema = f.read()
        
        with sqlite3.connect('db/problems.db') as conn:
            conn.executescript(schema)
            print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False
    
    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed successfully")
    except Exception as e:
        print(f"Error installing dependencies: {str(e)}")
        return False
    
    print("\nProject initialization completed successfully!")
    print("\nYou can now run the application using:")
    print("python main.py")
    
    return True

if __name__ == "__main__":
    init_project() 