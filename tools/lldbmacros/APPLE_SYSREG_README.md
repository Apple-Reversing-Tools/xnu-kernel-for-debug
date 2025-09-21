# Apple Silicon 시스템 레지스터 분석 도구

이 프로젝트는 Apple Silicon 프로세서의 시스템 레지스터들을 포괄적으로 분석하고 연구할 수 있는 도구들을 제공합니다.


## 주요 기능

### 1. 시스템 레지스터 정의 (`apple_sysreg_definitions.py`)
- 100개 이상의 Apple 시스템 레지스터 정의
- 레지스터 카테고리별 분류 (HID, Performance Counters, Error Handling 등)
- Linux sys_reg 형식의 인코딩 지원

### 2. 레지스터 파싱 및 분석 (`apple_sysreg_parser.py`)
- 레지스터 값의 비트별 파싱
- 카테고리별 전용 파서 (HID, Performance Counter, Error 등)
- 사람이 읽기 쉬운 형태로 포맷팅

### 3. 레지스터 덤프 기능 (`apple_sysreg_dump.py`)
- 전체 또는 카테고리별 레지스터 덤프
- JSON/텍스트 형식으로 저장
- 덤프 비교 기능

### 4. 연구 및 열거 도구 (`apple_sysreg_research.py`)
- 레지스터 동작 패턴 분석
- 알려지지 않은 레지스터 발견
- 레지스터 간 상관관계 분석

### 5. 문서화 시스템 (`apple_sysreg_docs.py`)
- 상세한 레지스터 문서
- 비트 필드 설명
- 용어 사전 및 검색 기능

## 사용법

### 기본 명령어

#### 레지스터 디코딩
```lldb

# 인코딩으로 직접 읽기
(lldb) read_apple_sysreg --encoding s3_0_c15_c0_0
```

#### 레지스터 덤프
```lldb
# 모든 레지스터 덤프 (실제 값 읽기)
(lldb) dump_apple_sysregs

# 특정 카테고리 덤프
(lldb) dump_apple_sysregs HID

# 파일로 저장
(lldb) dump_apple_sysregs --save dump.json --format json

```



### 별칭 명령어

| 별칭 | 원래 명령어 | 설명 |
|------|-------------|------|
| `dasr` | `dump_apple_sysregs` | Apple 시스템 레지스터 덤프 |
| `das` | `dump_apple_sysreg` | 특정 레지스터 덤프 |
| `lasr` | `list_apple_sysregs` | 레지스터 목록 |
| `casr` | `compare_apple_sysregs` | 덤프 비교 |
| `rasr` | `read_apple_sysreg` | 레지스터 읽기 |

## 레지스터 카테고리

### 1. HID (Hardware Implementation Defined)
- CPU 기능 제어 및 최적화 설정
- Chicken bits (기능 비활성화)
- E-core 전용 레지스터 포함

### 2. Performance Counters
- 성능 모니터링 카운터
- PMC (Performance Monitor Counter)
- PMCR (Performance Monitor Control Register)

### 3. Error Handling
- LSU (Load Store Unit) 에러
- L2 Cache 에러
- FED (Front End Decoder) 에러
- MMU 에러

### 4. Apple Specific
- Apple만의 고유 기능
- 커널 키 관리
- VMSA (Virtual Memory System Architecture) 잠금

### 5. Memory Protection
- APRR (Access Protection and Read-only Region)
- CTRR (Configurable Text Read-only Region)
- 메모리 권한 제어

### 6. Interrupts
- IPI (Inter-processor Interrupt)
- 가상 머신 타이머
- 인터럽트 상태 관리

### 7. Power Management
- ACC (Apple Core Cluster) 제어
- 전력 관리 설정
- 딥 슬립 제어

### 8. Uncore Performance
- 클러스터 레벨 성능 카운터
- UPMC (Uncore Performance Monitor Counter)
- 시스템 전체 성능 모니터링

## 주요 레지스터 예시

### SYS_APL_HID0_EL1
```c
// 주요 비트 필드
[20] Loop Buffer Disable
[21] AMX Cache Fusion Disable  
[25] IC Prefetch Limit One "Brn"
[28] Fetch Width Disable
[33] PMULL Fuse Disable
[36] Cache Fusion Disable
[45] Same Pg Power Optimization
[62:60] Instruction Cache Prefetch Depth
```

### SYS_APL_PMCR0_EL1
```c
// 성능 카운터 제어
[7:0] Counter Enable for PMC #7-0
[10:8] Interrupt Mode (0=off 1=PMI 2=AIC 3=HALT 4=FIQ)
[11] PMI Interrupt Active
[19:12] Enable PMI for PMC #7-0
[20] Disable Counting on PMI
[30] User-mode Access Enable
```

### SYS_APL_L2C_ERR_STS_EL1
```c
// L2 캐시 에러 상태
[1] Recursive Fault
[7] Access Fault
[38..34] Enable Flags
[39] Enable SError Interrupts
[56] Write-1-to-clear Behavior
```

## 파일 구조

```
dbg/
├── apple_sysreg_definitions.py    # 레지스터 정의
├── apple_sysreg_parser.py         # 파싱 및 분석
├── apple_sysreg_dump.py           # 덤프 기능
├── apple_sysreg_research.py       # 연구 도구
├── apple_sysreg_docs.py           # 문서화
├── sysreg.py                      # 기존 sysreg.py (통합)
└── APPLE_SYSREG_README.md         # 이 파일
```

## 요구사항

- Python 3.6+
- LLDB (Low Level Debugger)
- Apple Silicon 프로세서 (M1, M2, M3 등)

## 실제 사용 예시

### 1. 기본 레지스터 읽기
```lldb
# HID0 레지스터 읽기
(lldb) read_apple_sysreg SYS_APL_HID0_EL1
# 출력: SYS_APL_HID0_EL1: 0x10002990120e0e00

# 인코딩으로 직접 읽기
(lldb) read_apple_sysreg --encoding s3_0_c15_c0_0
# 출력: s3_0_c15_c0_0: 0x10002990120e0e00
```




