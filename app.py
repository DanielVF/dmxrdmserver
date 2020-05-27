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
    return '{"status":"ok"}'

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
        'response': ' '.join('{:02x}'.format(x) for x in r.data[1:]),
        'rdm_response_type': rdm_response_type(r),
    })

@app.route('/v1/rdm_discovery', methods=['POST'])
def rdm_discovery():
    global tx
    p = RdmPacket()
    p.destination_uid = bytes([0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])
    sn = u.serial_number
    p.source_uid = bytes([0x45,0x4e,sn[3],sn[2],sn[1],sn[0]])
    p.transaction_number = tx
    tx = (tx + 1) % 255
    p.port_id_or_response_type = 1
    p.command_class = to_bytes("10")[0] # 0x10 = E120_DISCOVERY_COMMAND
    p.pid = to_bytes("00 01") # 0x0001 == E120_DISC_UNIQUE_BRANCH
    p.data = to_bytes(request.form['low'])+to_bytes(request.form['high'])
    
    r = u.rdm_disc_unique(p.serialize())


    return json.dumps({
        'request': ' '.join('{:02x}'.format(x) for x in p.serialize()),
        'interface_code': r.type,
        'response': ' '.join('{:02x}'.format(x) for x in r.data[1:]),
        'rdm_response_type': rdm_response_type(r),
        'fixture_address': ' '.join('{:02x}'.format(x) for x in look_for_discovery_response(r.data[1:]))
    })

def look_for_discovery_response(data):
    if len(data) == 0:
        return ''
    for i in range(0, len(data)):
        if data[i] == 0xaa:
            break
    i+=1
    
    out = []
    for j in range(0, 6):
        if len(data) < i + 2:
            return ''
        a = data[i]
        b = data[i+1]
        v = (a & ~0xAA) + (b & ~0x55)
        i+=2
        out.append(v)
    
    return bytes(out)
    

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

