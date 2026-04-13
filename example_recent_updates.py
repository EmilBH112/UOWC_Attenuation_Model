"""Example script showing the recent UOWC simulator receiver-chain updates.

What it demonstrates:
- exact Lumileds LED YAML loading
- Hamamatsu S5973-02 receiver parameters
- TIA gain in the receiver chain
- analog threshold = baseline offset + threshold_multiplier * noise floor
- comparator saturation to low/high rails
- PSoC logic-high detection

Run from the repository root, for example:
    python example_recent_updates.py
    python example_recent_updates.py --led green --threshold-mult 2.0 --baseline-offset 0.05
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from UOWC_SIM.uowc_sim.config import SimulationConfig
from UOWC_SIM.uowc_sim.plotting import plot_curves, plot_overlay_curves
from UOWC_SIM.uowc_sim.simulate import run_sim


REPO_ROOT = Path(__file__).resolve().parent
CONFIG_DIR = REPO_ROOT / "UOWC_SIM" / "configs"
LED_CONFIGS = {
    "royal_blue": CONFIG_DIR / "L135-U450003500000_98mA.yml",
    "blue": CONFIG_DIR / "L135-B475003500000_98mA.yml",
    "green": CONFIG_DIR / "L135-G525003500000_98mA.yml",
}


def apply_s5973_02_preset(cfg: SimulationConfig) -> SimulationConfig:
    """Apply the Hamamatsu S5973-02 receiver settings used in the recent updates."""
    cfg.receiver.area_m2 = math.pi * (0.2e-3 ** 2)  # 0.4 mm diameter active area
    cfg.receiver.responsivity_A_per_W = 0.301
    cfg.receiver.Idark_A = 1e-10
    cfg.receiver.tia_gain = 11.3
    cfg.receiver.baseline_offset_V = 0.0
    cfg.receiver.comparator_low_V = 0.0
    cfg.receiver.comparator_high_V = 3.3
    cfg.receiver.psoc_logic_high_threshold_V = 1.65
    return cfg


def build_results(cfg: SimulationConfig, threshold_mult: float):
    results = run_sim(cfg)

    threshold_mult = max(0.0, threshold_mult)
    baseline_offset_v = cfg.receiver.baseline_offset_V
    comp_low = cfg.receiver.comparator_low_V
    comp_high = cfg.receiver.comparator_high_V
    logic_high = cfg.receiver.psoc_logic_high_threshold_V

    results["V_threshold_noise_V"] = [threshold_mult * v for v in results["V_noise_rms_V"]]
    results["V_threshold_total_V"] = [baseline_offset_v + v for v in results["V_threshold_noise_V"]]
    results["signal_detected_full_scale"] = [
        1 if vs >= vt else 0
        for vs, vt in zip(results["V_sig_V"], results["V_threshold_total_V"])
    ]
    results["V_comparator_out_V"] = [
        comp_high if det == 1 else comp_low
        for det in results["signal_detected_full_scale"]
    ]
    results["V_psoc_logic_threshold_V"] = [logic_high for _ in results["distance_m"]]
    results["psoc_digital_high"] = [
        1 if v >= logic_high else 0
        for v in results["V_comparator_out_V"]
    ]
    return results


def print_summary(cfg: SimulationConfig, results: dict, threshold_mult: float, led_name: str) -> None:
    analog_detected = [
        d for d, det in zip(results["distance_m"], results["signal_detected_full_scale"])
        if det == 1
    ]
    digital_high = [
        d for d, det in zip(results["distance_m"], results["psoc_digital_high"])
        if det == 1
    ]

    print(f"LED preset: {led_name}")
    print(f"Wavelength: {cfg.transmitter.wavelength_nm:.1f} nm")
    print("Receiver: Hamamatsu S5973-02")
    print(f"TIA gain: {cfg.receiver.tia_gain:.2f}x")
    print(f"Baseline offset: {cfg.receiver.baseline_offset_V:.4f} V")
    print(f"Threshold multiplier: {threshold_mult:.3f} x noise floor")
    print(
        f"Comparator rails: {cfg.receiver.comparator_low_V:.3f} V to "
        f"{cfg.receiver.comparator_high_V:.3f} V"
    )
    print(f"PSoC logic-high threshold: {cfg.receiver.psoc_logic_high_threshold_V:.3f} V")
    if analog_detected:
        print(f"Max analog detection distance: {max(analog_detected)} m")
    else:
        print("No analog detections above threshold.")
    if digital_high:
        print(f"Max PSoC digital-high distance: {max(digital_high)} m")
    else:
        print("No distances produced a digital high at the simulated PSoC.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Example runner for the recent UOWC simulator updates.")
    parser.add_argument("--led", choices=sorted(LED_CONFIGS.keys()), default="green")
    parser.add_argument("--dmin", type=float, default=1.0)
    parser.add_argument("--dmax", type=float, default=20.0)
    parser.add_argument("--step", type=float, default=1.0)
    parser.add_argument("--threshold-mult", type=float, default=1.0)
    parser.add_argument("--baseline-offset", type=float, default=0.05)
    parser.add_argument("--tia-gain", type=float, default=11.3)
    parser.add_argument("--logic-high-threshold", type=float, default=1.65)
    parser.add_argument("--comparator-high", type=float, default=3.3)
    parser.add_argument("--comparator-low", type=float, default=0.0)
    parser.add_argument("--save", action="store_true", help="Save plots instead of only showing them.")
    args = parser.parse_args()

    cfg = SimulationConfig.from_yaml(str(LED_CONFIGS[args.led]))
    cfg = apply_s5973_02_preset(cfg)

    cfg.grid.d_min_m = args.dmin
    cfg.grid.d_max_m = args.dmax
    cfg.grid.d_step_m = args.step
    cfg.receiver.baseline_offset_V = args.baseline_offset
    cfg.receiver.tia_gain = args.tia_gain
    cfg.receiver.psoc_logic_high_threshold_V = args.logic_high_threshold
    cfg.receiver.comparator_high_V = args.comparator_high
    cfg.receiver.comparator_low_V = args.comparator_low

    results = build_results(cfg, args.threshold_mult)
    print_summary(cfg, results, args.threshold_mult, args.led)

    plot_curves(
        results["distance_m"],
        results["V_sig_V"],
        "Signal Voltage at Simulated PSoC (V)",
        "Simulated PSoC Signal Voltage vs Distance",
        save=args.save,
        outname="example_psoc_signal_voltage_V.png",
    )
    plot_overlay_curves(
        results["distance_m"],
        results["V_sig_V"],
        "Signal Voltage",
        results["V_threshold_total_V"],
        "Detection Threshold",
        "Voltage at Simulated PSoC (V)",
        "Signal Voltage and Detection Threshold vs Distance",
        save=args.save,
        outname="example_psoc_signal_threshold_voltage_V.png",
    )
    plot_overlay_curves(
        results["distance_m"],
        results["V_comparator_out_V"],
        "Comparator Output",
        results["V_psoc_logic_threshold_V"],
        "PSoC Logic Threshold",
        "Voltage (V)",
        "Comparator Output and PSoC Logic Threshold vs Distance",
        save=args.save,
        outname="example_psoc_digital_logic_voltage_V.png",
    )


if __name__ == "__main__":
    main()
