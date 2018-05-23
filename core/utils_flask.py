""" This module contains methods specific to flask. """

# global variable to remember if any user is logged in.
class RootUser:
    LoggedIn = False

# check's if the user is logged in
def logged_in(f):
    """ Wrapper function to check's if the user is logged in. """
    from functools import wraps
    from flask import session, flash, redirect, url_for

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('LOGGED_IN') is not None:
            RootUser.LoggedIn = True
            return f(*args, **kwargs)
        else:
            flash('Please log in first.', 'danger')
            return redirect(url_for('login.login_index'))
    return decorated_function

# source : http://flask.pocoo.org/snippets/12/
def flash_errors(form):
    """ Stacks all form.errors messages into the flash() """
    from flask import flash
    for field, errors in form.errors.items():
        for error in errors:
            flash(u" %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'warning')

# locks the iface around a function.
def resource_lock(iface, func, *args, **kargs):
    """ Locks the iface around a function. """
    from core.globals import Global
    try:
        Global.monCtrl.lock(iface)
        func(*args, **kargs)
    except:
        Global.monCtrl.unLock(iface)
    else:
        Global.monCtrl.unLock(iface)
