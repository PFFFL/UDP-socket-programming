import socket
import sys
import time
import random
import struct
import threading
import pandas as pd
import datetime

STUDENT_ID = 2910 ^ 0x5A3C  
WINDOW_SIZE = 400  
MIN_DATA_SIZE = 40
MAX_DATA_SIZE = 80
TIMEOUT_BASE = 300  
NUM_PACKETS = 30  
LOG_FILE = "run_log.txt"

class PacketType:
    CONNECT_REQUEST = 0x01
    CONNECT_RESPONSE = 0x02
    DATA = 0x03
    ACK = 0x04

class UDPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(TIMEOUT_BASE / 1000.0)
        self.connected = False
        self.lock = threading.Lock()
        self.log_file = open(LOG_FILE, 'w', encoding='utf-8')
        self.rtt_list = []
        self.total_packets_sent = 0
        self.packets_info = {}
        
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        log_msg = f"[{timestamp}] {message}\n"
        self.log_file.write(log_msg)
        self.log_file.flush()
        print(log_msg.strip())
    
    def send_connect_request(self):
        packet = struct.pack('!B H', PacketType.CONNECT_REQUEST, STUDENT_ID)
        self.log(f"发送连接请求, StudentID: {STUDENT_ID ^ 0x5A3C}")
        self.socket.sendto(packet, (self.server_ip, self.server_port))
        
        try:
            data, _ = self.socket.recvfrom(1024)
            if len(data) >= 2:
                pkt_type, status = struct.unpack('!B B', data)
                if pkt_type == PacketType.CONNECT_RESPONSE:
                    if status == 0x00:
                        self.connected = True
                        self.log("连接建立成功")
                        return True
                    else:
                        self.log(f"连接被拒绝, 状态码: {status}")
                        return False
        except socket.timeout:
            self.log("连接请求超时")
            return False
        return False
    
    def build_data_packet(self, seq_num, data):
        pkt_type = PacketType.DATA
        data_len = len(data)
        return struct.pack(f'!B H H {data_len}s', pkt_type, seq_num, data_len, data.encode())
    
    def parse_ack(self, data):
        if len(data) >= 3:
            pkt_type, ack_num = struct.unpack('!B H', data)
            if pkt_type == PacketType.ACK:
                return ack_num
        return None
    
    def run(self):
        if not self.send_connect_request():
            self.log_file.close()
            return
        
        base = 0
        next_seq = 0
        send_buffer = {}
        send_times = {}
        data_start = 0
        
        while next_seq < NUM_PACKETS or base < NUM_PACKETS:
            while next_seq < NUM_PACKETS and (next_seq - base) * MAX_DATA_SIZE < WINDOW_SIZE:
                data_size = random.randint(MIN_DATA_SIZE, MAX_DATA_SIZE)
                data = f"Data packet {next_seq} content".ljust(data_size)[:data_size]
                send_buffer[next_seq] = data
                send_times[next_seq] = time.time()
                self.total_packets_sent += 1
                
                data_end = data_start + data_size
                self.packets_info[next_seq] = (data_start, data_end)
                self.log(f"第{next_seq}个（第{data_start}~{data_end}字节）client端已经发送")
                
                packet = self.build_data_packet(next_seq, data)
                self.socket.sendto(packet, (self.server_ip, self.server_port))
                
                data_start = data_end
                next_seq += 1
            
            try:
                self.socket.settimeout(TIMEOUT_BASE / 1000.0)
                data, _ = self.socket.recvfrom(1024)
                ack_num = self.parse_ack(data)
                
                if ack_num is not None:
                    rtt = (time.time() - send_times[ack_num]) * 1000
                    self.rtt_list.append(rtt)
                    start, end = self.packets_info[ack_num]
                    self.log(f"第{ack_num}个（第{start}~{end}字节）server端已经收到，RTT是{rtt:.2f} ms")
                    
                    while base <= ack_num and base < NUM_PACKETS:
                        base += 1
                        
            except socket.timeout:
                seq_num = base
                if seq_num < NUM_PACKETS:
                    send_times[seq_num] = time.time()
                    self.total_packets_sent += 1
                    start, end = self.packets_info[seq_num]
                    self.log(f"超时，重传第{seq_num}个（第{start}~{end}字节）数据包")
                    packet = self.build_data_packet(seq_num, send_buffer[seq_num])
                    self.socket.sendto(packet, (self.server_ip, self.server_port))
        
        loss_rate = (self.total_packets_sent - NUM_PACKETS) / self.total_packets_sent * 100
        self.log(f"\n【汇总】  丢包率：{loss_rate:.2f}%")
        
        if self.rtt_list:
            rtt_series = pd.Series(self.rtt_list)
            self.log(f"最大RTT：{rtt_series.max():.2f} ms")
            self.log(f"最小RTT：{rtt_series.min():.2f} ms")
            self.log(f"平均RTT：{rtt_series.mean():.2f} ms")
            self.log(f"RTT标准差：{rtt_series.std():.2f} ms")
        
        self.log_file.close()
        self.socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python udpclient.py <serverIP> <serverPort>")
        sys.exit(1)
    
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    
    client = UDPClient(server_ip, server_port)
    client.run()