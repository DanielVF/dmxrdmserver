class RdmPacket():
    
    def __init__(self):
        self.destination_uid = bytes([0,0,0,0,0,0])
        self.source_uid = bytes([0,0,0,0,0,0])
        self.transaction_number = 0
        self.port_id_or_response_type = 0
        self.message_count = 0
        self.sub_device = 0
        self.command_class = 0
        self.pid = 0
        self.data = bytes([])
        
    def serialize(self):
        pdl = len(self.data)
        packet_len = 24 + pdl
        out = bytearray([0x00] * (packet_len + 2))
        out[0] = 0xCC ## RDM start code
        out[1] = 0x01 ## Version
        out[2] = packet_len
        for i in range(0,6):
            out[3+i] = self.destination_uid[i]
        for i in range(0,6):
            out[9+i] = self.source_uid[i]
        out[15] = self.transaction_number
        out[16] = self.port_id_or_response_type
        out[17] = self.message_count
        out[18] = (self.sub_device >> 8) & 0xFF
        out[19] = (self.sub_device) & 0xFF
        out[20] = self.command_class
        out[21] = self.pid[0]
        out[22] = self.pid[1]
        out[23] = len(self.data)
        for i in range(0,len(self.data)):
            out[24+i] = self.data[i]
        checksum = 0
        for i in range(0, packet_len):
            checksum += out[i]
        out[packet_len+0] = (checksum >> 8) & 0xFF
        out[packet_len+1] = checksum & 0xFF
        return out