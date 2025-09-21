"""
Apple 시스템 레지스터 연구 및 열거 기능

이 모듈은 Apple Silicon 프로세서의 시스템 레지스터들을 연구하고 분석합니다.
"""

from apple_sysreg_definitions import *
from apple_sysreg_parser import AppleSysRegParser
from core.lldbwrap import GetTarget, GetProcess
import json
import os
import time
from datetime import datetime

# xnu 모듈은 나중에 import하지 않음 (순환 참조 방지)
def lldb_command(name):
    def decorator(func):
        return func
    return decorator
from collections import defaultdict

class AppleSysRegResearcher:
    """Apple 시스템 레지스터 연구자 클래스"""
    
    def __init__(self):
        self.target = GetTarget()
        self.process = GetProcess()
        self.parser = AppleSysRegParser()
        self.research_data = {}
        self.unknown_registers = set()
        self.register_patterns = defaultdict(list)
    
    def enumerate_all_registers(self, verbose=False):
        """모든 레지스터를 열거하고 분석합니다"""
        print("Apple 시스템 레지스터 열거 시작...")
        
        research_results = {
            'timestamp': datetime.now().isoformat(),
            'total_registers': 0,
            'categories': {},
            'unknown_registers': [],
            'patterns': {},
            'statistics': {}
        }
        
        total_registers = 0
        
        for category, registers in REGISTER_CATEGORIES.items():
            print(f"\n[{category}] 카테고리 분석 중... ({len(registers)}개 레지스터)")
            
            category_data = {
                'count': len(registers),
                'registers': [],
                'patterns': [],
                'unknown_values': []
            }
            
            for register_tuple in registers:
                reg_name = get_register_name(register_tuple)
                total_registers += 1
                
                try:
                    # 실제 레지스터 값 읽기
                    value = self.parser.read_register(register_tuple)
                    
                    register_info = {
                        'name': reg_name,
                        'tuple': register_tuple,
                        'value': value,
                        'category': category,
                        'parsed': None
                    }
                    
                    # 레지스터 파싱 시도
                    try:
                        parsed = self.parser.parse_register(register_tuple, value)
                        register_info['parsed'] = parsed
                        
                        # 패턴 분석
                        self._analyze_register_patterns(register_tuple, value, parsed)
                        
                    except Exception as e:
                        register_info['parse_error'] = str(e)
                        if verbose:
                            print(f"  파싱 실패: {reg_name} - {e}")
                    
                    category_data['registers'].append(register_info)
                    
                    if verbose:
                        print(f"  {reg_name}: 0x{value:016x}")
                
                except Exception as e:
                    if verbose:
                        print(f"  읽기 실패: {reg_name} - {e}")
                    self.unknown_registers.add(register_tuple)
            
            research_results['categories'][category] = category_data
        
        research_results['total_registers'] = total_registers
        research_results['unknown_registers'] = list(self.unknown_registers)
        research_results['patterns'] = dict(self.register_patterns)
        research_results['statistics'] = self._calculate_statistics(research_results)
        
        self.research_data = research_results
        return research_results
    
    def research_register_behavior(self, register_name, iterations=100, delay=0.01):
        """특정 레지스터의 동작을 연구합니다"""
        # 레지스터 이름으로 튜플 찾기
        register_tuple = None
        for reg_tuple, name in REGISTER_NAMES.items():
            if name == register_name:
                register_tuple = reg_tuple
                break
        
        if register_tuple is None:
            raise ValueError(f"알 수 없는 레지스터: {register_name}")
        
        print(f"{register_name} 레지스터 동작 연구 시작... (반복: {iterations}회)")
        
        values = []
        changes = []
        
        for i in range(iterations):
            try:
                # 실제 레지스터 값 읽기
                value = self.parser.read_register(register_tuple)
                values.append(value)
                
                if i > 0 and value != values[i-1]:
                    changes.append({
                        'iteration': i,
                        'old_value': values[i-1],
                        'new_value': value,
                        'timestamp': datetime.now().isoformat()
                    })
                
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"반복 {i}에서 오류: {e}")
                break
        
        research_result = {
            'register': register_name,
            'iterations': len(values),
            'values': values,
            'changes': changes,
            'unique_values': len(set(values)),
            'is_stable': len(changes) == 0,
            'timestamp': datetime.now().isoformat()
        }
        
        return research_result
    
    def find_register_patterns(self):
        """레지스터 패턴을 찾습니다"""
        print("레지스터 패턴 분석 중...")
        
        patterns = {
            'naming_patterns': self._analyze_naming_patterns(),
            'encoding_patterns': self._analyze_encoding_patterns(),
            'value_patterns': self._analyze_value_patterns(),
            'bit_patterns': self._analyze_bit_patterns()
        }
        
        return patterns
    
    def discover_unknown_registers(self, op0_range=(0, 7), op1_range=(0, 7), 
                                 crn_range=(0, 15), crm_range=(0, 15), op2_range=(0, 7)):
        """알려지지 않은 레지스터들을 발견합니다"""
        print("알려지지 않은 레지스터 탐색 중...")
        
        known_registers = set(REGISTER_NAMES.keys())
        discovered = []
        
        for op0 in range(op0_range[0], op0_range[1] + 1):
            for op1 in range(op1_range[0], op1_range[1] + 1):
                for crn in range(crn_range[0], crn_range[1] + 1):
                    for crm in range(crm_range[0], crm_range[1] + 1):
                        for op2 in range(op2_range[0], op2_range[1] + 1):
                            register_tuple = (op0, op1, crn, crm, op2)
                            
                            if register_tuple not in known_registers:
                                try:
                                    # 실제 레지스터 값 읽기
                                    value = self.parser.read_register(register_tuple)
                                    
                                    if value is not None and value != 0:  # 0이 아닌 값이 있는 경우만
                                        discovered.append({
                                            'tuple': register_tuple,
                                            'value': value,
                                            'encoding': f"sys_reg({op0}, {op1}, {crn}, {crm}, {op2})",
                                            'timestamp': datetime.now().isoformat()
                                        })
                                        
                                except Exception as e:
                                    # 읽을 수 없는 레지스터는 무시
                                    pass
        
        return discovered
    
    def analyze_register_correlations(self):
        """레지스터 간 상관관계를 분석합니다"""
        print("레지스터 상관관계 분석 중...")
        
        correlations = {}
        
        # 모든 레지스터의 값을 수집
        register_values = {}
        for register_tuple in REGISTER_NAMES.keys():
            try:
                value = self.parser.read_register(register_tuple)
                if value is not None:
                    register_values[register_tuple] = value
            except:
                continue
        
        # 상관관계 계산
        register_list = list(register_values.keys())
        for i, reg1 in enumerate(register_list):
            for reg2 in register_list[i+1:]:
                val1 = register_values[reg1]
                val2 = register_values[reg2]
                
                # 간단한 상관관계 계산 (실제로는 더 정교한 통계 방법 사용)
                if val1 == val2:
                    correlation = 1.0
                elif val1 == 0 or val2 == 0:
                    correlation = 0.0
                else:
                    correlation = min(val1, val2) / max(val1, val2)
                
                if correlation > 0.5:  # 임계값
                    reg1_name = get_register_name(reg1)
                    reg2_name = get_register_name(reg2)
                    correlations[f"{reg1_name} <-> {reg2_name}"] = {
                        'correlation': correlation,
                        'reg1': reg1_name,
                        'reg2': reg2_name,
                        'val1': val1,
                        'val2': val2
                    }
        
        return correlations
    
    def generate_research_report(self, output_file=None):
        """연구 보고서를 생성합니다"""
        if not self.research_data:
            print("연구 데이터가 없습니다. 먼저 enumerate_all_registers()를 실행하세요.")
            return None
        
        report = {
            'title': 'Apple 시스템 레지스터 연구 보고서',
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(),
            'detailed_analysis': self.research_data,
            'recommendations': self._generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"연구 보고서가 저장되었습니다: {output_file}")
        
        return report
    
    def _analyze_register_patterns(self, register_tuple, value, parsed):
        """레지스터 패턴을 분석합니다"""
        op0, op1, crn, crm, op2 = register_tuple
        
        # 인코딩 패턴
        encoding_key = f"op0={op0},op1={op1}"
        self.register_patterns[encoding_key].append(register_tuple)
        
        # 값 패턴
        if value == 0:
            self.register_patterns['zero_values'].append(register_tuple)
        elif value == 0xFFFFFFFFFFFFFFFF:
            self.register_patterns['all_ones'].append(register_tuple)
        elif (value & 0xFFFF) == 0:
            self.register_patterns['high_bits_only'].append(register_tuple)
        elif (value >> 48) == 0:
            self.register_patterns['low_bits_only'].append(register_tuple)
    
    def _analyze_naming_patterns(self):
        """네이밍 패턴을 분석합니다"""
        patterns = defaultdict(list)
        
        for register_tuple, name in REGISTER_NAMES.items():
            if name.startswith('SYS_APL_HID'):
                patterns['HID_registers'].append(name)
            elif name.startswith('SYS_APL_PMC'):
                patterns['PMC_registers'].append(name)
            elif name.startswith('SYS_APL_UPMC'):
                patterns['UPMC_registers'].append(name)
            elif 'ERR' in name:
                patterns['Error_registers'].append(name)
            elif 'CTRR' in name:
                patterns['CTRR_registers'].append(name)
            elif 'APRR' in name:
                patterns['APRR_registers'].append(name)
        
        return dict(patterns)
    
    def _analyze_encoding_patterns(self):
        """인코딩 패턴을 분석합니다"""
        patterns = defaultdict(list)
        
        for register_tuple in REGISTER_NAMES.keys():
            op0, op1, crn, crm, op2 = register_tuple
            patterns[f"op0_{op0}"].append(register_tuple)
            patterns[f"op1_{op1}"].append(register_tuple)
            patterns[f"crn_{crn}"].append(register_tuple)
            patterns[f"crm_{crm}"].append(register_tuple)
            patterns[f"op2_{op2}"].append(register_tuple)
        
        return dict(patterns)
    
    def _analyze_value_patterns(self):
        """값 패턴을 분석합니다"""
        # 실제 구현에서는 레지스터 값을 읽어서 분석
        return {
            'zero_values': [],
            'all_ones': [],
            'high_bits_only': [],
            'low_bits_only': []
        }
    
    def _analyze_bit_patterns(self):
        """비트 패턴을 분석합니다"""
        # 실제 구현에서는 레지스터 값의 비트 패턴을 분석
        return {
            'common_bit_fields': [],
            'reserved_bits': [],
            'control_bits': []
        }
    
    def _calculate_statistics(self, research_data):
        """통계를 계산합니다"""
        total_registers = research_data['total_registers']
        categories = research_data['categories']
        
        stats = {
            'total_registers': total_registers,
            'categories_count': len(categories),
            'largest_category': max(categories.keys(), key=lambda k: categories[k]['count']),
            'smallest_category': min(categories.keys(), key=lambda k: categories[k]['count']),
            'unknown_registers_count': len(research_data['unknown_registers']),
            'patterns_count': len(research_data['patterns'])
        }
        
        return stats
    
    def _generate_summary(self):
        """요약을 생성합니다"""
        if not self.research_data:
            return "연구 데이터가 없습니다."
        
        stats = self.research_data['statistics']
        return f"""
Apple 시스템 레지스터 연구 요약:
- 총 레지스터 수: {stats['total_registers']}
- 카테고리 수: {stats['categories_count']}
- 가장 큰 카테고리: {stats['largest_category']}
- 가장 작은 카테고리: {stats['smallest_category']}
- 알려지지 않은 레지스터: {stats['unknown_registers_count']}
- 발견된 패턴: {stats['patterns_count']}
        """.strip()
    
    def _generate_recommendations(self):
        """권장사항을 생성합니다"""
        recommendations = []
        
        if self.research_data.get('unknown_registers'):
            recommendations.append("알려지지 않은 레지스터들을 추가로 연구해보세요.")
        
        if len(self.research_data.get('patterns', {})) > 0:
            recommendations.append("발견된 패턴들을 더 자세히 분석해보세요.")
        
        recommendations.extend([
            "레지스터 값의 변화를 모니터링해보세요.",
            "다른 CPU 코어와의 차이점을 비교해보세요.",
            "시스템 상태에 따른 레지스터 동작을 관찰해보세요."
        ])
        
        return recommendations

