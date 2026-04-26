#!/usr/bin/env bash
python -m UOWC_SIM.uowc_sim.cli --list       #Lists Wavelength options and a,b,c variables for those diffrent wavelenghts in varing water conditions
python -m UOWC_SIM.uowc_sim.cli run --preset coastal_ocean --tx led --turb gengamma --dmin 0.01 --dmax 5 --step 0.01
python -m UOWC_SIM.uowc_sim.cli run --preset pure_sea --tx led --turb lognormal --dmin 0.001 --dmax 100 --step 1
python -m UOWC_SIM.uowc_sim.cli run --preset clear_ocean --tx ld --turb weibull --wb-k 0.8 --wb-lambda 1.0 --save
python -m UOWC_SIM.uowc_sim.cli run --preset turbid_harbor --tx ld --turb weibull --wb-k 0.7 --wb-lambda 1.0 --save
# Pipe/TIR example using CLI options directly (instead of only a config file)
python -m UOWC_SIM.uowc_sim.cli run --led blue --preset coastal_ocean --pipe-tir --pipe-radius-m 0.012 --pipe-wall-reflectivity 0.985 --pipe-water-n 1.343 --pipe-wall-n 1.490 --pipe-coupling-efficiency 0.82 --pipe-max-gain 35 --baud 1200 --dmin 0.2 --dmax 5 --step 0.2
