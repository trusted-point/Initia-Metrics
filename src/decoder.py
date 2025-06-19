from base64 import b64decode
from hashlib import sha256
from bech32 import bech32_encode, bech32_decode, convertbits
from typing import Union

class KeysUtils:
    default_bech32_prefix: str = ""

    @staticmethod
    def _ensure_bytes(pub_key: Union[bytes, str]) -> bytes:
        """
        Ensure that the public key is in bytes.
        If it is provided as a base64-encoded string, decode it first.

        Args:
            pub_key (Union[bytes, str]): The public key in bytes or base64-encoded string.

        Returns:
            bytes: The public key as bytes.
        """
        if isinstance(pub_key, str):
            return b64decode(pub_key)
        return pub_key

    @staticmethod
    def pub_key_to_consensus_hex(pub_key: Union[bytes, str]) -> str:
        """
        Convert a Tendermint Ed25519 public key to a consensus hex string.

        For Ed25519, the consensus address is SHA256(pubkey)[:20], uppercased hex.

        Args:
            pub_key (Union[bytes, str]): The public key as raw bytes or base64-encoded string.

        Returns:
            str: The consensus hex address (first 20 bytes of sha256(pub_key), in uppercase hex).
        """
        pub_key = KeysUtils._ensure_bytes(pub_key)
        sha256_digest = sha256(pub_key).digest()
        consensus_hex = sha256_digest[:20].hex().upper()
        return consensus_hex

    @staticmethod
    def pub_key_to_bech32(pub_key: Union[bytes, str], bech32_prefix: str = None, address_refix: str = "") -> str:
        """
        Convert a public key to a Bech32 address.

        Args:
            pub_key (Union[bytes, str]): The public key, either as bytes or as a base64-encoded string.
            bech32_prefix (str, optional): The Bech32 prefix. If None, defaults to KeysUtils.default_bech32_prefix.
            address_refix (str, optional): Additional prefix for the address. Defaults to "".

        Returns:
            str: The Bech32-encoded address.
        """

        if bech32_prefix is None:
            bech32_prefix = KeysUtils.default_bech32_prefix
        pub_key = KeysUtils._ensure_bytes(pub_key)

        address_bytes = sha256(pub_key).digest()[:20]
        converted_bits = convertbits(address_bytes, 8, 5)

        return bech32_encode(f"{bech32_prefix}{address_refix}", converted_bits)
    
    @staticmethod
    def valoper_to_account(valoper: str) -> str:
        prefix, words = bech32_decode(valoper)
        account_prefix = prefix.replace("valoper", "")
        return bech32_encode(account_prefix, words)

    @staticmethod
    def consensus_pubkey_bytes_to_hex(address_bytes: bytes) -> str:
        return address_bytes.hex().upper()

    @staticmethod
    def conver_valcons_to_hex(valcons: str) -> str:
        _ , data = bech32_decode(valcons)
        witness = convertbits(data, 5, 8, False)
        return ''.join(format(byte, '02x') for byte in witness).upper()
    

if __name__ == "__main__":

    KeysUtils.default_bech32_prefix = "init"
    pub_key = "Q+KbGyQzh+GgvHxsPjZQ6O0QIfutPOO47xBdcpze/co="
    _bytes_pub_key= b"\xbf\xa7kX\xfd\xc2\xcb\x9e\x1f\xc3h\xc8\xcf['\x8a\xe0\xa1\xd9\xb8"

    # valcons = KeysUtils.pub_key_to_bech32(pub_key=pub_key, address_refix="valcons")
    # print(valcons)
    # _hex = KeysUtils.pub_key_to_consensus_hex(pub_key=pub_key)
    # print(_hex)
    # _wallet = KeysUtils.valoper_to_account(valoper = "initvaloper19qnvqux2nqvw3p89njee5ma3jde4wvux0t2s2m")
    # print(_wallet)

    # _hex_1 = KeysUtils.pub_key_to_consensus_hex(pub_key=pub_key)
    # print(_hex_1)

    # _hex_2 = KeysUtils.pub_key_to_consensus_hex(pub_key=_bytes_pub_key)
    # print(_hex_2)
