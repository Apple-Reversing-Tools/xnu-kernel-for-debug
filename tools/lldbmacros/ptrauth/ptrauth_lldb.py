"""
Implements lldb macros and helper functions for debugging PAC functionality
in xnu.
"""

from xnu import ArgumentError, ArgumentStringToInt, kern, lldb_command, unsigned

from .apple_kdf import kdf, KdfUsage
from .feat_pauth import Auth, AddPAC, Strip

_ARM_KEYS = ['DA', 'DB', 'IA', 'IB']
_ALL_KEYS = _ARM_KEYS + ['KERN']
_GLOBAL_KEYS = [i for i in _ALL_KEYS if not i.endswith('B')]
_SIGN_BIT = 1 << 55

_KERNEL_ROP_ID = 0xfeedfacefeedfacf
_KERNEL_KERNKEY_ID = _KERNEL_ROP_ID + 4
_KERNEL_JOP_ID = _KERNEL_KERNKEY_ID + 2


def _bottom_pac_bit(ptr):
    """ Compute the index of the lowest non-canonical address bit for a provided
        pointer.

        params:
            ptr - int, the input pointer

        returns:
            int, the index of the lowest non-canonical address bit in ptr
    """

    if (ptr & _SIGN_BIT) == 0:
        txsz = kern.GetGlobalVariable('gT0Sz')
    else:
        txsz = kern.GetGlobalVariable('gT1Sz')

    return 64 - txsz


def _tbi(ptr, data):
    """ Compute whether the top byte is ignored when translating the provided
        pointer.

        params:
            ptr - int, the input pointer
            data - bool, whether ptr is being used to access data (rather than
                   an instruction)

        returns:
            bool - whether ptr's top byte is ignored during this access
    """

    # pylint: disable=invalid-name
    TCR_TBI0_TOPBYTE_IGNORED = 1 << 37
    TCR_TBI1_TOPBYTE_IGNORED = 1 << 38
    TCR_TBID0_TBI_DATA_ONLY = 1 << 51
    TCR_TBID1_TBI_DATA_ONLY = 1 << 52

    sysreg_restore = kern.GetGlobalVariable('sysreg_restore')
    tcr_el1 = unsigned(sysreg_restore.tcr_el1)
    if (ptr & _SIGN_BIT) == 0:
        topbyte_ignored = tcr_el1 & TCR_TBI0_TOPBYTE_IGNORED
    else:
        topbyte_ignored = tcr_el1 & TCR_TBI1_TOPBYTE_IGNORED

    if (ptr & _SIGN_BIT) == 0:
        tbi_data_only = tcr_el1 & TCR_TBID0_TBI_DATA_ONLY
    else:
        tbi_data_only = tcr_el1 & TCR_TBID1_TBI_DATA_ONLY

    return topbyte_ignored and (data or not tbi_data_only)


def _enhanced_pac():
    """ Compute whether this CPU implements EnhancedPAC.

        returns:
            bool - whether this CPU implemented EnhancedPAC
    """

    pac_state = kern.GetGlobalVariable('faulting_pac_state')
    return pac_state.id_aa64isar1_el1_api in (0b0010, 0b0011)


def _enhanced_pac2():
    """ Compute whether this CPU implements EnhancedPAC2.

        returns:
            bool - whether this CPU implemented EnhancedPAC2
    """

    pac_state = kern.GetGlobalVariable('faulting_pac_state')
    return pac_state.id_aa64isar1_el1_api in (0b0100, 0b0101)


def _cpu_key(key_name):
    """ Looks up a key currently loaded into the CPU.

        Keys read from the CPU have already been diversified with MKey, but not
        mixed with KERNKey.  If this key will be passed to feat_pauth.AddPAC or
        feat_pauth.Auth, KERNKey should be mixed in by calling _mix_kernkey().

        params:
            key_name - str, one of 'DA', 'DB', 'IA', or 'IB'

        returns:
            (int, int) - the upper and lower 64 bits of the key (respectively)
    """

    pac_state = kern.GetGlobalVariable('faulting_pac_state')

    if key_name == 'DA':
        k_hi = unsigned(pac_state.apdakeyhi_el1)
        k_lo = unsigned(pac_state.apdakeylo_el1)
    elif key_name == 'DB':
        k_hi = unsigned(pac_state.apdbkeyhi_el1)
        k_lo = unsigned(pac_state.apdbkeylo_el1)
    elif key_name == 'IA':
        k_hi = unsigned(pac_state.apiakeyhi_el1)
        k_lo = unsigned(pac_state.apiakeylo_el1)
    elif key_name == 'IB':
        k_hi = unsigned(pac_state.apibkeyhi_el1)
        k_lo = unsigned(pac_state.apibkeylo_el1)
    else:
        raise ArgumentError('Invalid key name {}'.format(key_name))

    return (k_hi, k_lo)


