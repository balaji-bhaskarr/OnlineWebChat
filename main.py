from flask import Flask, render_template, session, redirect, request, url_for
from flask_socketio import SocketIO, send, join_room, leave_room
import random
from string import ascii_uppercase
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'webchat2023'
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ''
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code

@app.route("/", methods=['POST', 'GET'])
def home():
    session.clear()
    if request.method == 'POST':
        name = request.form.get('user_name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('home.html', error='Please enter a name', user_name=name, code=code)
        if join!=False and not code:
            return render_template('home.html', error='Please enter a room code', user_name=name, code=code)
        
        room = code
        if create!=False:
            room = generate_unique_code(4)
            rooms[room] = {'members':0, 'messages':[]}
        elif code not in rooms:
            return render_template('home.html', error='Room does not exist', user_name=name, code=code)

        session['room'] = room
        session['name'] = name
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    
    print(rooms[room]['messages'])
    return render_template('room.html', code=room, messages = rooms[room]['messages'])


@socketio.on('message')
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    content = {
        'name' : session.get('name'),
        'message' : data['data'],
        'date' : data['date']
    }
    send(content, to=room)
    rooms[room]['messages'].append(content)

@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({'name':name, 'message':'has joined the room', 'date': str(datetime.now())}, to=room)
    rooms[room]['members']+=1
    print(f'{name} joined the room {room}')

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')
    leave_room(room)

    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members']<=0:
            del rooms[room]
    send({'name':name, 'message':'has left the room', 'date': str(datetime.now())}, to=room)
    print(f'{name} left the room {room}')
if __name__=='__main__':
    socketio.run(app, debug=True)
