"""
Apple 시스템 레지스터 덤프 기능

이 모듈은 Apple Silicon 프로세서의 시스템 레지스터들을 덤프하고 분석합니다.
"""

from apple_sysreg_definitions import *
from apple_sysreg_parser import AppleSysRegParser
from core.lldbwrap import GetTarget, GetProcess
import json
import os
from datetime import datetime

# xnu 모듈은 나중에 import하지 않음 (순환 참조 방지)
def lldb_command(name):
    def decorator(func):
        return func
    return decorator

class AppleSysRegDumper:
    """Apple 시스템 레지스터 덤퍼 클래스"""
    
    def __init__(self):
        self.target = GetTarget()
        self.process = GetProcess()
        self.parser = AppleSysRegParser()
        self.dump_data = {}
    
    def dump_all_registers(self, categories=None):
        """모든 레지스터를 덤프합니다"""
        if categories is None:
            categories = list(REGISTER_CATEGORIES.keys())
        
        self.dump_data = {
            'timestamp': datetime.now().isoformat(),
            'target_info': self._get_target_info(),
            'registers': {}
        }
        
        for category in categories:
            if category in REGISTER_CATEGORIES:
                self.dump_data['registers'][category] = {}
                registers = REGISTER_CATEGORIES[category]
                
                for register_tuple in registers:
                    reg_name = get_register_name(register_tuple)
                    try:
                        # 실제 레지스터 값 읽기
                        value = self.parser.read_register(register_tuple)
                        if value is not None:
                            parsed = self.parser.parse_register(register_tuple, value)
                            self.dump_data['registers'][category][reg_name] = parsed
                        else:
                            self.dump_data['registers'][category][reg_name] = {
                                'register': reg_name,
                                'value': None,
                                'error': '레지스터를 읽을 수 없습니다'
                            }
                    except Exception as e:
                        self.dump_data['registers'][category][reg_name] = {
                            'error': str(e),
                            'register': reg_name
                        }
        
        return self.dump_data
    
    def dump_category(self, category):
        """특정 카테고리의 레지스터들을 덤프합니다"""
        if category not in REGISTER_CATEGORIES:
            raise ValueError(f"알 수 없는 카테고리: {category}")
        
        registers = REGISTER_CATEGORIES[category]
        category_data = {}
        
        for register_tuple in registers:
            reg_name = get_register_name(register_tuple)
            try:
                value = 0  # self._read_register_value(register_tuple)
                parsed = self.parser.parse_register(register_tuple, value)
                category_data[reg_name] = parsed
            except Exception as e:
                category_data[reg_name] = {
                    'error': str(e),
                    'register': reg_name
                }
        
        return {
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'registers': category_data
        }
    
    def dump_register(self, register_name):
        """특정 레지스터를 덤프합니다"""
        # 레지스터 이름으로 튜플 찾기
        register_tuple = None
        for reg_tuple, name in REGISTER_NAMES.items():
            if name == register_name:
                register_tuple = reg_tuple
                break
        
        if register_tuple is None:
            raise ValueError(f"알 수 없는 레지스터: {register_name}")
        
        try:
            value = self.parser.read_register(register_tuple)
            parsed = self.parser.parse_register(register_tuple, value)
            return {
                'register': register_name,
                'timestamp': datetime.now().isoformat(),
                'data': parsed
            }
        except Exception as e:
            return {
                'register': register_name,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def save_dump(self, filename=None, format='json'):
        """덤프 데이터를 파일로 저장합니다"""
        if not self.dump_data:
            raise ValueError("덤프 데이터가 없습니다. 먼저 dump_all_registers()를 실행하세요.")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"apple_sysreg_dump_{timestamp}.{format}"
        
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.dump_data, f, indent=2, ensure_ascii=False)
        elif format == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self._format_dump_text())
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
        
        return filename
    
    def _get_target_info(self):
        """타겟 정보를 가져옵니다"""
        try:
            return {
                'arch': self.target.GetTriple(),
                'process_id': self.process.GetProcessID(),
                'state': str(self.process.GetState()),
                'address_size': self.target.GetAddressByteSize()
            }
        except:
            return {
                'arch': 'unknown',
                'process_id': 0,
                'state': 'unknown',
                'address_size': 8
            }
    
    def _format_dump_text(self):
        """덤프 데이터를 텍스트 형식으로 포맷팅합니다"""
        output = []
        output.append("=" * 80)
        output.append("Apple 시스템 레지스터 덤프")
        output.append("=" * 80)
        output.append(f"타임스탬프: {self.dump_data['timestamp']}")
        output.append("")
        
        # 타겟 정보
        target_info = self.dump_data['target_info']
        output.append("타겟 정보:")
        for key, value in target_info.items():
            output.append(f"  {key}: {value}")
        output.append("")
        
        # 레지스터 데이터
        for category, registers in self.dump_data['registers'].items():
            output.append(f"[{category}]")
            output.append("-" * 40)
            
            for reg_name, reg_data in registers.items():
                output.append(f"\n{reg_name}:")
                if 'error' in reg_data:
                    output.append(f"  오류: {reg_data['error']}")
                else:
                    output.append(f"  값: {reg_data.get('value', 'N/A')}")
                    if 'bits' in reg_data and reg_data['bits']:
                        output.append("  비트 필드:")
                        for bit_name, bit_value in reg_data['bits'].items():
                            output.append(f"    {bit_name}: {bit_value}")
                    if 'access_protection_table' in reg_data:
                        output.append("  접근 보호 테이블:")
                        for entry, protection in reg_data['access_protection_table'].items():
                            output.append(f"    {entry}: X={protection['X']} W={protection['W']} R={protection['R']}")
            output.append("")
        
        return "\n".join(output)
    
    def compare_dumps(self, dump1, dump2):
        """두 덤프를 비교합니다"""
        differences = {
            'timestamp': datetime.now().isoformat(),
            'differences': []
        }
        
        # 레지스터 값 비교
        for category in dump1.get('registers', {}):
            if category not in dump2.get('registers', {}):
                differences['differences'].append({
                    'type': 'missing_category',
                    'category': category,
                    'dump': 'dump2'
                })
                continue
            
            for reg_name in dump1['registers'][category]:
                if reg_name not in dump2['registers'][category]:
                    differences['differences'].append({
                        'type': 'missing_register',
                        'category': category,
                        'register': reg_name,
                        'dump': 'dump2'
                    })
                    continue
                
                reg1 = dump1['registers'][category][reg_name]
                reg2 = dump2['registers'][category][reg_name]
                
                if reg1.get('value') != reg2.get('value'):
                    differences['differences'].append({
                        'type': 'value_change',
                        'category': category,
                        'register': reg_name,
                        'old_value': reg1.get('value'),
                        'new_value': reg2.get('value')
                    })
        
        return differences
    
    def load_dump(self, filename):
        """덤프 파일을 로드합니다"""
        with open(filename, 'r', encoding='utf-8') as f:
            if filename.endswith('.json'):
                self.dump_data = json.load(f)
            else:
                raise ValueError("지원하지 않는 파일 형식")
        return self.dump_data

