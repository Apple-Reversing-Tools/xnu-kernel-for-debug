"""
A software implementation of ARMv8.3 pointer authentication, including Apple
extensions.
"""

try:
    from .ptrauth_lldb import ptrauth_auth, ptrauth_check_kernel_keys, \
                              ptrauth_kernel_key, ptrauth_sign, ptrauth_strip
    __all__ = ['ptrauth_auth', 'ptrauth_check_kernel_keys',
               'ptrauth_kernel_key', 'ptrauth_sign', 'ptrauth_strip']
except ModuleNotFoundError as e:
    if e.name == 'lldb':
        # Sometimes you just need to launch a Python REPL, import
        # ptrauth.feat_pauth, and poke around with various inputs to Auth() or
        # AddPAC().  Allow that use-case, but warn the user that some stuff is
        # missing.
        print('{} package imported without lldb macros: {}'.format(__name__, e))
        __all__ = []
    else:
        raise
