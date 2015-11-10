from hashlib import sha256

from flask import Flask \
                , render_template \
                , redirect \
                , url_for \
                , request
                  
from flask_oauthlib.provider import OAuth2Provider

app = Flask(__name__)
oauth = OAuth2Provider(app)

import db

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('register_form'))

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register_form.html')
    
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    if not username:
        return render_template('register_fail.html', reason='Empty username not allowed.')

    password = request.form['password']
    if len(password) < 6:
        return render_template('register_fail.html', reason='Password is too short')

    name = request.form['name'] or None
    email = request.form['email'] or None
    phone = request.form['phone'] or None

    if db.user(username=username):
        return render_template('register_fail.html', reason='User {} already exists.'.format(username))

    db.user.insert(username=username,
                   password_hash=sha256(password.encode('UTF-8')).digest(),
                   name=name,
                   email=email,
                   phone=phone)
    db.user.commit()

    return render_template('register_ok.html', username=request.form['username'])

if __name__ == '__main__':
    app.run(port=5050, debug=True)




