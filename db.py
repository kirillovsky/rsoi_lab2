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
    authorization_code.create('code', 'expire_time')

token = Base('db/token.pdl')
if token.exists():
    token.open()
else:
    token.create('access', 'expire_time', 'refresh')

user = Base('db/user.pdl')
if user.exists():
    user.open()
else:
    user.create('login', 'password_hash', 'name', 'email', 'phone')

food = Base('db/food.pdl')
if food.exists():
    food.open()
else:
    food.create('name', 'price')

order = Base('db/order.pdl')
if order.exists():
    order.open()
else:
    order.create('client_id', 'delivery_location', 'time_placed', 'time_delivered')

order_item = Base('db/order_item.pdl')
if order_item.exists():
    order_item.open()
else:
    order_item.create('order_id', 'food_id', 'food_amount')
