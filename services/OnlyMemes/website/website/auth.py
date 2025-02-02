from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from .forms import LoginForm, RegistrationForm
auth = Blueprint("auth", __name__)

def ordinaltg(n):
    return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
           next_page = url_for('views.home')

        message = "Hello! "+ user.username + ", here is your token: {}".format(user.token)
        flash(message)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form, user=current_user)

@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.get_token(user.username)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are our {} registered user! Here is your token: {}".format(ordinaltg(user.id),user.token))
        return redirect(url_for('views.home'))
    return render_template('signup.html', title='Register', form=form,user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))

