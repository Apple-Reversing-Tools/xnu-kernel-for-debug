
https://asahilinux.org
기반으로 제작한 lldb script


## 새로 추가된 파일들

### 1. Apple System Register 관련 도구들
- **apple_sysreg_definitions.py** - Apple 시스템 레지스터 정의
- **apple_sysreg_docs.py** - Apple 시스템 레지스터 문서화 도구
- **apple_sysreg_dump.py** - Apple 시스템 레지스터 덤프 도구
- **apple_sysreg_parser.py** - Apple 시스템 레지스터 파서
- **apple_sysreg_reader.py** - Apple 시스템 레지스터 리더
- **apple_sysreg_research.py** - Apple 시스템 레지스터 연구 도구
- **apple_sysreg_simple.py** - Apple 시스템 레지스터 간단 도구
- **test_apple_sysreg.py** - Apple 시스템 레지스터 테스트

### 2. 문서 파일들
- **APPLE_SYSREG_QUICK_START.md** - Apple 시스템 레지스터 빠른 시작 가이드
- **APPLE_SYSREG_README.md** - Apple 시스템 레지스터 상세 문서
- **kbase_info.md** - 커널 베이스 정보 문서

### 3. Pointer Authentication 관련 도구들
- **ptrauth/** 폴더 전체
  - `__init__.py`
  - `apple_kdf.py` - Apple KDF (Key Derivation Function)
  - `feat_pauth.py` - Pointer Authentication 기능
  - `prince.py` - PRINCE 암호화
  - `ptrauth_lldb.py` - Pointer Authentication LLDB 도구

### 4. 기타 도구들
- **gdb_register_demo.py** - GDB 레지스터 데모
- **builtinkexts/** 폴더 - 내장 커널 익스텐션 관련 도구들


## 사용 방법

### Apple System Register 도구 사용
```bash
# 빠른 시작 가이드 참조
cat APPLE_SYSREG_QUICK_START.md

# 상세 문서 참조  
cat APPLE_SYSREG_README.md
```
