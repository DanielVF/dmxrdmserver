import serial, sys, time


OLA_UNLOCK_KEY = bytes([0xd7, 0xb2, 0x11, 0x0d])

PORT_ASSIGNMENT_LABEL = 141;
SET_PORT_ASSIGNMENT_LABEL = 145;
GET_WIDGET_PARAMS=3
GET_WIDGET_PARAMS_REPLY=3
SET_WIDGET_PARAMS=4
RECEIVE_DMX_PORT1=5
SEND_DMX_PORT1=6
SEND_DMX_RDM_TX=7
RECEIVE_DMX_ON_CHANGE=8
RECEIVED_DMX_COS_TYPE=9
GET_WIDGET_SN=10
RDM_DISCOVERY_1 = 11,
RDM_TIMEOUT_1 = 12,
SET_API_KEY_LABEL=13
HARDWARE_VERSION_LABEL=14


class EnttecPacket():
    
    @classmethod
    def Deserialize(cls, b):
        packet = EnttecPacket()

        START_CODE = 0x7E
        END_CODE = 0xE7
        # display(' '.join('{:02x}'.format(x) for x in b))
        
        i = 0
        len_bytes = len(b)
        
        # Read to next start code
        while i < len_bytes:
            if b[i] == START_CODE:
                i+=1
                break
            else:
                i+=1
        # Read type
        packet.type = b[i];
        i+=1
        # Read data length
        packet.length = b[i];
        i+=1
        packet.length += b[i] * 256;
        i+=1
        
        if packet.length > 600:
            raise "Packet larger than allowed length"
        
        end_i = i + packet.length       
        packet.data = []
        while i < end_i:
            packet.data.append(b[i])
            i += 1
        
        return packet
    
    @classmethod
    def Serialize(cls, label, data=bytes([])):
        START_CODE = 0x7E
        END_CODE = 0xE7
        out = bytes([START_CODE])
        out += bytes([label])
        out += bytes([len(data) & 0xFF])
        out += bytes([(len(data) >> 8) & 0xFF])
        out += data
        out += bytes([END_CODE])
        # display(' '.join('{:02x}'.format(x) for x in out))
        return out
    
    def __repr__(self):
        return " ".join([
            "PACKET Type: ", str(self.type),
            "Data: ",
            ' '.join('{:02x}'.format(x) for x in self.data)
        ])
        

    
    
class UsbPro():
    def __init__(self, serial_port):
        self.serial = serial.Serial(serial_port, baudrate=57600, timeout=0.2)
        self._request(13, bytes([0xC7, 0xA2, 0x01, 0xE2]))  # API key
        self._request(221, bytes([0x01, 0x01]))  # Port assignments
        self.serial_number = self.get_serial_number()

    def _send(self, label, data):
        p = EnttecPacket.Serialize(label, data)
        self.serial.write(p)

    def _request(self, label, data=bytes([]), reply_expected=True):
        p = EnttecPacket.Serialize(label, data)
        self.serial.write(p)
        if reply_expected:
            return self._read_packet()
        else:
            return None
    
    def _read_packet(self):
        """
        In the future this can use the packet Data to decide how much to read, and read exactly one packet.

        Avoids just sitting arround waiting for the timeout.
        """
        b = self.serial.read(600)
        if b == None or len(b) == 0:
            return None
        return EnttecPacket.Deserialize(b)
    
    def dmx(self,dmx):
        """
        dmx = bytes([0x00]*513)
        """
        SEND_DMX_PORT1 = 6
        return self._request(SEND_DMX_PORT1, dmx)

    def rdm(self, rdm_bytes):
        SEND_DMX_RDM_TX = 7
        return self._request(SEND_DMX_RDM_TX, rdm_bytes)
    
    def rdm_disc_unique(self, rdm_bytes):
        SEND_RDM_DISCOVERY = 11
        return self._request(SEND_RDM_DISCOVERY, rdm_bytes)

    def get_serial_number(self):
        """Returns the four bytes of the serial number"""
        return self._request(10).data[0:4]
