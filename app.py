from flask import Flask
from flask import request
from flask import render_template
import json
import re
import configparser
from .usbpro import UsbPro
from .rdm import RdmPacket


app = Flask("DMX RDM Server")

config = configparser.ConfigParser()
config.read('config.ini')
serial_port = config['device']['serial_port']
print("Using %s" % serial_port)
u = UsbPro(serial_port)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/v1/dmx', methods=['POST'])
def dmx():
    dmx = [0x00]*513
    for k, v in request.form.items():
        if k.isnumeric():
            dmx[int(k)] = int(v)
    u.dmx(bytes(dmx))
    return 'DMX'

tx = 0

@app.route('/v1/rdm', methods=['POST'])
def rdm():
    global tx
    p = RdmPacket()
    p.destination_uid = to_bytes(request.form['destination'])
    sn = u.serial_number
    p.source_uid = bytes([0x45,0x4e,sn[3],sn[2],sn[1],sn[0]])
    p.transaction_number = tx
    tx = (tx + 1) % 255
    p.port_id_or_response_type = 1
    p.command_class = to_bytes(request.form['command_class'])[0]
    p.pid = to_bytes(request.form['pid'])
    p.data = to_bytes(request.form['data'])
    
    r = u.rdm(p.serialize())

    if r.type == 12:
        r = u.rdm(p.serialize())


    return json.dumps({
        'request': ' '.join('{:02x}'.format(x) for x in p.serialize()),
        'interface_code': r.type,
        'response': ' '.join('{:02x}'.format(x) for x in r.data),
        'rdm_response_type': rdm_response_type(r),
    })

CLEANER_RE = re.compile('[^0-9A-Za-z]')
def to_bytes(s):
    if s == None or len(s) == 0:
        return bytes([])
    print(s)
    cleaned = CLEANER_RE.sub('',s)
    print(cleaned)
    b = bytes.fromhex(cleaned)
    print(' '.join('{:02x}'.format(x) for x in b))
    return b

def rdm_response_type(r):
    TYPE_I = 24
    if len(r.data) <= 23:
        return 'none'
    code = r.data[TYPE_I]
    if code == 0x00:
        return 'ack'
    if code == 0x02:
        return 'nack'
    else:
        return 'other'

