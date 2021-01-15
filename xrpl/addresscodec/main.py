import base58
from .exceptions import XRPLAddressCodecException
from .utils import XRPL_ALPHABET

MAX_32_BIT_UNSIGNED_INT = 4294967295

PREFIX_BYTES_MAIN = bytes([0x05, 0x44])  # 5, 68
PREFIX_BYTES_TEST = bytes([0x04, 0x93])  # 4, 147

# To better understand the cryptographic details, visit
# https://github.com/xrp-community/standards-drafts/issues/6

# General format of an X-Address:
# [← 2 byte prefix →|← 160 bits of account ID →|← 8 bits of flags →|← 64 bits of tag →]


def encode_xaddress(classic_address_bytes, tag, test):
    """
    classic_address_bytes: bytes, representing the classic address
    tag: int, the destination tag
    test: boolean, whether it is the test network or not (aka the main network)

    Returns the X-Address representation of the data
    """
    if len(classic_address_bytes) != 20:
        raise XRPLAddressCodecException("Account ID must be 20 bytes")

    if tag is not None and tag > MAX_32_BIT_UNSIGNED_INT:
        raise XRPLAddressCodecException("Invalid tag")

    flag = tag is not None
    if tag is None:
        tag = 0

    bytestring = PREFIX_BYTES_TEST if test else PREFIX_BYTES_MAIN
    bytestring += classic_address_bytes
    encoded_tag = bytes(
        [
            flag,
            tag & 0xFF,
            tag >> 8 & 0xFF,
            tag >> 16 & 0xFF,
            tag >> 24 & 0xFF,
            0,
            0,
            0,
            0,
        ]
    )
    bytestring += encoded_tag

    return base58.b58encode_check(bytestring, alphabet=XRPL_ALPHABET).decode("utf-8")


def decode_xaddress(xaddress):
    """
    xaddress: string, a base58-encoded X-Address.

    Returns:
        classic_address: the byte-encoded classic address
        tag: the destination tag
        is_test: whether the address is on the test network
    """
    decoded = base58.b58decode_check(
        xaddress, alphabet=XRPL_ALPHABET
    )  # convert b58 to bytes
    is_test = _is_test_address(decoded[:2])
    classic_address = decoded[2:22]
    tag = _get_tag_from_buffer(decoded[22:])  # extracts the destination tag

    return (classic_address, tag, is_test)


def _is_test_address(prefix):
    """
    prefix: the first 2 bytes of an X-Address

    Returns whether a decoded X-Address is a test address.
    """
    if PREFIX_BYTES_MAIN == prefix:
        return False
    if PREFIX_BYTES_TEST == prefix:
        return True
    raise XRPLAddressCodecException("Invalid X-Address: bad prefix")


def _get_tag_from_buffer(buffer):
    """
    buffer: bytes

    Returns the destination tag extracted from the suffix of the X-Address.
    """
    flag = buffer[0]
    if flag >= 2:
        raise XRPLAddressCodecException("Unsupported X-Address")
    if flag == 1:  # Little-endian to big-endian
        return (
            buffer[1] + buffer[2] * 0x100 + buffer[3] * 0x10000 + buffer[4] * 0x1000000
        )  # inverse of what happens in encode
    if flag != 0:
        raise XRPLAddressCodecException("Flag must be zero to indicate no tag")
    if bytes.fromhex("0000000000000000") != buffer[1:9]:
        raise XRPLAddressCodecException("Remaining bytes must be zero")
    return None
