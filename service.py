import traceback
from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timedelta
import json
import math

import sys
from flask import Flask \
                , render_template \
                , redirect \
                , url_for \
                , request

app = Flask(__name__)


import db_load_or_install


@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('register_form'))


@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register_form.html')

    
@app.route('/register', methods=['POST'])
def register():
    login = request.form['login']
    if not login:
        return render_template('register_fail.html', reason='Empty login not allowed.')

    password = request.form['password']
    if len(password) < 6:
        return render_template('register_fail.html', reason='Password is too short')

    name = request.form['name'] or None
    email = request.form['email'] or None
    phone = request.form['phone'] or None

    if db_load_or_install.user(login=login):
        return render_template('register_fail.html', reason='User already exists.'.format(login))

    db_load_or_install.user.insert(login=login,
                   password_hash=sha256(password.encode('UTF-8')).digest(),
                   name=name,
                   email=email,
                   phone=phone)
    db_load_or_install.user.commit()

    return render_template('register_ok.html', login=request.form['login'])


@app.route('/oauth/authorize', methods=['GET'])
def authorize_form():
    response_type = request.args.get('response_type', None)
    client_id = request.args.get('client_id', None)
    state = request.args.get('state', None)

    if client_id is None:
        return render_template('authorize_fail.html', reason='Require client_id.')
    try:
        client_id = int(client_id)
    except:
        client_id = None
    if not client_id is None and client_id not in db_load_or_install.client:
        return render_template('authorize_fail.html', reason='client_id is invalid.')

    if response_type is None:
        return redirect(db_load_or_install.client[client_id]['redirect_uri'] + '?error=invalid_request' +
                                                              ('' if state is None else '&state=' + state), code=302)
    if response_type != 'code':
        return redirect(db_load_or_install.client[client_id]['redirect_uri'] + '?error=unsupported_response_type' +
                                                              ('' if state is None else '&state=' + state), code=302)

    return render_template('authorize_form.html', state=state,
                                                  client_id=client_id,
                                                  client_name=db_load_or_install.client[client_id]['name'])


@app.route('/oauth/authorize', methods=['POST'])
def authorize():
    client_id = int(request.form.get('client_id'))
    login = request.form.get('login')
    password = request.form.get('password')
    state = request.form.get('state', None)

    if not db_load_or_install.user(login=login):
        return redirect(db_load_or_install.client[client_id]['redirect_uri'] + '?error=access_denied' + ('' if state is None else '&state=' + state), code=302)
    if db_load_or_install.user(login=login)[0]['password_hash'] != sha256(password.encode('UTF-8')).digest():
        return redirect(db_load_or_install.client[client_id]['redirect_uri'] + '?error=access_denied' + ('' if state is None else '&state=' + state), code=302)

    code = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    db_load_or_install.authorization_code.insert(user_id=db_load_or_install.user(login=login)[0]['__id__'],
                                 code=code,
                                 expire_time=datetime.now() + timedelta(minutes=10))
    db_load_or_install.authorization_code.commit()

    return redirect(db_load_or_install.client[client_id]['redirect_uri'] + '?code=' + code + ('' if state is None else '&state=' + state), code=302)


