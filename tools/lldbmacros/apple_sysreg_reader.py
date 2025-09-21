"""
Apple 시스템 레지스터 실제 읽기 기능

이 모듈은 LLDB를 통해 실제 Apple 시스템 레지스터 값을 읽어옵니다.
"""

from core.lldbwrap import GetTarget, GetProcess
import lldb

# xnu 모듈은 나중에 import하지 않음 (순환 참조 방지)
def lldb_command(name):
    def decorator(func):
        return func
    return decorator

def lldb_alias(alias, command):
    pass

class AppleSysRegReader:
    """Apple 시스템 레지스터 실제 읽기 클래스"""
    
    def __init__(self):
        self.target = GetTarget()
        self.process = GetProcess()
    
    def read_register_by_encoding(self, op0, op1, crn, crm, op2):
        """sys_reg(op0, op1, crn, crm, op2) 형식으로 레지스터를 읽습니다"""
        try:
            # LLDB에서 시스템 레지스터를 읽는 방법
            result = lldb.SBCommandReturnObject()
            interpreter = self.target.GetDebugger().GetCommandInterpreter()
            
            # sys_reg 인코딩을 LLDB 명령어로 변환
            reg_name = f"s{op0}_{op1}_c{crn}_c{crm}_{op2}"
            
            # 먼저 register list로 레지스터 존재 확인
            command = f"register list {reg_name}"
            interpreter.HandleCommand(command, result)
            
            if not result.Succeeded() or reg_name not in result.GetOutput():
                # 레지스터가 존재하지 않으면 None 반환
                return None
            
            # register read 명령어 실행
            command = f"register read {reg_name}"
            interpreter.HandleCommand(command, result)
            
            if result.Succeeded():
                output = result.GetOutput()
                # 출력에서 16진수 값 추출
                import re
                
                # 여러 패턴으로 시도
                patterns = [
                    r'0x([0-9a-fA-F]+)',  # 기본 패턴
                    r'= 0x([0-9a-fA-F]+)',  # 등호 포함 패턴
                    r'{}\s*=\s*0x([0-9a-fA-F]+)'.format(reg_name),  # 레지스터 이름 포함
                ]
                
                for pattern in patterns:
                    hex_match = re.search(pattern, output)
                    if hex_match:
                        return int(hex_match.group(1), 16)
                
                # 마지막 시도: 출력에서 모든 16진수 찾기
                hex_matches = re.findall(r'0x([0-9a-fA-F]+)', output)
                if hex_matches:
                    # 가장 긴 16진수 값 사용 (일반적으로 레지스터 값)
                    longest_hex = max(hex_matches, key=len)
                    return int(longest_hex, 16)
            
            return None
            
        except Exception as e:
            print(f"레지스터 읽기 실패 s{op0}_{op1}_c{crn}_c{crm}_{op2}: {e}")
            return None
    
    def read_register_by_name(self, register_name):
        """레지스터 이름으로 읽습니다"""
        from apple_sysreg_definitions import REGISTER_NAMES
        
        # 레지스터 이름으로 튜플 찾기
        register_tuple = None
        for reg_tuple, name in REGISTER_NAMES.items():
            if name == register_name:
                register_tuple = reg_tuple
                break
        
        if register_tuple is None:
            return None
        
        op0, op1, crn, crm, op2 = register_tuple
        return self.read_register_by_encoding(op0, op1, crn, crm, op2)
    
    def read_all_known_registers(self):
        """알려진 모든 레지스터를 읽습니다"""
        from apple_sysreg_definitions import REGISTER_NAMES
        
        results = {}
        
        for register_tuple, register_name in REGISTER_NAMES.items():
            op0, op1, crn, crm, op2 = register_tuple
            value = self.read_register_by_encoding(op0, op1, crn, crm, op2)
            results[register_name] = {
                'encoding': f"s{op0}_{op1}_c{crn}_c{crm}_{op2}",
                'value': value,
                'tuple': register_tuple
            }
        
        return results
    
    def read_register_range(self, op0_range=(0, 7), op1_range=(0, 7), 
                           crn_range=(0, 15), crm_range=(0, 15), op2_range=(0, 7)):
        """지정된 범위의 모든 레지스터를 읽습니다"""
        results = {}
        
        for op0 in range(op0_range[0], op0_range[1] + 1):
            for op1 in range(op1_range[0], op1_range[1] + 1):
                for crn in range(crn_range[0], crn_range[1] + 1):
                    for crm in range(crm_range[0], crm_range[1] + 1):
                        for op2 in range(op2_range[0], op2_range[1] + 1):
                            encoding = f"s{op0}_{op1}_c{crn}_c{crm}_{op2}"
                            value = self.read_register_by_encoding(op0, op1, crn, crm, op2)
                            
                            if value is not None:
                                results[encoding] = {
                                    'encoding': encoding,
                                    'value': value,
                                    'tuple': (op0, op1, crn, crm, op2)
                                }
        
        return results
    
    def compare_with_known_values(self, known_values):
        """알려진 값과 비교합니다"""
        results = self.read_all_known_registers()
        comparison = {}
        
        for reg_name, reg_data in results.items():
            if reg_name in known_values:
                known_value = known_values[reg_name]
                actual_value = reg_data['value']
                
                comparison[reg_name] = {
                    'encoding': reg_data['encoding'],
                    'known_value': known_value,
                    'actual_value': actual_value,
                    'matches': known_value == actual_value if actual_value is not None else False
                }
        
        return comparison

