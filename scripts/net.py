"""Novas tentativas com espera exponencial (sem jitter: comportamento determinístico) para chamadas externas."""

import time


def backoff(attempts, base, factor):
    """Esperas entre tentativas: base, base*factor, ... (attempts-1 valores)."""
    return [base * factor**i for i in range(attempts - 1)]


def retry(fn, what="", attempts=4, base=3.0, factor=3.0, sleep=time.sleep, log=print):
    """Chama fn(); se levantar exceção, espera e tenta de novo. Na última falha, repassa a exceção."""
    waits = backoff(attempts, base, factor)
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if i == attempts - 1:
                raise
            log(f"{what or 'chamada'}: tentativa {i + 1}/{attempts} falhou ({type(e).__name__}: {e}); nova em {waits[i]:.0f}s")
            sleep(waits[i])
