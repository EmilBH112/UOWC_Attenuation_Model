
import math
from .optics import lambertian_order, Pi_indicator, cpc_gain

def received_power_led(Pt_W: float, eta_t: float, eta_r: float, c_m_inv: float, d_m: float,
                       theta_emit_deg: float, theta_half_deg: float,
                       g_tx: float, n_lens: float, fov_deg: float, phi_deg: float,
                       A_pd_m2: float, Fturb: float) -> float:
    # Eq. (16) LED-PS received power with alignment assumption; TS(phi)=1
    if d_m <= 0:
        return 0.0
    m = lambertian_order(theta_half_deg)
    cos_t = math.cos(math.radians(theta_emit_deg))
    lambert = (m + 1.0) / (2.0 * math.pi) * (max(0.0, cos_t) ** m)
    GTXPO = g_tx
    GRXCO = cpc_gain(n_lens, fov_deg, phi_deg)
    TS = 1.0
    PiFOV = Pi_indicator(abs(phi_deg) / max(1e-12, fov_deg))
    denom = 2.0 * math.pi * (d_m ** 2) * (1.0 - math.cos(math.radians(max(1e-9, theta_emit_deg))))
    geom = (A_pd_m2 * math.cos(math.radians(phi_deg))) / max(1e-30, denom)
    return (Pt_W * eta_t * eta_r * math.exp(-c_m_inv * d_m) * lambert *
            GTXPO * GRXCO * TS * Fturb * geom * PiFOV)

def received_power_ld(Pt_W: float, eta_t: float, eta_r: float, c_m_inv: float, d_m: float,
                      divergence_full_deg: float, g_tx: float, n_lens: float, fov_deg: float, phi_deg: float,
                      A_pd_m2: float, Fturb: float) -> float:
    # Eq. (22) LD-PS received power with alignment; TS(phi)=1
    if d_m <= 0:
        return 0.0
    GTXPO = g_tx
    GRXCO = cpc_gain(n_lens, fov_deg, phi_deg)
    TS = 1.0
    PiFOV = Pi_indicator(abs(phi_deg) / max(1e-12, fov_deg))
    theta = math.radians(max(1e-9, divergence_full_deg))
    denom = math.pi * (d_m ** 2) * (math.tan(theta) ** 2)
    geom = (A_pd_m2 * math.cos(math.radians(phi_deg))) / max(1e-30, denom)
    return (Pt_W * eta_t * eta_r * math.exp(-c_m_inv * d_m) *
            GTXPO * GRXCO * TS * Fturb * geom * PiFOV)
