---
layout: post
title: "Betting games for model comparison"
subtitle: "A simple way to interpret heldout log-likelihood scores"
date: 2026-04-02
tags: [statistics]
authors: ["Alex Williams"]
reviewers: ["n/a"]
---

Whenever we fit a model to neural or behavioral data, we need to benchmark it against simpler or well-known baselines.
Typically this is done by reporting the difference in log-likelihoods on heldout data.
For example, the popular "bits per spike" performance metric is simply the log (base 2) likelihood of the model minus the log (base 2) likelihood of a homogenous Poisson process (or another approriate baseline model), divided by the total number of spikes in the dataset.[^bits-per-spike]

This post offers some thoughts on how we can interpret this performance measure.
For example, if my model gives a 0.34 bits per spike improvement over the baseline, should I interpret that as very good? Marginal? Completely inconsequential?

I have struggled to answer these questions satisfactorily and this post is part of my attempt to rectify this fundamental gap in my understanding.
I'll focus on a particular interpretation that imagines the two models playing against each other in a zero-sum betting game based on forecasting heldout datapoints.
This game-theoretic framing has gained traction in certain corners of statistics


## Basic Setup

Let's formalize the problem.
Suppose that we have fit a model $Q$ and a baseline $B$ to a set of "training data" and that we're now ready to compare them head-to-head on a set of heldout test data.
Let $X_1, X_2, X_3, \dots$ denote a (potentially infinite) sequence of heldout data samples that we'd like to measure.
We assume these samples are independent and identically distributed according to an unknown distribution $P$.
Our hope is that $Q$ is in some sense "closer" to the true distribution $P$ than the basline model $B$.

We will make some mild assumptions.
In particular, that $Q$ and $B$ have density functions $q(x)$ and $b(x)$, and that these density functions have full support over the space of observations.
Thus, for any randomly observed datapoint $X \sim P$, we know that $q(X) > 0$ and $b(X) > 0$ almost surely.
Intuitively, this allows us to compute *likelihood ratios*, $q(X)/b(X)$, without having to worry about divide-by-zero errors.
This also assures us log-likelihoods, $\log q(X)$ and $\log b(X)$, are always finite.

Given an infinite amount of heldout data, our ideal measure of performance (at least for the purposes of this post) is the expected log-likelihood ratio:

$$
\begin{equation}
\mathcal{L} = \mathbb{E}_{X \sim P} \Big [ \log q(X)/ b(X) \Big ] = \mathbb{E}_{X \sim P} \Big [ \log q(X) - \log b(X) \Big ] 
\label{eq:expected-log-likelihood-ratio}
\end{equation}
$$

Note that the expectation is computed under $P$. 
Since $P$ is unknown in real world situations, we can estimate the expression above by holding out a test set with $T$ data samples and approximating the expectation with an empirical average:

$$
\mathcal{L} \approx \widehat{\mathcal{L}} = \frac{1}{T} \sum_{t=1}^T \log q(X_t)/ b(X_t)  = \frac{1}{T} \sum_{t=1}^T \Big [ \log q(X) - \log b(X) \Big ] 
\label{eq:empirical-log-likelihood-ratio}
$$

It is worth remarking that this entire post will not deal with the training process---i.e. how does one find $Q$?
This typically involves optimizing parameters, so one may elsewhere see the liklihood expressed as something like $q (x \mid \theta)$ where $\theta$ denotes trainable parameters.
However, we don't need to refer to $\theta$ at all for the purposes of this post so we simply write $q(x)$ in place of $q (x \mid \theta)$.

Similarly, we are often interested in fitting regression models, which predict outcomes (e.g. neural spikes) based on inputs variables (e.g. stimulus or behavioral variables).
Concretely, suppose that our test data comes as a sequence of paired observations $(X_1, U_1), (X_2, U_2), (X_3, U_3), \dots$ where the $U$'s denote inputs.
In this case, our model $Q$ and baseline $B$ would now take the form of conditional probability distributions, and the expected log-likelihood ratio would become $\log q ( X \mid U) / b ( X \mid U)$ taken in expectation over $X, U \sim P$.
So the extension to regression models is immediate and not worth cluttering notation by explicitly denoting input variables.

## Introducing the Game

Recall that our goal is to come up with intuitive interpretations of $\mathcal{L}$ as a measure of model performance.
One way to approach this is to imagine model $Q$ and model $B$ "playing a game" against each other by forecasting values of $X_1, X_2, X_3, \dots$ sampled as heldout data.