# LLDB 명령어 매크로들
@lldb_command('read_apple_sysreg')
def ReadAppleSysReg(cmd_args=None):
    """Apple 시스템 레지스터를 실제로 읽습니다
    사용법: read_apple_sysreg <register_name> [--encoding s3_0_c15_c0_0]
    """
    if not cmd_args or len(cmd_args) < 1:
        print("사용법: read_apple_sysreg <register_name> [--encoding s3_0_c15_c0_0]")
        return
    
    reader = AppleSysRegReader()
    
    if cmd_args[0] == '--encoding' and len(cmd_args) >= 2:
        # 인코딩으로 직접 읽기
        encoding = cmd_args[1]
        try:
            # s3_0_c15_c0_0 형식 파싱
            parts = encoding.split('_')
            op0 = int(parts[0][1:])  # s3 -> 3
            op1 = int(parts[1])      # 0
            crn = int(parts[2][1:])  # c15 -> 15
            crm = int(parts[3][1:])  # c0 -> 0
            op2 = int(parts[4])      # 0
            
            value = reader.read_register_by_encoding(op0, op1, crn, crm, op2)
            if value is not None:
                print(f"{encoding}: 0x{value:016x}")
            else:
                print(f"{encoding}: 읽기 실패")
        except Exception as e:
            print(f"인코딩 파싱 실패: {e}")
    else:
        # 레지스터 이름으로 읽기
        register_name = cmd_args[0]
        value = reader.read_register_by_name(register_name)
        if value is not None:
            print(f"{register_name}: 0x{value:016x}")
        else:
            print(f"{register_name}: 읽기 실패")

