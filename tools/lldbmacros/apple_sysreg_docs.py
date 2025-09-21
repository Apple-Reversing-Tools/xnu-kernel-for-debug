"""
Apple 시스템 레지스터 문서화 및 설명 기능

이 모듈은 Apple Silicon 프로세서의 시스템 레지스터들에 대한 상세한 문서와 설명을 제공합니다.
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

class AppleSysRegDocumentation:
    """Apple 시스템 레지스터 문서화 클래스"""
    
    def __init__(self):
        self.target = GetTarget()
        self.process = GetProcess()
        self.parser = AppleSysRegParser()
        self.documentation = self._load_documentation()
    
    def _load_documentation(self):
        """레지스터 문서를 로드합니다"""
        return {
            # HID 레지스터 문서
            'HID': {
                'SYS_APL_HID0_EL1': {
                    'description': 'Hardware Implementation Defined Register 0',
                    'purpose': 'CPU 기능 제어 및 최적화 설정',
                    'bit_fields': {
                        20: {'name': 'Loop Buffer Disable', 'description': '루프 버퍼 비활성화'},
                        21: {'name': 'AMX Cache Fusion Disable', 'description': 'AMX 캐시 퓨전 비활성화'},
                        25: {'name': 'IC Prefetch Limit One Brn', 'description': '명령어 캐시 프리페치 제한'},
                        28: {'name': 'Fetch Width Disable', 'description': '페치 폭 비활성화'},
                        33: {'name': 'PMULL Fuse Disable', 'description': 'PMULL 퓨즈 비활성화'},
                        36: {'name': 'Cache Fusion Disable', 'description': '캐시 퓨전 비활성화'},
                        45: {'name': 'Same Pg Power Optimization', 'description': '같은 페이지 파워 최적화'},
                        (60, 62): {'name': 'Instruction Cache Prefetch Depth', 'description': '명령어 캐시 프리페치 깊이'}
                    },
                    'notes': '대부분의 비트는 CPU 기능을 비활성화하는 chicken bits입니다.',
                    'references': ['Apple Silicon Architecture Guide', 'ARM System Registers']
                },
                'SYS_APL_EHID0_EL1': {
                    'description': 'E-core Hardware Implementation Defined Register 0',
                    'purpose': 'E-core 전용 기능 제어',
                    'bit_fields': {
                        45: {'name': 'nfpRetFwdDisb', 'description': 'E-core 전용 기능 비활성화'}
                    },
                    'notes': 'E-core에서만 사용되는 기능 제어 레지스터입니다.',
                    'references': ['Apple Silicon E-core Architecture']
                },
                'SYS_APL_HID1_EL1': {
                    'description': 'Hardware Implementation Defined Register 1',
                    'purpose': '고급 CPU 기능 제어',
                    'bit_fields': {
                        14: {'name': 'Disable CMP-Branch Fusion', 'description': 'CMP-브랜치 퓨전 비활성화'},
                        15: {'name': 'ForceMextL3ClkOn', 'description': 'L3 클럭 강제 활성화'},
                        23: {'name': 'rccForceAllIexL3ClksOn', 'description': '모든 IEX L3 클럭 강제 활성화'},
                        24: {'name': 'rccDisStallInactiveIexCtl', 'description': '비활성 IEX 제어 스톨 비활성화'},
                        25: {'name': 'disLspFlushWithContextSwitch', 'description': '컨텍스트 스위치 시 LSP 플러시 비활성화'},
                        44: {'name': 'Disable AES Fusion across groups', 'description': '그룹 간 AES 퓨전 비활성화'},
                        49: {'name': 'Disable MSR Speculation DAIF', 'description': 'MSR 추측 DAIF 비활성화'},
                        54: {'name': 'Trap SMC', 'description': 'SMC 트랩'},
                        58: {'name': 'enMDSBStallPipeLineECO', 'description': 'MDSB 스톨 파이프라인 ECO 활성화'},
                        60: {'name': 'Enable Branch Kill Limit / SpareBit6', 'description': '브랜치 킬 제한 활성화'}
                    },
                    'notes': '고급 CPU 기능과 성능 최적화를 제어합니다.',
                    'references': ['Apple Silicon Performance Tuning']
                }
            },
            
            # Performance Counter 문서
            'Performance_Counters': {
                'SYS_APL_PMCR0_EL1': {
                    'description': 'Performance Monitor Control Register 0',
                    'purpose': '성능 카운터 제어 및 설정',
                    'bit_fields': {
                        (0, 7): {'name': 'Counter Enable PMC 7-0', 'description': 'PMC 0-7 카운터 활성화'},
                        (8, 10): {'name': 'Interrupt Mode', 'description': '인터럽트 모드 (0=off, 1=PMI, 2=AIC, 3=HALT, 4=FIQ)'},
                        11: {'name': 'PMI Interrupt Active', 'description': 'PMI 인터럽트 활성 (0으로 클리어)'},
                        (12, 19): {'name': 'Enable PMI for PMC 7-0', 'description': 'PMC 0-7에 대한 PMI 활성화'},
                        20: {'name': 'Disable Counting on PMI', 'description': 'PMI에서 카운팅 비활성화'},
                        22: {'name': 'Block PMIs until after eret', 'description': 'eret 후까지 PMI 차단'},
                        23: {'name': 'Count Global L2C Events', 'description': '글로벌 L2C 이벤트 카운팅'},
                        30: {'name': 'User-mode Access Enable', 'description': '사용자 모드 접근 활성화'},
                        (32, 33): {'name': 'Counter Enable PMC 9-8', 'description': 'PMC 8-9 카운터 활성화'},
                        (44, 45): {'name': 'Enable PMI for PMC 9-8', 'description': 'PMC 8-9에 대한 PMI 활성화'}
                    },
                    'notes': '성능 모니터링의 핵심 제어 레지스터입니다.',
                    'references': ['ARM Performance Monitor Unit', 'Apple Silicon Performance Counters']
                },
                'SYS_APL_PMC0_EL1': {
                    'description': 'Performance Monitor Counter 0',
                    'purpose': 'CPU 사이클 카운터 (고정)',
                    'bit_fields': {
                        (0, 47): {'name': 'Counter Value', 'description': '카운터 값 (M1: 48비트, M2: 64비트)'},
                        47: {'name': 'Overflow Bit', 'description': '오버플로우 비트 (M1에서 PMI 트리거)'},
                        63: {'name': 'Overflow Bit', 'description': '오버플로우 비트 (M2에서 PMI 트리거)'}
                    },
                    'notes': 'CPU 사이클을 카운트하는 고정 카운터입니다.',
                    'references': ['ARM Performance Monitor Unit']
                }
            },
            
            # Error Handling 문서
            'Error_Handling': {
                'SYS_APL_L2C_ERR_STS_EL1': {
                    'description': 'L2 Cache Error Status Register',
                    'purpose': 'L2 캐시 에러 상태 및 제어',
                    'bit_fields': {
                        1: {'name': 'Recursive Fault', 'description': '재귀적 폴트 (다른 폴트가 대기 중일 때 발생)'},
                        7: {'name': 'Access Fault', 'description': '접근 폴트 (매핑되지 않은 물리 주소 등)'},
                        (34, 38): {'name': 'Enable Flags', 'description': '활성화 플래그 (iBoot 진입 시 모두 1)'},
                        39: {'name': 'Enable SError Interrupts', 'description': 'SError 인터럽트 활성화 (비동기 에러)'},
                        (40, 43): {'name': 'Enable Flags', 'description': '활성화 플래그 (iBoot 진입 시 모두 1)'},
                        56: {'name': 'Write-1-to-clear Behavior', 'description': '폴트 플래그에 대한 1-쓰기-클리어 동작'},
                        60: {'name': 'Some Enable', 'description': '일부 활성화 (진입 시 1)'}
                    },
                    'notes': 'L2 캐시 서브시스템의 폴트 제어 및 정보를 제공합니다.',
                    'references': ['ARM Cache Architecture', 'Apple Silicon Memory Hierarchy']
                },
                'SYS_APL_L2C_ERR_ADR_EL1': {
                    'description': 'L2 Cache Error Address Register',
                    'purpose': 'L2 캐시 폴트 주소 정보',
                    'bit_fields': {
                        (0, 41): {'name': 'Physical Address', 'description': '폴트의 물리 주소'},
                        42: {'name': 'Unknown Bit', 'description': '재귀적 명령어 페치 폴트 후 때때로 1'},
                        (55, 57): {'name': 'Access Type', 'description': '접근 타입 (5=데이터 쓰기, 6=데이터 읽기, 7=명령어 페치)'},
                        (61, 62): {'name': 'Core within Cluster', 'description': '폴트를 일으킨 클러스터 내 코어'}
                    },
                    'notes': 'L2 캐시 폴트의 주소와 접근 정보를 제공합니다.',
                    'references': ['ARM Cache Architecture']
                }
            },
            
            # Memory Protection 문서
            'Memory_Protection': {
                'SYS_APL_APRR_EL0': {
                    'description': 'Access Protection and Read-only Region Register (EL0)',
                    'purpose': 'EL0에서의 접근 보호 및 읽기 전용 영역 설정',
                    'bit_fields': {
                        'table': {
                            'description': '16개의 4비트 필드로 구성된 접근 보호 테이블',
                            'fields': {
                                'X': '실행 권한',
                                'W': '쓰기 권한', 
                                'R': '읽기 권한'
                            },
                            'index': 'PTE의 접근 보호 및 실행 보호 설정'
                        }
                    },
                    'notes': '페이지 테이블 엔트리의 권한을 제어하는 테이블입니다.',
                    'references': ['ARM Memory Management Unit', 'Apple Silicon Security']
                },
                'SYS_APL_CTRR_CTL_EL1': {
                    'description': 'Configurable Text Read-only Region Control Register',
                    'purpose': '설정 가능한 텍스트 읽기 전용 영역 제어',
                    'bit_fields': {
                        0: {'name': 'A MMU off write protect', 'description': 'A 영역 MMU 비활성화 시 쓰기 보호'},
                        1: {'name': 'A MMU on write protect', 'description': 'A 영역 MMU 활성화 시 쓰기 보호'},
                        2: {'name': 'B MMU off write protect', 'description': 'B 영역 MMU 비활성화 시 쓰기 보호'},
                        3: {'name': 'B MMU on write protect', 'description': 'B 영역 MMU 활성화 시 쓰기 보호'},
                        4: {'name': 'A PXN', 'description': 'A 영역 Privileged Execute Never'},
                        5: {'name': 'B PXN', 'description': 'B 영역 Privileged Execute Never'},
                        6: {'name': 'A UXN', 'description': 'A 영역 User Execute Never'},
                        7: {'name': 'B UXN', 'description': 'B 영역 User Execute Never'}
                    },
                    'notes': '코드 영역의 실행 권한을 제어합니다.',
                    'references': ['ARM Memory Management Unit', 'Code Signing']
                }
            },
            
            # Interrupts 문서
            'Interrupts': {
                'SYS_APL_IPI_RR_LOCAL_EL1': {
                    'description': 'Inter-processor Interrupt Round Robin Local Register',
                    'purpose': '로컬 IPI 라운드 로빈 제어',
                    'bit_fields': {
                        (0, 3): {'name': 'Target CPU', 'description': '대상 CPU'},
                        (28, 29): {'name': 'RR Type', 'description': '라운드 로빈 타입 (0=immediate, 1=retract, 2=deferred, 3=nowake)'}
                    },
                    'notes': 'AIC를 사용하지 않는 "빠른" IPI를 위한 레지스터입니다.',
                    'references': ['ARM Interrupt Controller', 'Apple Silicon Interrupts']
                },
                'SYS_APL_IPI_RR_GLOBAL_EL1': {
                    'description': 'Inter-processor Interrupt Round Robin Global Register',
                    'purpose': '글로벌 IPI 라운드 로빈 제어',
                    'bit_fields': {
                        (0, 3): {'name': 'Target CPU', 'description': '대상 CPU'},
                        (16, 20): {'name': 'Target Cluster', 'description': '대상 클러스터'},
                        (28, 29): {'name': 'RR Type', 'description': '라운드 로빈 타입 (0=immediate, 1=retract, 2=deferred, 3=nowake)'}
                    },
                    'notes': '클러스터 간 IPI를 위한 글로벌 레지스터입니다.',
                    'references': ['ARM Interrupt Controller', 'Apple Silicon Interrupts']
                }
            },
            
            # Power Management 문서
            'Power_Management': {
                'SYS_APL_ACC_OVRD_EL1': {
                    'description': 'Apple Core Cluster Override Register',
                    'purpose': 'Apple 코어 클러스터 전력 관리 제어',
                    'bit_fields': {
                        (13, 14): {'name': 'OK To Power Down SRM', 'description': 'SRM 전력 다운 허용 (3=deepsleep)'},
                        (15, 16): {'name': 'Disable L2 Flush For ACC Sleep', 'description': 'ACC 슬립을 위한 L2 플러시 비활성화 (2=deepsleep)'},
                        (17, 18): {'name': 'OK To Train Down Link', 'description': '링크 다운 트레이닝 허용 (3=deepsleep)'},
                        (25, 26): {'name': 'OK To Power Down CPM', 'description': 'CPM 전력 다운 허용 (2=deny, 3=deepsleep)'},
                        (27, 28): {'name': 'CPM Wakeup', 'description': 'CPM 웨이크업 (3=force)'},
                        29: {'name': 'Disable Clock Dtr', 'description': '클럭 DTR 비활성화'},
                        32: {'name': 'Disable PIO On WFI CPU', 'description': 'WFI CPU에서 PIO 비활성화'},
                        34: {'name': 'Enable Deep Sleep', 'description': '딥 슬립 활성화'}
                    },
                    'notes': '코어 복합체와 전력 관리 설정을 제어합니다.',
                    'references': ['Apple Silicon Power Management', 'ARM Power Management']
                }
            }
        }
    
    def get_register_documentation(self, register_name):
        """특정 레지스터의 문서를 가져옵니다"""
        for category, registers in self.documentation.items():
            if register_name in registers:
                return registers[register_name]
        return None
    
    def get_category_documentation(self, category):
        """특정 카테고리의 문서를 가져옵니다"""
        return self.documentation.get(category, {})
    
    def generate_register_help(self, register_name):
        """레지스터 도움말을 생성합니다"""
        doc = self.get_register_documentation(register_name)
        if not doc:
            return f"'{register_name}'에 대한 문서를 찾을 수 없습니다."
        
        help_text = []
        help_text.append(f"레지스터: {register_name}")
        help_text.append("=" * 50)
        help_text.append(f"설명: {doc.get('description', 'N/A')}")
        help_text.append(f"목적: {doc.get('purpose', 'N/A')}")
        help_text.append("")
        
        if 'bit_fields' in doc:
            help_text.append("비트 필드:")
            for bit_range, field_info in doc['bit_fields'].items():
                if isinstance(bit_range, tuple):
                    bit_str = f"비트 {bit_range[0]}-{bit_range[1]}"
                else:
                    bit_str = f"비트 {bit_range}"
                help_text.append(f"  {bit_str}: {field_info['name']}")
                help_text.append(f"    {field_info['description']}")
        
        if 'notes' in doc:
            help_text.append("")
            help_text.append(f"참고사항: {doc['notes']}")
        
        if 'references' in doc:
            help_text.append("")
            help_text.append("참고 자료:")
            for ref in doc['references']:
                help_text.append(f"  - {ref}")
        
        return "\n".join(help_text)
    
    def generate_category_help(self, category):
        """카테고리 도움말을 생성합니다"""
        doc = self.get_category_documentation(category)
        if not doc:
            return f"'{category}' 카테고리에 대한 문서를 찾을 수 없습니다."
        
        help_text = []
        help_text.append(f"카테고리: {category}")
        help_text.append("=" * 50)
        help_text.append(f"레지스터 수: {len(doc)}")
        help_text.append("")
        
        for reg_name, reg_doc in doc.items():
            help_text.append(f"• {reg_name}")
            help_text.append(f"  {reg_doc.get('description', 'N/A')}")
            help_text.append(f"  {reg_doc.get('purpose', 'N/A')}")
            help_text.append("")
        
        return "\n".join(help_text)
    
    def search_documentation(self, query):
        """문서를 검색합니다"""
        results = []
        query_lower = query.lower()
        
        for category, registers in self.documentation.items():
            for reg_name, reg_doc in registers.items():
                # 레지스터 이름 검색
                if query_lower in reg_name.lower():
                    results.append({
                        'type': 'register',
                        'name': reg_name,
                        'category': category,
                        'description': reg_doc.get('description', ''),
                        'match_type': 'name'
                    })
                
                # 설명 검색
                if 'description' in reg_doc and query_lower in reg_doc['description'].lower():
                    results.append({
                        'type': 'register',
                        'name': reg_name,
                        'category': category,
                        'description': reg_doc['description'],
                        'match_type': 'description'
                    })
                
                # 비트 필드 검색
                if 'bit_fields' in reg_doc:
                    for bit_range, field_info in reg_doc['bit_fields'].items():
                        if (query_lower in field_info['name'].lower() or 
                            query_lower in field_info['description'].lower()):
                            results.append({
                                'type': 'bit_field',
                                'register': reg_name,
                                'category': category,
                                'bit_range': bit_range,
                                'field_name': field_info['name'],
                                'description': field_info['description'],
                                'match_type': 'bit_field'
                            })
        
        return results
    
    def generate_complete_documentation(self, output_file=None):
        """완전한 문서를 생성합니다"""
        doc = {
            'title': 'Apple 시스템 레지스터 완전 문서',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'categories': self.documentation,
            'index': self._generate_index(),
            'glossary': self._generate_glossary()
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)
            print(f"완전한 문서가 저장되었습니다: {output_file}")
        
        return doc
    
    def _generate_index(self):
        """문서 인덱스를 생성합니다"""
        index = {}
        
        for category, registers in self.documentation.items():
            index[category] = list(registers.keys())
        
        return index
    
    def _generate_glossary(self):
        """용어 사전을 생성합니다"""
        return {
            'ACC': 'Apple Core Cluster - Apple 코어 클러스터',
            'HID': 'Hardware Implementation Defined Register - 하드웨어 구현 정의 레지스터',
            'EHID': 'Hardware Implementation Defined Register (e-core) - E-core용 HID 레지스터',
            'IPI': 'Inter-processor Interrupt - 프로세서 간 인터럽트',
            'APRR': 'Access Protection and Read-only Region - 접근 보호 및 읽기 전용 영역',
            'CTRR': 'Configurable Text Read-only Region - 설정 가능한 텍스트 읽기 전용 영역',
            'PMC': 'Performance Monitor Counter - 성능 모니터 카운터',
            'PMCR': 'Performance Monitor Control Register - 성능 모니터 제어 레지스터',
            'LSU': 'Load Store Unit - 로드 스토어 유닛',
            'L2C': 'L2 Cache - L2 캐시',
            'FED': 'Front End Decoder - 프론트엔드 디코더',
            'MMU': 'Memory Management Unit - 메모리 관리 유닛',
            'VMSA': 'Virtual Memory System Architecture - 가상 메모리 시스템 아키텍처',
            'PXN': 'Privileged Execute Never - 권한 실행 금지',
            'UXN': 'User Execute Never - 사용자 실행 금지',
            'DAIF': 'Debug, Abort, IRQ, FIQ mask bits - 디버그, 어보트, IRQ, FIQ 마스크 비트',
            'SMC': 'Secure Monitor Call - 보안 모니터 호출',
            'HVC': 'Hypervisor Call - 하이퍼바이저 호출',
            'WFI': 'Wait For Interrupt - 인터럽트 대기',
            'PMI': 'Performance Monitor Interrupt - 성능 모니터 인터럽트',
            'AIC': 'Apple Interrupt Controller - Apple 인터럽트 컨트롤러',
            'FIQ': 'Fast Interrupt Request - 빠른 인터럽트 요청',
            'IRQ': 'Interrupt Request - 인터럽트 요청'
        }

# LLDB 명령어 매크로들
@lldb_command('help_apple_sysreg')
def HelpAppleSysReg(cmd_args=None):
    """Apple 시스템 레지스터 도움말을 표시합니다
    사용법: help_apple_sysreg <register_name>
    """
    if not cmd_args or len(cmd_args) != 1:
        print("사용법: help_apple_sysreg <register_name>")
        print("사용 가능한 레지스터 목록을 보려면: list_apple_sysregs")
        return
    
    register_name = cmd_args[0]
    doc = AppleSysRegDocumentation()
    
    help_text = doc.generate_register_help(register_name)
    print(help_text)

@lldb_command('help_apple_sysreg_category')
def HelpAppleSysRegCategory(cmd_args=None):
    """Apple 시스템 레지스터 카테고리 도움말을 표시합니다
    사용법: help_apple_sysreg_category <category>
    """
    if not cmd_args or len(cmd_args) != 1:
        print("사용법: help_apple_sysreg_category <category>")
        print("사용 가능한 카테고리: " + ", ".join(REGISTER_CATEGORIES.keys()))
        return
    
    category = cmd_args[0]
    doc = AppleSysRegDocumentation()
    
    help_text = doc.generate_category_help(category)
    print(help_text)

@lldb_command('search_apple_sysreg')
def SearchAppleSysReg(cmd_args=None):
    """Apple 시스템 레지스터 문서를 검색합니다
    사용법: search_apple_sysreg <query>
    """
    if not cmd_args or len(cmd_args) != 1:
        print("사용법: search_apple_sysreg <query>")
        return
    
    query = cmd_args[0]
    doc = AppleSysRegDocumentation()
    
    results = doc.search_documentation(query)
    
    if not results:
        print(f"'{query}'에 대한 검색 결과가 없습니다.")
        return
    
    print(f"'{query}' 검색 결과 ({len(results)}개):")
    print("=" * 50)
    
    for result in results:
        if result['type'] == 'register':
            print(f"레지스터: {result['name']} ({result['category']})")
            print(f"  {result['description']}")
        elif result['type'] == 'bit_field':
            print(f"비트 필드: {result['field_name']} ({result['register']})")
            print(f"  {result['description']}")
        print()

@lldb_command('generate_apple_sysreg_docs')
def GenerateAppleSysRegDocs(cmd_args=None):
    """Apple 시스템 레지스터 완전 문서를 생성합니다
    사용법: generate_apple_sysreg_docs [output_file]
    """
    output_file = cmd_args[0] if cmd_args else None
    doc = AppleSysRegDocumentation()
    
    try:
        doc.generate_complete_documentation(output_file)
        if not output_file:
            print("문서 생성 완료")
    except Exception as e:
        print(f"문서 생성 실패: {e}")

@lldb_command('apple_sysreg_glossary')
def AppleSysRegGlossary(cmd_args=None):
    """Apple 시스템 레지스터 용어 사전을 표시합니다
    사용법: apple_sysreg_glossary [term]
    """
    doc = AppleSysRegDocumentation()
    glossary = doc._generate_glossary()
    
    if cmd_args and len(cmd_args) > 0:
        term = cmd_args[0].upper()
        if term in glossary:
            print(f"{term}: {glossary[term]}")
        else:
            print(f"'{term}'에 대한 정의를 찾을 수 없습니다.")
            print("사용 가능한 용어:")
            for key in sorted(glossary.keys()):
                print(f"  {key}")
    else:
        print("Apple 시스템 레지스터 용어 사전:")
        print("=" * 50)
        for term, definition in sorted(glossary.items()):
            print(f"{term}: {definition}")

# 별칭들은 xnu.py에서 정의됨
