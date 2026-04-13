import os
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def _prepare_outdir(save: bool):
    outdir = None
    if save:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        outdir = os.path.abspath(os.path.join("outputs", ts))
        os.makedirs(outdir, exist_ok=True)
    return outdir


def plot_curves(
    distances_m,
    values,
    ylabel,
    title,
    save=False,
    outname="plot.png",
    scale=1.0,
    x_min=None,
    x_max=None,
    y_min=None,
    y_max=None,
    zero_line=True,
    marker="o",
):
    outdir = _prepare_outdir(save)
    x = np.asarray(distances_m, dtype=float)
    y = np.asarray(values, dtype=float) * scale

    plt.figure(figsize=(8, 5))
    plt.plot(x, y, linewidth=2, marker=marker, markersize=4)

    if zero_line:
        plt.axhline(0.0, linewidth=1.2)

    plt.xlabel("Distance (m)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, which="both", alpha=0.4)

    if x_min is not None or x_max is not None:
        plt.xlim(left=x_min, right=x_max)
    if y_min is not None or y_max is not None:
        plt.ylim(bottom=y_min, top=y_max)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
    ax.ticklabel_format(style="plain", axis="y")

    if save and outdir:
        path = os.path.join(outdir, outname)
        plt.savefig(path, dpi=200, bbox_inches="tight")
    else:
        plt.show()

    plt.close()
    return outdir


def plot_overlay_curves(
    distances_m,
    values_a,
    label_a,
    values_b,
    label_b,
    ylabel,
    title,
    save=False,
    outname="plot_overlay.png",
    scale=1.0,
    x_min=None,
    x_max=None,
    y_min=None,
    y_max=None,
    zero_line=True,
):
    outdir = _prepare_outdir(save)
    x = np.asarray(distances_m, dtype=float)
    y_a = np.asarray(values_a, dtype=float) * scale
    y_b = np.asarray(values_b, dtype=float) * scale

    plt.figure(figsize=(8, 5))
    plt.plot(x, y_a, linewidth=2, marker="o", markersize=4, label=label_a)
    plt.plot(x, y_b, linewidth=2, marker="s", markersize=4, label=label_b)

    if zero_line:
        plt.axhline(0.0, linewidth=1.2)

    plt.xlabel("Distance (m)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, which="both", alpha=0.4)
    plt.legend()

    if x_min is not None or x_max is not None:
        plt.xlim(left=x_min, right=x_max)
    if y_min is not None or y_max is not None:
        plt.ylim(bottom=y_min, top=y_max)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
    ax.ticklabel_format(style="plain", axis="y")

    if save and outdir:
        path = os.path.join(outdir, outname)
        plt.savefig(path, dpi=200, bbox_inches="tight")
    else:
        plt.show()

    plt.close()
    return outdir
