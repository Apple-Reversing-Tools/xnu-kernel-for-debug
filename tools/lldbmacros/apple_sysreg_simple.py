"""
Apple 시스템 레지스터 간단한 명령어

LLDB에서 바로 사용할 수 있는 간단한 명령어들을 제공합니다.
"""

import lldb
from core.lldbwrap import GetTarget, GetProcess

# xnu 모듈은 나중에 import하지 않음 (순환 참조 방지)
def lldb_command(name):
    def decorator(func):
        return func
    return decorator

def lldb_alias(alias, command):
    pass

def read_apple_register(register_name):
    """Apple 시스템 레지스터를 읽습니다"""
    try:
        # 레지스터 이름을 인코딩으로 변환
        register_encodings = {
            'SYS_APL_HID0_EL1': (3, 0, 15, 0, 0),
            'SYS_APL_HID1_EL1': (3, 0, 15, 1, 0),
            'SYS_APL_HID2_EL1': (3, 0, 15, 2, 0),
            'SYS_APL_HID3_EL1': (3, 0, 15, 3, 0),
            'SYS_APL_HID4_EL1': (3, 0, 15, 4, 0),
            'SYS_APL_HID5_EL1': (3, 0, 15, 5, 0),
            'SYS_APL_HID6_EL1': (3, 0, 15, 6, 0),
            'SYS_APL_HID7_EL1': (3, 0, 15, 7, 0),
            'SYS_APL_HID8_EL1': (3, 0, 15, 8, 0),
            'SYS_APL_HID9_EL1': (3, 0, 15, 9, 0),
            'SYS_APL_HID10_EL1': (3, 0, 15, 10, 0),
            'SYS_APL_HID11_EL1': (3, 0, 15, 11, 0),
            'SYS_APL_PMCR0_EL1': (3, 1, 15, 0, 0),
            'SYS_APL_PMC0_EL1': (3, 2, 15, 0, 0),
            'SYS_APL_PMC1_EL1': (3, 2, 15, 1, 0),
        }
        
        if register_name not in register_encodings:
            print(f"알 수 없는 레지스터: {register_name}")
            return None
        
        op0, op1, crn, crm, op2 = register_encodings[register_name]
        
        # LLDB 명령어 실행
        target = GetTarget()
        result = lldb.SBCommandReturnObject()
        interpreter = target.GetDebugger().GetCommandInterpreter()
        
        # 여러 형식으로 시도
        reg_formats = [
            f"s{op0}_{op1}_c{crn}_c{crm}_{op2}",  # s3_0_c15_c0_0
            f"s{op0}_{op1}c{crn}c{crm}_{op2}",    # s3_0c15c0_0
            f"s{op0}_{op1}c{crn}c{crm}{op2}",     # s3_0c15c00
            f"sys_reg({op0},{op1},{crn},{crm},{op2})",  # sys_reg(3,0,15,0,0)
        ]
        
        for reg_name in reg_formats:
            # register read 명령어 실행
            command = f"register read {reg_name}"
            interpreter.HandleCommand(command, result)
            
            if result.Succeeded():
                output = result.GetOutput()
                # 출력에서 16진수 값 추출
                import re
                hex_match = re.search(r'0x([0-9a-fA-F]+)', output)
                if hex_match:
                    value = int(hex_match.group(1), 16)
                    print(f"{register_name} ({reg_name}): 0x{value:016x}")
                    return value
        
        # 방법 2: expression을 사용한 직접 읽기
        try:
            # ARM64 시스템 레지스터 읽기 명령어
            mrs_command = f"mrs x0, s{op0}_{op1}_c{crn}_c{crm}_{op2}"
            command = f"expression -- {mrs_command}"
            interpreter.HandleCommand(command, result)
            
            if result.Succeeded():
                output = result.GetOutput()
                # 출력에서 16진수 값 추출
                import re
                hex_match = re.search(r'0x([0-9a-fA-F]+)', output)
                if hex_match:
                    value = int(hex_match.group(1), 16)
                    print(f"{register_name} (MRS): 0x{value:016x}")
                    return value
        except:
            pass
        
        # 방법 3: Python을 통한 직접 접근
        try:
            # LLDB Python API를 통한 직접 접근
            frame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
            if frame.IsValid():
                # 시스템 레지스터를 직접 읽기
                # 이 방법은 LLDB의 내부 API를 사용합니다
                pass
        except:
            pass
        
        # 모든 방법이 실패한 경우
        print(f"{register_name}: 모든 방법으로 읽기 실패")
        return None
            
    except Exception as e:
        print(f"오류: {e}")
        return None