@lldb_command('read_all_apple_sysregs')
def ReadAllAppleSysRegs(cmd_args=None):
    """모든 Apple 시스템 레지스터를 읽습니다
    사용법: read_all_apple_sysregs [--compare]
    """
    compare = '--compare' in cmd_args if cmd_args else False
    
    reader = AppleSysRegReader()
    
    if compare:
        # 알려진 값과 비교
        known_values = {
            'SYS_APL_HID0_EL1': 0x10002990120e0e00,
            'SYS_APL_HID1_EL1': 0x40000002000000,
            'SYS_APL_HID2_EL1': 0x0,
            'SYS_APL_HID3_EL1': 0x4180000cf8001fe0,
            'SYS_APL_HID4_EL1': 0x130800000800,
            'SYS_APL_HID5_EL1': 0x2082df205700ff12,
            'SYS_APL_HID6_EL1': 0x7dc8031f007c0e,
            'SYS_APL_HID7_EL1': 0x3110000,
            'SYS_APL_HID8_EL1': 0x381c10a438000252,
            'SYS_APL_HID9_EL1': 0x100086c000000,
            'SYS_APL_HID10_EL1': 0x3180200,
            'SYS_APL_HID11_EL1': 0x804000010000000,
            'SYS_APL_HID13_EL1': 0x332200211010205,
            'SYS_APL_HID14_EL1': 0x200000bb8,
            'SYS_APL_HID16_EL1': 0x6900000440000000,
            'SYS_APL_HID17_EL1': 0x50090af8faa,
            'SYS_APL_HID18_EL1': 0x40004000,
            'SYS_APL_HID21_EL1': 0x1040000,
            'SYS_APL_PMCR0_EL1': 0x0,
            'SYS_APL_PMCR1_EL1': 0x0,
            'SYS_APL_PMCR2_EL1': 0x0,
            'SYS_APL_PMCR3_EL1': 0x0,
            'SYS_APL_PMCR4_EL1': 0x0,
            'SYS_APL_PMESR0_EL1': 0x0,
            'SYS_APL_PMESR1_EL1': 0x0,
            'SYS_APL_PMSR_EL1': 0x0,
            'SYS_APL_PMC0_EL1': 0x0,
            'SYS_APL_PMC1_EL1': 0x0,
            'SYS_APL_PMC2_EL1': 0x0,
            'SYS_APL_PMC3_EL1': 0x0,
            'SYS_APL_PMC4_EL1': 0x0,
            'SYS_APL_PMC5_EL1': 0x0,
            'SYS_APL_PMC6_EL1': 0x0,
            'SYS_APL_PMC7_EL1': 0x0,
            'SYS_APL_PMC8_EL1': 0x0,
            'SYS_APL_PMC9_EL1': 0x0,
            'SYS_APL_LSU_ERR_STS_EL1': 0x0,
            'SYS_APL_LSU_ERR_CTL_EL1': 0x1,
            'SYS_APL_L2C_ERR_STS_EL1': 0x11000ffc00000000,
            'SYS_APL_L2C_ERR_ADR_EL1': 0x0,
            'SYS_APL_L2C_ERR_INF_EL1': 0x0,
            'SYS_APL_FED_ERR_STS_EL1': 0x0,
            'SYS_APL_APCTL_EL1': 0xc,
            'SYS_APL_KERNELKEYLO_EL1': 0x0,
            'SYS_APL_KERNELKEYHI_EL1': 0x0,
            'SYS_APL_VMSA_LOCK_EL1': 0x0,
            'SYS_APL_CTRR_LOCK_EL1': 0x0,
            'SYS_APL_CTRR_A_LWR_EL1': 0x0,
            'SYS_APL_CTRR_A_UPR_EL1': 0x0,
            'SYS_APL_CTRR_CTL_EL1': 0x0,
            'SYS_APL_APRR_JIT_ENABLE_EL2': 0x0,
            'SYS_APL_APRR_JIT_MASK_EL2': 0x0,
            'SYS_APL_s3_4_c15_c5_0_EL1': 0x0,
            'SYS_APL_CTRR_LOCK_EL2': 0x0,
            'SYS_APL_CTRR_A_LWR_EL2': 0x0,
            'SYS_APL_CTRR_A_UPR_EL2': 0x0,
            'SYS_APL_CTRR_CTL_EL2': 0x0,
            'SYS_APL_IPI_RR_LOCAL_EL1': 0x0,
            'SYS_APL_IPI_RR_GLOBAL_EL1': 0x0,
            'SYS_APL_DPC_ERR_STS_EL1': 0x0,
            'SYS_APL_IPI_SR_EL1': 0x0,
            'SYS_APL_VM_TMR_LR_EL2': 0x1b0000001b,
            'SYS_APL_VM_TMR_FIQ_ENA_EL2': 0x0,
            'SYS_APL_IPI_CR_EL1': 0x1800,
            'SYS_APL_ACC_CFG_EL1': 0xd,
            'SYS_APL_CYC_OVRD_EL1': 0x0,
            'SYS_APL_ACC_OVRD_EL1': 0x180010102001c207,
            'SYS_APL_ACC_EBLK_OVRD_EL1': 0x0,
            'SYS_APL_MMU_ERR_STS_EL1': 0x0,
            'SYS_APL_E_MMU_ERR_STS_EL1': 0x0,
            'SYS_APL_AFPCR_EL0': 0x0,
            'SYS_APL_APSTS_EL1': 0x1,
            'SYS_APL_UPMCR0_EL1': 0x0,
            'SYS_APL_UPMESR0_EL1': 0x0,
            'SYS_APL_UPMECM0_EL1': 0x0,
            'SYS_APL_UPMECM1_EL1': 0x0,
            'SYS_APL_UPMPCM_EL1': 0x0,
            'SYS_APL_UPMSR_EL1': 0x0,
            'SYS_APL_UPMECM2_EL1': 0x0,
            'SYS_APL_UPMECM3_EL1': 0x0,
            'SYS_APL_UPMESR1_EL1': 0x0,
            'SYS_APL_UPMC0_EL1': 0x0,
            'SYS_APL_UPMC1_EL1': 0x0,
            'SYS_APL_UPMC2_EL1': 0x0,
            'SYS_APL_UPMC3_EL1': 0x0,
            'SYS_APL_UPMC4_EL1': 0x0,
            'SYS_APL_UPMC5_EL1': 0x0,
            'SYS_APL_UPMC6_EL1': 0x0,
            'SYS_APL_UPMC7_EL1': 0x0,
            'SYS_APL_UPMC8_EL1': 0x0,
            'SYS_APL_UPMC9_EL1': 0x0,
            'SYS_APL_UPMC10_EL1': 0x0,
            'SYS_APL_UPMC11_EL1': 0x0,
            'SYS_APL_UPMC12_EL1': 0x0,
            'SYS_APL_UPMC13_EL1': 0x0,
            'SYS_APL_UPMC14_EL1': 0x0,
            'SYS_APL_UPMC15_EL1': 0x0
        }
        
        comparison = reader.compare_with_known_values(known_values)
        
        print("Apple 시스템 레지스터 읽기 및 비교 결과:")
        print("=" * 60)
        
        matches = 0
        total = 0
        
        for reg_name, reg_data in comparison.items():
            total += 1
            if reg_data['matches']:
                matches += 1
                status = "✓"
            else:
                status = "✗"
            
            print(f"{status} {reg_name}")
            print(f"  인코딩: {reg_data['encoding']}")
            print(f"  알려진 값: 0x{reg_data['known_value']:016x}")
            print(f"  실제 값: 0x{reg_data['actual_value']:016x}")
            print()
        
        print(f"일치율: {matches}/{total} ({matches/total*100:.1f}%)")
    else:
        # 단순 읽기
        results = reader.read_all_known_registers()
        
        print("Apple 시스템 레지스터 읽기 결과:")
        print("=" * 50)
        
        for reg_name, reg_data in results.items():
            if reg_data['value'] is not None:
                print(f"{reg_name}: 0x{reg_data['value']:016x}")
            else:
                print(f"{reg_name}: 읽기 실패")

