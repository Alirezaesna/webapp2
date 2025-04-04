"""
PostgreSQL Database Backup and Restore Utilities

This module provides functions to backup and restore PostgreSQL database
using SQL dump files.
"""
import os
import subprocess
import logging
from datetime import datetime

def get_db_connection_params():
    """Get database connection parameters from environment variables."""
    return {
        'dbname': os.environ.get('PGDATABASE', ''),
        'user': os.environ.get('PGUSER', ''),
        'password': os.environ.get('PGPASSWORD', ''),
        'host': os.environ.get('PGHOST', ''),
        'port': os.environ.get('PGPORT', '')
    }

def backup_database(output_file=None):
    """
    Create a backup of the PostgreSQL database using pg_dump.
    
    Args:
        output_file (str, optional): Path to save the backup file.
            If not provided, a default name with timestamp will be used.
            
    Returns:
        str: Path to the backup file if successful, None otherwise.
    """
    # Get database connection parameters
    db_params = get_db_connection_params()
    
    # Set default output file if not provided
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'data/pg_backup_{timestamp}.sql'
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Set environment variables for pg_dump
    env = os.environ.copy()
    if db_params['password']:
        env['PGPASSWORD'] = db_params['password']
    
    # Prepare the pg_dump command
    cmd = [
        'pg_dump',
        '-h', db_params['host'],
        '-p', db_params['port'],
        '-U', db_params['user'],
        '-d', db_params['dbname'],
        '-f', output_file,
        '-v',  # Verbose output
        '--clean',  # Clean (drop) database objects before recreating
        '--if-exists',  # Add IF EXISTS to DROP commands
        '--no-owner',  # Skip restoration of object ownership
    ]
    
    try:
        # Execute pg_dump
        logging.info(f"Creating database backup to {output_file}")
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logging.info(f"Database backup completed successfully: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        logging.error(f"Database backup failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during database backup: {e}")
        return None

def restore_database(backup_file):
    """
    Restore a PostgreSQL database from a backup file using psql.
    
    Args:
        backup_file (str): Path to the backup file to restore from.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(backup_file):
        logging.error(f"Backup file not found: {backup_file}")
        return False
    
    # Get database connection parameters
    db_params = get_db_connection_params()
    
    # Set environment variables for psql
    env = os.environ.copy()
    if db_params['password']:
        env['PGPASSWORD'] = db_params['password']
    
    # Prepare the psql command
    cmd = [
        'psql',
        '-h', db_params['host'],
        '-p', db_params['port'],
        '-U', db_params['user'],
        '-d', db_params['dbname'],
        '-f', backup_file,
        '-v',  # Verbose output
    ]
    
    try:
        # Execute psql
        logging.info(f"Restoring database from {backup_file}")
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logging.info("Database restoration completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Database restoration failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error during database restoration: {e}")
        return False

def list_tables():
    """
    List all tables in the PostgreSQL database.
    
    Returns:
        list: List of table names
    """
    # Get database connection parameters
    db_params = get_db_connection_params()
    
    # Set environment variables for psql
    env = os.environ.copy()
    if db_params['password']:
        env['PGPASSWORD'] = db_params['password']
    
    # Prepare the psql command to list tables
    cmd = [
        'psql',
        '-h', db_params['host'],
        '-p', db_params['port'],
        '-U', db_params['user'],
        '-d', db_params['dbname'],
        '-c', "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
        '-t',  # Tuples only (no headers)
    ]
    
    try:
        # Execute psql
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        tables = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tables
    except Exception as e:
        logging.error(f"Error listing tables: {e}")
        return []

def table_row_count(table_name):
    """
    Get the number of rows in a table.
    
    Args:
        table_name (str): Name of the table
        
    Returns:
        int: Number of rows in the table, or -1 if error
    """
    # Get database connection parameters
    db_params = get_db_connection_params()
    
    # Set environment variables for psql
    env = os.environ.copy()
    if db_params['password']:
        env['PGPASSWORD'] = db_params['password']
    
    # Prepare the psql command to count rows
    cmd = [
        'psql',
        '-h', db_params['host'],
        '-p', db_params['port'],
        '-U', db_params['user'],
        '-d', db_params['dbname'],
        '-c', f"SELECT COUNT(*) FROM {table_name}",
        '-t',  # Tuples only (no headers)
    ]
    
    try:
        # Execute psql
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        count = int(result.stdout.strip())
        return count
    except Exception as e:
        logging.error(f"Error counting rows in {table_name}: {e}")
        return -1

def get_db_statistics():
    """
    Get statistics about the database.
    
    Returns:
        dict: Database statistics
    """
    stats = {
        'tables': {},
        'total_rows': 0
    }
    
    tables = list_tables()
    for table in tables:
        row_count = table_row_count(table)
        stats['tables'][table] = row_count
        if row_count > 0:
            stats['total_rows'] += row_count
    
    return stats