@app.route('/oauth/token', methods=['POST'])
def token():
    try:
        grant_type = request.form.get('grant_type')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')
    except KeyError:
        return json.dumps({'error': 'invalid_request'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    try:
        client_id = int(client_id)
    except:
        client_id = None
    if client_id not in db_load_or_install.client or db_load_or_install.client[client_id]['secret'] != client_secret:
        return json.dumps({'error': 'invalid_client'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    if grant_type == 'authorization_code':
        try:
            code = request.form.get('code')
        except KeyError:
            return json.dumps({'error': 'invalid_request'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        if not db_load_or_install.authorization_code(code=code) or db_load_or_install.authorization_code(code=code)[0]['expire_time'] < datetime.now():
            return json.dumps({'error': 'invalid_grant'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        user_id = db_load_or_install.authorization_code(code=code)[0]['user_id']

        db_load_or_install.authorization_code.delete(db_load_or_install.authorization_code(code=code))
        db_load_or_install.authorization_code.commit()

    elif grant_type == 'refresh_token':
        try:
            refresh_token = request.form.get('refresh_token')
        except KeyError:
            return json.dumps({'error': 'invalid_request'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        if not db_load_or_install.token(refresh=refresh_token):
            return json.dumps({'error': 'invalid_grant'}), 400, {
                'Content-Type': 'application/json;charset=UTF-8',        
            }

        user_id = db_load_or_install.token(refresh=refresh_token)[0]['user_id']

        db_load_or_install.token.delete(db_load_or_install.token(refresh=refresh_token))
        db_load_or_install.token.commit()
    else:
        traceback.print_exc(file=sys.stdout)
        return json.dumps({'error': 'unsupported_grant_type'}), 400, {
            'Content-Type': 'application/json;charset=UTF-8',        
        }

    access_token = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    expire_time = datetime.now() + timedelta(hours=1)
    refresh_token = sha256(str(uuid4()).encode('UTF-8')).hexdigest()
    db_load_or_install.token.insert(user_id=user_id,
                    access=access_token,
                    expire_time=expire_time,
                    refresh=refresh_token)
    db_load_or_install.token.commit()

    return json.dumps({
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': 3600,
        'refresh_token': refresh_token,
    }), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
        'Cache-Control': 'no-store',
        'Pragma': 'no-cache',
    }


@app.route('/ships/', methods=['GET'])
def get_ships():
    try:
        per_page = int(request.args.get('per_page', 20))
        if per_page <= 0:
            raise Exception()
        page = int(request.args.get('page', 0))
        if page < 0 or page > len(db_load_or_install.sailors) // per_page:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    items = []
    for i, ships in enumerate(db_load_or_install.ships):
        if i < page * per_page:
            continue
        if i >= (page + 1) * per_page:
            break
        items.append({
            'id': ships['__id__'],
            'name': ships['name'],
            'country': ships['country'],
        })

    return json.dumps({
        'items': items,
        'per_page': per_page,
        'page': page,
        'page_count': math.ceil(len(db_load_or_install.ships) / per_page)
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }


@app.route('/sailors/', methods=['GET'])
def get_sailors():
    try:
        per_page = int(request.args.get('per_page', 20))
        if per_page <= 0:
            raise Exception()
        page = int(request.args.get('page', 0))
        if page < 0 or page > len(db_load_or_install.sailors) // per_page:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    items = []
    for i, sailors in enumerate(db_load_or_install.sailors):
        if i < page * per_page:
            continue
        if i >= (page + 1) * per_page:
            break
        items.append({
            'id': sailors['__id__'],
            'firstname': sailors['firstname'],
            'lastname': sailors['lastname'],
            'ship_empl': sailors['ship_empl'],
        })

    return json.dumps({
        'items': items,
        'per_page': per_page,
        'page': page,
        'page_count': math.ceil(len(db_load_or_install.sailors) / per_page)
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',
    }


@app.route('/sailors/<id>', methods=['GET'])
def get_sailor(id):
    try:
        id = int(id)
        if id not in db_load_or_install.sailors:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    sailors = db_load_or_install.sailors[id]
    return json.dumps({
        'id': sailors['__id__'],
        'firstname': sailors['firstname'],
        'lastname': sailors['lastname'],
        'speciality': sailors['speciality'],
        'hiredate': datetime_to_string(sailors['hiredate']),
        'ship_empl': sailors['ship_empl']
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',        
    }


@app.route('/ships/<id>', methods=['GET'])
def get_ship(id):
    try:
        id = int(id)
        if id not in db_load_or_install.sailors:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    ships = db_load_or_install.ships[id]
    return json.dumps({
        'id': ships['__id__'],
        'name': ships['name'],
        'type': ships['type'],
        'country': ships['country']
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8',
    }


@app.route('/sailors/<id>', methods=['DELETE'])
def remove_sailor(id):
    try:
        get_access_token(request)
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 403
    
    try:
        id = int(id)
        if id not in db_load_or_install.sailors:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    db_load_or_install.sailors.delete(db_load_or_install.sailors[id])
    db_load_or_install.sailors.commit()

    return '', 200


@app.route('/ships/<id>', methods=['DELETE'])
def remove_ship(id):
    try:
        get_access_token(request)
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 403
    
    try:
        id = int(id)
        if id not in db_load_or_install.ships:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    db_load_or_install.ships.delete(db_load_or_install.ships[id])
    db_load_or_install.ships.commit()

    return '', 200


@app.route('/sailors/<id>', methods=['PUT', 'PATCH', 'POST'])
def update_sailor(id):
    try:
        get_access_token(request)
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 403
    
    try:
        id = int(id)
        if id not in db_load_or_install.sailors:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    try:
        sailor = request.json

        if int(sailor['ship_empl']) not in db_load_or_install.ships:
            raise Exception()

        hiredate = string_to_datetime(sailor['hiredate'])
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    db_load_or_install.sailors.update(db_load_or_install.sailors[id], firstname=sailor['firstname'],
                                        lastname=sailor['lastname'], speciality=sailor['speciality'],
                                        hiredate=hiredate, ship_empl=int(sailor['ship_empl']))
    db_load_or_install.sailors.commit()

    return '', 200


@app.route('/ships/<id>', methods=['PUT', 'PATCH', 'POST'])
def update_ship(id):
    try:
        get_access_token(request)
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 403
    
    try:
        id = int(id)
        if id not in db_load_or_install.ships:
            raise Exception()
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 404

    try:
        ships = request.json
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    db_load_or_install.ships.update(db_load_or_install.ships[id], name=ships['name'],
                                    type=ships['type'], country=ships['country'])
    db_load_or_install.ships.commit()

    return '', 200


@app.route('/ships/', methods=['POST'])
def insert_ship():
    try:
        get_access_token(request)
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 403
    
    try:
        ships = request.json
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    id = db_load_or_install.ships.insert(name=ships['name'], type=ships['type'],
                                         country=ships['country'])
    db_load_or_install.ships.commit()

    return '', 201, {
        'Location': '/ships/{}'.format(id)
    }


@app.route('/sailors/', methods=['POST'])
def insert_sailor():
    try:
        get_access_token(request)
    except:
        return '', 403

    

    try:
        sailor = request.json

        if int(sailor['ship_empl']) not in db_load_or_install.sailors:
            raise Exception()

        hiredate = string_to_datetime(sailor['hiredate'])
    except:
        traceback.print_exc(file=sys.stdout)
        return '', 400

    id = db_load_or_install.sailors.insert(firstname=sailor['firstname'],
                                            lastname=sailor['lastname'], speciality=sailor['speciality'],
                                            hiredate=hiredate, ship_empl=int(sailor['ship_empl']))
    db_load_or_install.sailors.commit()

    return '', 201, {
        'Location': '/sailors/{}'.format(id)
    }


@app.route('/me', methods=['GET'])
def get_me():
    try:
        access_token = get_access_token(request)
    except:
        return '', 403

    user_id = db_load_or_install.token(access=access_token)[0]['user_id']

    return json.dumps({
        'login': db_load_or_install.user[user_id]['login'],
        'name': db_load_or_install.user[user_id]['name'],
        'email': db_load_or_install.user[user_id]['email'],
        'phone': db_load_or_install.user[user_id]['phone'],
    }, indent=4), 200, {
        'Content-Type': 'application/json;charset=UTF-8'
    }


def string_to_datetime(string_date):
    return datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S.%f")


def datetime_to_string(date_time):
    return date_time.strftime("%Y-%m-%d %H:%M:%S.%f")


def get_access_token(request):
    access_token = request.headers.get('Authorization', '')[len('Bearer '):]
    if not db_load_or_install.token(access=access_token) or db_load_or_install.token(access=access_token)[0]['expire_time'] < datetime.now():
        raise Exception()
    return access_token

if __name__ == '__main__':
    app.run(port=5050, debug=True)




