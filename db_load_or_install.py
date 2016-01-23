from datetime import datetime
from pathlib import Path
from pydblite import Base

if not Path('db').exists():
    Path('db').mkdir()

client = Base('db/client.pdl')
if client.exists():
    client.open()
else:
    client.create('secret', 'redirect_uri', 'name')

authorization_code = Base('db/authorization_code.pdl')
if authorization_code.exists():
    authorization_code.open()
else:
    authorization_code.create('user_id', 'code', 'expire_time')

token = Base('db/token.pdl')
if token.exists():
    token.open()
else:
    token.create('user_id', 'access', 'expire_time', 'refresh')

user = Base('db/user.pdl')
if user.exists():
    user.open()
else:
    user.create('login', 'password_hash', 'name', 'email', 'phone')

sailors = Base('db/sailors.pdl')
if sailors.exists():
    sailors.open()
else:
    sailors.create('firstname', 'lastname', 'speciality', 'hiredate', 'ship_empl')

ships = Base('db/ships.pdl')
if ships.exists():
    ships.open()
else:
    ships.create('name', 'type', 'country')

if len(ships) == 0:
    ships.insert('Dwight D. Eisenhower', 'Aircraft carrier', 'USA')
    ships.insert('Carl Vinson', 'Aircraft carrier', 'GB')
    ships.insert('Udaloy', 'Destroyer', 'RUS')
    ships.insert('Kirov', 'Battlecruiser', 'RUS')
    ships.commit()

if len(sailors) == 0:
    sailors.insert('Valisyi', 'Bykov', 'Chief cook', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 4)
    sailors.insert('Yaroslav', 'Galych', 'Seaman', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 4)
    sailors.insert('Cavin', 'Lanister', 'Boatswain', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 1)
    sailors.insert('Mark', 'Brown', 'Physician', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 2)
    sailors.insert('Nick', 'Carroll', 'Seaman', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 2)
    sailors.insert('Eugene', 'Crownsberg', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 3)
    sailors.insert('Ulrich', 'Bloodaxe', 'Captain', datetime.strptime('2013-09-28 20:30:55.78200', "%Y-%m-%d %H:%M:%S.%f"), 3)
    sailors.commit()

if len(client) == 0:
    client.insert('TSTSECRET', 'https://www.yandex.com', 'app1')
    client.commit()