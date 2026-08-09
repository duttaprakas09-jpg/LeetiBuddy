import mysql.connector
import mysql.connector.pooling
from .leetcode_all_problems import fetch_all_problems
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT"))

# Resolve ca.pem relative to this file, not the current working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_PATH = os.path.join(BASE_DIR, "ca.pem")

pool = None  # created lazily by init_db()


def database_setup(conn):
    cursor = conn.cursor(buffered=True)

    cursor.execute("SHOW TABLES")
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute('''
            CREATE TABLE problem_list (
                leetcode_id INT PRIMARY KEY,
                title VARCHAR(150),
                difficulty VARCHAR(6)
            )
        ''')
        cursor.execute('''
            CREATE TABLE user_info (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(200),
                leetcode_username VARCHAR(200),
                password VARCHAR(60)
            )
        ''')
        cursor.execute('''
        CREATE TABLE completed_list
        (leetcode_id INT, user_id INT, approach VARCHAR(200),
        FOREIGN KEY (leetcode_id) REFERENCES problem_list(leetcode_id), 
        FOREIGN KEY (user_id) REFERENCES user_info(user_id),
        PRIMARY KEY(leetcode_id, user_id, approach));
        ''')

        data = fetch_all_problems()
        cursor.executemany(
            "INSERT INTO problem_list VALUES (%s, %s, %s)",
            data
        )
    else:
        data = fetch_all_problems()
        api_length = len(data)

        cursor.execute("SELECT COUNT(*) FROM problem_list")
        database_length = cursor.fetchone()[0]

        if api_length != database_length:
            cursor.executemany(
                "INSERT INTO problem_list VALUES (%s, %s, %s)",
                data[database_length:]
            )

    conn.commit()
    cursor.close()


def init_db():
    """
    Runs schema setup/bootstrap and creates the connection pool.
    Called explicitly (e.g. on FastAPI startup), NOT at import time,
    so importing this module never touches the network.
    """
    global pool

    if pool is not None:
        return  # already initialized, don't redo it

    try:
        _setup_conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            ssl_ca=CA_PATH,
            ssl_verify_cert=True,
            use_pure=True
        )
    except Exception:
        _bootstrap_conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            ssl_ca=CA_PATH,
            ssl_verify_cert=True,
            use_pure=True
        )
        _cursor = _bootstrap_conn.cursor()
        _cursor.execute(f'create database {DB_NAME}')
        _cursor.close()
        _bootstrap_conn.close()

        _setup_conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            ssl_ca=CA_PATH,
            ssl_verify_cert=True,
            use_pure=True
        )

    database_setup(_setup_conn)
    _setup_conn.close()

    pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="tracker_pool",
        pool_size=5,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        ssl_ca=CA_PATH,
        ssl_verify_cert=True,
        use_pure=True
    )


def connect_db():
    if pool is None:
        init_db()

    conn = pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()