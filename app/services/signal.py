import os
import aioredis
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


# This class `SignalProto` implements a protocol for secure communication using asymmetric key
# exchange, key derivation, encryption, and decryption with AES-GCM mode.
class SignalProto:
    def __init__(self, redis_port, redis_host):
        self.privateK = x25519.X25519PrivateKey.generate()
        self.publicK = self.privateK.public_key()
        self.redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}")

    async def _derive_keys(self, shared_secret, salt):
        """
        The function `_derive_keys` uses the HKDF algorithm with SHA3-256 to derive encryption and MAC
        keys from a shared secret and salt.

        :param shared_secret: The `shared_secret` parameter in the `_derive_keys` function is typically a
        secret value that is derived from a key exchange protocol such as Diffie-Hellman key exchange. It
        is a secret value that is shared between two parties and used to derive encryption and
        authentication keys for secure communication
        :param salt: The `salt` parameter is a random value used as an additional input to the key
        derivation function (KDF) to increase the security of the derived keys. It helps prevent
        precomputed dictionary attacks and rainbow table attacks by introducing randomness into the key
        derivation process
        :return: The `_derive_keys` function returns two keys: `enc_key` and `mac_key`.
        """
        kdf = HKDF(
            algorithm=hashes.SHA3_256(),
            length=32 + 16,
            salt=salt,
            info=None,
            backend=None
        )
        keys = kdf.derive(shared_secret)
        enc_key, mac_key = keys[:32], keys[32:]
        return enc_key, mac_key

    async def handshake_3D(self, uid, other_publicK):
        """
        The `handshake_3D` function performs a key exchange process and derives encryption and MAC keys
        for a given user ID.

        :param uid: The `uid` parameter in the `handshake_3D` method likely stands for "user ID" and is
        used to uniquely identify a user or entity participating in the handshake process. It is used to
        associate the derived encryption and MAC keys (`encK` and `macK`) with a
        :param other_publicK: The `other_publicK` parameter in the `handshake_3D` method is likely the
        public key of the other party involved in the handshake process. This public key is used to
        perform key exchange with the private key of the current instance (`self.privateK`) to establish a
        shared secret
        """
        shared_secret = self.privateK.exchange(other_publicK)
        salt = os.urandom(32)
        encK, macK = await self._derive_keys(shared_secret=shared_secret, salt=salt)

        await self.redis.set(f"enc_K:{uid}", encK)
        await self.redis.set(f"mac_K:{uid}", macK)

    async def encrypt_m(self, uid, message):
        """
        The function `encrypt_m` takes a user ID and a message, retrieves encryption and MAC keys from
        Redis, encrypts the message using AES-GCM with PKCS7 padding, and returns the ciphertext, IV, and
        MAC.

        :param uid: The `uid` parameter in the `encrypt_m` method is used as a unique identifier for a user.
        It is used to retrieve encryption and MAC keys specific to that user from the Redis database. These
        keys are then used for encrypting the message along with generating an initialization vector (iv),
        padding
        :param message: The code you provided is an asynchronous function that encrypts a message using
        AES-GCM mode. It retrieves encryption and MAC keys from Redis based on the given user ID (uid),
        generates a random initialization vector (iv), pads the message using PKCS7 padding, encrypts the
        padded data, and
        :return: The `encrypt_m` function is returning a tuple containing the ciphertext, initialization
        vector (iv), and the message authentication code (mac).
        """

        encK = await self.redis.get(f"enc_K:{uid}")
        macK = await self.redis.get(f"enc_K:{uid}")

        iv = os.urandom(12)
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(encK), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        mac = encryptor.compute_digest()

        return ciphertext, iv, mac

    async def decrypt_message(self, client_id, ciphertext, iv, mac):
        """
        The `decrypt_message` function decrypts a ciphertext using AES encryption with GCM mode and returns
        the plaintext message.

        :param client_id: The `client_id` parameter is used to identify the client for whom the message is
        being decrypted. It is used to retrieve the encryption key (`encK`) and MAC key (`macK`) associated
        with that client from the Redis database
        :param ciphertext: The `ciphertext` parameter in the `decrypt_message` function is the encrypted
        message that you want to decrypt. It is the input data that was encrypted using an AES encryption
        algorithm with a specific key
        :param iv: Initialization vector (IV) is a random value used in the encryption process to ensure
        that the same plaintext does not encrypt to the same ciphertext. It is used along with the
        encryption key to provide randomness and uniqueness to the encryption algorithm
        :param mac: The `mac` parameter in the `decrypt_message` function is typically used to verify the
        integrity of the message. It stands for Message Authentication Code, which is a short piece of
        information used to authenticate a message and to ensure that it has not been tampered with
        :return: The `decrypt_message` method decrypts a ciphertext using AES encryption with GCM mode. It
        retrieves the encryption key (`encK`) and MAC key (`macK`) from Redis based on the `client_id`. It
        then decrypts the ciphertext using the encryption key and verifies the integrity using the MAC key.
        The decrypted plaintext is then unpadded and returned as a decoded string.
        """
        encK = await self.redis.get(f"enc_key:{client_id}")
        macK = await self.redis.get(f"mac_key:{client_id}")

        cipher = Cipher(algorithms.AES(encK), modes.GCM(iv, mac))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode()
