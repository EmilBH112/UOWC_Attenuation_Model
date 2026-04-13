
import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

def _prepare_outdir(save: bool):
    outdir = None
    if save:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        outdir = os.path.abspath(os.path.join("outputs", ts))
        os.makedirs(outdir, exist_ok=True)
    return outdir

def plot_curves(distances_m, values, ylabel, title, save=False, outname="plot.png"):
    outdir = _prepare_outdir(save)
    x = np.asarray(distances_m, dtype=float)
    y = np.asarray(values, dtype=float)
    plt.figure()
    plt.plot(x, y)
    plt.xlabel("Distance (m)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, which="both")
    if save and outdir:
        path = os.path.join(outdir, outname)
        plt.savefig(path, dpi=200, bbox_inches="tight")
    else:
        plt.show()
    plt.close()
    return outdir

def plot_overlay_curves(distances_m, values_a, label_a, values_b, label_b, ylabel, title, save=False, outname="plot_overlay.png"):
    outdir = _prepare_outdir(save)
    x = np.asarray(distances_m, dtype=float)
    y_a = np.asarray(values_a, dtype=float)
    y_b = np.asarray(values_b, dtype=float)
    plt.figure()
    plt.plot(x, y_a, label=label_a)
    plt.plot(x, y_b, label=label_b)
    plt.xlabel("Distance (m)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, which="both")
    plt.legend()
    if save and outdir:
        path = os.path.join(outdir, outname)
        plt.savefig(path, dpi=200, bbox_inches="tight")
    else:
        plt.show()
    plt.close()
    return outdir
