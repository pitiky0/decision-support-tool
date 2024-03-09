from datetime import datetime, timezone, timedelta
from hashlib import md5
import json
import secrets
from time import time
import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import redis
import rq
from app import db, login

# Define association tables
users_roles = sa.Table(
    'users_roles',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('role_id', sa.Integer, sa.ForeignKey('role.id'), primary_key=True)
)

projects_users = sa.Table(
    'projects_users',
    db.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('project_id', sa.Integer, sa.ForeignKey('project.id'), primary_key=True)
)

# Models
class User(db.Model, UserMixin):
    id = so.mapped_column(sa.Integer, primary_key=True)
    email = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash = so.mapped_column(sa.String(256))
    full_name = so.mapped_column(sa.String(120), index=True)
    department = so.mapped_column(sa.String(120), index=True)
    workplace = so.mapped_column(sa.String(120))
    about_me = so.mapped_column(sa.String(256))
    last_seen = so.mapped_column(sa.DateTime, default=lambda: datetime.now(timezone.utc))
    token = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration = so.mapped_column(sa.DateTime)
    notifications = so.relationship('Notification', back_populates='user')
    tasks = so.relationship('Task', back_populates='user')
    projects = so.relationship('Project', secondary=projects_users, back_populates='users')
    roles = so.relationship('Role', secondary=users_roles, back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)

    def add_notification(self, name, data):
        self.notifications.filter(Notification.name == name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = db.session.query(User).filter(User.token == token).one_or_none()
        return user if user and user.token_expiration and user.token_expiration > datetime.now(timezone.utc) else None

class Role(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True)
    name = so.mapped_column(sa.String(128), index=True)
    users = so.relationship('User', secondary=users_roles, back_populates='roles')

    def __init__(self, name):
        self.name = name

class Notification(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True)
    name = so.mapped_column(sa.String(128), index=True)
    user_id = so.mapped_column(sa.Integer, sa.ForeignKey('user.id'), index=True)
    timestamp = so.mapped_column(sa.Float, index=True, default=time)
    payload_json = so.mapped_column(sa.Text)
    user = so.relationship('User', back_populates='notifications')

    def get_data(self):
        return json.loads(self.payload_json)

class Task(db.Model):
    id = so.mapped_column(sa.String(36), primary_key=True)
    name = so.mapped_column(sa.String(128), index=True)
    description = so.mapped_column(sa.String(128))
    user_id = so.mapped_column(sa.Integer, sa.ForeignKey('user.id'))
    complete = so.mapped_column(sa.Boolean, default=False)
    user = so.relationship('User', back_populates='tasks')

    # def get_rq_job(self):
    #     try:
    #         return rq.job.Job.fetch(self.id, connection=current_app.redis)
    #     except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
    #         return None

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job else 100

class Project(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True)
    name = so.mapped_column(sa.String(120), index=True)
    requests = so.relationship('Request', back_populates='project')
    users = so.relationship('User', secondary=projects_users, back_populates='projects')

    def __init__(self, name):
        self.name = name

class Request(db.Model):
    id = so.mapped_column(sa.Integer, primary_key=True)
    num = so.mapped_column(sa.String(64), unique=True)
    request_type = so.mapped_column(sa.String(64), index=True)
    subject = so.mapped_column(sa.String(120))
    sender = so.mapped_column(sa.String(120))
    receiver = so.mapped_column(sa.String(120))
    request_date = so.mapped_column(sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    body = so.mapped_column(sa.Text)
    attachments = so.mapped_column(sa.Text)
    project_id = so.mapped_column(sa.Integer, sa.ForeignKey('project.id'), index=True)
    project = so.relationship('Project', back_populates='requests')


class Dictionary(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    term: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    definition: so.Mapped[str] = so.mapped_column(sa.Text)
    is_deleted: so.Mapped[bool] = so.mapped_column(sa.Boolean, index=True, default=False)

    def __init__(self, term, definition):
        self.term = term
        self.definition = definition

    @classmethod
    def get_all_active(cls):
        query = sa.select(Dictionary).where(Dictionary.is_deleted == False)
        result = db.session.execute(query)
        return result.scalars()

    @classmethod
    def search(cls, term):
        search_words = term.lower().split()
        search_expr = sa.or_(
            *[getattr(Dictionary, column_name).ilike(f'%{word}%') for word in search_words for column_name in
              ['term', 'definition']]
        )
        query = sa.select(Dictionary).where(
            db.and_(search_expr, Dictionary.is_deleted == False)
        )
        result = db.session.execute(query)
        return set(result.scalars())

# User loader for Flask-Login
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

