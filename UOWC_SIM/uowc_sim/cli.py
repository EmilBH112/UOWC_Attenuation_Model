
import argparse, os, csv, json, math
from datetime import datetime
from .config import SimulationConfig, ReceiverConfig, TransmitterConfig, WaterConfig, TurbulenceConfig, NoiseConfig, SimulationGrid
from .water import PRESETS_520NM
from .simulate import run_sim
from .plotting import plot_curves

CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))
LED_CONFIGS = {
    "royal_blue": os.path.join(CONFIGS_DIR, "L135-U450003500000_98mA.yml"),
    "blue": os.path.join(CONFIGS_DIR, "L135-B475003500000_98mA.yml"),
    "green": os.path.join(CONFIGS_DIR, "L135-G525003500000_98mA.yml"),
    "L135-U450003500000": os.path.join(CONFIGS_DIR, "L135-U450003500000_98mA.yml"),
    "L135-B475003500000": os.path.join(CONFIGS_DIR, "L135-B475003500000_98mA.yml"),
    "L135-G525003500000": os.path.join(CONFIGS_DIR, "L135-G525003500000_98mA.yml"),
}

# Hamamatsu S5973-02 built-in receiver preset.
# Active area is modeled as a 0.4 mm diameter circle.
# Responsivity is set to a visible-band reference value.
# Dark current is reduced to reflect the low-noise device.
S5973_02_AREA_M2 = math.pi * (0.2e-3 ** 2)
RX_PRESETS = {
    "s5973-02": {
        "area_m2": S5973_02_AREA_M2,
        "responsivity_A_per_W": 0.301,
        "Idark_A": 1e-10,
    },
    "S5973-02": {
        "area_m2": S5973_02_AREA_M2,
        "responsivity_A_per_W": 0.301,
        "Idark_A": 1e-10,
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
    print("  - s5973-02 -> Hamamatsu S5973-02")
    print("Applies the S5973-02 active area, responsivity, and dark current.")

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
    p = argparse.ArgumentParser(prog="uowc_sim")
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
    runp.add_argument("--save", action="store_true")
    runp.add_argument("--out", default=None, help="Output directory (used with --save)")

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

        results = run_sim(cfg)

        min_ber = min(results["BER"])
        min_idx = results["BER"].index(min_ber)
        print(f"Ran {source_desc}  tx={cfg.tx_type}  turb={cfg.turb.model}  distances={results['distance_m'][0]}..{results['distance_m'][-1]} m")
        print(f"Min BER observed: {min_ber:.3e} at distance={results['distance_m'][min_idx]} m")

        outdir = None
        if args.save:
            outdir = args.out or os.path.abspath(os.path.join("outputs", "latest"))
            os.makedirs(outdir, exist_ok=True)

        plot_curves(results["distance_m"], results["Pr_dBm"], "Received Power (dBm)",
                    "Received Power vs Distance", save=args.save, outname="received_power_dBm.png")
        plot_curves(results["distance_m"], results["SNR_dB"], "SNR (dB)",
                    "SNR vs Distance", save=args.save, outname="snr_dB.png")
        plot_curves(results["distance_m"], results["BER"], "BER",
                    "BER vs Distance", save=args.save, outname="ber.png")

        if args.save:
            csvp, jsonp = _save_csv_json(outdir, results)
            print(f"Saved CSV: {csvp}")
            print(f"Saved JSON: {jsonp}")
        return

    p.print_help()

if __name__ == "__main__":
    main()
