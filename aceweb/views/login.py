from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from configparser import ConfigParser
import os
import bcrypt

from core.utils_flask import logged_in, flash_errors, RootUser
from core.globals import Global

login = Blueprint( "login", __name__)


# index page
@login.route("/")
@login.route("/login")
def login_index():

    form = LoginForm()
    if session.get("LOGGED_IN") is not None:
        return redirect( url_for("dashboard.show_dashboard") )
    else:
        # make sure only one root is logged in at a given time.
        if RootUser.LoggedIn == True:
            form.username.render_kw = {'disabled': 'disabled'}
            form.password.render_kw = {'disabled': 'disabled'}
            form.login.render_kw = {'disabled': 'disabled'}

            flash("Note WiFiACE only allow's one login at a time, Please logout of other devices to login from here.", "warning")

        return render_template("login.html", form=form)



@login.route("/check_login", methods=["POST"])
def check_login():
    # make sure only one root is logged in at a given time.
    if RootUser.LoggedIn == True:
        flash("Note WiFiACE only allow's one login at a time, Please logout of other devices to login from here.", "warning")
        return redirect( url_for("dashboard.show_dashboard") )

    form = LoginForm(request.form)

    if form.validate_on_submit():

        try:
            wconf = ConfigParser()
            wconf.read(Global.WIFIACE_CONF)

            username = str(wconf["core"]["username"])
            hashed_pw = str(wconf["core"]["password"])

            if  username == str(form.username.data) and bcrypt.hashpw(str(form.password.data), hashed_pw) == hashed_pw:
                session["LOGGED_IN"] = True
                flash("Logged in succesfully", "success")

                # Mark user logged in.
                RootUser.LoggedIn = True

                return redirect( url_for("dashboard.show_dashboard") )
            else:
                flash("Login Failed.", "danger")

        except Exception, e:
            flash("Configuration file error : " + str(e), "danger")
    else:
        flash_errors(form)

    return redirect( url_for("login.login_index") )

@login.route("/logout")
@logged_in
def logout():
    try:
        del session["LOGGED_IN"]
        RootUser.LoggedIn = False

        flash("Logged out succesfully", "success")
        return redirect( url_for("login.login_index") )

    except:
        flash("Login first to loggout", "warning")
        return redirect(request.referrer)



# WTForm's Classes.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, InputRequired

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired( message = "Please enter Username")])
    password = PasswordField("Password", validators=[InputRequired(message = "Please enter Password")])
    login = SubmitField("Login")