@lldb_command('scan_apple_sysregs')
def ScanAppleSysRegs(cmd_args=None):
    """지정된 범위의 Apple 시스템 레지스터를 스캔합니다
    사용법: scan_apple_sysregs [op0_max] [op1_max] [crn_max] [crm_max] [op2_max]
    """
    # 기본 범위 설정
    ranges = [(0, 7), (0, 7), (0, 15), (0, 15), (0, 7)]
    
    if cmd_args and len(cmd_args) >= 5:
        ranges = [
            (0, int(cmd_args[0])),
            (0, int(cmd_args[1])),
            (0, int(cmd_args[2])),
            (0, int(cmd_args[3])),
            (0, int(cmd_args[4]))
        ]
    
    reader = AppleSysRegReader()
    
    print(f"Apple 시스템 레지스터 스캔 중... (범위: {ranges})")
    results = reader.read_register_range(
        op0_range=ranges[0], op1_range=ranges[1], 
        crn_range=ranges[2], crm_range=ranges[3], op2_range=ranges[4]
    )
    
    print(f"\n발견된 레지스터: {len(results)}개")
    print("-" * 50)
    
    for encoding, reg_data in results.items():
        print(f"{encoding}: 0x{reg_data['value']:016x}")

# 테스트 명령어
@lldb_command('test_apple_sysreg')
def TestAppleSysReg(cmd_args=None):
    """Apple 시스템 레지스터 테스트
    사용법: test_apple_sysreg
    """
    print("Apple 시스템 레지스터 테스트 시작...")
    
    try:
        reader = AppleSysRegReader()
        
        # 간단한 레지스터 테스트
        test_registers = [
            (3, 0, 15, 0, 0),  # SYS_APL_HID0_EL1
            (3, 0, 15, 1, 0),  # SYS_APL_HID1_EL1
            (3, 1, 15, 0, 0),  # SYS_APL_PMCR0_EL1
        ]
        
        for op0, op1, crn, crm, op2 in test_registers:
            reg_name = f"s{op0}_{op1}_c{crn}_c{crm}_{op2}"
            value = reader.read_register_by_encoding(op0, op1, crn, crm, op2)
            if value is not None:
                print(f"✓ {reg_name}: 0x{value:016x}")
            else:
                print(f"✗ {reg_name}: 읽기 실패")
        
        print("테스트 완료")
        
    except Exception as e:
        print(f"테스트 실패: {e}")

# 별칭들은 xnu.py에서 정의됨
