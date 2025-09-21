# Apple 시스템 레지스터 빠른 시작 가이드

## 문제 해결

현재 LLDB에서 명령어가 인식되지 않는 문제가 있습니다. 다음 단계를 따라 해결하세요:

### 1. 모듈 다시 로드

```lldb
# 기존 모듈 언로드
(lldb) command script delete xnu

# 모듈 다시 로드
(lldb) command script import /Users/gap_dev/bob_proj/dbg/xnu.py
```

### 2. 테스트 명령어 실행

```lldb
# Apple 시스템 레지스터 테스트
(lldb) test_apple_sysreg
```

### 3. 기본 명령어들

```lldb
# 개별 레지스터 읽기
(lldb) read_apple_sysreg SYS_APL_HID0_EL1
(lldb) read_apple_sysreg --encoding s3_0_c15_c0_0


# 레지스터 덤프
(lldb) dump_apple_sysregs

```

## 문제가 지속되는 경우

### 1. 수동으로 모듈 로드

```lldb
# 각 모듈을 개별적으로 로드
(lldb) command script import /Users/gap_dev/bob_proj/dbg/apple_sysreg_reader.py
(lldb) command script import /Users/gap_dev/bob_proj/dbg/apple_sysreg_dump.py
(lldb) command script import /Users/gap_dev/bob_proj/dbg/apple_sysreg_research.py
(lldb) command script import /Users/gap_dev/bob_proj/dbg/apple_sysreg_docs.py
```

### 2. 직접 함수 호출

```lldb
# Python 코드로 직접 실행
(lldb) script
>>> from apple_sysreg_reader import AppleSysRegReader
>>> reader = AppleSysRegReader()
>>> value = reader.read_register_by_encoding(3, 0, 15, 0, 0)
>>> print(f"HID0: 0x{value:016x}")
```

## 예상 출력

성공적으로 작동하면 다음과 같은 출력을 볼 수 있습니다:

```
Apple 시스템 레지스터 테스트 시작...
✓ s3_0_c15_c0_0: 0x10002990120e0e00
✓ s3_0_c15_c1_0: 0x40000002000000
✗ s3_1_c15_c0_0: 읽기 실패
테스트 완료
```