The game starts by giving player $Q$ and player $B$ one unit of initial _wealth_:

$$
W_0^Q = W_0^B = 1
$$

We use $W_t^Q$ and $W_t^B$ to denote each player's wealth after playing $t$ rounds of the game.
After each round, the wealth scores are updated according to a _betting function_ $S(x) > 0$ as follows:

$$
\begin{align}
W_t^Q &= W_{t-1}^Q \cdot S( X_{t} ) \label{eq:game-1}
\\
W_t^B &= W_{t-1}^B / S( X_{t} ) \label{eq:game-2}
\end{align}
$$

Note that this is a [zero-sum game](https://en.wikipedia.org/wiki/Zero-sum_game) in terms of log wealth; that is, since $W_t^Q W_t^B = W_0^Q W_0^B$ for all $t$, we have:

$$
\log W_t^Q + \log W_t^B  = 0, \quad \text{for all}~t.
$$

It is easy to calculate the long-run performance of each player in the game.
For player $Q$, we have:

$$
\begin{align}
W_T^Q = \prod_{t=1}^T S( X_{t} ) 
      &= \exp \log \prod_{t=1}^T S( X_{t} ) \\
      &= \exp \sum_{t=1}^T \log S( X_{t} ) \\
      &= \exp \Big ( T \cdot \Big ( \tfrac{1}{T} \sum_{t=1}^T \log S(X_t) \Big ) \Big ) \\
      &\approx \exp \Big ( T \cdot \mathbb{E}_{X \sim P} \log S(X) \Big )
      \label{eq:q-wealth-growth}
\end{align}
$$

Note that the approximation in the final line becomes exact as $T \rightarrow \infty$.
<!-- Thus, under their belief that $P=Q$, player $Q$ believes their wealth will grow exponentially at a rate of $\mathbb{E}_{X \sim Q} \log S(X)$. -->
By an analogous set of calculations, we find the long-run performance of player $B$ to be

$$
\begin{align}
W_T^B &\approx \exp \Big ( -T \cdot \mathbb{E}_{X \sim P} \log S(X) \Big )
\label{eq:b-wealth-growth}
\end{align}
$$

Thus, in the long run, one of the two player's wealth will grow exponentially fast while the other's will decay to zero exponentially quickly.
Player $Q$ will win if $\mathbb{E}\_{X \sim P} \log S(X)$ is greater than zero and player $B$ will win if $\mathbb{E}\_{X \sim P} \log S(X)$ is less than zero.

<!-- Thus, under their belief that $P=B$, player $B$ believes their wealth will grow exponentially at a rate of $-1 \cdot \mathbb{E}_{X \sim B} \log S(X)$. -->

## The Likelihood Ratio is the "Best" Betting Function

Before they play the game the two players need to agree on a fair betting function, $S(x)$.
We assume that the two players commit fully to their respective models---that is, player $Q$ believes that $P=Q$ and player $B$ believes that $P=B$.

Somewhat remarkably, this is more-or-less sufficient to pin down a unique solution to the betting function, and this solution is the likelihood ratio:

$$
\begin{equation}
S(x) = \frac{q(x)}{b(x)}
\label{eq:betting-function-equals-likelihood-ratio}
\end{equation}
$$

Under a couple technical but reasonable assumptions, it turns out that both players will agree that this betting function is fair.
Moreover, out of the space of fair betting functions, both players will believe that this choice is maximally beneficial to their long-term wealth growth.
The math behind this is simple, but it takes a little while to unpack.
I sketch the proof in [**Supplemental Note 1**](#) of this post.

## The Log Likelihood Ratio Determines Wealth Growth

Combining \eqref{eq:betting-function-equals-likelihood-ratio} with \eqref{eq:q-wealth-growth} and the definition of $\mathcal{L}$ in \eqref{eq:expected-log-likelihood-ratio}, we see that, for large $T$:

$$
\begin{equation}
W^Q_T \approx \exp \Big ( \mathcal{L} \cdot T \Big )
\label{eq:player-q-long-term-wealth}
\end{equation}
$$

In other words, the wealth accumulated player $Q$ in the game will, over the long run, grow or decay exponentially fast at a rate given by the expected log-likelihood ratio.
Likewise, the long-run wealth of player $B$ is well approximated by:

$$
\begin{equation}
W^B_T \approx \exp \Big ( -\mathcal{L} \cdot T \Big )
\label{eq:player-b-long-term-wealth}
\end{equation}
$$

Equations \eqref{eq:player-q-long-term-wealth} and \eqref{eq:player-b-long-term-wealth} are the main punchline of this post.
They reveal that $\mathcal{L}$ represents the rate at which the proposed model $Q$ outperforms (in terms of accumulated wealth) a baseline forecaster using model $B$.
Importantly, even small amounts of incremental outperformance can snowball into exponentially large gains over the long haul.

We have thus far used natural logarithms, but it may help to substitute base-2 logarithms into the results to aid interpretation.
By the change of base formula, $\mathcal{L}_2 = \mathcal{L} / \log(2)$ is the expected base-2 log likelihood.
For large $T$, we have $W^Q_T \approx 2^{\mathcal{L}_2 T}$, and so we can interpret $1 / \mathcal{L}_2$ as the time it takes for $Q$ to double it's wealth on average over the long run.

## Connection to Hypothesis Testing

I personally already find the interpretations sketched above very appealing, more so than thinking about information transmission.
But what makes this perspective very powerful is the following connection to hypothesis testing, through the following result known as [Ville's inequality](https://en.wikipedia.org/wiki/Ville%27s_inequality).

<div class="callout callout-theorem">
<p><strong>Ville's Inequality (informal).</strong> Let $(M_t)_{t \geq 0}$ be a sequence of random variables such that $M_t \geq 0$ almost surely for all $t$ and $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] \leq M_{t-1}$ for all $t$.
Then for any $\alpha > 0$,</p>
$$
P\!\left( \sup_{t \geq 0} M_t \, \geq \, 1/\alpha \right) \, \leq \, \alpha \cdot \mathbb{E}[M_0] .
$$
</div>

Intuitively, this result states that if the random sequence $(M\_t)\_{t \geq 0}$ is memoryless and not increasing it expectation,[^martingale] then $M_t$ cannot be very large at *any moment in time*. 

To see why this matters in our setting, suppose for the moment that the baseline $B$ is in fact the true data-generating distribution---i.e. $P = B$. 
Under this assumption, the wealth process $(W\_t^Q)\_{t \geq 0}$ satisfies all the conditions placed on $(M_t)_{t \geq 0}$ in Ville's inequality.
This is easy to check:

$$
\mathbb{E}_{X_t \sim B}\!\big[ W_t^Q \mid W_0^Q \dots W_{t-1}^Q \big]
\,=\, W_{t-1}^Q \cdot \mathbb{E}_{X_t \sim B} \left[ \frac{q(X_t)}{b(X_t)} \right]
\,=\, W_{t-1}^Q .
$$

since the expectation of the likelihood ratio equals one.[^expectation-derivation]
Ville's inequality then tells us that the probability of player $Q$'s wealth *ever* exceeding the threshold $1/\alpha$---at any round of the game---is at most $\alpha$:

$$
P\!\left( \sup_{t \geq 0} W_t^Q \, \geq \, 1/\alpha \right) \, \leq \, \alpha .
$$

This furnishes an *anytime-valid* hypothesis test of the null $H_0 : P = B$: we may reject $H_0$ at level $\alpha$ as soon as $W_t^Q$ crosses $1/\alpha$, regardless of how many rounds have been played. Unlike classical fixed-sample tests, we are free to peek at the data, stop early, or keep collecting more samples adaptively, all without inflating the type I error rate.

For example, if we adopt the customary significance threshold of $\alpha = 0.05$, then Ville's inequality tells us that we can reject the null hypothesis that $P = B$ if player $Q$'s wealth ever exceeds 20.



---

[^bits-per-spike]: Normalizing by the number of spikes in the dataset has always seemed like a weird choice to me, and I might dig into this in a future post.

[^martingale]: For those who appreciate jargon, we call $(M\_t)\_{t \geq 0}$ a *supermartingale* if it satisfies $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] \leq M_{t-1}$ and we call $(M\_t)\_{t \geq 0}$ a [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] = M_{t-1}$, we call $(M_t)_{t \geq 0}$. Ville's inequality says that all nonnegative martingales and supermartingales are upper bounded 

[^expectation-derivation]: Concretely, $\mathbb{E}_{X \sim B} \left[ \frac{q(X)}{b(X)} \right] = \int \frac{q(x)b(x)}{b(x)} dx =  \int q(x) dx = 1$.



