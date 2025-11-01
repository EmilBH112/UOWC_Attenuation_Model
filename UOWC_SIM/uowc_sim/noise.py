
import math
Q_E = 1.602176634e-19
K_B = 1.380649e-23

def shot_variance(responsivity_A_per_W: float, Pr_W: float, B_Hz: float) -> float:
    return 2.0 * Q_E * responsivity_A_per_W * max(0.0, Pr_W) * max(0.0, B_Hz)

def thermal_variance(T_K: float, B_Hz: float, R_load_ohm: float) -> float:
    return (4.0 * K_B * max(0.0, T_K) * max(0.0, B_Hz)) / max(1e-30, R_load_ohm)

def dark_variance(Idark_A: float, B_Hz: float) -> float:
    return 2.0 * Q_E * max(0.0, Idark_A) * max(0.0, B_Hz)

def rin_variance(rin: float, Pr_W: float, B_Hz: float) -> float:
    return max(0.0, rin) * (max(0.0, Pr_W) ** 2) * max(0.0, B_Hz)

def total_variance(R_A_per_W: float, Pr_W: float, B_Hz: float, T_K: float, R_load_ohm: float, Idark_A: float, rin: float) -> float:
    return (shot_variance(R_A_per_W, Pr_W, B_Hz) +
            thermal_variance(T_K, B_Hz, R_load_ohm) +
            dark_variance(Idark_A, B_Hz) +
            rin_variance(rin, Pr_W, B_Hz))
