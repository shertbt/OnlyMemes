from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Post, User
from . import db
from .forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm
from sqlalchemy import text
views = Blueprint("views", __name__)


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
        post = Post(title=title,text=text, author=current_user.id)
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
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('views.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',user=current_user, title='Edit Profile',
                           form=form)


@views.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('views.home'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('views.user', username=username))
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
    if search != "":
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
    else:
        return redirect(url_for('views.home'))

    '''  form=SearchForm()
    if form.validate_on_submit():
        query=form.query.data
        users = User.query.filter(User.username.like('%' + query + '%' ))
        if users is None:
            flash('User {} not found.'.format(query))
            return redirect(url_for('views.home'))
        else:
            users = users.order_by(User.username).all()
            return render_template("usersList.html",current_user=current_user,users=users,form=form)
    else:
        return redirect(url_for('views.home'))
    '''
    
    
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