
import os
from flask import Flask
from flask import jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token
from flask_jwt_extended import current_user
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate

BASEDIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
    os.path.join(BASEDIR, "app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

jwt = JWTManager(app)
db = SQLAlchemy(app)

Migrate(app, db)
db.init_app(app)
CORS(app)

followers = db.Table('followers',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    posts = db.relationship('Post', backref='post', lazy=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.user_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self) -> str:
        return "<User %r>" % self.username

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "posts":self.posts,
        }

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)

    def __repr__(self) -> str:
        return "<Post %r>" 

    def serialize(self):
        return {
            "id": self.id,
            "message": self.message,
            "user_id": self.user_id,
        }

@app.route('/follower/<int:id>', methods=['POST'])
def follower_user_add(id):
    user1 = db.session.query(User).get(id)
    user2 = db.session.query(User).get(request.json.get("user"))
    user1.follow(user2)
    if user1 is not None and user2 is not None:
        db.session().add(user1)
        db.session().commit()
        return jsonify(user1.serialize()), 200
    else:
        return jsonify({"msg": "user not found"}), 404


@app.route('/followed/<int:id>', methods=['GET'])
def follower_user(id):
    followers=[]
    user1 = db.session.query(User).get(id)
    users = db.session.query(User).all()
    for follow in users:
        if user1.is_following(follow):
            followers.append(follow.serialize())
    if user1 is not None:
        return jsonify({ "user" : user1.serialize(), "followers" :followers}), 200
    else:
        return jsonify({"msg": "user not found"}), 404


@app.route('/user', methods=['POST'])
def create_user():
    try:
        user = User()
        user.username = request.json.get("username")
        user.email = request.json.get("email")
        db.session().add(user)
        db.session().commit()
        return jsonify(user.serialize()), 201
    except Exception as e:
        return jsonify({"message": "ups algo salio mal "}), 500


@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.query(User).all()
    list_user = list()
    for user in users:
        list_user.append({"nombre": user.username, "email": user.email})
    print(users)
    return jsonify({"users": list_user})


@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.query(User).get(id)
    print(user)
    if user is not None:
        return jsonify(user.serialize()), 200
    else:
        return jsonify({"msg": "user not found"}), 404


@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.query(User).get(id)
    if user is not None:
        user.username = request.json.get("username")
        user.email = request.json.get("email")
        db.session.commit()
        return jsonify(user.serialize()), 200
    else:
        return jsonify({"msg": "user not found"}), 404


@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.query(User).get(id)
    if user is not None:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"msg": "success"}), 200
    else:
        return jsonify({"msg": "user not found"}), 404


@app.route('/post/user/<int:id>', methods=['POST'])
def create_post(id):
    try:
        post = Post()
        post.message = request.json.get("message")
        post.user_id = id
        db.session().add(post)
        db.session().commit()
        return jsonify(post.serialize()), 201
    except Exception as e:
        return jsonify({"message": "ups algo salio mal "}), 500

@app.route('/user/<int:id>/posts', methods=['GET'])
def get_post_user(id):
    response = []
    user = db.session.query(User).get(id)
    posts = db.session.query(Post).filter( Post.user_id == id)
    for post in posts:
        response.append({"id": post.id, "message" : post.message, "username" : user.username})
    if response is not None:
        return jsonify(response), 200
    else:
        return jsonify({"msg": "post of user not found"}), 404


@app.route('/posts', methods=['GET'])
def get_posts():
    response = []
    for p, u in db.session.query(Post,User).filter( User.id== Post.user_id):
        response.append({"id": p.id, "message" : p.message, "username" : u.username})
    if response is not None:
        return jsonify(response), 200
    else:
        return jsonify({"msg": "post of user not found"}), 404

@app.route('/post/<int:id>', methods=['GET'])
def get_post(id):
    post = db.session.query(Post).get(id)
    if post is not None:
        return jsonify(post.serialize()), 200
    else:
        return jsonify({"msg": "post not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
