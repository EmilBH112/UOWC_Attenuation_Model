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


def _visible_mask(x, x_min=None, x_max=None):
    mask = np.ones_like(x, dtype=bool)
    if x_min is not None:
        mask &= x >= x_min
    if x_max is not None:
        mask &= x <= x_max
    return mask


def _auto_ylim_from_visible(x, y_values, x_min=None, x_max=None, y_min=None, y_max=None, pad_fraction=0.08):
    """Return y limits using only the data visible in the requested x window.

    This prevents hidden points outside the plotted x-range, or different distance
    step sizes, from changing the apparent y-axis scale of cropped plots.
    """
    if y_min is not None and y_max is not None:
        return y_min, y_max

    mask = _visible_mask(x, x_min, x_max)
    visible_arrays = []

    for y in y_values:
        arr = np.asarray(y, dtype=float)
        if arr.size == x.size:
            arr = arr[mask]
        arr = arr[np.isfinite(arr)]
        if arr.size:
            visible_arrays.append(arr)

    if not visible_arrays:
        return y_min, y_max

    visible = np.concatenate(visible_arrays)
    data_min = float(np.min(visible))
    data_max = float(np.max(visible))

    if data_min == data_max:
        pad = abs(data_max) * pad_fraction if data_max != 0 else 1.0
    else:
        pad = (data_max - data_min) * pad_fraction

    auto_min = data_min - pad
    auto_max = data_max + pad

    if y_min is not None:
        auto_min = y_min
    if y_max is not None:
        auto_max = y_max

    return auto_min, auto_max


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
    auto_y_from_visible=False,
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

    if auto_y_from_visible:
        y_min, y_max = _auto_ylim_from_visible(x, [y], x_min, x_max, y_min, y_max)

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
    auto_y_from_visible=False,
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

    if auto_y_from_visible:
        y_min, y_max = _auto_ylim_from_visible(x, [y_a, y_b], x_min, x_max, y_min, y_max)

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
