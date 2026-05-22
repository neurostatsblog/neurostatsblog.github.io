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
I'll focus on a particular interpretation that imagines the model playing a betting game against the "market" defined by the baseline model.
This game-theoretic framing has gained traction in a certain corner of statistics, a lot of which is very accesible in recent tutorials and reviews (see [**Further Reading**](#further-reading)).

## Basic Setup

Suppose that we have fit a model $Q$ and a baseline $B$ to a set of "training data" and that we're now ready to compare them head-to-head on a set of heldout test data.
Let $X_1, X_2, X_3, \dots$ denote a (potentially infinite) sequence of heldout data samples that we'd like to measure.
We assume these samples are independent and identically distributed according to an unknown distribution $P$.
Our hope is that $Q$ is in some sense "closer" to the true distribution $P$ than the basline model $B$.

We will make some mild assumptions.
In particular, that $Q$ and $B$ have density functions $q(x)$ and $b(x)$, and that these density functions have full support over the space of observations.
Thus, for any randomly observed datapoint $X \sim P$, we know that $q(X) > 0$ and $b(X) > 0$ almost surely.
Intuitively, this allows us to compute *likelihood ratios*, $q(X)/b(X)$, without having to worry about divide-by-zero errors.
This also assures us that log-likelihoods, $\log q(X)$ and $\log b(X)$, are always finite.

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

<!-- Similarly, we are often interested in fitting regression models, which predict outcomes (e.g. neural spikes) based on inputs variables (e.g. stimulus or behavioral variables).
Concretely, suppose that our test data comes as a sequence of paired observations $(X_1, U_1), (X_2, U_2), (X_3, U_3), \dots$ where the $U$'s denote inputs.
In this case, our model $Q$ and baseline $B$ would now take the form of conditional probability distributions, and the expected log-likelihood ratio would become $\log q ( X \mid U) / b ( X \mid U)$ taken in expectation over $X, U \sim P$.
So the extension to regression models is immediate and not worth cluttering notation by explicitly denoting input variables. -->

## Introducing the Game

Recall that our goal is to come up with intuitive interpretations of $\mathcal{L}$ as a measure of model performance.
One way to approach this is to imagine model $Q$ as a "player" in a betting game based on forecasting values of $X_1, X_2, X_3, \dots$ sampled as heldout data.
The bets made by the player are set by the "market" which operates according to the baseline model $B$.

The game starts by giving player $Q$ one unit of wealth:

$$
W_0 = 1
$$

We use $W_t$ denote the player's wealth after playing $t$ rounds of the game.
After each round, the wealth is updated according to a *betting function* or *contract* $S(x) > 0$ as follows:

$$
\begin{align}
W_t &= W_{t-1} \cdot S( X_{t} ) . \label{eq:wealth-process}
\end{align}
$$

To play the game, $Q$ needs to pay a price to buy the contract *S* on the free market.
There is a very basic argument that the fair price is given by the expected value of the contract's payoff under the *average beliefs* of all market participants (see [**Supplementary Note 1**](#supplementary-note-1)).
Here we will assume that player $Q$ only represents a very small part of the market,[^q-small] and that the market's beliefs are reflected by the baseline model $B$.

Under these assumptions it can be shown (see [**Supplementary Note 1**](#supplementary-note-1)) that a contract $S$ sold for price $p$ must satisfy the constraint that:

$$
\begin{equation}
\mathbb{E}_{X \sim B} \, \big [ \, p \cdot S(X) \, \big ] \leq p . \label{eq:pricing-constraint-verbose}
\end{equation}
$$

which is obviously equivalent to the constraint that:

$$
\begin{equation}
\mathbb{E}_{X \sim B} \, \big [ \, S(X) \, \big ] \leq 1 . \label{eq:pricing-constraint}
\end{equation}
$$

Under this pricing constraint, there is a very straightforward interpretation of the wealth update equation, given by \eqref{eq:wealth-process}.
At each round of betting, the player has $W_t$ units of wealth to purchase contracts on the free market.
We assume they bet everything---i.e. they purchase a contract with at price $p = W_t$ whose payoff is equal to $p \cdot S(X)$.
Thus, at the next round of betting the player will have $W_{t+1} = p \cdot S(X_t) = W_t \cdot S(X_t)$ units of wealth.

## Choosing the optimal contract function

Out of all the feasible contract functions that satisfy this constraint, what should $Q$ choose to play?
Over a very large number of betting rounds, say $T$, the player will accumulate

$$
\begin{align}
W_T = \prod_{t=1}^T S( X_{t} ) 
      &= \exp \log \prod_{t=1}^T S( X_{t} ) \\
      &= \exp \sum_{t=1}^T \log S( X_{t} ) \\
      &= \exp \Big ( T \cdot \Big ( \tfrac{1}{T} \sum_{t=1}^T \log S(X_t) \Big ) \Big ) \\
      &\approx \exp \Big ( T \cdot \mathbb{E}_{X \sim P} \log S(X) \Big )
      \label{eq:q-wealth-growth}
\end{align}
$$

units of wealth.
The approximation in the final line comes from replacing the empirical expectation $\tfrac{1}{T} \sum_{t=1}^T \log S(X_t)$ with the true expected value under $P$.

Since the player believes that $P = Q$, they anticipate to maximize their exponential rate of wealth growth under \eqref{eq:q-wealth-growth} by choosing $S(\cdot)$ in order to

$$
\text{maximize} ~~ \mathbb{E}_{X \sim Q} \log S(X) \quad \text{subject to} ~ \eqref{eq:pricing-constraint}.
\label{eq:kelly-criterion}
$$

Quite pleasingly, as shown in [**Supplemental Note 2**](#supplementary-note-2), the solution to this optimization problem turns out to be the likelihood ratio!

$$
\begin{equation}
S(x) = \frac{q(x)}{b(x)}
\label{eq:betting-function-equals-likelihood-ratio}
\end{equation}
$$

Combining equations \eqref{eq:betting-function-equals-likelihood-ratio} and \eqref{eq:q-wealth-growth} with the definition of $\mathcal{L}$ in \eqref{eq:expected-log-likelihood-ratio}, we see that the long-run wealth of the player is approximated by

$$
\begin{equation}
W_T \approx \exp \Big ( \mathcal{L} \cdot T \Big )
\label{eq:player-q-long-term-wealth}
\end{equation}
$$

for large $T$.
In other words, the wealth accumulated player $Q$ in the game will, over the long run, grow or decay exponentially fast at a rate given by the expected log-likelihood ratio.[^kelly]

## Some Interpretation

Equation \eqref{eq:player-q-long-term-wealth} is one of the main punchlines of this post.
It reveals that $\mathcal{L}$ represents the rate at which the proposed model $Q$ outperforms (in terms of accumulated wealth) a baseline forecaster using model $B$.
Importantly, even small amounts of incremental outperformance can snowball into exponentially large gains over the long haul.

We have thus far used natural logarithms, but it may help to substitute base-2 logarithms into the results to aid interpretation.
By the change of base formula, $\mathcal{L}_2 = \mathcal{L} / \log(2)$ is the expected base-2 log likelihood.
For large $T$, we have $W_T \approx 2^{\mathcal{L}_2 T}$, and so we can interpret $1 / \mathcal{L}_2$ as the time it takes for $Q$ to double it's wealth on average over the long run.

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
Under this assumption, the wealth process $(W\_t)\_{t \geq 0}$ satisfies all the conditions placed on $(M_t)_{t \geq 0}$ in Ville's inequality.
This is easy to check:

$$
\mathbb{E}_{X_t \sim B}\!\big[ W_t \mid W_0 \dots W_{t-1} \big]
\,=\, W_{t-1} \cdot \mathbb{E}_{X_t \sim B} \left[ \frac{q(X_t)}{b(X_t)} \right]
\,=\, W_{t-1} .
$$

since the expectation of the likelihood ratio equals one.[^expectation-derivation]
Ville's inequality then tells us that the probability of player $Q$'s wealth *ever* exceeding the threshold $1/\alpha$---at any round of the game---is at most $\alpha$:

$$
P\!\left( \sup_{t \geq 0} W_t \, \geq \, 1/\alpha \right) \, \leq \, \alpha .
$$

This furnishes an *anytime-valid* hypothesis test of the null $H_0 : P = B$: we may reject $H_0$ at level $\alpha$ as soon as $W_t^Q$ crosses $1/\alpha$, regardless of how many rounds have been played. Unlike classical fixed-sample tests, we are free to peek at the data, stop early, or keep collecting more samples adaptively, all without inflating the type I error rate.
For example, if we use $\alpha = 0.05$ (as is customary), then we can reject the null hypothesis that $P = B$ if player $Q$'s wealth *ever* exceeds 20.

---

### Further Reading

Review paper by Ramdas, Grünwald, Vovk, and Shafer (2023). ["Game-Theoretic Statistics and Safe Anytime-Valid Inference."](https://doi.org/10.1214/23-STS894) *Statist. Sci.* 38 (4) 576-601. 


Youtube Tutorial Lectures by Ramdas, "A Martingale Theory of Evidence"
[(Part I)](https://youtu.be/U8ZOtTwUYBs?si=sGIDVAl8aeUQoXtx)
[(Part II)](https://youtu.be/H8nviC_cDAE?si=QHnWGhYtgJ2qzVga)
[(Part III)](https://youtu.be/LNHU4JLOnQc?si=ngPutFxWo2U67Dsw)

Textbook Ramdas and Wang (2025). ["Hypothesis Testing With E-Values."](https://www.stat.cmu.edu/~aramdas/ebook-final.pdf)


[^bits-per-spike]: Normalizing by the number of spikes in the dataset has always seemed like a weird choice to me, and I might dig into this in a future post.

[^q-small]: This ensures that $Q$'s beliefs do not appreciably drive the price of contracts. If $Q$ were extremely wealthy and using all of their purchasing power to buy contracts at each round of betting, then their demands would pull the market pricing distribution closer in line to their beliefs.

[^kelly]: It is also interesting to note that the player's anticipated rate of return is given by the [KL divergence](https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence). Specifically, if we replace the expectation with respect to $P$ appearing in \eqref{eq:q-wealth-growth} with an expectation with respect to $Q$, then we arrive at $\exp \Big ( D_{\mathrm{KL}}(Q \,\|\|\, B) \cdot T \Big )$. Equivalently, if the player models the world perfectly, i.e. $Q = P$, then the KL divergence from $Q$ to $B$ sets the rate of exponential wealth growth. This interpretation of KL divergence is due to JL Kelly Jr. in a [tech report from 1956](https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf). The principle that the player should choose their bet to maximize the term in the exponent appearing in \eqref{eq:q-wealth-growth} is named after him---it is known as the [Kelly criterion](https://en.wikipedia.org/wiki/Kelly_criterion) in quantitative finance.

[^martingale]: For those who appreciate jargon, we call $(M\_t)\_{t \geq 0}$ a *supermartingale* if it satisfies $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] \leq M_{t-1}$ and we call $(M\_t)\_{t \geq 0}$ a [martingale](https://en.wikipedia.org/wiki/Martingale_(probability_theory) $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] = M_{t-1}$, we call $(M_t)_{t \geq 0}$. Ville's inequality says that all nonnegative martingales and supermartingales are upper bounded 

[^expectation-derivation]: Concretely, $\mathbb{E}_{X \sim B} \left[ \frac{q(X)}{b(X)} \right] = \int \frac{q(x)b(x)}{b(x)} dx =  \int q(x) dx = 1$.

<div class="supplementary-notes" markdown="1">

## Supplementary Note 1

Here we sketch how the market price constraint \eqref{eq:pricing-constraint} arises in more detail.
For simplicity, let's consider a case where the random outcomes $X \sim P$ take on one of $n$ discrete values.
That is, $X \in \\{1, \dots, n\\}$ almost surely.
The same argument can be extended to continuous-valued random variables with sufficient care.

By assuming there are only $n$ discrete outcomes, then we can express any potential contract function $S(\cdot)$ as a linear combination of elementary basis functions:

$$
S(X) = u_1 \delta_1(X) + \dots + u_n \delta_n(X)
$$

where $u_1, \dots, u_n$ are scalar coefficients and

$$
\delta_i(x) = \begin{cases}
1 & x = i \\
0 & x \neq i
\end{cases}.
$$

Let $\pi(S)$ denote the price of a contract function $S$. 
Our goal will be to show that:

$$
\pi(S) = \mathbb{E}_{X \sim B}  \left [ S(X) \right ]
$$

for an appropriate choice of distribution $B$.
We will show that this is true if the market is organized such that no player can recieve "free money" without taking any risk (in other words, there are no [arbitrage](https://en.wikipedia.org/wiki/Arbitrage) opportunities).

**The pricing function $\pi$ must be linear.** For any scalar $c$ we have we must have $\pi(c \cdot S) = c \pi(S)$. Otherwise, 


## Supplementary Note 2

</div>
