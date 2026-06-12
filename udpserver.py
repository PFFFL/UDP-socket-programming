import socket
import sys
import time
import random
import struct
import threading
import datetime

LOSS_RATE = 0.3  
LOG_FILE = "server_log.txt"

class PacketType:
    CONNECT_REQUEST = 0x01
    CONNECT_RESPONSE = 0x02
    DATA = 0x03
    ACK = 0x04

class UDPServer:
    def __init__(self, port):
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', port))
        self.clients = {}
        self.lock = threading.Lock()
        self.log_file = open(LOG_FILE, 'a', encoding='utf-8')
        self.log(f"服务器启动，监听端口 {port}")
    
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        log_msg = f"[{timestamp}] [SERVER] {message}\n"
        self.log_file.write(log_msg)
        self.log_file.flush()
        print(log_msg.strip())
    
    def validate_student_id(self, student_id):
        decoded = student_id ^ 0x5A3C
        return 0 <= decoded <= 9999
    
    def handle_connect_request(self, data, addr):
        if len(data) >= 3:
            pkt_type, student_id = struct.unpack('!B H', data[:3])
            if pkt_type == PacketType.CONNECT_REQUEST:
                self.log(f"收到连接请求 from {addr}, StudentID: {student_id ^ 0x5A3C}")
                
                if self.validate_student_id(student_id):
                    response = struct.pack('!B B', PacketType.CONNECT_RESPONSE, 0x00)
                    self.socket.sendto(response, addr)
                    self.clients[addr] = {'next_expected': 0, 'buffer': {}}
                    self.log(f"连接建立成功，客户端: {addr}")
                    return True
                else:
                    response = struct.pack('!B B', PacketType.CONNECT_RESPONSE, 0x01)
                    self.socket.sendto(response, addr)
                    self.log(f"StudentID验证失败，拒绝连接 from {addr}")
                    return False
        return False
    
    def handle_data_packet(self, data, addr):
        if len(data) >= 5:
            pkt_type, seq_num, data_len = struct.unpack('!B H H', data[:5])
            if pkt_type == PacketType.DATA:
                if addr not in self.clients:
                    self.log(f"未认证的客户端 {addr} 发送数据，已忽略")
                    return
                
                if random.random() < LOSS_RATE:
                    self.log(f"模拟丢包，丢弃序列号 {seq_num} 的数据包")
                    return
                
                actual_data = data[5:5+data_len].decode()
                self.log(f"收到数据，序列号: {seq_num}, 长度: {data_len}")
                
                client_info = self.clients[addr]
                next_expected = client_info['next_expected']
                
                if seq_num == next_expected:
                    client_info['next_expected'] += 1
                    ack_packet = struct.pack('!B H', PacketType.ACK, seq_num)
                    self.socket.sendto(ack_packet, addr)
                    self.log(f"发送ACK，确认序列号: {seq_num}")
                    
                    while client_info['next_expected'] in client_info['buffer']:
                        client_info['next_expected'] += 1
                        ack_packet = struct.pack('!B H', PacketType.ACK, client_info['next_expected'] - 1)
                        self.socket.sendto(ack_packet, addr)
                        self.log(f"发送累积ACK，确认序列号: {client_info['next_expected'] - 1}")
                elif seq_num > next_expected:
                    if seq_num not in client_info['buffer']:
                        client_info['buffer'][seq_num] = actual_data
    
    def run(self):
        try:
            while True:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    if len(data) == 0:
                        continue
                    
                    pkt_type = data[0]
                    if pkt_type == PacketType.CONNECT_REQUEST:
                        self.handle_connect_request(data, addr)
                    elif pkt_type == PacketType.DATA:
                        self.handle_data_packet(data, addr)
                    else:
                        self.log(f"未知数据包类型: {pkt_type}")
                except Exception as e:
                    self.log(f"接收数据异常: {e}")
        except KeyboardInterrupt:
            self.log("服务器停止")
        finally:
            self.log_file.close()
            self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python udpserver.py <serverPort>")
        sys.exit(1)
    
    server_port = int(sys.argv[1])
    server = UDPServer(server_port)
    server.run()