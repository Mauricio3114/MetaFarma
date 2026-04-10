from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    db.create_all()

    email = input("E-mail do admin: ").strip().lower()
    nome = input("Nome do admin: ").strip()
    senha = input("Senha do admin: ").strip()

    existente = Usuario.query.filter_by(email=email).first()

    if existente:
        print("Já existe um usuário com esse e-mail.")
    else:
        usuario = Usuario(nome=nome, email=email, ativo=True)
        usuario.set_senha(senha)

        db.session.add(usuario)
        db.session.commit()

        print("Admin criado com sucesso.")