def _mix_kernkey(k_hi, k_lo):
    """ Checks if KERNKey is currently enabled, and if so mixes it into the
        input key.

        This step should happen after the key is diversified with MKey
        (apple_kdf.kdf) but before the key is used (feat_pauth.AddPAC or
        feat_pauth.Auth).

        params:
           k_hi - int, the upper 64 bits of the input key
           k_lo - int, the lower 64 bits of the input key

        returns:
           (int, int) - (k_hi, k_lo), with KERNKey mixed in as needed
    """

    pac_state = kern.GetGlobalVariable('faulting_pac_state')

    if pac_state.apctl_el1_kernkeyen:
        k_hi ^= unsigned(pac_state.kernkeyhi_el1)
        k_lo ^= unsigned(pac_state.kernkeylo_el1)
    return k_hi, k_lo


@lldb_command('ptrauth_auth')
def PtrauthAuthCommand(cmd_args=None): # pylint: disable=invalid-name
    """
Authenticate a signed kernel pointer with an optional <modifier>.

Syntax: (lldb) ptrauth_auth <DA|DB|IA|IB> <ptr> [<modifier>]
    """
    if cmd_args is None or len(cmd_args) < 2 or \
            cmd_args[0].upper() not in _ARM_KEYS:
        raise ArgumentError()

    key_name = cmd_args[0].upper()
    ptr = ArgumentStringToInt(cmd_args[1])
    modifier = ArgumentStringToInt(cmd_args[2]) if len(cmd_args) > 2 else 0

    ret = ptrauth_auth(key_name, ptr, modifier)
    print('0x{:016x}'.format(ret))


def ptrauth_auth(key_name, ptr, modifier=0):
    """ Authenticate a signed pointer using one of the keys loaded into the
        CPU at panic time.

        params:
            key_name - str, one of 'DA', 'DB', 'IA', or 'IB'
            ptr - int, the input pointer
            modifier - int, a 64-bit diversifier

        returns:
            int, an authenticated version of the input pointer
    """
    k_hi, k_lo = _cpu_key(key_name)
    k_hi, k_lo = _mix_kernkey(k_hi, k_lo)

    b_key = key_name.endswith('B')
    bottom_pac_bit = _bottom_pac_bit(ptr)
    tbi = _tbi(ptr, key_name.startswith('D'))
    have_enhanced_pac2 = _enhanced_pac2()

    return Auth(ptr, k_hi, k_lo, b_key, modifier, bottom_pac_bit, tbi,
                have_enhanced_pac2)


@lldb_command('ptrauth_sign')
def PtrauthSignCommand(cmd_args=None): # pylint: disable=invalid-name
    """
Sign a kernel pointer with an optional <modifier>.

Syntax: (lldb) ptrauth_sign <DA|DB|IA|IB> <ptr> [<modifier>]
    """
    if cmd_args is None or len(cmd_args) < 2 or \
            cmd_args[0].upper() not in _ARM_KEYS:
        raise ArgumentError()

    key_name = cmd_args[0].upper()
    ptr = ArgumentStringToInt(cmd_args[1])
    modifier = ArgumentStringToInt(cmd_args[2]) if len(cmd_args) > 2 else 0

    ret = ptrauth_sign(key_name, ptr, modifier)
    print('0x{:016x}'.format(ret))


def ptrauth_sign(key_name, ptr, modifier=0):
    """ Sign a pointer using one of the keys loaded into the CPU at panic time.

        params:
            key_name - str, one of 'DA', 'DB', 'IA', or 'IB'
            ptr - int, the input pointer
            modifier - int, a 64-bit diverisifer

        returns:
            int, a signed version of the input pointer
    """
    k_hi, k_lo = _cpu_key(key_name)
    k_hi, k_lo = _mix_kernkey(k_hi, k_lo)

    bottom_pac_bit = _bottom_pac_bit(ptr)
    tbi = _tbi(ptr, key_name.startswith('D'))
    have_enhanced_pac = _enhanced_pac()
    have_enhanced_pac2 = _enhanced_pac2()

    return AddPAC(ptr, k_hi, k_lo, modifier, bottom_pac_bit, tbi,
                  have_enhanced_pac, have_enhanced_pac2)


@lldb_command('ptrauth_strip', 'D')
def PtrauthStripCommand(cmd_args=None, cmd_options={}): # pylint: disable=dangerous-default-value,invalid-name
    """
Strip the authentication bits from a signed pointer.

Syntax: (lldb) ptrauth_strip [-D] <ptr>
    -D: treat <ptr> as a data pointer, not an instruction pointer
    """
    if cmd_args is None or len(cmd_args) == 0:
        raise ArgumentError()

    ptr = ArgumentStringToInt(cmd_args[0])
    data = '-D' in cmd_options

    ret = ptrauth_strip(ptr, data)
    print('0x{:016x}'.format(ret))


