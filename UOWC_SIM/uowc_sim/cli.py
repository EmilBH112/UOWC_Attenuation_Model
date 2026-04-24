import argparse, os, csv, json, math
from datetime import datetime
from .config import SimulationConfig, ReceiverConfig, TransmitterConfig, WaterConfig, TurbulenceConfig, NoiseConfig, SimulationGrid
from .water import PRESETS_520NM
from .simulate import run_sim
from .plotting import plot_curves, plot_overlay_curves

CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))
LED_CONFIGS = {
    "royal_blue": os.path.join(CONFIGS_DIR, "L135-U450003500000_98mA.yml"),
    "blue": os.path.join(CONFIGS_DIR, "L135-B475003500000_98mA.yml"),
    "green": os.path.join(CONFIGS_DIR, "L135-G525003500000_98mA.yml"),
    "L135-U450003500000": os.path.join(CONFIGS_DIR, "L135-U450003500000_98mA.yml"),
    "L135-B475003500000": os.path.join(CONFIGS_DIR, "L135-B475003500000_98mA.yml"),
    "L135-G525003500000": os.path.join(CONFIGS_DIR, "L135-G525003500000_98mA.yml"),
}

S5973_02_AREA_M2 = math.pi * (0.2e-3 ** 2)
RX_PRESETS = {
    "s5973-02": {
        "area_m2": S5973_02_AREA_M2,
        "responsivity_A_per_W": 0.301,
        "Idark_A": 1e-10,
        "tia_gain": 11.3,
        "baseline_offset_V": 0.0,
        "comparator_low_V": 0.0,
        "comparator_high_V": 3.3,
        "psoc_logic_high_threshold_V": 1.65,
    },
    "S5973-02": {
        "area_m2": S5973_02_AREA_M2,
        "responsivity_A_per_W": 0.301,
        "Idark_A": 1e-10,
        "tia_gain": 11.3,
        "baseline_offset_V": 0.0,
        "comparator_low_V": 0.0,
        "comparator_high_V": 3.3,
        "psoc_logic_high_threshold_V": 1.65,
    },
}


def _preset_to_config(name: str, tx_type: str, turb_model: str, args) -> SimulationConfig:
    tx_type = tx_type or "led"
    turb_model = turb_model or "lognormal"
    wm = PRESETS_520NM[name]
    water = WaterConfig(name=wm.name, alpha_m_inv=wm.alpha_m_inv, beta_m_inv=wm.beta_m_inv)
    tx = TransmitterConfig()
    rx = ReceiverConfig()
    grid = SimulationGrid(
        d_min_m=args.dmin if args.dmin is not None else 1.0,
        d_max_m=args.dmax if args.dmax is not None else 100.0,
        d_step_m=args.step if args.step is not None else 1.0,
        mc_realizations=args.mc if args.mc is not None else 1,
        seed=args.seed if args.seed is not None else 12345,
    )
    noise = NoiseConfig()
    if tx_type.lower() == "ld" and args.rin is None:
        noise.rin = 1e-15
    elif args.rin is not None:
        noise.rin = args.rin
    turb = TurbulenceConfig(
        model=turb_model,
        scint_index=args.scint if args.scint is not None else 0.1,
        gg_alpha=args.gg_alpha if args.gg_alpha is not None else 1.0,
        gg_beta=args.gg_beta if args.gg_beta is not None else 2.0,
        gg_nu=args.gg_nu if args.gg_nu is not None else 1.0,
        wb_k=args.wb_k if args.wb_k is not None else 1.2,
        wb_lambda=args.wb_lambda if args.wb_lambda is not None else 1.0,
    )
    return SimulationConfig(tx, rx, water, turb, noise, grid, tx_type=tx_type)


