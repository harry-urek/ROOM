import os
import aioredis
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class SignalProto:
    def __init__(self, redis_port, redis_host):
        self.privateK = x25519.X25519PrivateKey.generate()
        self.publicK = self.privateK.public_key()
        self.redis = aioredis.from_url(f"redis://{redis_host}:{redis_port}")

    async def _derive_keys(self, shared_secret, salt):
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
        shared_secret = self.privateK.exchange(other_publicK)
        salt = os.urandom(32)
        encK, macK = await self._derive_keys(shared_secret=shared_secret, salt=salt)

        await self.redis.set(f"enc_K:{uid}", encK)
        await self.redis.set(f"mac_K:{uid}", macK)

    async def encrypt_m(self, uid, message):

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
        encK = await self.redis.get(f"enc_key:{client_id}")
        macK = await self.redis.get(f"mac_key:{client_id}")

        cipher = Cipher(algorithms.AES(encK), modes.GCM(iv, mac))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode()
