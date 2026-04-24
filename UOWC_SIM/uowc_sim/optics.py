
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


def pipe_tir_guiding_gain(d_m: float,
                          beam_axis_deg: float,
                          radius_m: float,
                          wall_reflectivity: float,
                          n_water: float,
                          n_wall: float,
                          coupling_efficiency: float,
                          max_guiding_gain: float) -> float:
    """Approximate gain from a glossy water-filled pipe with internal guiding.

    This combines reduced geometric spread (guided path) with per-bounce wall/TIR loss.
    """
    if d_m <= 0.0:
        return 1.0

    theta_axis_deg = min(89.0, max(0.1, abs(beam_axis_deg)))
    theta_axis = math.radians(theta_axis_deg)

    n_water = max(1.0, n_water)
    n_wall = max(1e-9, n_wall)
    wall_reflectivity = min(1.0, max(0.0, wall_reflectivity))
    coupling_efficiency = min(1.0, max(0.0, coupling_efficiency))

    theta_normal_deg = 90.0 - theta_axis_deg
    critical_deg = 90.0
    if n_water > n_wall:
        critical_deg = math.degrees(math.asin(n_wall / n_water))
    tir_active = theta_normal_deg >= critical_deg

    reflectivity_effective = 0.999 if tir_active else wall_reflectivity
    radius = max(1e-5, radius_m)
    bounces_per_m = math.tan(theta_axis) / (2.0 * radius)
    bounce_transmission = reflectivity_effective ** (bounces_per_m * d_m)

    confinement_gain = (max(0.1, d_m) / 0.2) ** 2
    confinement_gain = min(max(1.0, confinement_gain), max(1.0, max_guiding_gain))

    return coupling_efficiency * confinement_gain * bounce_transmission
