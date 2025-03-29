from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blacklist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

STATIC_TOKEN = "Bearer blackSecretToken"


# Modelo de datos para la lista negra
class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    app_uuid = db.Column(db.String(36), nullable=False)
    blocked_reason = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, email, app_uuid, blocked_reason, ip_address):
        self.email = email
        self.app_uuid = app_uuid
        self.blocked_reason = blocked_reason
        self.ip_address = ip_address


# Decorador para verificar el token de autorización
def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if auth != STATIC_TOKEN:
            return jsonify({'message': 'Token ausente o inválido'}), 401
        return func(*args, **kwargs)

    return decorated


# Endpoint para agregar un email a la lista negra (POST /blacklists)
@app.route('/blacklists', methods=['POST'])
@token_required
def add_blacklist():
    data = request.get_json(force=True)
    if not data:
        return jsonify({'message': 'No se proporcionaron datos de entrada'}), 400

    email = data.get('email')
    app_uuid_value = data.get('app_uuid')
    blocked_reason = data.get('blocked_reason')

    if not email or not app_uuid_value:
        return jsonify({'message': 'Se requieren los campos email y app_uuid'}), 400

    try:
        uuid.UUID(app_uuid_value)
    except ValueError:
        return jsonify({'message': 'Formato inválido para app_uuid'}), 400

    ip_address = request.remote_addr or '0.0.0.0'

    new_entry = Blacklist(email, app_uuid_value, blocked_reason, ip_address)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'message': 'Email agregado a la lista negra correctamente'}), 201


# Endpoint para consultar si un email está en la lista negra (GET /blacklists/<email>)
@app.route('/blacklists/<string:email>', methods=['GET'])
@token_required
def check_blacklist(email):
    entry = Blacklist.query.filter_by(email=email).first()
    if entry:
        return jsonify({'blacklisted': True, 'blocked_reason': entry.blocked_reason}), 200
    else:
        return jsonify({'blacklisted': False, 'blocked_reason': None}), 200


# Endpoint de health check (GET /health)
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'healthy': True}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
