
from typing import Dict, List
import math
import numpy as np
from .config import SimulationConfig
from .turbulence import rng, draw_fturb
from .noise import total_variance
from .transmitter import received_power_led, received_power_ld
from .metrics import snr_linear, snr_db, ber_from_snr, to_dBm
from .optics import pipe_tir_guiding_gain

def run_sim(config: SimulationConfig) -> Dict[str, List[float]]:
    g = config.grid
    distances = np.arange(g.d_min_m, g.d_max_m + 1e-9, g.d_step_m, dtype=float)
    r = rng(g.seed)
    tx = config.transmitter
    rx = config.receiver
    water = config.water
    noise = config.noise
    turb = config.turb

    out_Pr = []
    out_SNRlin = []
    out_SNRdB = []
    out_BER = []
    out_Isig = []
    out_Inoise_rms = []
    out_Vsig = []
    out_Vnoise_rms = []

    for d in distances:
        acc_Pr = 0.0
        for _ in range(max(1, g.mc_realizations)):
            Ft = draw_fturb(turb.model, {
                "scint_index": turb.scint_index,
                "gg_alpha": turb.gg_alpha, "gg_beta": turb.gg_beta, "gg_nu": turb.gg_nu,
                "wb_k": turb.wb_k, "wb_lambda": turb.wb_lambda
            }, r)
            Fpipe = 1.0
            if config.pipe_tir.enabled:
                incidence_axis_deg = config.pipe_tir.incidence_axis_deg
                tir_beam_axis = (tx.led_divergence_deg / 2.0) if config.tx_type.lower() == "led" else (tx.ld_divergence_deg / 2.0)
                tir_beam_axis = tir_beam_axis if incidence_axis_deg is None else incidence_axis_deg
                Fpipe = pipe_tir_guiding_gain(
                    d_m=d,
                    beam_axis_deg=tir_beam_axis,
                    radius_m=config.pipe_tir.radius_m,
                    wall_reflectivity=config.pipe_tir.wall_reflectivity,
                    n_water=config.pipe_tir.water_refractive_index,
                    n_wall=config.pipe_tir.wall_refractive_index,
                    coupling_efficiency=config.pipe_tir.coupling_efficiency,
                    max_guiding_gain=config.pipe_tir.max_guiding_gain,
                )

            if config.tx_type.lower() == "led":
                Pr = received_power_led(
                    Pt_W=tx.power_W, eta_t=tx.eta_t, eta_r=rx.eta_r,
                    c_m_inv=water.alpha_m_inv + water.beta_m_inv, d_m=d,
                    theta_emit_deg=tx.led_divergence_deg, theta_half_deg=tx.led_theta_half_deg,
                    g_tx=tx.g_tx, n_lens=rx.n_lens, fov_deg=rx.fov_deg, phi_deg=0.0,
                    A_pd_m2=rx.area_m2, Fturb=Ft, Fpipe=Fpipe
                )
            else:
                Pr = received_power_ld(
                    Pt_W=tx.power_W, eta_t=tx.eta_t, eta_r=rx.eta_r,
                    c_m_inv=water.alpha_m_inv + water.beta_m_inv, d_m=d,
                    divergence_full_deg=tx.ld_divergence_deg, g_tx=tx.g_tx,
                    n_lens=rx.n_lens, fov_deg=rx.fov_deg, phi_deg=0.0,
                    A_pd_m2=rx.area_m2, Fturb=Ft, Fpipe=Fpipe
                )
            acc_Pr += Pr
        Pr_mean = acc_Pr / float(max(1, g.mc_realizations))

        nvar = total_variance(
            R_A_per_W=rx.responsivity_A_per_W, Pr_W=Pr_mean, B_Hz=rx.bandwidth_Hz,
            T_K=rx.T, R_load_ohm=rx.R_load, Idark_A=rx.Idark_A, rin=noise.rin
        )

        i_sig = rx.responsivity_A_per_W * Pr_mean
        i_noise_rms = math.sqrt(max(0.0, nvar))
        tia_gain = max(0.0, rx.tia_gain)
        v_sig = i_sig * rx.R_load * tia_gain
        v_noise_rms = i_noise_rms * rx.R_load * tia_gain

        snr_lin = snr_linear(rx.responsivity_A_per_W, Pr_mean, nvar)
        out_Pr.append(Pr_mean)
        out_SNRlin.append(snr_lin)
        out_SNRdB.append(snr_db(snr_lin))
        out_BER.append(ber_from_snr(snr_lin))
        out_Isig.append(i_sig)
        out_Inoise_rms.append(i_noise_rms)
        out_Vsig.append(v_sig)
        out_Vnoise_rms.append(v_noise_rms)

    return {
        "distance_m": distances.tolist(),
        "Pr_W": out_Pr,
        "Pr_dBm": [to_dBm(p) for p in out_Pr],
        "SNR_lin": out_SNRlin,
        "SNR_dB": out_SNRdB,
        "BER": out_BER,
        "I_sig_A": out_Isig,
        "I_noise_rms_A": out_Inoise_rms,
        "V_sig_V": out_Vsig,
        "V_noise_rms_V": out_Vnoise_rms,
    }