# LLDB 명령어 매크로들
@lldb_command('research_apple_sysregs')
def ResearchAppleSysRegs(cmd_args=None):
    """Apple 시스템 레지스터를 연구합니다
    사용법: research_apple_sysregs [--verbose] [--output filename]
    """
    verbose = False
    output_file = None
    
    if cmd_args:
        for i, arg in enumerate(cmd_args):
            if arg == '--verbose':
                verbose = True
            elif arg == '--output' and i + 1 < len(cmd_args):
                output_file = cmd_args[i + 1]
    
    researcher = AppleSysRegResearcher()
    
    try:
        results = researcher.enumerate_all_registers(verbose=verbose)
        
        print("\n" + "="*60)
        print("Apple 시스템 레지스터 연구 결과")
        print("="*60)
        print(researcher._generate_summary())
        
        if output_file:
            report = researcher.generate_research_report(output_file)
            print(f"\n상세 보고서가 저장되었습니다: {output_file}")
        
    except Exception as e:
        print(f"연구 실패: {e}")

@lldb_command('analyze_register_behavior')
def AnalyzeRegisterBehavior(cmd_args=None):
    """특정 레지스터의 동작을 분석합니다
    사용법: analyze_register_behavior <register_name> [iterations] [delay]
    """
    if not cmd_args or len(cmd_args) < 1:
        print("사용법: analyze_register_behavior <register_name> [iterations] [delay]")
        return
    
    register_name = cmd_args[0]
    iterations = int(cmd_args[1]) if len(cmd_args) > 1 else 100
    delay = float(cmd_args[2]) if len(cmd_args) > 2 else 0.01
    
    researcher = AppleSysRegResearcher()
    
    try:
        result = researcher.research_register_behavior(register_name, iterations, delay)
        
        print(f"\n{register_name} 레지스터 동작 분석 결과:")
        print("-" * 50)
        print(f"반복 횟수: {result['iterations']}")
        print(f"고유 값 수: {result['unique_values']}")
        print(f"안정성: {'안정' if result['is_stable'] else '불안정'}")
        print(f"변화 횟수: {len(result['changes'])}")
        
        if result['changes']:
            print("\n변화 내역:")
            for change in result['changes'][:10]:  # 처음 10개만 표시
                print(f"  반복 {change['iteration']}: 0x{change['old_value']:016x} -> 0x{change['new_value']:016x}")
            if len(result['changes']) > 10:
                print(f"  ... 및 {len(result['changes']) - 10}개 더")
    
    except Exception as e:
        print(f"분석 실패: {e}")

