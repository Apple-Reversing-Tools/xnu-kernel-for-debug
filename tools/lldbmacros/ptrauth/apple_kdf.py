"""
Implements the Key Derivation Function described in Section 5.4.8 of the
Apple ISA Extensions to ARMv8 version H13.
"""

from enum import IntEnum
from .prince import modified_prince


class KdfUsage(IntEnum):
    """ An enumeration describing which key is being derived. """
    # pylint: disable=invalid-name
    APIAKey = 0b0000
    APIBKey = 0b0001
    APDAKey = 0b0010
    APDBKey = 0b0011
    APGAKey = 0b0100
    KERNKey = 0b0101
    JAPIAKey = 0b1000
    JAPIBKey = 0b1001


def kdf(ikey_hi, ikey_lo, data_hi, data_lo, usage):
    """ Derives a new 128-bit output key from an input key and data.

        Typically the input key is {H,V}MKey, and the input data is the
        undiversified value which software wrote to the *Key registers.  For
        example, when software writes 0xfeedfacefeedfad0:0xfeedfacefeedfacf to
        APIBKey in Apple mode, hardware effectively updates APIBKey as follows:

            APIBKey <= kdf(MKeyHi, MKeyLo,
                           0xfeedfacefeedfad0, 0xfeedfacefeedfacf,
                           KdfUsage.APIBKey)

        params:
            ikey_hi - int, the upper 64 bits of the input key
            ikey_lo - int, the lower 64 bits of the input key
            data_hi - int, the upper 64 bits of the input data
            data_lo - int, the lower 64 bits of the input data
            usage - one of KdfUsage.*Key, indicating which key is being derived

        returns:
            (int, int), the upper and lower 64 bits of the output key
                        (respectively)
    """
    modifier1 = ((usage & 0b1000) << 2) | 0b00000 | (usage & 0b111)
    tmp1 = modified_prince(data_hi, ikey_hi, ikey_lo, modifier1)
    okey_hi = modified_prince(tmp1 ^ data_lo, ikey_hi, ikey_lo, modifier1)

    modifier2 = ((usage & 0b1000) << 2) | 0b01000 | (usage & 0b111)
    tmp2 = modified_prince(data_hi, ikey_hi, ikey_lo, modifier2)
    okey_lo = modified_prince(tmp2 ^ data_lo, ikey_hi, ikey_lo, modifier2)

    return (okey_hi, okey_lo)