def _apply_overrides(cfg: SimulationConfig, args) -> SimulationConfig:
    if args.tx is not None:
        cfg.tx_type = args.tx
    if args.turb is not None:
        cfg.turb.model = args.turb
    if args.scint is not None:
        cfg.turb.scint_index = args.scint
    if args.gg_alpha is not None:
        cfg.turb.gg_alpha = args.gg_alpha
    if args.gg_beta is not None:
        cfg.turb.gg_beta = args.gg_beta
    if args.gg_nu is not None:
        cfg.turb.gg_nu = args.gg_nu
    if args.wb_k is not None:
        cfg.turb.wb_k = args.wb_k
    if args.wb_lambda is not None:
        cfg.turb.wb_lambda = args.wb_lambda
    if args.rin is not None:
        cfg.noise.rin = args.rin
    if args.dmin is not None:
        cfg.grid.d_min_m = args.dmin
    if args.dmax is not None:
        cfg.grid.d_max_m = args.dmax
    if args.step is not None:
        cfg.grid.d_step_m = args.step
    if args.mc is not None:
        cfg.grid.mc_realizations = args.mc
    if args.seed is not None:
        cfg.grid.seed = args.seed
    if args.tia_gain is not None:
        cfg.receiver.tia_gain = args.tia_gain
    if args.baseline_offset is not None:
        cfg.receiver.baseline_offset_V = args.baseline_offset
    if args.comparator_low is not None:
        cfg.receiver.comparator_low_V = args.comparator_low
    if args.comparator_high is not None:
        cfg.receiver.comparator_high_V = args.comparator_high
    if args.logic_high_threshold is not None:
        cfg.receiver.psoc_logic_high_threshold_V = args.logic_high_threshold
    if args.baud is not None:
        cfg.receiver.bandwidth_Hz = max(1.0, args.baud)
    if args.pipe_tir is not None:
        cfg.pipe_tir.enabled = args.pipe_tir
    if args.pipe_radius_m is not None:
        cfg.pipe_tir.radius_m = args.pipe_radius_m
    if args.pipe_wall_reflectivity is not None:
        cfg.pipe_tir.wall_reflectivity = args.pipe_wall_reflectivity
    if args.pipe_water_n is not None:
        cfg.pipe_tir.water_refractive_index = args.pipe_water_n
    if args.pipe_wall_n is not None:
        cfg.pipe_tir.wall_refractive_index = args.pipe_wall_n
    if args.pipe_incidence_deg is not None:
        cfg.pipe_tir.incidence_axis_deg = args.pipe_incidence_deg
    if args.pipe_coupling_efficiency is not None:
        cfg.pipe_tir.coupling_efficiency = args.pipe_coupling_efficiency
    if args.pipe_max_gain is not None:
        cfg.pipe_tir.max_guiding_gain = args.pipe_max_gain
    return cfg


def _apply_rx_preset(cfg: SimulationConfig, rx_name: str) -> SimulationConfig:
    preset = RX_PRESETS[rx_name]
    for key, value in preset.items():
        setattr(cfg.receiver, key, value)
    return cfg


def _resolve_led_config(name: str) -> str:
    return LED_CONFIGS[name]


def _print_water_presets():
    print("Water presets (lambda=520 nm):")
    for k, v in PRESETS_520NM.items():
        print(f"  - {k}: alpha={v.alpha_m_inv}  beta={v.beta_m_inv}  c={v.c_m_inv}")


def _print_led_presets():
    print("LED presets:")
    print("  - royal_blue -> L135-U450003500000_98mA.yml")
    print("  - blue       -> L135-B475003500000_98mA.yml")
    print("  - green      -> L135-G525003500000_98mA.yml")
    print("You can also pass the exact part number to --led.")


def _print_rx_presets():
    print("Receiver presets:")
    print("  - s5973-02 -> Hamamatsu S5973-02 with tia_gain=11.3, comparator rails 0.0/3.3 V, logic-high threshold 1.65 V")
    print("Applies the S5973-02 active area, responsivity, dark current, TIA gain, comparator model, and comparator baseline offset.")


