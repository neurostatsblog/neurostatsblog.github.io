# Betting-game demo on real neural data

Companion code for the post **["Betting games for model comparison"](https://neurostatsblog.github.io/)**.

Fits a Poisson GLM (`Q`) to one head-direction cell from the Peyrache et al. (2015) anterior-thalamus dataset, compares it against a homogeneous-Poisson baseline (`B`) by running the wealth-process described in the post on the held-out half of the recording.

## Setup

This is a standard Python project, separate from the Jekyll/Ruby site. Recommended:

```bash
cd code/betting

# Create + activate a virtual env (any flavor — pyenv, conda, uv, etc.)
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

`nemos` pulls in `jax` and `jaxlib`. On an M-series Mac the default `pip` install picks the right wheel; if you want GPU/CUDA, follow the JAX install instructions for your platform first.

## Run

```bash
python head_direction_betting.py
```

Optional flags:

```bash
python head_direction_betting.py --bin-size 0.02 --n-basis 12 --alpha 0.05
```

Outputs go to `figures/` (vector PDFs):

- `wealth_trajectory.pdf` — cumulative $\log_2 W_t$ over test bins for three conditions (strong cell, weak cell, shuffled-HD null), with the $\alpha = 0.05$ rejection threshold marked and a zoomed inset over the first 400 bins.
- `tuning_curves.pdf` — empirical vs. GLM tuning for both the strong and weak cell side by side.

The first run downloads the dataset (~150 MB) via `nemos.fetch.fetch_data` into a cache directory; subsequent runs are fast.
