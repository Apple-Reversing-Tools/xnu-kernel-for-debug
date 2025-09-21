"""
Apple 시스템 레지스터 파서 및 분석기

이 모듈은 Apple Silicon 프로세서의 시스템 레지스터 값들을 파싱하고 분석합니다.
"""

from apple_sysreg_definitions import *
from core.lldbwrap import GetTarget, GetProcess
import lldb

class AppleSysRegParser:
    """Apple 시스템 레지스터 파서 클래스"""
    
    def __init__(self):
        self.target = GetTarget()
        self.process = GetProcess()
    
    def read_register(self, register_tuple):
        """시스템 레지스터 값을 읽어옵니다"""
        try:
            from apple_sysreg_reader import AppleSysRegReader
            reader = AppleSysRegReader()
            op0, op1, crn, crm, op2 = register_tuple
            return reader.read_register_by_encoding(op0, op1, crn, crm, op2)
        except Exception as e:
            print(f"레지스터 읽기 실패: {e}")
            return None
    
    def parse_hid_register(self, register_tuple, value):
        """HID 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        # HID 레지스터별 비트 필드 파싱
        if register_tuple == SYS_APL_HID0_EL1:
            parsed['bits'] = {
                'Loop Buffer Disable': (value >> 20) & 1,
                'AMX Cache Fusion Disable': (value >> 21) & 1,
                'IC Prefetch Limit One Brn': (value >> 25) & 1,
                'Fetch Width Disable': (value >> 28) & 1,
                'PMULL Fuse Disable': (value >> 33) & 1,
                'Cache Fusion Disable': (value >> 36) & 1,
                'Same Pg Power Optimization': (value >> 45) & 1,
                'Instruction Cache Prefetch Depth': (value >> 60) & 0x7
            }
        elif register_tuple == SYS_APL_EHID0_EL1:
            parsed['bits'] = {
                'nfpRetFwdDisb': (value >> 45) & 1
            }
        elif register_tuple == SYS_APL_HID1_EL1:
            parsed['bits'] = {
                'Disable CMP-Branch Fusion': (value >> 14) & 1,
                'ForceMextL3ClkOn': (value >> 15) & 1,
                'rccForceAllIexL3ClksOn': (value >> 23) & 1,
                'rccDisStallInactiveIexCtl': (value >> 24) & 1,
                'disLspFlushWithContextSwitch': (value >> 25) & 1,
                'Disable AES Fusion across groups': (value >> 44) & 1,
                'Disable MSR Speculation DAIF': (value >> 49) & 1,
                'Trap SMC': (value >> 54) & 1,
                'enMDSBStallPipeLineECO': (value >> 58) & 1,
                'Enable Branch Kill Limit / SpareBit6': (value >> 60) & 1
            }
        elif register_tuple == SYS_APL_EHID1_EL1:
            parsed['bits'] = {
                'Disable MSR Speculation DAIF': (value >> 30) & 1
            }
        # 다른 HID 레지스터들도 비슷하게 구현...
        
        return parsed
    
    def parse_performance_counter(self, register_tuple, value):
        """성능 카운터 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        if 'PMCR' in reg_name:
            if register_tuple == SYS_APL_PMCR0_EL1:
                parsed['bits'] = {
                    'Counter Enable PMC 7-0': value & 0xFF,
                    'Interrupt Mode': (value >> 8) & 0x7,
                    'PMI Interrupt Active': (value >> 11) & 1,
                    'Enable PMI for PMC 7-0': (value >> 12) & 0xFF,
                    'Disable Counting on PMI': (value >> 20) & 1,
                    'Block PMIs until after eret': (value >> 22) & 1,
                    'Count Global L2C Events': (value >> 23) & 1,
                    'User-mode Access Enable': (value >> 30) & 1,
                    'Counter Enable PMC 9-8': (value >> 32) & 0x3,
                    'Enable PMI for PMC 9-8': (value >> 44) & 0x3
                }
        elif 'PMC' in reg_name:
            # PMC는 카운터 값이므로 특별한 파싱이 필요하지 않음
            parsed['counter_value'] = value
            parsed['overflow'] = (value >> 47) & 1 if 'UPMC' not in reg_name else (value >> 63) & 1
        
        return parsed
    
    def parse_error_register(self, register_tuple, value):
        """에러 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        if register_tuple == SYS_APL_L2C_ERR_STS_EL1:
            parsed['bits'] = {
                'Recursive Fault': (value >> 1) & 1,
                'Access Fault': (value >> 7) & 1,
                'Enable Flags 38-34': (value >> 34) & 0x1F,
                'Enable SError Interrupts': (value >> 39) & 1,
                'Enable Flags 43-40': (value >> 40) & 0xF,
                'Write-1-to-clear Behavior': (value >> 56) & 1,
                'Some Enable': (value >> 60) & 1
            }
        elif register_tuple == SYS_APL_L2C_ERR_ADR_EL1:
            parsed['bits'] = {
                'Physical Address': value & 0xFFFFFFFFFFFF,
                'Unknown Bit 42': (value >> 42) & 1,
                'Access Type': (value >> 55) & 0x7,
                'Core within Cluster': (value >> 61) & 0x3
            }
        elif register_tuple == SYS_APL_L2C_ERR_INF_EL1:
            parsed['bits'] = {
                'Error Information': value & 0xFFFFFFFF,
                'Address Alignment': (value >> 26) & 1
            }
        
        return parsed
    
    def parse_aprr_register(self, register_tuple, value):
        """APRR 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'access_protection_table': {}
        }
        
        # APRR는 16개의 4비트 필드로 구성된 테이블
        for i in range(16):
            field_value = (value >> (i * 4)) & 0xF
            protection = {
                'X': (field_value >> 0) & 1,
                'W': (field_value >> 1) & 1,
                'R': (field_value >> 2) & 1
            }
            parsed['access_protection_table'][f'Entry_{i}'] = protection
        
        return parsed
    
    def parse_ctrr_register(self, register_tuple, value):
        """CTRR 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        if 'CTL' in reg_name:
            parsed['bits'] = {
                'A MMU off write protect': (value >> 0) & 1,
                'A MMU on write protect': (value >> 1) & 1,
                'B MMU off write protect': (value >> 2) & 1,
                'B MMU on write protect': (value >> 3) & 1,
                'A PXN': (value >> 4) & 1,
                'B PXN': (value >> 5) & 1,
                'A UXN': (value >> 6) & 1,
                'B UXN': (value >> 7) & 1
            }
        elif 'LWR' in reg_name:
            parsed['bits'] = {
                'Lower Address': value & 0xFFFFFFFFFFFF
            }
        elif 'UPR' in reg_name:
            parsed['bits'] = {
                'Upper Address': value & 0xFFFFFFFFFFFF
            }
        elif 'LOCK' in reg_name:
            parsed['bits'] = {
                'Lock Status': value & 1
            }
        
        return parsed
    
    def parse_ipi_register(self, register_tuple, value):
        """IPI 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        if 'RR_LOCAL' in reg_name or 'RR_GLOBAL' in reg_name:
            parsed['bits'] = {
                'Target CPU': value & 0xF,
                'RR Type': (value >> 28) & 0x3
            }
            if 'GLOBAL' in reg_name:
                parsed['bits']['Target Cluster'] = (value >> 16) & 0x1F
        elif 'SR' in reg_name:
            parsed['bits'] = {
                'IPI Pending': value & 1
            }
        elif 'CR' in reg_name:
            parsed['bits'] = {
                'Deferred IPI Countdown': value & 0xFFFF
            }
        elif 'TMR' in reg_name:
            if 'LR' in reg_name:
                parsed['bits'] = {
                    'State': (value >> 62) & 0x3
                }
            elif 'FIQ_ENA' in reg_name:
                parsed['bits'] = {
                    'CNTV Guest Timer Mask': value & 1,
                    'CNTP Guest Timer Mask': (value >> 1) & 1
                }
        
        return parsed
    
    def parse_acc_register(self, register_tuple, value):
        """ACC 레지스터 값을 파싱합니다"""
        if value is None:
            return None
            
        reg_name = get_register_name(register_tuple)
        parsed = {
            'register': reg_name,
            'value': f"0x{value:016x}",
            'bits': {}
        }
        
        if register_tuple == SYS_APL_ACC_OVRD_EL1:
            parsed['bits'] = {
                'OK To Power Down SRM': (value >> 13) & 0x3,
                'Disable L2 Flush For ACC Sleep': (value >> 15) & 0x3,
                'OK To Train Down Link': (value >> 17) & 0x3,
                'OK To Power Down CPM': (value >> 25) & 0x3,
                'CPM Wakeup': (value >> 27) & 0x3,
                'Disable Clock Dtr': (value >> 29) & 1,
                'Disable PIO On WFI CPU': (value >> 32) & 1,
                'Enable Deep Sleep': (value >> 34) & 1
            }
        elif register_tuple == SYS_APL_ACC_CFG_EL1:
            parsed['bits'] = {
                'BP Sleep': (value >> 2) & 0x3
            }
        elif register_tuple == SYS_APL_CYC_OVRD_EL1:
            parsed['bits'] = {
                'Disable WFI Return': value & 1,
                'FIQ Mode': (value >> 20) & 0x3,
                'IRQ Mode': (value >> 22) & 0x3,
                'OK To Power Down': (value >> 24) & 0x3
            }
        
        return parsed
    
    def parse_register(self, register_tuple, value=None):
        """레지스터를 자동으로 파싱합니다"""
        if value is None:
            value = self.read_register(register_tuple)
        
        if value is None:
            return None
        
        category = get_register_category(register_tuple)
        
        if category == "HID":
            return self.parse_hid_register(register_tuple, value)
        elif category == "Performance_Counters":
            return self.parse_performance_counter(register_tuple, value)
        elif category == "Error_Handling":
            return self.parse_error_register(register_tuple, value)
        elif category == "Memory_Protection":
            if 'APRR' in get_register_name(register_tuple):
                return self.parse_aprr_register(register_tuple, value)
            elif 'CTRR' in get_register_name(register_tuple):
                return self.parse_ctrr_register(register_tuple, value)
        elif category == "Interrupts":
            return self.parse_ipi_register(register_tuple, value)
        elif category == "Power_Management":
            return self.parse_acc_register(register_tuple, value)
        else:
            # 기본 파싱
            return {
                'register': get_register_name(register_tuple),
                'value': f"0x{value:016x}",
                'category': category,
                'raw_value': value
            }
    
    def format_parsed_register(self, parsed):
        """파싱된 레지스터 정보를 포맷팅합니다"""
        if not parsed:
            return "레지스터 파싱 실패"
        
        output = []
        output.append(f"레지스터: {parsed['register']}")
        output.append(f"값: {parsed['value']}")
        
        if 'category' in parsed:
            output.append(f"카테고리: {parsed['category']}")
        
        if 'bits' in parsed and parsed['bits']:
            output.append("비트 필드:")
            for bit_name, bit_value in parsed['bits'].items():
                if isinstance(bit_value, int):
                    output.append(f"  {bit_name}: {bit_value} (0b{bit_value:b})")
                else:
                    output.append(f"  {bit_name}: {bit_value}")
        
        if 'access_protection_table' in parsed:
            output.append("접근 보호 테이블:")
            for entry, protection in parsed['access_protection_table'].items():
                output.append(f"  {entry}: X={protection['X']} W={protection['W']} R={protection['R']}")
        
        if 'counter_value' in parsed:
            output.append(f"카운터 값: {parsed['counter_value']}")
            if 'overflow' in parsed:
                output.append(f"오버플로우: {parsed['overflow']}")
        
        return "\n".join(output)
