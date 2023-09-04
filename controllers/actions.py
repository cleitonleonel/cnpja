from models.user import db, User
from sqlalchemy.exc import IntegrityError


def save_user(email, api_key):
    user = User(email=email, api_key=api_key)
    db.session.add(user)
    try:
        db.session.commit()
        return {
            "result": True,
            "object": {
                "api_key": api_key
            },
            "message": "Usuário cadastrado com sucesso!"
        }
    except IntegrityError:
        db.session.rollback()
        return {"result": False, "message": "Usuário já existe!"}


def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return {
            "result": True,
            "object": {
                "id": user.id,
                "email": user.email,
                "api_key": user.api_key,
                "created": user.created.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    else:
        return {"result": False, "message": "Usuário não encontrado!"}


def get_all_users():
    users = User.query.all()
    if users:
        user_list = []
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "api_key": user.api_key,
                "created": user.created.strftime("%Y-%m-%d %H:%M:%S")
            }
            user_list.append(user_data)

        return {
            "result": True,
            "object": user_list
        }
    else:
        return {"result": False, "message": "Nenhum usuário encontrado!"}
