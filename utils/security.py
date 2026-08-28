"""
Módulo de seguridad con Argon2id.

Parámetros según OWASP Password Storage Cheat Sheet (2024):
- type: argon2id (hibrido, resistente a ataques side-channel y GPU)
- time_cost: 3 iteraciones (OWASP recomienda >= 3)
- memory_cost: 65536 KB (64 MB, OWASP recomienda >= 64 MB)
- parallelism: 4 threads (OWASP recomienda >= 4)
- hash_len: 32 bytes (256 bits de entropía)
- salt_len: 16 bytes (128 bits, genera automáticamente)
"""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

# Parámetros OWASP para Argon2id
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB en KB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

ph = PasswordHasher(
    time_cost=ARGON2_TIME_COST,
    memory_cost=ARGON2_MEMORY_COST,
    parallelism=ARGON2_PARALLELISM,
    hash_len=ARGON2_HASH_LEN,
    salt_len=ARGON2_SALT_LEN,
)


def hash_password(password: str) -> str:
    """Genera un hash Argon2id de la contraseña con parámetros OWASP."""
    return ph.hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verifica una contraseña contra su hash Argon2id.
    Retorna True si coincide, False si no.
    """
    try:
        return ph.verify(stored_hash, password)
    except VerifyMismatchError:
        return False
    except InvalidHashError:
        return False
