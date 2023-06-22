from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from hashlib import md5
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash

pepper = "$2b$12$1gUiRuxbLsODzGi6LNs5Du4e3aca00b74feb1e30ab896b3c8b00?Lk#UH?9v*^XaS*!Tm8%DHY79e!Tm8%DHY79e3L="
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    about_me = db.Column(db.String(140))
    about_me_privacy = db.Column(db.String(5))
    token = db.Column(db.String(150))
    salt = db.Column(db.String(50))
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    posts = db.relationship('Post', backref='user', passive_deletes=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw((pepper+password).encode('utf-8'), self.salt)

    def check_password(self, password):
        return self.password == bcrypt.hashpw((pepper+password).encode('utf-8'), self.salt)
    
    def get_token(self,str):
        self.token = md5(str.encode('utf-8')).hexdigest()

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user.id):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, id):
        return self.followed.filter(
            followers.c.followed_id == id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.author)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(author=self.id)
        return followed.union(own).order_by(Post.date_created.desc())
    
    def following_users(self):
        following_user=self.followed
        return following_user.order_by(User.username.asc())
    
    def get_followers(self):
        user_followers = self.followers
        return user_followers.order_by(User.username.asc())
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    image_name = db.Column(db.String(120), nullable=True)
    author = db.Column(db.Integer, db.ForeignKey(
        'user.id', ondelete="CASCADE"), nullable=False)
