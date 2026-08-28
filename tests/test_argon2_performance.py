"""
Tests de rendimiento para Argon2id.

Mide el tiempo de hash y verificación con los parámetros OWASP,
y compara con variantes más livianas para encontrar el balance
óptimo entre seguridad y tiempo de respuesta.
"""
import time
from argon2 import PasswordHasher


PARAMS_CONFIGS = {
    "OWASP Recomendado (production)": {"time_cost": 3, "memory_cost": 65536, "parallelism": 4},
    "OWASP Mínimo (production)": {"time_cost": 2, "memory_cost": 46592, "parallelism": 4},
    "Rápido (testing/dev)": {"time_cost": 1, "memory_cost": 16384, "parallelism": 4},
    "Máxima Seguridad": {"time_cost": 5, "memory_cost": 131072, "parallelism": 4},
}

TEST_PASSWORDS = [
    "password123",
    "MiContraseñaSegura!2024",
    "a",  # contraseña muy corta
    "xK9#mP2$vL5nQ8wR3tY6",  # contraseña compleja
]


def benchmark_hash(ph: PasswordHasher, password: str, iterations: int = 5) -> dict:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        h = ph.hash(password)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg_ms = (sum(times) / len(times)) * 1000
    min_ms = min(times) * 1000
    max_ms = max(times) * 1000
    return {"avg_ms": round(avg_ms, 2), "min_ms": round(min_ms, 2), "max_ms": round(max_ms, 2), "hash": h}


def benchmark_verify(ph: PasswordHasher, password: str, stored_hash: str, iterations: int = 5) -> dict:
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = ph.verify(stored_hash, password)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg_ms = (sum(times) / len(times)) * 1000
    min_ms = min(times) * 1000
    max_ms = max(times) * 1000
    return {"avg_ms": round(avg_ms, 2), "min_ms": round(min_ms, 2), "max_ms": round(max_ms, 2), "valid": result}


def run_benchmarks():
    print("=" * 80)
    print("BENCHMARK DE ARGON2ID - PARÁMETROS OWASP")
    print("=" * 80)

    for config_name, params in PARAMS_CONFIGS.items():
        print(f"\n{'─' * 80}")
        print(f"Configuración: {config_name}")
        print(f"  time_cost={params['time_cost']}, memory_cost={params['memory_cost']}KB"
              f" ({params['memory_cost'] // 1024}MB), parallelism={params['parallelism']}")
        print(f"{'─' * 80}")

        ph = PasswordHasher(
            time_cost=params["time_cost"],
            memory_cost=params["memory_cost"],
            parallelism=params["parallelism"],
            hash_len=32,
            salt_len=16,
        )

        for pwd in TEST_PASSWORDS:
            print(f"\n  Contraseña: {'*' * len(pwd) if len(pwd) > 3 else pwd}")
            hash_result = benchmark_hash(ph, pwd)
            verify_result = benchmark_verify(ph, pwd, hash_result["hash"])
            print(f"    Hash:     avg={hash_result['avg_ms']}ms  "
                  f"min={hash_result['min_ms']}ms  max={hash_result['max_ms']}ms")
            print(f"    Verify:   avg={verify_result['avg_ms']}ms  "
                  f"min={verify_result['min_ms']}ms  max={verify_result['max_ms']}ms")
            print(f"    Hash len: {len(hash_result['hash'])} chars")

    print(f"\n{'=' * 80}")
    print("RECOMENDACIÓN: OWASP Recomendado (time_cost=3, memory=64MB, parallelism=4)")
    print("  - Balance óptimo entre seguridad y rendimiento")
    print("  - Tiempo de hash ~200-500ms (aceptable para registro/login)")
    print("  - Resistente a ataques GPU/ASIC y side-channel")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    run_benchmarks()
