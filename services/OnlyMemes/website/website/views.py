from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file,abort
from flask_login import login_required, current_user
from .models import Post, User
from . import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm,TokenForm
from sqlalchemy import text,desc
import os 
from io import BytesIO
from PIL import Image
import requests
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from datetime import datetime
views = Blueprint("views", __name__)

IMAGE_LOAD_URL="http://imageserver:8081"
ALLOWED_EXTENSIONS= ['jpg', 'png']

@views.route("/image/<filename>")
@login_required
def get_image(filename):
    filename = secure_filename(filename)
    post = Post.query.filter_by(image_name=filename).first()
    if not post:
        flash("Post does not exist.", category='error')
        return redirect(url_for('views.home'))
    elif current_user.id == post.author or current_user.is_following(post.author):
        image_url = IMAGE_LOAD_URL+'/download/'+filename
        item_image_raw = requests.get(image_url)
        
        content_type = item_image_raw.headers.get("content-type")
        item_image_raw = BytesIO(item_image_raw.content)
        return send_file(item_image_raw, mimetype=content_type)
    else:
        abort(403)
          
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form=PostForm()
    if form.validate_on_submit():
        text=form.text.data
        title=form.title.data
        
        if form.picture.data:
            try:
                
                filename=secure_filename(form.picture.data.filename)
                if allowed_file(filename):
                    
                    name,ext = os.path.splitext(filename)
                    now = datetime.now()
                    current_time = now.strftime("%H%M%S")
                    image_fn = str(current_user.id)+current_time + ext

                    image_url = IMAGE_LOAD_URL+'/upload'
                
                    post_response = requests.post(image_url,
                                    files={'file': (image_fn, form.picture.data.stream, form.picture.data.mimetype)})
                    if post_response.status_code != 200:
                        raise Exception
                    else:
                        picture_file = post_response.json().get('image_name')
                        post = Post(title=title,text=text,image_name=picture_file, author=current_user.id)
                        db.session.add(post)
                        db.session.commit()
                        flash('Post created!', category='success')
                        return redirect(url_for('views.home'))
                else:
                    raise Exception
            except Exception:
                flash('Try again!', category='error') 
        elif form.url.data:
            try:
                
                filename=os.path.basename(urlparse(form.url.data).path)
                filename=secure_filename(filename)

                if allowed_file(filename):
                    response = requests.get(form.url.data)
                    if response.status_code != 200:
                        raise Exception
                    else:
                        content_type = response.headers.get("content-type")
                        name,ext = os.path.splitext(filename)
                        now = datetime.now()
                        current_time = now.strftime("%H%M%S")
                        image_fn = str(current_user.id)+current_time + ext
                        image_url = IMAGE_LOAD_URL+'/upload'
                        post_response = requests.post(image_url,
                                    files={'file': (image_fn, BytesIO(response.content),content_type)})
                        if post_response.status_code != 200:
                            raise Exception
                        else:
                            picture_file = post_response.json().get('image_name')
                            post = Post(title=title,text=text,image_name=picture_file, author=current_user.id)
                            db.session.add(post)
                            db.session.commit()
                            flash('Post created!', category='success')
                            return redirect(url_for('views.home'))
                else:
                    raise Exception
            except Exception:
                flash('Try again!', category='error') 
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
        abort(403)
    elif current_user.id != post.author:
        abort(403)
    else:
        if post.image_name:
            try:
                image_url = IMAGE_LOAD_URL+'/delete/'+post.image_name
                post_response = requests.get(image_url)
                if post_response.status_code != 200:
                    raise Exception
                else:
                    db.session.delete(post)
                    db.session.commit()
                    flash('Post deleted.', category='success')
                    return redirect(url_for('views.home'))
            except Exception:
                flash('Try again!', category='error')
                return redirect(url_for('views.home'))
        else: 
            db.session.delete(post)
            db.session.commit()
            flash('Post deleted.', category='success')
            return redirect(url_for('views.home'))

@views.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts=Post.query.filter_by(author=user.id).order_by(Post.date_created.desc()).paginate(
        page=page, per_page=10, error_out=False)
    next_url = url_for('views.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('views.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('account.html', user=user, posts=posts.items,form=form,  next_url=next_url, prev_url=prev_url)

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
        return redirect(url_for('views.user',username=current_user.username))
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
            flash('Wrong token!', category='error')
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