def ptrauth_strip(ptr, data=False):
    """ Strip the authentication bits from a signed pointer.

        params:
            ptr - int, the input pointer
            data - bool, whether ptr is being used to access data (rather than
                   an instruction)

        returns:
            int, the original version of the input pointer
    """
    bottom_pac_bit = _bottom_pac_bit(ptr)
    tbi = _tbi(ptr, data)

    stripped_ptr = Strip(ptr, bottom_pac_bit, tbi)
    return stripped_ptr


@lldb_command('ptrauth_kernel_key')
def PtrauthKernelKeyCommand(cmd_args=None): # pylint: disable=invalid-name
    """
Compute a kernel PAC key.

There is currently no way to compute the DB or IB keys, which are
frequently changed at runtime and depend on the current_task().

Syntax: (lldb) ptrauth_key <DA|IA|KERN>
    """
    if cmd_args is None or len(cmd_args) < 1 or cmd_args[0].upper() not in _GLOBAL_KEYS:
        raise ArgumentError()

    key_name = cmd_args[0].upper()

    k_hi, k_lo = ptrauth_kernel_key(key_name)
    reg_name = 'KERNKey' if key_name == 'KERN' else 'AP{}Key'.format(key_name)
    print('{}Hi: 0x{:016x}'.format(reg_name, k_hi))
    print('{}Lo: 0x{:016x}'.format(reg_name, k_lo))


def ptrauth_kernel_key(key_name):
    """ Computes a kernel PAC key.

        The returned values have been diversified with MKey, but have not been
        mixed with KERNKey (if applicable on this CPU).  This value reflects
        what software should actually read out of the AP*Key registers
        at EL1.

        There is currently no way to compute the DB or IB keys, which are
        frequently changed at runtime and depend on the current_task().

        params:
            key_name - str, one of 'DA', 'IA', 'KERN'

        returns:
            (int, int) - the upper and lower 64 bits of the key (respectively)
    """
    pac_state = kern.GetGlobalVariable('faulting_pac_state')
    mkey_hi = unsigned(pac_state.acc_mkeyhi)
    mkey_lo = unsigned(pac_state.acc_mkeylo)

    if key_name == 'IA':
        data_lo = _KERNEL_JOP_ID
        usage = KdfUsage.APIAKey
    elif key_name == 'DA':
        data_lo = _KERNEL_JOP_ID + 2
        usage = KdfUsage.APDAKey
    elif key_name == 'KERN':
        data_lo = _KERNEL_KERNKEY_ID
        usage = KdfUsage.KERNKey
    else:
        raise ArgumentError('Invalid key name {}'.format(key_name))
    data_hi = data_lo + 1

    return kdf(mkey_hi, mkey_lo, data_hi, data_lo, usage)

@lldb_command('ptrauth_check_kernel_keys')
def PtrauthCheckCpuKeysCommand(cmd_args=None): # pylint: disable=invalid-name
    """
Checks that xnu's kernel keys are currently loaded into the CPU.

Syntax: (lldb) ptrauth_check_kernel_keys
    """
    if cmd_args is None:
        raise ArgumentError()

    ptrauth_check_kernel_keys()


def ptrauth_check_kernel_keys(silent=False):
    """ Checks that xnu's kernel keys are currently loaded into the CPU.

        params:
            silent - bool, whether to print() any mismatched keys

        returns:
            bool - whether all of the CPU keys match xnu's kernel keys
    """
    print_fn = print if not silent else lambda _: None
    ret = True

    for key_name in _GLOBAL_KEYS:
        k_hi, k_lo = ptrauth_kernel_key(key_name)
        if key_name == 'KERN':
            reg_name = 'KERNKey'
            pac_state = kern.GetGlobalVariable('faulting_pac_state')
            cpu_k_hi = unsigned(pac_state.kernkeyhi_el1)
            cpu_k_lo = unsigned(pac_state.kernkeylo_el1)
        else:
            reg_name = 'AP{}Key'.format(key_name)
            cpu_k_hi, cpu_k_lo = _cpu_key(key_name)

        match_str = 'Current {reg_name}{suffix}' \
            ' matches expected ' \
            '{reg_name}{suffix} (0x{expected:016x})'
        mismatch_str = 'Current {reg_name}{suffix} (0x{actual:016x})' \
            ' does not match expected ' \
            '{reg_name}{suffix} (0x{expected:016x})'

        if cpu_k_hi == k_hi:
            print_fn(match_str.format(reg_name=reg_name,
                                      suffix='Hi',
                                      expected=k_hi))
        else:
            print_fn(mismatch_str.format(reg_name=reg_name,
                                         suffix='Hi',
                                         actual=cpu_k_hi,
                                         expected=k_hi))
            ret = False

        if cpu_k_lo == k_lo:
            print_fn(match_str.format(reg_name=reg_name,
                                      suffix='Lo',
                                      expected=k_lo))
        else:
            print_fn(mismatch_str.format(reg_name=reg_name,
                                         suffix='Lo',
                                         actual=cpu_k_lo,
                                         expected=k_lo))
            ret = False

    return ret
