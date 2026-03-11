from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields

from config import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(500), nullable=True)

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')
    
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))
    
    @validates('username')
    def validate_username(self, key, username):
        if not isinstance(username, str):
            raise ValueError(f"{key} must be a string.")
        if len(username) < 3 or len(username) > 50:
            raise ValueError(f"{key} must be between 3 and 50 characters.")
        return username
    
    @validates('_password_hash')
    def validate_password_hash(self, key, password_hash):
        if password_hash is not None and not isinstance(password_hash, str):
            raise ValueError(f"{key} must be a string or None.")
        if password_hash is not None and len(password_hash) > 128:
            raise ValueError(f"{key} must be 128 characters or less.")
        return password_hash
    
    @validates('image_url')
    def validate_image_url(self, key, image_url):
        if not isinstance(image_url, str):
            raise ValueError(f"{key} must be a string.")
        if len(image_url) > 255:
            raise ValueError(f"{key} must be 255 characters or less.")
        return image_url
    
    @validates('bio')
    def validate_bio(self, key, bio):
        if not isinstance(bio, str):
            raise ValueError(f"{key} must be a string.")
        if len(bio) > 500:
            raise ValueError(f"{key} must be 500 characters or less.")
        return bio
    
    recipes = db.relationship('Recipe', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"

class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.String(1000), nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    __table_args__ = (
        CheckConstraint('instructions >= 50', name='instructions_length_check'),
    )

    @validates('title')
    def validate_title(self, key, title):
        if not isinstance(title, str):
            raise ValueError(f"{key} must be a string.")
        if len(title) < 3 or len(title) > 100:
            raise ValueError(f"{key} must be between 3 and 100 characters.")
        return title
    
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not isinstance(instructions, str):
            raise ValueError(f"{key} must be a string.")
        if len(instructions) < 50 or len(instructions) > 1000:
            raise ValueError(f"{key} must be between 50 and 1000 characters.")
        return instructions
    
    @validates('minutes_to_complete')
    def validate_minutes_to_complete(self, key, minutes_to_complete):
        if not isinstance(minutes_to_complete, int):
            raise ValueError(f"{key} must be an integer.")
        if minutes_to_complete < 1 or minutes_to_complete > 1440:
            raise ValueError(f"{key} must be between 1 and 1440.")
        return minutes_to_complete
    
    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if user_id is not None and not isinstance(user_id, int):
            raise ValueError(f"{key} must be an integer or None.")
        return user_id

    user = db.relationship('User', back_populates='recipes')  


    def __repr__(self):
        return f"<Recipe id={self.id} title={self.title}>"

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    image_url = fields.Str()
    bio = fields.Str()

class RecipeSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    instructions = fields.Str(required=True)
    minutes_to_complete = fields.Int(required=True)
    user_id = fields.Int()