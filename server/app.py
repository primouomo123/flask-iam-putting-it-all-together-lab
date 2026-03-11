#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        try:
            request_json = request.get_json()
            if not request_json or 'username' not in request_json:
                return {'error': 'Username is required'}, 422
            new_user = User(
                username=request_json['username'],
                image_url=request_json.get('image_url'),
                bio=request_json.get('bio')
            )
            new_user.password_hash = request_json['password']
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            user_schema = UserSchema()
            return user_schema.dump(new_user), 201
        except IntegrityError:
            return {'error': 'Username already exists'}, 400

class CheckSession(Resource):
    def get(self):
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                user_schema = UserSchema()
                return user_schema.dump(user), 200
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        request_json = request.get_json()
        if not request_json or 'username' not in request_json or 'password' not in request_json:
            return {'error': 'Username and password are required'}, 422
        user = User.query.filter_by(username=request_json['username']).first()
        if user and user.authenticate(request_json['password']):
            session['user_id'] = user.id
            user_schema = UserSchema()
            return user_schema.dump(user), 200
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if 'user_id' in session and session['user_id'] is not None:
            session.pop('user_id')
            return {}, 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        if 'user_id' not in session or session['user_id'] is None:
            return {'error': 'Unauthorized'}, 401
        recipes = Recipe.query.filter_by(user_id=session['user_id']).all()
        recipe_schema = RecipeSchema(many=True)
        return recipe_schema.dump(recipes), 200
    
    def post(self):
        if 'user_id' not in session or session['user_id'] is None:
            return {'error': 'Unauthorized'}, 401
        request_json = request.get_json()
        if not request_json:
            return {'error': 'Invalid JSON'}, 400
        try:
            new_recipe = Recipe(
                title=request_json['title'],
                instructions=request_json['instructions'],
                minutes_to_complete=request_json['minutes_to_complete'],
                user_id=session['user_id']
            )
            db.session.add(new_recipe)
            db.session.commit()
            recipe_schema = RecipeSchema()
            return recipe_schema.dump(new_recipe), 201
        except (KeyError, ValueError) as e:
            return {'error': str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)