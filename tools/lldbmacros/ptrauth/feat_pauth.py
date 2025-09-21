"""
Implements FEAT_PAuth in software, building on the encryption primitives in
prince.py.

This software implementation diverges from the ARM ARM in a couple of
notable ways:

- It replaces ComputePAC() with Apple's private cipher.

- The Python functions use slightly different inputs so that they can be
  implemented as "pure" functions which do not depend on internal CPU state.
  For example, the ARM ARM AddPAC() function uses implicit CPU state to turn
  a boolean input `data' into another boolean flag `tbi'.  The Python
  AddPAC() instead takes `tbi' as an explicit input, which lldbmacros can
  compute using information in an xnu core dump.
"""

from .prince import modified_prince

# pylint: disable=invalid-name,too-many-arguments,too-many-locals

def _BitMask(bit_from, bit_to):
    """ Compute a bitmask that includes all bits in a consecutive range.

        params:
            bit_to - int, address of the highest bit
            bit_from - int, address of the lowest bit

        returns:
            int - a bitmask that includes bits [bit_to, bit_from]
    """
    return ((1 << (bit_to - bit_from + 1)) - 1) << bit_from


def _PACMask(bottom_pac_bit, tbi):
    """ Compute a bitmask for where the PAC bits are stored in a pointer.

        params:
            bottom_pac_bit - int, the index of the lowest non-canonical address
                             bit
            tbi - bool, whether the CPU would ignore the top bits when
                  translating this pointer

        returns:
            int - a bitmask that includes all PAC bits contained in this
                  pointer
    """
    ret = _BitMask(bottom_pac_bit, 54)
    if not tbi:
        ret |= _BitMask(56, 63)
    return ret


def AddPAC(ptr, k_hi, k_lo, modifier=0, bottom_pac_bit=39, tbi=False,
           have_enhanced_pac=False, have_enhanced_pac2=False):
    """ Sign a provided pointer, by computing and mixing a
        pointer-authentication code into the non-canonical address bits.

        params:
            ptr - int, the input pointer
            k_hi - int, the upper 64 bits of the pointer-authentication key
            k_lo - int, the lower 64 bits of the pointer-authentication key
            modifier - int, a 64-bit diversifier
            bottom_pac_bit - int, the index of the lowest non-canonical address
                             bit
            tbi - bool, whether the CPU would ignore the top bits when
                  translating this pointer
            have_enhanced_pac - bool, whether the CPU implements EnhancedPAC
            have_enhanced_pac2 - bool, whether the CPU implements EnhancedPAC2

        returns:
            int, a signed version of the input pointer
    """
    top_bit = 55 if tbi else 63
    original_ptr = Strip(ptr, bottom_pac_bit, tbi)

    extension_mask = _BitMask(bottom_pac_bit, top_bit)
    extension_bits = ptr & extension_mask
    input_is_poisoned = extension_bits not in (0, extension_mask)

    if input_is_poisoned and have_enhanced_pac:
        pac = 0
    else:
        pac = modified_prince(original_ptr, k_hi, k_lo, modifier)
        if input_is_poisoned and not have_enhanced_pac2:
            pac ^= (1 << (top_bit - 1))

    pac_mask = _PACMask(bottom_pac_bit, tbi)

    ret = ptr
    if have_enhanced_pac2:
        ret ^= (pac & pac_mask)
    else:
        ret &= ~pac_mask
        ret |= (pac & pac_mask)
    return ret


def Auth(ptr, k_hi, k_lo, b_key, modifier=0, bottom_pac_bit=39, tbi=False,
         have_enhanced_pac2=False):
    """ Authenticate a provided pointer, returning either the original address
        or a poisoned version of it.

        params:
            ptr - int, the input pointer
            k_hi - int, the upper 64 bits of the pointer-authentication key
            k_lo - int, the lower 64 bits of the pointer-authentication key
            b_key - bool, whether [k_hi, k_lo] corresponds to a "B" key (i.e.,
                    one of AP{D,I}BKey)
            modifier - int, a 64-bit diversifier
            bottom_pac_bit - int, the index of the lowest non-canonical address
                             bit
            tbi - bool, whether the CPU would ignore the top bits when
                  translating this pointer
            have_enhanced_pac2 - bool, whether the CPU implements EnhancedPAC2

        returns:
            int, an authenticated version of the input pointer
    """
    original_ptr = Strip(ptr, bottom_pac_bit, tbi)
    pac = modified_prince(original_ptr, k_hi, k_lo, modifier)

    pac_mask = _PACMask(bottom_pac_bit, tbi)
    if have_enhanced_pac2:
        return ptr ^ (pac & pac_mask)

    ret = original_ptr
    if (ptr & pac_mask) != (pac & pac_mask):
        error_code = 0b10 if b_key else 0b01
        error_code_shift = 53 if tbi else 61
        ret &= ~(0b11 << error_code_shift)
        ret |= (error_code << error_code_shift)
    return ret


def Strip(ptr, bottom_pac_bit=39, tbi=False):
    """ Reconstruct the original address from a provided pointer, by replacing
        all pointer-authentication bits with 0 or 1 as appropriate.

        params:
            ptr - int, the input pointer
            bottom_pac_bit - int, the index of the lowest non-canonical address
                             bit
            tbi - bool, whether the CPU would ignore the top bits when
                  translating this pointer

        returns:
            int, the original version of the input pointer
    """
    pac_mask = _PACMask(bottom_pac_bit, tbi)
    ret = ptr & ~pac_mask
    if ptr & (1 << 55):
        ret |= pac_mask
    return ret
