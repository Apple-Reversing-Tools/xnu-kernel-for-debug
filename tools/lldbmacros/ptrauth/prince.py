"""
Implements the PRINCE and Apple-specific Modified PRINCE encryption
algorithms.

This module is only intended for debugging Apple's implementation of ARM
FEAT_PAuth, and does NOT make any promises about performance or
cryptographic security.
"""

# This module's structure and naming scheme are patterned after the
# paper "PRINCE - A Low-latency Block Cipher for Pervasive Computing
# Applications".  Refer to this paper for further documentation.
#
# pylint: disable=invalid-name,missing-function-docstring

M_PRIME = [
    0x0888000000000000,
    0x4044000000000000,
    0x2202000000000000,
    0x1110000000000000,
    0x8880000000000000,
    0x0444000000000000,
    0x2022000000000000,
    0x1101000000000000,
    0x8808000000000000,
    0x4440000000000000,
    0x0222000000000000,
    0x1011000000000000,
    0x8088000000000000,
    0x4404000000000000,
    0x2220000000000000,
    0x0111000000000000,
    0x0000888000000000,
    0x0000044400000000,
    0x0000202200000000,
    0x0000110100000000,
    0x0000880800000000,
    0x0000444000000000,
    0x0000022200000000,
    0x0000101100000000,
    0x0000808800000000,
    0x0000440400000000,
    0x0000222000000000,
    0x0000011100000000,
    0x0000088800000000,
    0x0000404400000000,
    0x0000220200000000,
    0x0000111000000000,
    0x0000000088800000,
    0x0000000004440000,
    0x0000000020220000,
    0x0000000011010000,
    0x0000000088080000,
    0x0000000044400000,
    0x0000000002220000,
    0x0000000010110000,
    0x0000000080880000,
    0x0000000044040000,
    0x0000000022200000,
    0x0000000001110000,
    0x0000000008880000,
    0x0000000040440000,
    0x0000000022020000,
    0x0000000011100000,
    0x0000000000000888,
    0x0000000000004044,
    0x0000000000002202,
    0x0000000000001110,
    0x0000000000008880,
    0x0000000000000444,
    0x0000000000002022,
    0x0000000000001101,
    0x0000000000008808,
    0x0000000000004440,
    0x0000000000000222,
    0x0000000000001011,
    0x0000000000008088,
    0x0000000000004404,
    0x0000000000002220,
    0x0000000000000111,
]

RC = [
    0x0000000000000000,
    0x13198a2e03707344,
    0xa4093822299f31d0,
    0x082efa98ec4e6c89,
    0x452821e638d01377,
    0xbe5466cf34e90c6c,
    0x7ef84f78fd955cb1,
    0x85840851f1ac43aa,
    0xc882d32f25323c54,
    0x64a51195e0e3610d,
    0xd3b5a399ca0c2399,
    0xc0ac29b7c97c50dd
]

RC_Apple = [
    0x0000000000000000,
    0x13198a2e03707344,
    0xa4093822299f31d0,
    0x082efa98ec4e6c89,
    0x452821e638d01377,
    0xbe5466cf34e90c6c,
    0xc0ac29b7c97c50dd,
    0x3f84d5b5b5470917,
    0x9216d5d98979fb1b,
    0xd1310ba698dfb5ac,
    0x2ffd72dbd01adfb7,
    0xb8e1afed6a267e97
]

S = [0xb, 0xf, 0x3, 0x2,
     0xa, 0xc, 0x9, 0x1,
     0x6, 0x7, 0x8, 0x0,
     0xe, 0x5, 0xd, 0x4]

SR = [0, 5, 10, 15,
      4, 9, 14, 3,
      8, 13, 2, 7,
      12, 1, 6, 11]


def s(state):
    ret = 0
    for i in range(0, 64, 4):
        nybble = (state >> i) & 0b1111
        ret |= (S[nybble] << i)
    return ret


def s_inv(state):
    ret = 0
    for i in range(0, 64, 4):
        nybble = (state >> i) & 0b1111
        ret |= (S.index(nybble) << i)
    return ret


def extract_nybble(val, i):
    return (val >> ((15 - i) * 4)) & 0b1111


def set_nybble(val, i):
    return val << ((15 - i) * 4)


def sr(state):
    ret = 0
    for i in range(16):
        nybble = extract_nybble(state, SR[i])
        ret |= set_nybble(nybble, i)
    return ret


def sr_inv(state):
    ret = 0
    for i in range(16):
        sr_inv_i = SR.index(i)
        nybble = extract_nybble(state, sr_inv_i)
        ret |= set_nybble(nybble, i)
    return ret


def m(state):
    state = m_prime(state)
    state = sr(state)
    return state


def m_inv(state):
    state = sr_inv(state)
    state = m_prime(state)
    return state


def m_prime(state):
    ret = 0
    for i in range(0, 64):
        state_i = (state >> (63-i)) & 1
        ret ^= state_i * M_PRIME[i]
    return ret


def prince_core(state, k1, rc=RC): # pylint: disable=dangerous-default-value
    state ^= k1
    state ^= rc[0]

    for i in range(1, 6):
        state = s(state)
        state = m(state)
        state ^= rc[i]
        state ^= k1

    state = s(state)
    state = m_prime(state)
    state = s_inv(state)

    for i in range(6, 11):
        state ^= k1
        state ^= rc[i]
        state = m_inv(state)
        state = s_inv(state)

    state ^= rc[11]
    state ^= k1

    return state


def prince(val, k0, k1, rc=RC): # pylint: disable=dangerous-default-value
    k0_ror_1 = (k0 >> 1) | ((k0 & 1) << 63)
    k0_inv = k0_ror_1 ^ (k0 >> 63)

    state = val ^ k0
    state = prince_core(state, k1, rc)
    state = state ^ k0_inv

    return state


def modified_prince(val, k0, k1, modifier):
    return prince(val, k0, k1 ^ modifier, RC_Apple)
