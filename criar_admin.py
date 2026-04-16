from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():

    # verifica se já existe
    admin_existente = Usuario.query.filter_by(email="admin@metafarma.com").first()

    if admin_existente:
        print("Admin já existe!")
    else:
        admin = Usuario(
            nome="Administrador",
            email="admin@metafarma.com"
        )
        admin.set_senha("123456")

        db.session.add(admin)
        db.session.commit()

        print("Admin criado com sucesso!")