def _save_csv_json(outdir, results):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, f"results_{ts}.csv")
    json_path = os.path.join(outdir, f"results_{ts}.json")
    keys = list(results.keys())
    rows = zip(*[results[k] for k in keys])
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for row in rows:
            w.writerow(row)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return csv_path, json_path


def main():
    p = argparse.ArgumentParser(
        prog="uowc_sim",
        epilog="Example: python -m UOWC_SIM.uowc_sim.cli run --led green --rx s5973-02 --dmax 4 --threshold-mult 2.0 --baseline-offset 0.05 --save",
    )
    sub = p.add_subparsers(dest="cmd")

    p.add_argument("--list", action="store_true", help="List water presets and exit")
    p.add_argument("--list-leds", action="store_true", help="List built-in LED configs and exit")
    p.add_argument("--list-rx", action="store_true", help="List built-in receiver configs and exit")

    runp = sub.add_parser("run", help="Run a simulation")
    runp.add_argument("--preset", choices=list(PRESETS_520NM.keys()), default=None)
    runp.add_argument("--config", default=None, help="Path to YAML config file")
    runp.add_argument("--led", default=None, help="Built-in LED config name or exact Lumileds part number")
    runp.add_argument("--rx", default=None, help="Built-in receiver preset name")
    runp.add_argument("--tx", choices=["led", "ld"], default=None)
    runp.add_argument("--turb", choices=["lognormal", "gengamma", "weibull"], default=None)
    runp.add_argument("--dmin", type=float, default=None)
    runp.add_argument("--dmax", type=float, default=None)
    runp.add_argument("--step", type=float, default=None)
    runp.add_argument("--mc", type=int, default=None)
    runp.add_argument("--seed", type=int, default=None)
    runp.add_argument("--scint", type=float, default=None, help="Scintillation index for lognormal")
    runp.add_argument("--gg-alpha", type=float, default=None)
    runp.add_argument("--gg-beta", type=float, default=None)
    runp.add_argument("--gg-nu", type=float, default=None)
    runp.add_argument("--wb-k", type=float, default=None)
    runp.add_argument("--wb-lambda", type=float, default=None)
    runp.add_argument("--rin", type=float, default=None, help="Relative Intensity Noise factor")
    runp.add_argument("--tia-gain", type=float, default=None, help="Extra analog gain applied after the photodiode current-to-voltage stage")
    runp.add_argument("--baseline-offset", type=float, default=None, help="Fixed comparator or baseline offset in volts added to the detection threshold")
    runp.add_argument("--comparator-low", type=float, default=None, help="Comparator low output rail in volts")
    runp.add_argument("--comparator-high", type=float, default=None, help="Comparator high output rail in volts")
    runp.add_argument("--logic-high-threshold", type=float, default=None, help="PSoC logic high threshold in volts")
    runp.add_argument("--baud", type=float, default=None, help="Approximate symbol rate in baud; mapped to receiver noise bandwidth")
    runp.add_argument("--pipe-tir", action=argparse.BooleanOptionalAction, default=None, help="Enable/disable glossy pipe total internal reflection guiding model")
    runp.add_argument("--pipe-radius-m", type=float, default=None, help="Inner pipe radius in meters")
    runp.add_argument("--pipe-wall-reflectivity", type=float, default=None, help="Inner wall reflectivity when TIR condition is not met")
    runp.add_argument("--pipe-water-n", type=float, default=None, help="Water refractive index inside the pipe")
    runp.add_argument("--pipe-wall-n", type=float, default=None, help="Pipe wall refractive index (or surrounding medium)")
    runp.add_argument("--pipe-incidence-deg", type=float, default=None, help="Beam incidence angle relative to pipe axis; defaults to source divergence")
    runp.add_argument("--pipe-coupling-efficiency", type=float, default=None, help="Source-to-pipe coupling efficiency")
    runp.add_argument("--pipe-max-gain", type=float, default=None, help="Cap on geometric guiding gain")
    runp.add_argument("--threshold-mult", type=float, default=1.0, help="Detection threshold multiplier applied to simulated noise floor voltage")
    runp.add_argument("--save", action="store_true")
    runp.add_argument("--out", default=None, help="Output directory (used with --save)")
    runp.add_argument("--voltage-plot-xmin", type=float, default=None,
                      help="Lower x-limit for voltage plots in meters (default: 0.1 m when --save, else 0.0 m)")

    args = p.parse_args()

    if args.list:
        _print_water_presets()
    if args.list_leds:
        _print_led_presets()
    if args.list_rx:
        _print_rx_presets()
    if args.list or args.list_leds or args.list_rx:
        return

    if args.cmd == "run":
        if args.config and args.led:
            p.error("Use either --config or --led, not both.")

        if args.config:
            cfg = SimulationConfig.from_yaml(args.config)
            cfg = _apply_overrides(cfg, args)
            source_desc = f"config={args.config}"
        elif args.led:
            if args.led not in LED_CONFIGS:
                p.error(f"Unknown LED preset '{args.led}'. Use --list-leds to see available options.")
            cfg_path = _resolve_led_config(args.led)
            cfg = SimulationConfig.from_yaml(cfg_path)
            cfg = _apply_overrides(cfg, args)
            source_desc = f"led={os.path.basename(cfg_path)}"
        else:
            preset_name = args.preset or "pure_sea"
            cfg = _preset_to_config(preset_name, args.tx, args.turb, args)
            source_desc = f"preset={preset_name}"

        if args.rx is not None:
            if args.rx not in RX_PRESETS:
                p.error(f"Unknown receiver preset '{args.rx}'. Use --list-rx to see available options.")
            cfg = _apply_rx_preset(cfg, args.rx)
            source_desc = f"{source_desc}  rx={args.rx}"

        cfg = _apply_overrides(cfg, args)
        results = run_sim(cfg)

        threshold_mult = max(0.0, args.threshold_mult)
        baseline_offset_v = cfg.receiver.baseline_offset_V
        results["V_threshold_noise_V"] = [threshold_mult * v for v in results["V_noise_rms_V"]]
        results["V_threshold_total_V"] = [baseline_offset_v + v for v in results["V_threshold_noise_V"]]
        results["signal_detected_full_scale"] = [1 if vs >= vt else 0 for vs, vt in zip(results["V_sig_V"], results["V_threshold_total_V"])]

        comp_low = cfg.receiver.comparator_low_V
        comp_high = cfg.receiver.comparator_high_V
        logic_high = cfg.receiver.psoc_logic_high_threshold_V

        results["V_comparator_out_V"] = [comp_high if det == 1 else comp_low for det in results["signal_detected_full_scale"]]
        results["V_psoc_logic_threshold_V"] = [logic_high for _ in results["distance_m"]]
        results["psoc_digital_high"] = [1 if v >= logic_high else 0 for v in results["V_comparator_out_V"]]

        detected_distances = [d for d, det in zip(results["distance_m"], results["signal_detected_full_scale"]) if det == 1]
        max_detect_distance = max(detected_distances) if detected_distances else None
        digital_high_distances = [d for d, det in zip(results["distance_m"], results["psoc_digital_high"]) if det == 1]
        max_digital_high_distance = max(digital_high_distances) if digital_high_distances else None

        min_ber = min(results["BER"])
        min_idx = results["BER"].index(min_ber)
        print(f"Ran {source_desc}  tx={cfg.tx_type}  turb={cfg.turb.model}  distances={results['distance_m'][0]}..{results['distance_m'][-1]} m")
        print(f"Min BER observed: {min_ber:.3e} at distance={results['distance_m'][min_idx]} m")
        print(f"Detection threshold multiplier: {threshold_mult:.3f} x noise floor")
        print(f"Fixed baseline offset: {baseline_offset_v:.6f} V")
        print(f"Comparator rails: low={comp_low:.3f} V, high={comp_high:.3f} V")
        print(f"PSoC logic-high threshold: {logic_high:.3f} V")
        print(f"Receiver bandwidth (Hz): {cfg.receiver.bandwidth_Hz:.2f}")
        if cfg.pipe_tir.enabled:
            print("Glossy pipe TIR guiding: enabled")
            print(f"  pipe radius={cfg.pipe_tir.radius_m:.4f} m  wall reflectivity={cfg.pipe_tir.wall_reflectivity:.3f}")
            print(f"  n_water={cfg.pipe_tir.water_refractive_index:.3f}  n_wall={cfg.pipe_tir.wall_refractive_index:.3f}")
        else:
            print("Glossy pipe TIR guiding: disabled")
        if max_detect_distance is not None:
            print(f"Max detected distance above analog threshold: {max_detect_distance} m")
        else:
            print("No distances exceeded the analog detection threshold.")
        if max_digital_high_distance is not None:
            print(f"Max distance interpreted as digital high by PSoC: {max_digital_high_distance} m")
        else:
            print("No distances produced a valid digital high at the simulated PSoC.")

        outdir = None
        if args.save:
            outdir = args.out or os.path.abspath(os.path.join("outputs", "latest"))
            os.makedirs(outdir, exist_ok=True)

        plot_curves(results["distance_m"], results["Pr_dBm"], "Received Power (dBm)",
                    "Received Power vs Distance", save=args.save, outname="received_power_dBm.png", outdir=outdir)
        plot_curves(results["distance_m"], results["SNR_dB"], "SNR (dB)",
                    "SNR vs Distance", save=args.save, outname="snr_dB.png", outdir=outdir)
        voltage_plot_x_max = min(4.0, max(results["distance_m"]))
        default_voltage_x_min = 0.1 if args.save else 0.0
        voltage_plot_x_min = args.voltage_plot_xmin if args.voltage_plot_xmin is not None else default_voltage_x_min
        voltage_plot_x_min = max(0.0, min(voltage_plot_x_min, voltage_plot_x_max))

        plot_curves(results["distance_m"], results["V_sig_V"], "Signal Voltage at Simulated PSoC (µV)",
                    "Simulated PSoC Signal Voltage vs Distance", save=args.save, outname="psoc_signal_voltage_uV.png",
                    scale=1e6, x_min=voltage_plot_x_min, x_max=voltage_plot_x_max, y_min=0.0,
                    auto_y_from_visible=True, outdir=outdir)
        plot_overlay_curves(results["distance_m"], results["V_sig_V"], "Signal Voltage", results["V_threshold_total_V"], "Detection Threshold",
                            "Voltage at Simulated PSoC (µV)", "Simulated PSoC Signal Voltage and Threshold vs Distance", save=args.save, outname="psoc_signal_threshold_voltage_uV.png",
                            scale=1e6, x_min=voltage_plot_x_min, x_max=voltage_plot_x_max, y_min=0.0,
                            auto_y_from_visible=True, outdir=outdir)
        plot_overlay_curves(results["distance_m"], results["V_comparator_out_V"], "Comparator Output", results["V_psoc_logic_threshold_V"], "PSoC Logic Threshold",
                            "Voltage (V)", "Comparator Output and PSoC Logic Threshold vs Distance", save=args.save, outname="psoc_digital_logic_voltage_V.png",
                            scale=1.0, x_min=voltage_plot_x_min, x_max=voltage_plot_x_max, y_min=0.0, outdir=outdir)
        plot_curves(results["distance_m"], results["BER"], "BER",
                    "BER vs Distance", save=args.save, outname="ber.png", outdir=outdir)

        if args.save:
            csvp, jsonp = _save_csv_json(outdir, results)
            print(f"Saved CSV: {csvp}")
            print(f"Saved JSON: {jsonp}")
        return

    p.print_help()


if __name__ == "__main__":
    main()