# LLDB 명령어 매크로들
@lldb_command('dump_apple_sysregs')
def DumpAppleSysRegs(cmd_args=None):
    """Apple 시스템 레지스터들을 덤프합니다
    사용법: dump_apple_sysregs [category] [--save filename] [--format json|txt]
    """
    dumper = AppleSysRegDumper()
    
    # 명령어 인수 파싱
    category = None
    save_file = None
    format_type = 'txt'
    
    if cmd_args:
        i = 0
        while i < len(cmd_args):
            if cmd_args[i] == '--save' and i + 1 < len(cmd_args):
                save_file = cmd_args[i + 1]
                i += 2
            elif cmd_args[i] == '--format' and i + 1 < len(cmd_args):
                format_type = cmd_args[i + 1]
                i += 2
            elif not cmd_args[i].startswith('--'):
                category = cmd_args[i]
                i += 1
            else:
                i += 1
    
    try:
        if category:
            dump_data = dumper.dump_category(category)
        else:
            dump_data = dumper.dump_all_registers()
            dumper.dump_data = dump_data
        
        # 출력
        if format_type == 'txt':
            print(dumper._format_dump_text())
        else:
            print(json.dumps(dump_data, indent=2, ensure_ascii=False))
        
        # 파일 저장
        if save_file:
            filename = dumper.save_dump(save_file, format_type)
            print(f"\n덤프가 저장되었습니다: {filename}")
            
    except Exception as e:
        print(f"덤프 실패: {e}")

