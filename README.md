# What is XNU?

XNU kernel is part of the Darwin operating system for use in macOS and iOS operating systems. XNU is an acronym for X is Not Unix.
XNU is a hybrid kernel combining the Mach kernel developed at Carnegie Mellon University with components from FreeBSD and a C++ API for writing drivers called IOKit.
XNU runs on x86_64 and ARM64 for both single processor and multi-processor configurations.

# XNU kernel for debugging

xnu-kernel-for-debug/tools/lldbmacros

https://asahilinux.org/docs/hw/cpu/system-registers/

https://developer.arm.com/documentation/109576/0100/Pointer-Authentication-Code/Introduction-to-PAC

등의 자료를 바탕으로 apple silicon 전용 레지스터를 분석할 수 있는 lldb 스크립트를 추가하였습니다.

- 해당 repo 는 apple xnu 커널 저작권을 따라갑니다.

- 해당 repo 는 리버싱과 asahi 문서 기반으로 추측된 내용을 기반으로 합니다. 신뢰성있는 디버깅 스크립트가 아닙니다.