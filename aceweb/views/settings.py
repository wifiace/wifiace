from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import os, signal
from configparser import ConfigParser
import bcrypt

from core.utils_flask import logged_in, flash_errors
from core.globals import Global

settings = Blueprint( "settings", __name__)


@settings.route("/")
@logged_in
def show_settings():
    form = ChangeSettingsForm()
    return render_template("settings.html", form=form)

@settings.route("/change_password", methods=["POST"])
@logged_in
def changes_password():

    form = ChangeSettingsForm(request.form)

    if form.validate_on_submit():
        try:
            wconf = ConfigParser()
            wconf.read(Global.WIFIACE_CONF)

            username = str(wconf["core"]["username"])
            hashed_pw = str(wconf["core"]["password"])

            # change password if old password matches.
            if bcrypt.hashpw(str(form.old_password.data), hashed_pw) == hashed_pw:

                new_hashed = bcrypt.hashpw(str(form.new_password.data), bcrypt.gensalt())
                wconf.set("core", "password", new_hashed)

                with open(Global.WIFIACE_CONF, "w") as cf:
                    wconf.write(cf)

                flash("Password succesfully changed", "success")
                return redirect( url_for('login.logout') )
            else:
                flash("Old password didn't matched", "danger")

        except Exception, e:
            flash("Confiuration file erro : " + str(e), "danger")
    else:
        flash_errors(form)

    return redirect( url_for("settings.show_settings") )

@settings.route("/system_shutdown")
@logged_in
def system_shutdown():
    # shutdown after 5 sec.
    os.system("shutdown -t 5")
    return redirect( url_for("shutdown_server") )

@settings.route("/system_restart")
@logged_in
def system_restart():
    # restart after 5 sec.
    os.system("shutdown -t 5 -r")
    return redirect( url_for("shutdown_server") )


# WTForms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, InputRequired, EqualTo, Length, Regexp

class ChangeSettingsForm(FlaskForm):
    old_password = PasswordField("Older Password", validators=[InputRequired(message = "Please enter Password")])

    new_password = PasswordField("New Password", validators=[InputRequired(),
    EqualTo('confirm_password', message = "password must match"),
    Length(min=4, max =15, message="new password length should be between 4-15 characters"),
    Regexp('^[A-Za-z0-9@#$%^&+=]+$', message="new password contains invailid characters")])

    confirm_password = PasswordField("Repeat Password", validators=[InputRequired()])
