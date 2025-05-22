from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.utils.helpers import get_db

reset_password_bp = Blueprint('reset_password_bp', __name__)

@reset_password_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    error = None
    message = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            error = "Please enter your email address."
        else:
            db = get_db()
            cursor = db.cursor()
            user_row = cursor.execute('SELECT id FROM users WHERE username = ?', (email,)).fetchone()
            if user_row:
                # For now, redirect to set_password page (no email delivery yet)
                return redirect(url_for('set_password', user_id=user_row['id']))
            else:
                error = "No account found for that email address. If you just submitted a form, please use the same email address you entered on the form."
    return render_template('reset_password.html', error=error, message=message)
