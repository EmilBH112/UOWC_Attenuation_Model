
import math

def lambertian_order(theta_half_deg: float) -> float:
    # Compute LED Lambertian order m from semi-angle at half power (deg).
    theta = math.radians(theta_half_deg)
    return -math.log(2.0) / math.log(max(1e-12, math.cos(theta)))

def Pi_indicator(x: float) -> float:
    # Unit step Pi(x<=1).
    return 1.0 if x <= 1.0 else 0.0

def cpc_gain(n_lens: float, fov_deg: float, phi_deg: float) -> float:
    # Receiver collection optics gain per eq. (19): n^2 / sin^2(FOV) within FOV, else 0.
    phi = abs(phi_deg)
    fov = abs(fov_deg)
    if phi > fov:
        return 0.0
    s = math.sin(math.radians(fov))
    if s == 0.0:
        return 0.0
    return (n_lens ** 2) / (s ** 2)

def tx_optics_gain(f1: float = None, f2: float = None, keplerian: bool = False, default: float = 1.0) -> float:
    # TX optics gain per eq. (20)/(21). If focal lengths not provided, return default (1.0).
    if f1 is None or f2 is None:
        return default
    if keplerian:
        return f2 / f1
    # Galilean (magnitude of f1 used)
    return f2 / abs(f1)
