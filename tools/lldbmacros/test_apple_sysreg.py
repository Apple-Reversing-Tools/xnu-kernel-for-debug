"""
Apple 시스템 레지스터 테스트 모듈

LLDB에서 바로 사용할 수 있는 간단한 테스트 명령어들을 제공합니다.
"""

import lldb
from core.lldbwrap import GetTarget, GetProcess

def test_apple_sysreg():
    """Apple 시스템 레지스터 테스트"""
    print("Apple 시스템 레지스터 테스트 시작...")
    print("=" * 50)
    
    try:
        target = GetTarget()
        result = lldb.SBCommandReturnObject()
        interpreter = target.GetDebugger().GetCommandInterpreter()
        
        # 테스트할 레지스터들
        test_registers = [
            ('SYS_APL_HID0_EL1', 's3_0_c15_c0_0'),
            ('SYS_APL_HID1_EL1', 's3_0_c15_c1_0'),
            ('SYS_APL_PMCR0_EL1', 's3_1_c15_c0_0'),
            ('SYS_APL_PMC0_EL1', 's3_2_c15_c0_0'),
        ]
        
        success_count = 0
        total_count = len(test_registers)
        
        for reg_name, reg_encoding in test_registers:
            # register read 명령어 실행
            command = f"register read {reg_encoding}"
            interpreter.HandleCommand(command, result)
            
            if result.Succeeded():
                output = result.GetOutput()
                # 출력에서 16진수 값 추출
                import re
                hex_match = re.search(r'0x([0-9a-fA-F]+)', output)
                if hex_match:
                    value = int(hex_match.group(1), 16)
                    print(f"✓ {reg_name} ({reg_encoding}): 0x{value:016x}")
                    success_count += 1
                else:
                    print(f"✗ {reg_name} ({reg_encoding}): 값을 찾을 수 없습니다")
            else:
                print(f"✗ {reg_name} ({reg_encoding}): 읽기 실패 - {result.GetError()}")
        
        print(f"\n테스트 완료: {success_count}/{total_count} 성공")
        
    except Exception as e:
        print(f"테스트 실패: {e}")

def list_available_registers():
    """LLDB에서 사용 가능한 레지스터 목록을 표시합니다"""
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

# LLDB 명령어 등록
def register_commands():
    """LLDB 명령어를 등록합니다"""
    try:
        from xnu import lldb_command, lldb_alias
        
        @lldb_command('test_apple_sysreg')
        def TestAppleSysReg(cmd_args=None):
            """Apple 시스템 레지스터 테스트
            사용법: test_apple_sysreg
            """
            test_apple_sysreg()
        
        @lldb_command('list_available_regs')
        def ListAvailableRegs(cmd_args=None):
            """LLDB에서 사용 가능한 레지스터 목록을 표시합니다
            사용법: list_available_regs
            """
            list_available_registers()
        
        # 별칭들은 xnu.py에서 정의됨
        
        print("Apple 시스템 레지스터 테스트 명령어가 등록되었습니다.")
        
    except ImportError:
        print("xnu 모듈을 찾을 수 없습니다. LLDB 환경에서 실행하세요.")

# 모듈이 직접 실행될 때
if __name__ == "__main__":
    register_commands()
