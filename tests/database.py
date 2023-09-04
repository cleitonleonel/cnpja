import os
import sqlite3

BASE_DIR = os.getcwd()

if not os.path.exists(os.path.join(BASE_DIR, 'data')):
    os.makedirs(os.path.join(BASE_DIR, 'data'))


def get_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            api_key TEXT NOT NULL,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
    """)


def save_user(email, api_key):
    result_dict = check_existence(email)
    if not result_dict["result"]:
        cursor.execute("""
        INSERT INTO Users (
            email,
            api_key
            ) VALUES (?,?)
        """, (email, api_key))
        connection.commit()
        result_dict["result"] = True
        result_dict["object"] = check_existence(email)["object"]
        result_dict["message"] = "Usuário cadastrado com sucesso!!!"
    else:
        result_dict["result"] = False
        result_dict["object"] = result_dict["object"]
        result_dict["message"] = result_dict["message"]
    cursor.close()
    return result_dict


def check_existence(email):
    user_email = email
    cursor.execute(f"SELECT * FROM Users WHERE email=?", (user_email,))
    user = cursor.fetchone()
    result_dict = {}
    result_dict["result"] = False
    if user and len(user) > 0:
        result_dict["result"] = True
        result_dict["message"] = "Usuário já existe!!!"
        result_dict["object"] = dict(user)
    return result_dict


connection = get_db_connection("data/pycnpj.db")
cursor = connection.cursor()
create_table()
