from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Swipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_like = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @staticmethod
    def get_conversation(user_a, user_b):
        from sqlalchemy import or_, and_
        return Message.query.filter(
            or_(
                and_(Message.sender_id == user_a, Message.receiver_id == user_b),
                and_(Message.sender_id == user_b, Message.receiver_id == user_a),
            )
        ).order_by(Message.created_at.asc()).all()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    name = db.Column(db.String(80))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    bio = db.Column(db.Text)
    interests = db.Column(db.String(200))
    location = db.Column(db.String(120))
    avatar_filename = db.Column(db.String(255))  # stored uploaded photo name in static/uploads

    swipes_made = db.relationship('Swipe', foreign_keys=[Swipe.user_id], backref='swiper', lazy='dynamic')
    swipes_received = db.relationship('Swipe', foreign_keys=[Swipe.target_id], backref='swiped', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def display_name(self):
        return self.name or self.username

    @staticmethod
    def get_matches(user_id: int):
        # Users this user liked
        likes = Swipe.query.filter_by(user_id=user_id, is_like=True).all()
        like_ids = [s.target_id for s in likes]

        from sqlalchemy import and_
        mutual = (
            User.query.join(Swipe, Swipe.user_id == User.id)
            .filter(
                and_(
                    Swipe.target_id == user_id,
                    Swipe.is_like.is_(True),
                    User.id.in_(like_ids),
                )
            )
            .all()
        )
        return mutual


def is_match(user_a: int, user_b: int) -> bool:
    like_ab = Swipe.query.filter_by(user_id=user_a, target_id=user_b, is_like=True).first()
    like_ba = Swipe.query.filter_by(user_id=user_b, target_id=user_a, is_like=True).first()
    return like_ab is not None and like_ba is not None