@lldb_command('dump_apple_sysreg')
def DumpAppleSysReg(cmd_args=None):
    """특정 Apple 시스템 레지스터를 덤프합니다
    사용법: dump_apple_sysreg <register_name>
    """
    if not cmd_args or len(cmd_args) != 1:
        print("사용법: dump_apple_sysreg <register_name>")
        return
    
    register_name = cmd_args[0]
    dumper = AppleSysRegDumper()
    
    try:
        dump_data = dumper.dump_register(register_name)
        if 'error' in dump_data:
            print(f"오류: {dump_data['error']}")
        else:
            print(dumper.parser.format_parsed_register(dump_data['data']))
    except Exception as e:
        print(f"덤프 실패: {e}")

@lldb_command('list_apple_sysregs')
def ListAppleSysRegs(cmd_args=None):
    """사용 가능한 Apple 시스템 레지스터들을 나열합니다
    사용법: list_apple_sysregs [category]
    """
    if cmd_args and len(cmd_args) > 0:
        category = cmd_args[0]
        if category in REGISTER_CATEGORIES:
            registers = REGISTER_CATEGORIES[category]
            print(f"\n[{category}] 카테고리의 레지스터들:")
            print("-" * 50)
            for register_tuple in registers:
                reg_name = get_register_name(register_tuple)
                print(f"  {reg_name}")
        else:
            print(f"알 수 없는 카테고리: {category}")
            print(f"사용 가능한 카테고리: {', '.join(REGISTER_CATEGORIES.keys())}")
    else:
        print("\n사용 가능한 Apple 시스템 레지스터 카테고리:")
        print("=" * 50)
        for category, registers in REGISTER_CATEGORIES.items():
            print(f"\n[{category}] ({len(registers)}개 레지스터)")
            for register_tuple in registers[:5]:  # 처음 5개만 표시
                reg_name = get_register_name(register_tuple)
                print(f"  {reg_name}")
            if len(registers) > 5:
                print(f"  ... 및 {len(registers) - 5}개 더")

@lldb_command('compare_apple_sysregs')
def CompareAppleSysRegs(cmd_args=None):
    """두 Apple 시스템 레지스터 덤프를 비교합니다
    사용법: compare_apple_sysregs <dump1.json> <dump2.json>
    """
    if not cmd_args or len(cmd_args) != 2:
        print("사용법: compare_apple_sysregs <dump1.json> <dump2.json>")
        return
    
    try:
        dumper = AppleSysRegDumper()
        dump1 = dumper.load_dump(cmd_args[0])
        dump2 = dumper.load_dump(cmd_args[1])
        
        differences = dumper.compare_dumps(dump1, dump2)
        
        print("Apple 시스템 레지스터 덤프 비교 결과:")
        print("=" * 50)
        
        if not differences['differences']:
            print("차이점이 없습니다.")
        else:
            for diff in differences['differences']:
                if diff['type'] == 'value_change':
                    print(f"값 변경: {diff['category']}.{diff['register']}")
                    print(f"  이전: {diff['old_value']}")
                    print(f"  현재: {diff['new_value']}")
                elif diff['type'] == 'missing_register':
                    print(f"누락된 레지스터: {diff['category']}.{diff['register']} (dump2)")
                elif diff['type'] == 'missing_category':
                    print(f"누락된 카테고리: {diff['category']} (dump2)")
                print()
    
    except Exception as e:
        print(f"비교 실패: {e}")

# 별칭들은 xnu.py에서 정의됨
