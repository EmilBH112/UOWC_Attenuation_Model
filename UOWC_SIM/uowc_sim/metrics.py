
import math

def snr_linear(responsivity_A_per_W: float, Pr_W: float, noise_var: float) -> float:
    num = (responsivity_A_per_W * max(0.0, Pr_W)) ** 2
    den = max(1e-30, noise_var)
    return num / den

def snr_db(snr_lin: float) -> float:
    return 10.0 * math.log10(max(1e-30, snr_lin))

def qfunc(x: float) -> float:
    return 0.5 * math.erfc(x / math.sqrt(2.0))

def ber_from_snr(snr_lin: float) -> float:
    return qfunc(math.sqrt(max(0.0, snr_lin)))

def to_dBm(P_W: float) -> float:
    return 10.0 * math.log10(max(1e-30, P_W) / 1e-3)
