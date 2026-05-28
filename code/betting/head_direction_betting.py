"""Head-direction cell betting game.

Demonstrates the betting framework from the "Betting games for model
comparison" blog post on real neural data, and runs four trajectories
plus a calibration loop:

  (1) STRONG cell:       most head-direction modulated unit, real test data
      → expect wealth to grow fast (model crushes baseline).
  (2) INTERMEDIATE cell: median-modulation cell, real test data
      → expect wealth to grow at a moderate rate.
  (3) WEAK cell:         least head-direction modulated unit (above a
      min-spike floor), real test data
      → expect wealth to grow slowly or hover around 1 (model offers
      little advantage over baseline).
  (4) TRUE NULL:         strong cell's Q model evaluated on SYNTHETIC
      spike counts drawn from Poisson(lambda_b). This is the actual null
      Ville's inequality bounds — under y ~ b the wealth process is a
      B-martingale, so P(sup_t W_t >= 1/alpha) <= alpha.

After the three trajectories, a calibration loop repeats experiment (3)
across `--n-calibration` independent null draws and reports the
empirical false-rejection rate. This should land at or below alpha.

Q is a Poisson GLM with cyclic B-spline basis on head direction.
B is a homogeneous-Poisson baseline (constant rate fit on the same train
half as Q).

Outputs (figures/):
  - wealth_trajectory.pdf  3-condition wealth plot with zoomed inset
  - tuning_curves.pdf      strong-cell and weak-cell tuning comparison
"""

from __future__ import annotations

import argparse
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import nemos as nmo
import numpy as np
import pandas as pd
import pynapple as nap

THIS_DIR = Path(__file__).resolve().parent
FIG_DIR = THIS_DIR / "figures"

# Bump default font sizes + line widths across all figures (blog post +
# PDF both benefit from larger labels). Per-call fontsize args override
# these as needed.
plt.rcParams.update({
    "font.size":         15,
    "axes.titlesize":    17,
    "axes.labelsize":    16,
    "xtick.labelsize":   14,
    "ytick.labelsize":   14,
    "legend.fontsize":   14,
    "figure.titlesize":  18,
    "axes.linewidth":    1.2,
    "xtick.major.width": 1.2,
    "ytick.major.width": 1.2,
})
# Mirror each PDF as a PNG inside the Jekyll asset tree so the post can
# embed the figures directly (web markdown wants raster images served from
# /assets/...). The script writes PDF + PNG in one go.
WEB_FIG_DIR = THIS_DIR.parent.parent / "assets" / "img" / "posts" / "2026-06-01-betting"


