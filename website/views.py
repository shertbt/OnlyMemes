from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Post, User
from . import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm,TokenForm
from sqlalchemy import text
import os 
import io
from base64 import encode
from PIL import Image
import requests
views = Blueprint("views", __name__)

IMAGE_LOAD_URL="http://127.0.0.1:8080"
ACCESS_APIKEY = "1234"

@views.route("/image/<filename>")
@login_required
def get_image(filename):
    
    image_url = IMAGE_LOAD_URL+'/download/'+filename
    item_image_raw = requests.get(image_url,headers= {"ACCESS_APIKEY": ACCESS_APIKEY})
        
    content_type = item_image_raw.headers.get("content-type")
    item_image_raw = io.BytesIO(item_image_raw.content)
    return send_file(item_image_raw, mimetype=content_type)
   
@views.route("/")
@views.route("/home")
@login_required
def home():
    posts = current_user.followed_posts()
    return render_template("home.html", user=current_user, posts=posts)

@views.route("/post/<int:id>")
@login_required
def post(id):
    post=Post.query.get_or_404(id)
    user=User.query.get_or_404(post.author)
    return render_template("view_post.html",post=post,author=user.username)

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form=PostForm()
    if form.validate_on_submit():
        text=form.text.data
        title=form.title.data
        if form.picture.data:
            try:
                
                image_url = IMAGE_LOAD_URL+'/upload'
                post_response = requests.post(image_url,
                                    files={'file': (form.picture.data.filename, form.picture.data.stream, form.picture.data.mimetype)},
                                    headers= {"ACCESS_APIKEY": ACCESS_APIKEY})
                if post_response.status_code != 200:
                    raise Exception
                else:
                    picture_file = post_response.json().get('image_name')
                    post = Post(title=title,text=text,image_name=picture_file, author=current_user.id)
                    db.session.add(post)
                    db.session.commit()
                    flash('Post created!', category='success')
                    return redirect(url_for('views.home'))
            except Exception:
                flash('Try again!', category='success') 
        else:
            post = Post(title=title,text=text,image_name=None, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('views.home'))

    return render_template('create_post.html',form=form, user=current_user)

@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.author:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('views.home'))


@views.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user.id).all()
    form = EmptyForm()
    return render_template('account.html', user=user, posts=posts,form=form)

@views.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.about_me_privacy = form.about_me_privacy.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('views.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.about_me_privacy.data = current_user.about_me_privacy
    return render_template('edit_profile.html',user=current_user, title='Edit Profile',
                           form=form)


@views.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = TokenForm()
    if form.validate_on_submit():
        token=form.token.data
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('views.home'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        if token==user.token:
            current_user.follow(user)
            db.session.commit()
            flash('You are following {}!'.format(username))
            return redirect(url_for('views.user', username=username))
        else:
            flash('Wrong token!')
            return redirect(url_for('views.home'))
    else:
        return redirect(url_for('views.home'))


@views.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('views.home'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('views.user', username=username))
    else:
        return redirect(url_for('views.home'))

@views.context_processor
def base():
    form=EmptyForm()
    return dict(form=form)

@views.route("/search", methods=['POST'])
@login_required
def search():
    
    search = ""
    order = None
    if "search" in request.form:
        search = request.form["search"] 
    if "order" in request.form:
        order = request.form["order"]
    if order is None:
        users = User.query.filter(User.username.like("%{}%".format(search)))
    else:
        users = User.query.filter(
                User.username.like("%{}%".format(search))
            ).order_by(text(order))
    if users is None:
        flash('User {} not found.'.format(search))
        return redirect(url_for('views.home'))
    else:
        return render_template("usersList.html",current_user=current_user,users=users)
    
     
@views.route('/user/<username>/following')
@login_required
def showFollowing(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('views.home'))

    return render_template('usersList.html', users = user.following_users())

@views.route('/user/<username>/followers')
def showFollowers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('views.home'))
    return render_template('usersList.html', users = user.get_followers())