# LLDB 명령어 매크로들
@lldb_command('read_apple_reg')
def ReadAppleReg(cmd_args=None):
    """Apple 시스템 레지스터를 읽습니다
    사용법: read_apple_reg <register_name>
    """
    if not cmd_args or len(cmd_args) != 1:
        print("사용법: read_apple_reg <register_name>")
        print("예: read_apple_reg SYS_APL_HID0_EL1")
        return
    
    register_name = cmd_args[0]
    read_apple_register(register_name)

@lldb_command('list_apple_regs')
def ListAppleRegs(cmd_args=None):
    """사용 가능한 Apple 시스템 레지스터 목록을 표시합니다
    사용법: list_apple_regs
    """
    registers = [
        'SYS_APL_HID0_EL1', 'SYS_APL_HID1_EL1', 'SYS_APL_HID2_EL1',
        'SYS_APL_HID3_EL1', 'SYS_APL_HID4_EL1', 'SYS_APL_HID5_EL1',
        'SYS_APL_HID6_EL1', 'SYS_APL_HID7_EL1', 'SYS_APL_HID8_EL1',
        'SYS_APL_HID9_EL1', 'SYS_APL_HID10_EL1', 'SYS_APL_HID11_EL1',
        'SYS_APL_PMCR0_EL1', 'SYS_APL_PMC0_EL1', 'SYS_APL_PMC1_EL1'
    ]
    
    print("사용 가능한 Apple 시스템 레지스터:")
    print("=" * 50)
    for reg in registers:
        print(f"  {reg}")

@lldb_command('list_available_regs')
def ListAvailableRegs(cmd_args=None):
    """LLDB에서 실제로 사용 가능한 레지스터 목록을 표시합니다
    사용법: list_available_regs
    """
    try:
        target = GetTarget()
        result = lldb.SBCommandReturnObject()
        interpreter = target.GetDebugger().GetCommandInterpreter()
        
        # register list 명령어 실행
        command = "register list"
        interpreter.HandleCommand(command, result)
        
        if result.Succeeded():
            output = result.GetOutput()
            print("LLDB에서 사용 가능한 레지스터 목록:")
            print("=" * 50)
            
            # Apple 관련 레지스터만 필터링
            lines = output.split('\n')
            apple_regs = []
            for line in lines:
                if any(keyword in line.lower() for keyword in ['s3_', 'sys_', 'hid', 'pmc', 'apple']):
                    apple_regs.append(line.strip())
            
            if apple_regs:
                for reg in apple_regs:
                    print(f"  {reg}")
            else:
                print("Apple 관련 레지스터를 찾을 수 없습니다.")
                print("전체 레지스터 목록:")
                print(output)
        else:
            print(f"레지스터 목록을 가져올 수 없습니다: {result.GetError()}")
            
    except Exception as e:
        print(f"오류: {e}")

@lldb_command('test_apple_regs')
def TestAppleRegs(cmd_args=None):
    """Apple 시스템 레지스터들을 테스트합니다
    사용법: test_apple_regs
    """
    test_registers = [
        'SYS_APL_HID0_EL1',
        'SYS_APL_HID1_EL1', 
        'SYS_APL_PMCR0_EL1',
        'SYS_APL_PMC0_EL1'
    ]
    
    print("Apple 시스템 레지스터 테스트 시작...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(test_registers)
    
    for reg_name in test_registers:
        value = read_apple_register(reg_name)
        if value is not None:
            success_count += 1
    
    print(f"\n테스트 완료: {success_count}/{total_count} 성공")

# 별칭들은 xnu.py에서 정의됨
