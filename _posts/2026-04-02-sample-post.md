---
layout: post
title: "Sample Blog Post"
subtitle: "This is just a test. Please pardon us while we're under construction."
date: 2026-04-02
tags: [Gaussian processes, neural decoding, Bayesian inference]
---

Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum

## Heading

Let $y_t \in \mathbb{R}^N$ be the spike count vector across $N$ neurons at time $t$, and let $x_t \in \mathbb{R}^d$ be a low-dimensional latent state we want to infer. A standard generative model is:

$$
x \sim \mathcal{GP}(0, k_\theta)
\qquad
y_t \mid x_t \sim p(y_t \mid f(x_t))
$$

where $f: \mathbb{R}^d \to \mathbb{R}^N$ is a tuning function and $k_\theta$ is a kernel with hyperparameters $\theta$. This is, roughly, the structure of GPFA (Yu et al., 2009) and its many descendants.

The GP prior over the latent trajectory does two things: it smooths the inferred path in time (or space), and it controls how uncertainty propagates. The bandwidth of a squared exponential kernel, for instance, sets the timescale over which the latent state is expected to vary. Choose it too short and you overfit to noise; too long and you wash out genuine dynamics.

## What the kernel encodes

Different kernel choices correspond to different beliefs about the latent process:

**Squared exponential (RBF):** $k(t, t') = \sigma^2 \exp\!\left(-\frac{(t-t')^2}{2\ell^2}\right)$. Infinitely differentiable sample paths. Good when the latent variable changes smoothly — e.g., slowly-varying motor variables during reaching. The lengthscale $\ell$ is the key hyperparameter and should be set by marginal likelihood optimization, not by hand.

**Matérn-$\frac{3}{2}$:** $k(t, t') = \sigma^2\!\left(1 + \frac{\sqrt{3}\,|t-t'|}{\ell}\right)\exp\!\left(-\frac{\sqrt{3}\,|t-t'|}{\ell}\right)$. Once-differentiable paths. Better for processes with sharper transients, like peri-event dynamics locked to a stimulus onset.

**Periodic:** $k(t, t') = \sigma^2 \exp\!\left(-\frac{2\sin^2(\pi|t-t'|/p)}{\ell^2}\right)$. Enforces periodicity with period $p$. Useful for oscillatory latents or when you want to model theta-band activity as a structured prior.

**Linear + RBF:** Additive kernels let you separately model a smooth trend and non-stationary drift. This corresponds to assuming a slow underlying state plus fast fluctuations.

The choice is not merely cosmetic. If the true latent is periodic and you use an RBF kernel, you'll systematically misattribute oscillatory structure to noise, inflating your uncertainty estimates and potentially confounding downstream analyses.

## Marginal likelihood as model selection

One of the cleanest properties of GP models is that the marginal likelihood $p(y \mid \theta)$ is available in closed form under Gaussian observations:

$$
\log p(y \mid \theta) = -\frac{1}{2} y^\top (K_\theta + \sigma_n^2 I)^{-1} y - \frac{1}{2}\log |K_\theta + \sigma_n^2 I| - \frac{n}{2}\log 2\pi
$$

The first term rewards fit; the second penalizes model complexity. This is Occam's razor made explicit in the algebra. Maximizing this over $\theta$ — including lengthscale, variance, and noise — is both efficient and principled. For Poisson observations (more realistic for spiking), the marginal likelihood requires approximation (Laplace, variational, etc.), but the structure of the trade-off persists.

Empirically, marginal likelihood optimization tends to recover sensible lengthscales when the signal-to-noise ratio is reasonable. It breaks down when the number of inducing points is too small (in sparse approximations) or when the likelihood is severely non-Gaussian and the Laplace approximation is poor.

## Practical considerations

A few things that bite you in practice:

**Initialization.** The marginal likelihood surface is not convex. Multiple random restarts, or warm-starting from a Fourier analysis of the data (which gives a rough power spectrum → lengthscale correspondence), usually helps.

**Scaling.** Exact GP inference is $O(n^3)$ in the number of timepoints. For trial-length data ($T \lesssim 1000$ bins) this is fine. For long recordings you need sparse approximations — inducing point methods (SVGP, etc.) or state-space equivalents of GPs via the Kalman filter (Solin & Särkkä, 2020), which reduce inference to $O(n)$.

**Identifiability.** When $f$ is nonlinear and learned from data, there's a fundamental non-identifiability between the kernel and the tuning function: you can always absorb variance into one or the other. Fixing the output scale of the kernel to 1 and learning a gain parameter in $f$ is one way to handle this, but you should be explicit about what's identified and what isn't.

**Multi-output.** For $N$ neurons, the naive approach uses $N$ independent GPs on the output side. A richer model — the linear model of coregionalization, or a deep kernel — can share statistical strength across neurons. Whether this helps depends on whether neurons share latent inputs, which is precisely what you're often trying to test.

## Summary

The Gaussian process prior in neural decoding is not just a smoothing device — it's a formal encoding of beliefs about latent structure. The kernel determines the inductive bias, the marginal likelihood optimizes hyperparameters in a principled way, and the posterior gives calibrated uncertainty estimates that can be propagated into downstream analyses.

For most motor decoding problems, an RBF or Matérn kernel with marginal likelihood hyperparameter tuning is a good default. For richer structure — oscillations, non-stationarities, multi-timescale dynamics — additive or spectral kernels are worth the extra complexity. And if your data is long, go to a state-space formulation.

---

*Further reading:* Yu et al. (2009) GPFA paper; Duncker & Sahani (2018) on structured VAEs for neural data; Solin & Särkkä (2020) on Hilbert space GPs; Rasmussen & Williams (2006) for the GP foundations.
