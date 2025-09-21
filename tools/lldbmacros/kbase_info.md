# kbase 읽기 기능 위치

## **주요 파일들**

### **1. core/kernelcore.py**
- **KernelTarget 클래스**: 커널 디버깅의 핵심 클래스
- **GetLoadAddressForSymbol()**: 심볼의 로드 주소를 가져오는 메서드
- **GetGlobalVariable()**: 커널 전역 변수를 가져오는 메서드

### **2. xnu.py**
- **kern 객체**: KernelTarget의 인스턴스
- **GetLLDBThreadForKernelThread()**: 커널 스레드 관련 기능
- **KernelDebugCommandsHelp()**: 커널 디버깅 명령어 도움말

### **3. microstackshot.py**
- **vm_kernel_stext**: 커널 텍스트 세그먼트 시작 주소
```python
base_kern_text = kern.GetGlobalVariable('vm_kernel_stext')
```

### **4. kmemory/kmem.py**
- **stext**: 커널 텍스트 세그먼트 주소
```python
self.stext = target.chkFindFirstGlobalVariable('vm_kernel_stext').xGetValueAsInteger()
```

### **5. kmemory/btlog.py**
- **stext**: 커널 텍스트 세그먼트 주소
```python
self.stext = target.chkFindFirstGlobalVariable('vm_kernel_stext').xGetValueAsInteger()
```

## 🔧 **주요 메서드들**

### **GetLoadAddressForSymbol(name, target=None)**
```python
def GetLoadAddressForSymbol(self, name, target=None):
    """심볼의 로드 주소를 가져옵니다."""
    name = str(name)
    syms_arr = target.FindSymbols(name)
    if syms_arr.IsValid() and len(syms_arr) > 0:
        symbol = syms_arr[0].GetSymbol()
        if symbol.IsValid():
            return int(symbol.GetStartAddress().GetLoadAddress(target))
    raise LookupError("Symbol not found: " + name)
```

### **GetGlobalVariable(name, target=None)**
```python
def GetGlobalVariable(name, target=None):
    """커널 전역 변수를 가져옵니다."""
    return value(target.FindGlobalVariables(name, 1).GetValueAtIndex(0))
```

## 📋 **사용 예시**

### **커널 베이스 주소 읽기:**
```python
# 커널 텍스트 세그먼트 시작 주소
kernel_text_start = kern.GetGlobalVariable('vm_kernel_stext')

# 특정 심볼의 로드 주소
symbol_addr = kern.GetLoadAddressForSymbol('_start')

# 커널 버전 문자열
kernel_version = kern.GetGlobalVariable('version')
```

### **LLDB 명령어로 사용:**
```lldb
# 커널 텍스트 세그먼트 시작 주소
(lldb) p/x (unsigned long)kern.GetGlobalVariable('vm_kernel_stext')

# 특정 심볼의 로드 주소
(lldb) p/x (unsigned long)kern.GetLoadAddressForSymbol('_start')

# 커널 버전
(lldb) p (char*)kern.GetGlobalVariable('version')
```

## 🎯 **핵심 포인트**

1. **kern 객체**: `core/kernelcore.py`의 `KernelTarget` 클래스 인스턴스
2. **vm_kernel_stext**: 커널 텍스트 세그먼트의 시작 주소를 나타내는 전역 변수
3. **GetLoadAddressForSymbol()**: 심볼의 로드 주소를 가져오는 메서드
4. **GetGlobalVariable()**: 커널 전역 변수를 가져오는 메서드

## 📁 **관련 파일들**

- `core/kernelcore.py`: 핵심 커널 디버깅 클래스
- `xnu.py`: 메인 LLDB 스크립트
- `microstackshot.py`: 마이크로 스택샷 관련
- `kmemory/kmem.py`: 커널 메모리 관리
- `kmemory/btlog.py`: 백트레이스 로그
- `pmap.py`: 페이지 맵 관련
- `memory.py`: 메모리 관련 유틸리티
