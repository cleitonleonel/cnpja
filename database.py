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


def save(data):
    result_dict = check_existence(data)
    if not result_dict["result"]:
        cursor.execute("""
        INSERT INTO Users (
            email,
            api_key
            ) VALUES (?,?)
        """, (data["email"], data["key"]))
        connection.commit()
        result_dict["result"] = True
        result_dict["object"] = check_existence(data)["object"]
        result_dict["message"] = "Usuário cadastrado com sucesso!!!"
    else:
        result_dict["result"] = False
        result_dict["object"] = result_dict["object"]
        result_dict["message"] = result_dict["message"]
    cursor.close()
    return result_dict


def check_existence(data):
    user_email = data["email"]
    cursor.execute(f"SELECT * FROM Users WHERE email=?", (user_email,))
    rows = cursor.fetchall()
    users_list = []
    result_dict = {}
    for row in rows:
        users_list.append(dict(row))
    result_dict["result"] = False
    if len(users_list) > 0:
        result_dict["result"] = True
        result_dict["message"] = "Usuário já existe!!!"
    result_dict["object"] = users_list
    return result_dict


connection = get_db_connection("data/cnpja.db")
cursor = connection.cursor()
create_table()
