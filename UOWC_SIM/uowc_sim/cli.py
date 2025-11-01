
import argparse, os, csv, json
from datetime import datetime
from .config import SimulationConfig, ReceiverConfig, TransmitterConfig, WaterConfig, TurbulenceConfig, NoiseConfig, SimulationGrid
from .water import PRESETS_520NM
from .simulate import run_sim
from .plotting import plot_curves

def _preset_to_config(name: str, tx_type: str, turb_model: str, args) -> SimulationConfig:
    wm = PRESETS_520NM[name]
    water = WaterConfig(name=wm.name, alpha_m_inv=wm.alpha_m_inv, beta_m_inv=wm.beta_m_inv)
    tx = TransmitterConfig()
    rx = ReceiverConfig()
    grid = SimulationGrid(d_min_m=args.dmin, d_max_m=args.dmax, d_step_m=args.step, mc_realizations=args.mc, seed=args.seed)
    noise = NoiseConfig()
    if tx_type.lower() == "ld" and args.rin is None:
        noise.rin = 1e-15
    elif args.rin is not None:
        noise.rin = args.rin
    turb = TurbulenceConfig(model=turb_model,
                            scint_index=args.scint if args.scint is not None else 0.1,
                            gg_alpha=args.gg_alpha, gg_beta=args.gg_beta, gg_nu=args.gg_nu,
                            wb_k=args.wb_k, wb_lambda=args.wb_lambda)
    return SimulationConfig(tx, rx, water, turb, noise, grid, tx_type=tx_type)

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

    runp = sub.add_parser("run", help="Run a simulation")
    runp.add_argument("--preset", choices=list(PRESETS_520NM.keys()), default="pure_sea")
    runp.add_argument("--tx", choices=["led","ld"], default="led")
    runp.add_argument("--turb", choices=["lognormal","gengamma","weibull"], default="lognormal")
    runp.add_argument("--dmin", type=float, default=1.0)
    runp.add_argument("--dmax", type=float, default=100.0)
    runp.add_argument("--step", type=float, default=1.0)
    runp.add_argument("--mc", type=int, default=1)
    runp.add_argument("--seed", type=int, default=12345)
    runp.add_argument("--scint", type=float, default=None, help="Scintillation index for lognormal")
    runp.add_argument("--gg-alpha", type=float, default=1.0)
    runp.add_argument("--gg-beta", type=float, default=2.0)
    runp.add_argument("--gg-nu", type=float, default=1.0)
    runp.add_argument("--wb-k", type=float, default=1.2)
    runp.add_argument("--wb-lambda", type=float, default=1.0)
    runp.add_argument("--rin", type=float, default=None, help="Relative Intensity Noise factor")
    runp.add_argument("--save", action="store_true")
    runp.add_argument("--out", default=None, help="Output directory (used with --save)")

    args = p.parse_args()

    if args.list:
        print("Water presets (lambda=520 nm):")
        for k,v in PRESETS_520NM.items():
            print(f"  - {k}: alpha={v.alpha_m_inv}  beta={v.beta_m_inv}  c={v.c_m_inv}")
        return

    if args.cmd == "run":
        cfg = _preset_to_config(args.preset, args.tx, args.turb, args)
        results = run_sim(cfg)

        # Summary
        min_ber = min(results["BER"])
        min_idx = results["BER"].index(min_ber)
        print(f"Ran {args.preset}  tx={args.tx}  turb={args.turb}  distances={results['distance_m'][0]}..{results['distance_m'][-1]} m")
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
