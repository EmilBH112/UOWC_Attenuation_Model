#!/usr/bin/env bash
python -m uowc_sim.cli --list
python -m uowc_sim.cli run --preset pure_sea --tx led --turb lognormal --dmin 1 --dmax 100 --step 1
python -m uowc_sim.cli run --preset clear_ocean --tx ld --turb weibull --wb-k 0.8 --wb-lambda 1.0 --save
