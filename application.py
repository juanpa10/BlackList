from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_marshmallow import Marshmallow
from datetime import datetime
import uuid

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blacklist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)

STATIC_TOKEN = "Bearer mysecrettoken"


# Modelo de datos para la lista negra
class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    app_uuid = db.Column(db.String(36), nullable=False)  # UUID (36 caracteres)
    blocked_reason = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)  # Soporta IPv4 e IPv6
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, email, app_uuid, blocked_reason, ip_address):
        self.email = email
        self.app_uuid = app_uuid
        self.blocked_reason = blocked_reason
        self.ip_address = ip_address


# Esquema para la serialización de datos usando Marshmallow
class BlacklistSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Blacklist


blacklist_schema = BlacklistSchema()
blacklists_schema = BlacklistSchema(many=True)


# Decorador para verificar el token de autorización
def token_required(func):
    from functools import wraps

    @wraps(func)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if auth != STATIC_TOKEN:
            return jsonify({'message': 'Token ausente o inválido'}), 401
        return func(*args, **kwargs)

    return decorated


# Endpoint para agregar un email a la lista negra: POST /blacklists
class BlacklistAdd(Resource):
    @token_required
    def post(self):
        data = request.get_json()
        if not data:
            return {'message': 'No se proporcionaron datos de entrada'}, 400

        email = data.get('email')
        app_uuid_value = data.get('app_uuid')
        blocked_reason = data.get('blocked_reason', None)

        if not email or not app_uuid_value:
            return {'message': 'Se requieren los campos email y app_uuid'}, 400

        try:
            uuid.UUID(app_uuid_value)
        except ValueError:
            return {'message': 'Formato inválido para app_uuid'}, 400

        ip_address = request.remote_addr or '0.0.0.0'

        new_black_email = Blacklist(email=email, app_uuid=app_uuid_value, blocked_reason=blocked_reason,
                                    ip_address=ip_address)
        db.session.add(new_black_email)
        db.session.commit()

        return {'message': 'Email agregado a la lista negra correctamente'}, 201


# Endpoint para consultar si un email está en la lista negra: GET /blacklists/<email>
class BlacklistCheck(Resource):
    @token_required
    def get(self, email):
        black_email = Blacklist.query.filter_by(email=email).first()
        if black_email:
            return {'blacklisted': True, 'blocked_reason': black_email.blocked_reason}, 200
        else:
            return {'blacklisted': False, 'blocked_reason': None}, 200


class HealthCheck(Resource):
    @staticmethod
    def get():
        return {'healthy': True}, 200


api.add_resource(BlacklistAdd, '/blacklists')
api.add_resource(BlacklistCheck, '/blacklists/<string:email>')
api.add_resource(HealthCheck, '/health')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