@lldb_command('find_register_patterns')
def FindRegisterPatterns(cmd_args=None):
    """레지스터 패턴을 찾습니다
    사용법: find_register_patterns
    """
    researcher = AppleSysRegResearcher()
    
    try:
        patterns = researcher.find_register_patterns()
        
        print("\n레지스터 패턴 분석 결과:")
        print("=" * 50)
        
        for pattern_type, pattern_data in patterns.items():
            print(f"\n[{pattern_type}]")
            for pattern_name, registers in pattern_data.items():
                print(f"  {pattern_name}: {len(registers)}개")
                if len(registers) <= 5:
                    for reg in registers:
                        if isinstance(reg, tuple):
                            print(f"    {reg}")
                        else:
                            print(f"    {reg}")
                else:
                    print(f"    ... {len(registers)}개 레지스터")
    
    except Exception as e:
        print(f"패턴 분석 실패: {e}")

@lldb_command('discover_unknown_registers')
def DiscoverUnknownRegisters(cmd_args=None):
    """알려지지 않은 레지스터들을 발견합니다
    사용법: discover_unknown_registers [op0_max] [op1_max] [crn_max] [crm_max] [op2_max]
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
    
    researcher = AppleSysRegResearcher()
    
    try:
        print(f"알려지지 않은 레지스터 탐색 중... (범위: {ranges})")
        discovered = researcher.discover_unknown_registers(
            op0_range=ranges[0], op1_range=ranges[1], 
            crn_range=ranges[2], crm_range=ranges[3], op2_range=ranges[4]
        )
        
        print(f"\n발견된 레지스터: {len(discovered)}개")
        print("-" * 50)
        
        for reg in discovered[:20]:  # 처음 20개만 표시
            print(f"  {reg['encoding']}: 0x{reg['value']:016x}")
        
        if len(discovered) > 20:
            print(f"  ... 및 {len(discovered) - 20}개 더")
    
    except Exception as e:
        print(f"탐색 실패: {e}")

# 별칭들은 xnu.py에서 정의됨