def _save_figure(fig, out_path):
    """Save matplotlib figure as PDF to `out_path`, and mirror as PNG into
    `WEB_FIG_DIR` so the blog post (which references PNGs) updates in lockstep.
    Both file paths are created/overwritten."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    WEB_FIG_DIR.mkdir(parents=True, exist_ok=True)
    png_path = WEB_FIG_DIR / out_path.with_suffix(".png").name
    fig.savefig(png_path, dpi=150)
    plt.close(fig)

# Site palette
COLOR_STRONG  = "#3a3fbf"   # site primary indigo
COLOR_MID     = "#3a8c8c"   # teal — visually "between" indigo and gray
COLOR_WEAK    = "#6b6860"   # site muted gray
COLOR_NULL    = "#c75450"   # red — clearly distinct, says "null/wrong"


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_session():
    path = nmo.fetch.fetch_data("Mouse32-140822.nwb")
    return nap.load_file(path)


def get_wake_epoch(data):
    """Pull the wake epoch out of the NWB IntervalSet (tags column has
    array-valued tags per row in NWB convention)."""
    eps = data["epochs"]
    tags = eps["tags"]

    def _is_wake(row):
        if isinstance(row, (list, tuple, np.ndarray)):
            return any("wake" in str(t).lower() for t in row)
        return "wake" in str(row).lower()

    mask = np.array([_is_wake(t) for t in tags], dtype=bool)
    if not mask.any():
        raise RuntimeError(f"No wake epoch found. Tags: {list(tags)}")
    return eps[mask]


def compute_tuning_curves(spikes, head_dir, wake_ep, n_bins=60):
    """Wrapper that handles pynapple API change (>=0.10 vs older)."""
    if hasattr(nap, "compute_tuning_curves"):
        return nap.compute_tuning_curves(
            data=spikes,
            features=head_dir,
            bins=n_bins,
            range=(0.0, 2 * np.pi),
            epochs=wake_ep,
            return_pandas=True,
        )
    return nap.compute_1d_tuning_curves(
        group=spikes, feature=head_dir, nb_bins=n_bins,
        minmax=(0.0, 2 * np.pi), ep=wake_ep,
    )


def rank_cells_by_training_bits(spikes, head_dir, wake_ep, *,
                                 bin_size, n_hd_bins=60, min_spikes=200):
    """Rank cells by approximate per-bin KL gain of their empirical
    head-direction tuning curve over a constant-rate Poisson baseline.

    This is a much better predictor of betting-game performance than
    modulation depth alone because it weighs by total firing rate: a
    cell with sharp tuning but very low rate (few spikes to bet on) gets
    a small score, while a cell with moderate tuning and high rate can
    rank higher.

    Concretely, for each cell:
        bits/bin = (1/T) Σ_t [y_t log(λ̂(u_t)/λ̄) - (λ̂(u_t) - λ̄)] / log 2
    where λ̂(u) is the empirical mean spike count per bin conditioned on
    HD bin, and λ̄ is the cell's overall mean spike count per bin.

    Returns a pandas Series of bits/bin values indexed by cell_id, sorted
    descending.  Cells with < min_spikes total spikes are dropped."""
    hd_tsd = head_dir.bin_average(bin_size=bin_size, ep=wake_ep)
    hd = np.asarray(hd_tsd.values).astype(float).reshape(-1)
    valid = np.isfinite(hd)
    hd_valid = hd[valid]

    edges = np.linspace(0.0, 2 * np.pi, n_hd_bins + 1)
    hd_bin_idx = np.clip(np.digitize(hd_valid, edges) - 1, 0, n_hd_bins - 1)

    bits = {}
    for cell_id in spikes.index:
        y_tsd = spikes[cell_id].count(bin_size=bin_size, ep=wake_ep)
        y = np.asarray(y_tsd.values).astype(float).reshape(-1)
        n_min = min(len(y), len(valid))
        y_valid = y[:n_min][valid[:n_min]]

        if y_valid.sum() < min_spikes:
            continue

        lambda_b = float(y_valid.mean())
        if lambda_b < 1e-12:
            continue

        # Empirical tuning: mean spike count per bin, conditioned on HD bin
        tuning_emp = np.full(n_hd_bins, lambda_b)
        for i in range(n_hd_bins):
            m = (hd_bin_idx == i)
            if m.any():
                tuning_emp[i] = y_valid[m].mean()
        tuning_emp = np.maximum(tuning_emp, 1e-9)

        lambda_q = tuning_emp[hd_bin_idx]
        log_gain = (y_valid * (np.log(lambda_q) - np.log(lambda_b))
                    - (lambda_q - lambda_b))
        bits[cell_id] = float(log_gain.mean() / np.log(2))

    return pd.Series(bits).sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Features & counts
# ---------------------------------------------------------------------------

def build_features(head_dir, wake_ep, *, bin_size, n_basis):
    """Bin-average head direction, build cyclic B-spline features.

    Returns (X, valid_mask, basis, hd_valid) where valid_mask flags bins
    with a finite head direction (occasional tracker NaNs are dropped)
    and hd_valid is the per-bin head direction array (post-filter)."""
    hd_tsd = head_dir.bin_average(bin_size=bin_size, ep=wake_ep)
    hd = np.asarray(hd_tsd.values).astype(float).reshape(-1)
    valid = np.isfinite(hd)
    hd_valid = hd[valid]
    basis = nmo.basis.CyclicBSplineEval(n_basis_funcs=n_basis)
    X = np.asarray(basis.compute_features(hd_valid))
    return X, valid, basis, hd_valid


def empirical_tuning(y, hd, *, n_bins=60, bin_size,
                     hd_range=(0.0, 2 * np.pi)):
    """Mean firing rate (Hz) per head-direction bin, for one cell."""
    edges = np.linspace(hd_range[0], hd_range[1], n_bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    rate = np.full(n_bins, np.nan)
    for i in range(n_bins):
        m = (hd >= edges[i]) & (hd < edges[i + 1])
        if i == n_bins - 1:
            m |= np.isclose(hd, edges[i + 1])
        if m.any():
            rate[i] = float(np.mean(y[m])) / bin_size
    return centers, rate


def split_indices(n, *, shuffle=True, seed=0):
    """Return (train_idx, test_idx). Matches `split_half`'s internal
    permutation for the same seed, so empirical tuning computed via
    these indices lines up with the train/test sets actually used by
    `run_experiment`."""
    if shuffle:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n)
    else:
        perm = np.arange(n)
    cut = n // 2
    return perm[:cut], perm[cut:]


def get_cell_counts(spikes, wake_ep, *, bin_size, cell_id, valid):
    """Bin spikes for one cell, aligned to the same bins as build_features."""
    y_tsd = spikes[cell_id].count(bin_size=bin_size, ep=wake_ep)
    y = np.asarray(y_tsd.values).astype(float).reshape(-1)
    n = min(len(y), len(valid))
    return y[:n][valid[:n]]


def split_half(X, y, *, shuffle=True, seed=0):
    """Optionally shuffle bins, then split into halves. Shuffling is OK
    because Q has no autoregressive component."""
    n = len(y)
    if shuffle:
        rng = np.random.default_rng(seed)
        perm = rng.permutation(n)
        X = X[perm]
        y = y[perm]
    cut = n // 2
    return X[:cut], y[:cut], X[cut:], y[cut:]


def simulate_null_counts(n, lambda_b, *, seed):
    """Sample n spike counts from the null Poisson(lambda_b)."""
    rng = np.random.default_rng(seed)
    return rng.poisson(lambda_b, size=n).astype(float)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def fit_Q(X_train, y_train):
    return nmo.glm.GLM(solver_name="LBFGS").fit(X_train, y_train)


def fit_B(y_train):
    return float(np.mean(y_train))


# ---------------------------------------------------------------------------
# Betting game
# ---------------------------------------------------------------------------

def log_wealth_per_bin(lambda_q, lambda_b, y):
    """log S(y | u) for Poisson Q vs Poisson B, y! terms cancel."""
    lambda_q = np.clip(np.asarray(lambda_q).reshape(-1), 1e-12, None)
    lambda_b = max(lambda_b, 1e-12)
    return (lambda_b - lambda_q) + y * (np.log(lambda_q) - np.log(lambda_b))


def anticipated_log_wealth_per_bin(lambda_q, lambda_b):
    """Per-bin log wealth Q ANTICIPATES — i.e., the player's expected gain
    under the (possibly wrong) assumption that P = Q.

    For Poisson, E_{Y~Poisson(lambda_q)}[log S(Y|u)] = lambda_q log(lambda_q/lambda_b)
    - (lambda_q - lambda_b), which is the per-bin KL divergence
    KL(Poisson(lambda_q) || Poisson(lambda_b)). Summing over bins gives
    Q's anticipated wealth trajectory; comparing to the realized trajectory
    (run_game) exposes any model mismatch (residual KL(P || Q) gap)."""
    lambda_q = np.clip(np.asarray(lambda_q).reshape(-1), 1e-12, None)
    lambda_b = max(lambda_b, 1e-12)
    return lambda_q * (np.log(lambda_q) - np.log(lambda_b)) - (lambda_q - lambda_b)


def run_game(model_q, lambda_b, X_test, y_test):
    lambda_q = np.asarray(model_q.predict(X_test)).reshape(-1)
    log_W = np.cumsum(log_wealth_per_bin(lambda_q, lambda_b, y_test))
    log_W_ant = np.cumsum(anticipated_log_wealth_per_bin(lambda_q, lambda_b))
    return log_W, log_W_ant


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

def run_experiment(label, X, y, *, seed):
    """Fit Q + B on training half, run game on the real test half."""
    X_tr, y_tr, X_te, y_te = split_half(X, y, shuffle=True, seed=seed)
    model_q = fit_Q(X_tr, y_tr)
    lambda_b = fit_B(y_tr)
    log_W, log_W_ant = run_game(model_q, lambda_b, X_te, y_te)
    return {
        "label":     label,
        "log_W":     log_W,
        "log_W_ant": log_W_ant,
        "model_q":   model_q,
        "lambda_b":  lambda_b,
        "n_test":    len(y_te),
        "n_train":   len(y_tr),
    }


def run_reps(experiment_fn, *, n_reps, seed_start):
    """Run `experiment_fn(seed=...)` `n_reps` times, return a result dict
    with `log_W_reps` (list of arrays) and `log_W_ant_reps` (list of arrays;
    the player's anticipated trajectories under P=Q), plus `model_q` /
    `lambda_b` from the FIRST rep (used for tuning-curve display)."""
    log_W_reps = []
    log_W_ant_reps = []
    first = None
    for i in range(n_reps):
        s = seed_start + i
        res = experiment_fn(seed=s)
        log_W_reps.append(res["log_W"])
        log_W_ant_reps.append(res["log_W_ant"])
        if i == 0:
            first = res
    out = dict(first)
    out["log_W_reps"]     = log_W_reps
    out["log_W_ant_reps"] = log_W_ant_reps
    out.pop("log_W", None)
    out.pop("log_W_ant", None)
    return out


def run_experiment_true_null(label, X, y, *, seed):
    """Fit Q + B on the real training half, then run the game on SYNTHETIC
    spike counts drawn from Poisson(lambda_b).

    This is the actual null that Ville's inequality bounds: y ~ b.
    Q's predictions can be anything — what matters is that the data
    really is from B, so the wealth process is a B-martingale and
    P(sup_t W_t >= 1/alpha) <= alpha.
    """
    X_tr, y_tr, X_te, _ = split_half(X, y, shuffle=True, seed=seed)
    model_q = fit_Q(X_tr, y_tr)
    lambda_b = fit_B(y_tr)
    y_te_sim = simulate_null_counts(len(X_te), lambda_b, seed=seed + 7919)
    log_W, log_W_ant = run_game(model_q, lambda_b, X_te, y_te_sim)
    return {
        "label":     label,
        "log_W":     log_W,
        "log_W_ant": log_W_ant,
        "model_q":   model_q,
        "lambda_b":  lambda_b,
        "n_test":    len(y_te_sim),
        "n_train":   len(y_tr),
    }


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def _crossing_idx(log_W, alpha):
    thresh = -np.log(alpha)
    crossings = np.where(log_W >= thresh)[0]
    return int(crossings[0]) if len(crossings) else None


def plot_wealth(results, *, alpha, bin_size, out_path, y_unit="bits",
                xmax_strong=250, xmax_mid=8000, xmax_weak=None,
                x_in_seconds=False, show_anticipated=False):
    """Three horizontal subplots — strong | intermediate | weak — each
    overlaying its `n_reps` wealth trajectories at semi-transparent alpha.
    Each panel uses its own x-range (passed via xmax_* kwargs; None = full
    test set) so the dynamics are visible at an appropriate scale.

    `y_unit` controls the y-axis:
      "bits":             log_2(W_t) — number of doublings of starting wealth.
                          Threshold log_2(1/alpha) ≈ 4.32 for alpha=0.05.
      "alpha_rejections": log_{1/alpha}(W_t) — number of α-rejection's worth
                          of evidence accumulated. Threshold sits at y = 1
                          (W_t = 1/alpha). The slope is "α-rejections per
                          second"; its reciprocal is "seconds to first reject".
    """
    if y_unit == "bits":
        # log_W is in nats; divide by log 2 to get bits (doublings).
        # Title rate is reported per-bin (intrinsic to the data, not the
        # binning choice) so 1 bit/bin means "wealth doubles every bin."
        transform    = lambda lw: lw / np.log(2)
        threshold    = -np.log2(alpha)
        ylabel       = r"Cumulative $\log_2 W_t$"
        rate_label   = "bits/bin"
        unit_factor  = 1.0 / np.log(2)
        time_divisor = 1.0          # per-bin
        title_tag    = ""
    elif y_unit == "alpha_rejections":
        log_arecip   = np.log(1.0 / alpha)
        transform    = lambda lw: lw / log_arecip
        threshold    = 1.0
        ylabel       = fr"Cumulative $\log_{{1/\alpha}} W_t$"
        rate_label   = r"$\alpha$-rej/s"
        unit_factor  = 1.0 / log_arecip
        time_divisor = bin_size     # per-second
        title_tag    = "  (α-normalized)"
    else:
        raise ValueError(f"y_unit must be 'bits' or 'alpha_rejections'; "
                         f"got {y_unit!r}")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    trajectory_alpha = 0.45

    cell_specs = [
        ("strong", COLOR_STRONG, "Strong",       xmax_strong),
        ("mid",    COLOR_MID,    "Intermediate", xmax_mid),
        ("weak",   COLOR_WEAK,   "Weak",         xmax_weak),
    ]

    for ax, (key, color, title_prefix, x_max) in zip(axes, cell_specs):
        res = results[key]
        log_W_reps = res["log_W_reps"]
        log_W_ant_reps = res["log_W_ant_reps"]
        n_reps = len(log_W_reps)
        n_bins_full = len(log_W_reps[0])

        # Realized wealth: 10 noisy trajectories
        for log_W in log_W_reps:
            y = transform(log_W)
            t = np.arange(1, len(y) + 1)
            if x_max is not None:
                m = t <= x_max
                t, y = t[m], y[m]
            x_plot = t * bin_size if x_in_seconds else t
            ax.plot(x_plot, y, color=color, lw=1.6, alpha=trajectory_alpha)

        # Optional: anticipated wealth (under P=Q) — straight reference
        # line through origin with slope = mean per-bin
        # KL(Poisson(lambda_q) || Poisson(lambda_b)) averaged across reps.
        # Gap to the realized trajectories visualizes residual model
        # mismatch (mean-calibration of Q's predicted rates).
        ant_rate_in_unit = None
        if show_anticipated:
            ant_finals_nats = np.array([lw[-1] for lw in log_W_ant_reps])
            ant_slope_nats = ant_finals_nats.mean() / n_bins_full
            t_line = np.arange(1, (x_max if x_max is not None else n_bins_full) + 1)
            ant_line_nats = ant_slope_nats * t_line
            ant_line_y = transform(ant_line_nats)
            ant_x = t_line * bin_size if x_in_seconds else t_line
            ant_rate_in_unit = ant_slope_nats / time_divisor * unit_factor
            ax.plot(ant_x, ant_line_y, color="black", ls="-", lw=2.5, alpha=0.85,
                    label=fr"anticipated")

        ax.axhline(threshold, color="red", ls=":", lw=2.5,
                   label=fr"reject @ $\alpha={alpha}$", alpha=0.55)
        ax.axhline(0, color="red", lw=2.5, alpha=0.55)

        finals = np.array([lw[-1] for lw in log_W_reps])  # nats
        rate = (finals.mean() / n_bins_full
                / time_divisor * unit_factor)
        n_rej = sum(1 for lw in log_W_reps
                    if _crossing_idx(lw, alpha) is not None)

        cell_id = res["cell_id"]
        if show_anticipated:
            title_line2 = (f"actual / anticipated: "
                           f"{rate:+.2f} / {ant_rate_in_unit:+.2f} "
                           f"{rate_label}")
        else:
            title_line2 = (f"{rate:+.3f} {rate_label}  "
                           f"({n_rej}/{n_reps} reject)")
        ax.set_title(f"{title_prefix} cell {cell_id}\n{title_line2}")
        ax.set_xlabel("Time (s)" if x_in_seconds
                      else f"Test bin index $t$  (bin size {bin_size*1000:.0f} ms)")
        if ax is axes[0]:
            ax.set_ylabel(ylabel)
        ax.legend(frameon=False, loc="best")
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(f"Wealth trajectories: GLM vs. homogeneous Poisson baseline "
                 f"({len(results['strong']['log_W_reps'])} reps per cell)"
                 f"{title_tag}")
    fig.tight_layout()
    _save_figure(fig, out_path)


def plot_tuning_triple(results, basis, *, bin_size, out_path, which):
    """Side-by-side tuning curves for strong, intermediate, and weak cells.

    `which` is "train" or "test" — picks which split's empirical tuning
    to overlay on the (always train-fit) GLM curve."""
    assert which in ("train", "test")

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharey=False)

    for ax, (key, color, title_prefix) in zip(
        axes,
        [("strong", COLOR_STRONG, "Strong cell"),
         ("mid",    COLOR_MID,    "Intermediate cell"),
         ("weak",   COLOR_WEAK,   "Weak cell")],
    ):
        res = results[key]
        cell_id = res["cell_id"]
        hd_centers, rate_emp_hz = res[f"tuning_{which}"]

        hd_grid = np.linspace(0, 2 * np.pi, 200)
        X_grid = np.asarray(basis.compute_features(hd_grid))
        rate_glm_hz = (np.asarray(res["model_q"].predict(X_grid)).reshape(-1)
                       / bin_size)

        ax.plot(hd_centers, rate_emp_hz, "o", color="black",
                alpha=0.55, ms=6, label=f"empirical")
        ax.plot(hd_grid, rate_glm_hz, color=color, lw=2.8,
                label="GLM Q")
        ax.axhline(res["lambda_b"] / bin_size, color="gray", ls="--",
                   lw=1.8, label=f"baseline B")
        ax.set_xlabel("Head direction (rad)")
        ax.set_ylabel("Rate (Hz)")
        ax.set_title(f"{title_prefix}: cell {cell_id}")
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(f"Empirical tuning on {which} set vs. GLM fit "
                 f"(fit on train set)")
    fig.tight_layout()
    _save_figure(fig, out_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bin-size", type=float, default=0.05)
    parser.add_argument("--n-basis", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--min-spikes", type=int, default=200,
                        help="Exclude cells with fewer wake-epoch spikes.")
    parser.add_argument("--xmax-strong", type=int, default=100,
                        help="x-axis upper limit (bins) for the strong-cell "
                             "panel of the wealth figure.")
    parser.add_argument("--xmax-mid", type=int, default=2000,
                        help="x-axis upper limit (bins) for the "
                             "intermediate-cell panel of the wealth figure.")
    parser.add_argument("--xmax-weak", type=int, default=0,
                        help="x-axis upper limit (bins) for the weak-cell "
                             "panel of the wealth figure (0 = full test set).")
    parser.add_argument("--n-reps", type=int, default=10,
                        help="Number of independent train/test splits to "
                             "plot per condition (semi-transparent overlays).")
    parser.add_argument("--n-calibration", type=int, default=100,
                        help="Repetitions for the true-null calibration "
                             "check at the end (0 to skip).")
    args = parser.parse_args()

    FIG_DIR.mkdir(exist_ok=True)

    print("Loading session ...")
    data = load_session()
    spikes = data["units"]
    head_dir = data["ry"]
    wake_ep = get_wake_epoch(data)
    print(f"  units: {len(spikes)}  |  wake duration: "
          f"{float(wake_ep.tot_length()):.1f} s")

    print("Ranking cells by empirical bits/bin "
          "(KL of tuning curve vs constant baseline) ...")
    ranking = rank_cells_by_training_bits(
        spikes, head_dir, wake_ep,
        bin_size=args.bin_size, min_spikes=args.min_spikes,
    )
    best_id  = int(ranking.index[0])
    mid_idx  = len(ranking) // 2
    mid_id   = int(ranking.index[mid_idx])
    worst_id = int(ranking.index[-1])
    print(f"  {len(ranking)} cells pass ≥{args.min_spikes}-spike filter")
    print(f"  strongest:    cell {best_id}  "
          f"(bits/bin = {ranking.iloc[0]:.4f}, "
          f"= {ranking.iloc[0]/args.bin_size:.2f} bits/s)")
    print(f"  intermediate: cell {mid_id}  "
          f"(bits/bin = {ranking.iloc[mid_idx]:.4f}, "
          f"= {ranking.iloc[mid_idx]/args.bin_size:.2f} bits/s)")
    print(f"  weakest:      cell {worst_id}  "
          f"(bits/bin = {ranking.iloc[-1]:.4f}, "
          f"= {ranking.iloc[-1]/args.bin_size:.2f} bits/s)")

    print("Building shared head-direction features ...")
    X, valid, basis, hd_valid = build_features(
        head_dir, wake_ep, bin_size=args.bin_size, n_basis=args.n_basis,
    )
    print(f"  bins: {len(X)}  |  n_basis: {args.n_basis}")

    train_idx, test_idx = split_indices(
        len(X), shuffle=True, seed=args.seed,
    )
    hd_train = hd_valid[train_idx]
    hd_test  = hd_valid[test_idx]

    print(f"Running 4 conditions × {args.n_reps} reps each ...")
    y_strong = get_cell_counts(
        spikes, wake_ep, bin_size=args.bin_size, cell_id=best_id, valid=valid,
    )
    y_mid = get_cell_counts(
        spikes, wake_ep, bin_size=args.bin_size, cell_id=mid_id, valid=valid,
    )
    y_weak = get_cell_counts(
        spikes, wake_ep, bin_size=args.bin_size, cell_id=worst_id, valid=valid,
    )

    res_strong = run_reps(
        partial(run_experiment, f"strong cell {best_id}", X, y_strong),
        n_reps=args.n_reps, seed_start=args.seed,
    )
    res_mid = run_reps(
        partial(run_experiment, f"intermediate cell {mid_id}", X, y_mid),
        n_reps=args.n_reps, seed_start=args.seed,
    )
    res_weak = run_reps(
        partial(run_experiment, f"weak cell {worst_id}", X, y_weak),
        n_reps=args.n_reps, seed_start=args.seed,
    )
    res_null = run_reps(
        partial(run_experiment_true_null,
                "true null: y ~ Poisson($\\lambda_b$)", X, y_strong),
        n_reps=args.n_reps, seed_start=args.seed,
    )

    for tag, res in [("strong", res_strong),
                     ("mid",    res_mid),
                     ("weak",   res_weak),
                     ("null",   res_null)]:
        finals = np.array([lw[-1] / np.log(2) for lw in res["log_W_reps"]])
        rates  = finals / len(res["log_W_reps"][0]) / args.bin_size
        n_rej  = sum(1 for lw in res["log_W_reps"]
                     if _crossing_idx(lw, args.alpha) is not None)
        msg = (f"  {tag:6s}  {res['label']:42s}  "
               f"log2 W_T = {finals.mean():+8.1f} ± {finals.std():6.1f}  "
               f"({rates.mean():+.2f} ± {rates.std():.2f} bits/s)  "
               f"rejected {n_rej}/{args.n_reps}")
        print(msg)

    # Attach per-cell metadata + train/test empirical tunings for plotting.
    for key, cell_id, y_cell in [
        ("strong", best_id,  y_strong),
        ("mid",    mid_id,   y_mid),
        ("weak",   worst_id, y_weak),
    ]:
        res = {"strong": res_strong, "mid": res_mid, "weak": res_weak}[key]
        res["cell_id"]       = cell_id
        res["tuning_train"]  = empirical_tuning(
            y_cell[train_idx], hd_train, bin_size=args.bin_size,
        )
        res["tuning_test"]   = empirical_tuning(
            y_cell[test_idx],  hd_test,  bin_size=args.bin_size,
        )

    results_for_plot = {
        "strong": res_strong,
        "mid":    res_mid,
        "weak":   res_weak,
        "null":   res_null,
    }

    print("Saving figures ...")
    xmax_weak = args.xmax_weak if args.xmax_weak > 0 else None
    plot_wealth(
        results_for_plot,
        alpha=args.alpha, bin_size=args.bin_size,
        out_path=FIG_DIR / "wealth_trajectory.pdf",
        y_unit="bits",
        xmax_strong=args.xmax_strong,
        xmax_mid=args.xmax_mid,
        xmax_weak=xmax_weak,
    )
    plot_wealth(
        results_for_plot,
        alpha=args.alpha, bin_size=args.bin_size,
        out_path=FIG_DIR / "wealth_alpha_normalized.pdf",
        y_unit="alpha_rejections",
        x_in_seconds=True,
        xmax_strong=args.xmax_strong,
        xmax_mid=args.xmax_mid,
        xmax_weak=xmax_weak,
    )
    plot_wealth(
        results_for_plot,
        alpha=args.alpha, bin_size=args.bin_size,
        out_path=FIG_DIR / "wealth_alpha_anticipated.pdf",
        y_unit="alpha_rejections",
        x_in_seconds=True,
        show_anticipated=True,
        xmax_strong=args.xmax_strong,
        xmax_mid=args.xmax_mid,
        xmax_weak=xmax_weak,
    )
    plot_tuning_triple(
        results_for_plot, basis,
        bin_size=args.bin_size,
        out_path=FIG_DIR / "tuning_curves_train.pdf",
        which="train",
    )
    plot_tuning_triple(
        results_for_plot, basis,
        bin_size=args.bin_size,
        out_path=FIG_DIR / "tuning_curves_test.pdf",
        which="test",
    )
    for name in ("wealth_trajectory", "wealth_alpha_normalized",
                 "wealth_alpha_anticipated",
                 "tuning_curves_train", "tuning_curves_test"):
        print(f"  wrote {FIG_DIR}/{name}.pdf  +  {WEB_FIG_DIR}/{name}.png")

    # ----------------------------------------------------------------------
    # Calibration check: empirical type-I error under the TRUE null.
    # Under y ~ Poisson(lambda_b), the wealth process is a B-martingale,
    # so Ville's inequality guarantees P(sup_t W_t >= 1/alpha) <= alpha.
    # We confirm this empirically across `args.n_calibration` independent
    # null draws.
    # ----------------------------------------------------------------------
    if args.n_calibration > 0:
        from tqdm import trange
        print(f"\nCalibration: empirical false-rejection rate under true null "
              f"(target <= {args.alpha:.2f}, {args.n_calibration} reps)")
        n_reject = 0
        for s in trange(args.seed + 1, args.seed + args.n_calibration + 1,
                        desc="  null reps"):
            res = run_experiment_true_null(
                "calibration",
                X, y_strong, seed=s,
            )
            if _crossing_idx(res["log_W"], args.alpha) is not None:
                n_reject += 1
        emp_rate = n_reject / args.n_calibration
        print(f"  rejected {n_reject}/{args.n_calibration} = "
              f"{emp_rate:.3f}  (target <= {args.alpha:.3f})")



if __name__ == "__main__":
    main()
