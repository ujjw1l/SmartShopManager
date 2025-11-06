import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """
    Establish and return a connection to the MySQL database.
    Make sure the MySQL server is running before calling this.
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='@Ujjw1lGupt1#',
            database="smartshopmanager"
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print("❌ Error while connecting to MySQL:", e)
        return None


def close_db_connection(connection):
    """
    Closes the database connection safely.
    """
    try:
        if connection.is_connected():
            connection.close()
    except Exception as e:
        print("⚠️ Error while closing the connection:", e)
