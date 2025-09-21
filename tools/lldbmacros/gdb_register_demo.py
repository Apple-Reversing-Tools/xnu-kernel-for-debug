"""
GDB 서버를 통한 레지스터 읽기 데모

이 스크립트는 GDB 서버와의 통신 원리를 보여줍니다.
"""

import socket
import struct
import time

class GDBClient:
    """GDB 클라이언트 구현"""
    
    def __init__(self, host='localhost', port=1234):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self):
        """GDB 서버에 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"GDB 서버에 연결됨: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False
    
    def send_packet(self, data):
        """GDB 패킷 전송"""
        if not self.connected:
            return None
        
        # GDB RSP 패킷 형식: $<data>#<checksum>
        packet = f"${data}"
        checksum = sum(ord(c) for c in data) % 256
        packet += f"#{checksum:02x}"
        
        print(f"전송: {packet}")
        self.socket.send(packet.encode())
        
        # 응답 수신
        response = self.socket.recv(1024).decode()
        print(f"수신: {response}")
        
        if response.startswith('$') and response.endswith('#'):
            # 패킷 파싱
            data_part = response[1:-3]  # $와 #checksum 제거
            return data_part
        elif response.startswith('+'):
            # ACK 수신, 다시 시도
            return self.send_packet(data)
        else:
            return None
    
    def read_all_registers(self):
        """모든 레지스터 읽기"""
        print("모든 레지스터 읽기 시도...")
        response = self.send_packet("g")
        
        if response:
            # 레지스터 값들을 파싱 (ARM64 기준)
            reg_count = len(response) // 16  # 64비트 = 16자리 16진수
            print(f"읽은 레지스터 수: {reg_count}")
            
            # 각 레지스터 값 출력
            for i in range(min(reg_count, 10)):  # 처음 10개만 출력
                start = i * 16
                end = start + 16
                reg_value = response[start:end]
                print(f"  x{i}: 0x{reg_value}")
            
            return response
        return None
    
    def read_register(self, reg_num):
        """특정 레지스터 읽기"""
        print(f"레지스터 {reg_num} 읽기 시도...")
        response = self.send_packet(f"p{reg_num:x}")
        
        if response:
            # 16진수 값을 파싱
            if len(response) >= 8:
                # 리틀 엔디안으로 파싱
                reg_value = int(response, 16)
                print(f"  레지스터 {reg_num}: 0x{reg_value:016x}")
                return reg_value
        return None
    
    def write_register(self, reg_num, value):
        """레지스터 쓰기"""
        print(f"레지스터 {reg_num}에 0x{value:x} 쓰기 시도...")
        response = self.send_packet(f"P{reg_num:x}={value:x}")
        
        if response == "OK":
            print("  쓰기 성공")
            return True
        else:
            print(f"  쓰기 실패: {response}")
            return False
    
    def disconnect(self):
        """연결 종료"""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("연결 종료")

def demonstrate_gdb_communication():
    """GDB 통신 데모"""
    print("GDB 서버 통신 데모")
    print("=" * 50)
    
    # GDB 클라이언트 생성
    client = GDBClient()
    
    # 연결 시도
    if client.connect():
        try:
            # 모든 레지스터 읽기
            client.read_all_registers()
            
            # 특정 레지스터 읽기
            client.read_register(0)  # x0
            client.read_register(1)  # x1
            client.read_register(30) # x30 (LR)
            client.read_register(31) # x31 (SP)
            
            # 레지스터 쓰기 (예시)
            # client.write_register(0, 0x1234567890abcdef)
            
        finally:
            client.disconnect()
    else:
        print("GDB 서버에 연결할 수 없습니다.")
        print("실제 GDB 서버를 실행한 후 다시 시도하세요.")

def explain_register_reading_process():
    """레지스터 읽기 과정 설명"""
    print("\n레지스터 읽기 과정 설명")
    print("=" * 50)
    
    print("1. 사용자 명령어:")
    print("   (lldb) register read x0")
    print()
    
    print("2. LLDB 내부 처리:")
    print("   - 명령어 파싱")
    print("   - 레지스터 번호 매핑 (x0 → 0)")
    print("   - GDB RSP 패킷 생성: 'p0'")
    print()
    
    print("3. GDB 서버 통신:")
    print("   LLDB → GDB Server: '$p0#<checksum>'")
    print("   GDB Server → LLDB: '$<register_value>#<checksum>'")
    print()
    
    print("4. GDB 서버의 하드웨어 접근:")
    print("   - 디버 인터페이스 사용 (JTAG, SWD, etc.)")
    print("   - CPU 레지스터 직접 읽기")
    print("   - 값을 16진수 문자열로 변환")
    print()
    
    print("5. LLDB 응답 처리:")
    print("   - 패킷 파싱 및 검증")
    print("   - 16진수 값을 정수로 변환")
    print("   - 사용자에게 결과 출력")

if __name__ == "__main__":
    explain_register_reading_process()
    print("\n" + "=" * 50)
    demonstrate_gdb_communication()
