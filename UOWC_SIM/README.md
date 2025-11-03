# UOWC_SIM — End-to-End Underwater Optical Wireless Communication Simulation

This repository implements an end-to-end UOWC simulation pipeline aligned with the two flowcharts you provided and the formulas in the research paper:

- Zayed & Shokair (2025), "Modeling and simulation of optical wireless communication channels in IoUT considering water types, turbulence and transmitter selection" (Scientific Reports).

## Features

- Modular pipeline following the flowcharts:
  1. Define system parameters (wavelength, water type, channel model, transmitter, receiver)
  2. Generate optical signal (OOK default)
  3. Apply channel impairments (absorption, scattering via Beer–Lambert, turbulence: log-normal / generalized-gamma / Weibull, noise: shot + thermal + dark + RIN)
  4. Transmit through channel (geometry and optics; LED-PS vs LD-PS link budget)
  5. Compute metrics (Received power, SNR, BER, Data rate)
  6. Analyze and visualize results (matplotlib)
  7. Simple protocol optimization hints (choose source, power, FOV)  

- Presets for water types (pure sea, clear ocean, coastal ocean, turbid harbor) at lambda=520 nm per Table 3 in the paper.
- Configuration first: edit `configs/*.yml` or pass CLI flags.
- CLI interface to pick scenario and run plots.
- Minimal dependencies: numpy, pyyaml, matplotlib.

> Note: Formulas implemented as in-paper equations: (7)-(10) noise, (16)/(22) received power for LED-PS / LD-PS, (18) Lambertian order, (19) receiver concentrator gain, (20)/(21) TX optics gain, (23) SNR, (24) BER ~= Q(sqrt(SNR)).

## Quickstart

```bash
pip install -r requirements.txt

# List presets
python -m UOWC_SIM.uowc_sim.cli --list

# Run a preset scenario (Pure Sea, LED, Log-Normal turbulence)
python -m UOWC_SIM.uowc_sim.cli run --preset pure_sea --tx led --turb lognormal --dmin 1 --dmax 100 --step 1

# Laser source in Clear Ocean with Generalized-Gamma turbulence (shape params via CLI)
python -m UOWC_SIM.uowc_sim.cli run --preset clear_ocean --tx ld --turb gengamma --gg-alpha 1.0 --gg-beta 2.0 --gg-nu 1.0

# Produce summary tables and save plots
python -m UOWC_SIM.uowc_sim.cli run --preset turbid_harbor --tx ld --turb weibull --wb-k 0.7 --wb-lambda 1.0 --save
```

Outputs (plots + CSV/JSON) are saved under `outputs/<timestamp>/` when `--save` is used.

## Repository Layout

```
uowc_sim/
  __init__.py
  config.py
  water.py
  optics.py
  turbulence.py
  noise.py
  transmitter.py
  metrics.py
  simulate.py
  plotting.py
  cli.py
configs/
  pure_sea.yml
  clear_ocean.yml
  coastal_ocean.yml
  turbid_harbor.yml
scripts/
  example_run.sh
```

## Notes

- You can change wavelength and extend `water.py` with alpha(lambda), beta(lambda) tables for other wavelengths.
- CLI accepts Monte-Carlo count for turbulence (`--mc`) to average metrics.
- The "protocol optimization" step is a placeholder that prints hints based on results.

## License

MIT.
