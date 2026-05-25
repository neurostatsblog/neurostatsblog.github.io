---
layout: post
title: "Betting games for model comparison"
subtitle: "A simple way to interpret heldout log-likelihood scores"
date: 2026-05-01
tags: [statistics]
authors:
  - name: Alex Williams
    affiliation: New York University
    email: alex.h.williams@nyu.edu
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
At each round of the game, player $Q$ uses all of their wealth to purchase *prediction contracts*, specified by a function $C(x) > 0$.
The player then recieves a random sequence of returns $C(X_t), C(X_2), C(X_3), \dots$ over discrete rounds of the game.
The wealth updates according to:
$$
\begin{align}
W_t &= \big ( \, W_{t-1} / \pi(C) \, \big ) \cdot C( X_{t} ) . \label{eq:wealth-process-verbose}
\end{align}
$$
where $\pi(S)$ denotes the *price* of the contract.

Equation \eqref{eq:wealth-process-verbose} is simple.
The first term, $W_{t-1} / \pi(C)$, is the number of contracts purchased using the wealth from the previous round.
This is multiplied by the contract's payoff $C(X_t)$ where $X_t$ is the randomly sampled datapoint at round $t$.
Note that we allow the wealth and the number of purchased contracts to be infinitely divisible into fractions.

Intuitively, the price of a contract is set by what people are willing to buy and sell it for, which reflects their expectations about the underlying distribution $P$.
For the purposes of our game we'll assume that the market consensus---or the ["wisdom of the crowd"](https://en.wikipedia.org/wiki/Wisdom_of_the_crowd)---coincides with the baseline model $B$.
Formally, it turns out that the fair price of a contract is given by its expected value under the market consensus distribution.
That is,
$$
\begin{equation}
\pi(C) = \mathbb{E}_{X \sim B} \, \big [ \,  C(X) \, \big ] . \label{eq:general-pricing-constraint}
\end{equation}
$$
See [**Supplementary Note 1**](#supplementary-note-1) for a quick derivation of this equation.

The pricing constraint in equation \eqref{eq:general-pricing-constraint} allows us to simplify the structure of the game by assuming that the contracts have unit price.
Indeed, for any contract $C(\cdot)$, we can define a new contract $S(x) = C(x)/\pi(C)$ which has unit price, $\pi(S) = 1$.
The wealth update for $C$ and $S$ is equivalent since
$$
\big ( \, W_{t-1} / \pi(C) \, \big ) \cdot C( X_{t} ) = W_{t-1} \cdot S(X_t),
$$
by the definition of $S$.
Therefore, for the rest of this post we will focus on the simplified wealth process

<div class="callout callout-theorem">
<p><strong>Simplified wealth process.</strong> 
Assuming that the player purchases nonnegative contracts $S(x) \geq 0$ of unit price, 
$$
\begin{align}
\mathbb{E}_{X \sim B} \big [ \, S(X) \, \big ] = 1 \label{eq:unit-price-constraint}
\end{align}
$$
then the player's wealth evolves according to
$$
\begin{align}
W_t &=  W_{t-1} \cdot S( X_{t} ) . \label{eq:wealth-process}
\end{align}
$$
</p>
</div>

## Choosing the optimal contract function

Player $Q$ is allowed to choose the function $S(\cdot)$ however they like, so long as it satisfies \eqref{eq:unit-price-constraint}.
Out of this space of feasible contracts, which one should $Q$ choose to play?

After $T$ rounds of betting according to equation \eqref{eq:wealth-process}, the player will accumulate
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

Since the player believes that $P = Q$, they anticipate that their wealth can grow exponentially over time according to:
$$
\begin{equation}
W_T \approx \exp \Big ( T \cdot \mathbb{E}_{X \sim Q} \log S(X) \Big )
\end{equation}
$$
To maximize their rate of wealth growth, a reasonable strategy is to choose $S(\cdot)$ in order to
$$
\begin{align}
\text{maximize} ~~ \mathbb{E}_{X \sim Q} \log S(X) \quad \text{subject to } \eqref{eq:unit-price-constraint} 
\label{eq:kelly-criterion}
\end{align}
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

[^kelly]: It is also interesting to note that the player's anticipated rate of return is given by the [KL divergence](https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence). Specifically, if we replace the expectation with respect to $P$ appearing in \eqref{eq:q-wealth-growth} with an expectation with respect to $Q$, then we arrive at $\exp \Big ( D_{\mathrm{KL}}(Q \,\Vert\, B) \cdot T \Big )$. Equivalently, if the player models the world perfectly, i.e. $Q = P$, then the KL divergence from $Q$ to $B$ sets the rate of exponential wealth growth. This interpretation of KL divergence is due to JL Kelly Jr. in a [tech report from 1956](https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf). The principle that the player should choose their bet to maximize the term in the exponent appearing in \eqref{eq:q-wealth-growth} is named after him---it is known as the [Kelly criterion](https://en.wikipedia.org/wiki/Kelly_criterion) in quantitative finance.

[^martingale]: For those who appreciate jargon, we call $(M\_t)\_{t \geq 0}$ a *supermartingale* if it satisfies $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] \leq M_{t-1}$ and we call $(M\_t)\_{t \geq 0}$.
In the stricter case where the inequality is saturated, i.e. $\mathbb{E}[M_{t} \mid M_0, \dots, M_{t-1}] = M_{t-1}$, we call $(M\_t)\_{t \geq 0}$ a [*martingale*](https://en.wikipedia.org/wiki/Martingale_(probability_theory)). Ville's inequality says that all nonnegative supermartingales (and martingales) are upper bounded for all time with high probability.

[^expectation-derivation]: Concretely, $\mathbb{E}_{X \sim B} \left[ \frac{q(X)}{b(X)} \right] = \int \frac{q(x)b(x)}{b(x)} dx =  \int q(x) dx = 1$.

<div class="supplementary-notes" markdown="1">

## Supplementary Note 1

Here we sketch how the market price constraint \eqref{eq:general-pricing-constraint} arises in more detail.
For simplicity, let's consider a case where the random outcomes $X \sim P$ take on one of $n$ discrete values.
That is, $X \in \\{1, \dots, n\\}$ almost surely.
The same argument can be extended to continuous-valued random variables with sufficient care.

By assuming there are only $n$ discrete outcomes, then we can express any potential contract function $C(\cdot)$ as a finite linear combination of elementary basis functions:
$$
\begin{equation}
C(x) = \sum_{i=1}^n r_i \delta_i(x)
\label{eq:contract-decomposition}
\end{equation}
$$
where $r_1, \dots, r_n$ are scalar coefficients denoting the return of outcome $x = i$,
$$
\begin{equation}
r_i = C(i) ~,
\end{equation}
$$
and $\delta_1, \dots, \delta_n$ are contracts that pays off one unit of wealth if the outcome is $x = i$,
$$
\delta_i(x) = \begin{cases}
1 & x = i \\
0 & x \neq i
\end{cases} ~ .
$$


Recall that our goal is to show $\pi(C) = \mathbb{E} \left [ C(X) \right ]$, with the expectation taken with respect to some appropriate choice of distribution $B$.
We will show that this is true if the market is organized such that no player can recieve "free money" without taking any risk (in other words, there are no [arbitrage](https://en.wikipedia.org/wiki/Arbitrage) opportunities).
We assume that any player can either buy or sell contracts, and that [fractional contracts](https://en.wikipedia.org/wiki/Fractional_ownership) are supported in the market (e.g. by sharing contracts with other players).


**Observation 1 -- The pricing function $\pi$ must be linear.** For any scalar $c>0$ we have we must have $\pi(c \cdot S) = c \pi(S)$.
If $\pi(c \cdot S) > c \cdot \pi(S)$ a player would get free money by selling the contract $c \cdot S$ and simultaneously buying $c$ contracts of $S$.
For any outcome $X \sim P$, the player neither gains nor losses any wealth and they pocket $\pi(c \cdot S) - c \cdot \pi(S) > 0$ units of wealth.
Conversely, if $\pi(c \cdot S) < c \cdot \pi(S)$ a player would get free money by buying the contract $c \cdot S$ and simultaneously selling $c$ contracts of $S$.
Thus, we must have that $\pi(c \cdot S) = c \cdot \pi(S)$.

Next, for any two contracts $S_1$ and $S_2$ we must have that $\pi(S_1 + S_2) = \pi(S_1) + \pi(S_2)$.
The argument is quite similar to above.
If $\pi(S_1 + S_2) > \pi(S_1) + \pi(S_2)$ then a player would get free money by selling the contract $S_3(x) = S_1(x) + S_2(x)$ and simultaneously buying $S_1$ and $S_2$.
Since $S_1(x) + S_2(x) - S_3(x) = 0$ for all $x$, the play  neither gains nor losses any wealth based on the random outcome and they pocket $\pi(S_3) - \pi(S_1 + S_2) > 0$ units of wealth.
Conversely, if $\pi(S_1 + S_2) < \pi(S_1) + \pi(S_2)$ then run the same trade in reverse to get free money.

Taken together, we conclude that pricing must be linear.
Applying this to \eqref{eq:contract-decomposition} we can conclude that the price of any contract can be written down as:
$$
\begin{equation}
\pi(S) = \sum_{i=1}^n r_i \pi(\delta_i)
\label{eq:contract-price-decomposition}
\end{equation}
$$
Thus, we can determine the price of any contract by determing the prices of the elementary basis contracts $\delta_1, \dots, \delta_n$.

**Observation 2 -- the prices $\pi(\delta_1), \dots, \pi(\delta_n)$ are nonnegative and sum to one.**
First we prove nonnegativity.
The random payout for each contract, $\delta_i(X)$ for $X \sim P$, is greater than or equal to zero almost surely.
Thus, the price of each contract must be nonnegative---if it were negative, it would imply that the player is *paid* to accept a contract that never results in a loss (i.e. recieve free money).

Next we prove the normalization condition that $\sum_i \pi(\delta_i) = 1$.
Note that we can construct a contract with constant payoff $S(X) = 1$, almost surely, by setting $r_1 = r_2 = \dots = r_n = 1$ in equation \eqref{eq:contract-decomposition}.
If the price of this contract were less than one, a player would get free money by purchasing it.
Likewise, if the price were greater than one, a player would get free money by selling it.

**Putting it together.** From observation 2, it is clear that the prices $\pi(\delta_1), \dots, \pi(\delta_n)$ define a probability measure over outcomes $x \in \{ 1, \dots, n \}$.
Call this probability measure $B$.
Then, recalling that $r_i = S(i)$ denotes the return of outcome $x = i$ under the contract, we deduce from equation \eqref{eq:contract-price-decomposition}:
$$
\pi(S) = \sum_{i=1}^n r_i \pi(\delta_i) = \mathbb{E}_{X \sim B}  \left [ S(X) \right ]
$$
confirming our claim that the price of a contract is given by the expected payoff of the contract under an appropriate distribution $B$.

## Supplementary Note 2

We prove that the optimization problem stated in \eqref{eq:kelly-criterion} is solved by the likelihood ratio $S^\star(x) = q(x)/b(x)$ given in \eqref{eq:betting-function-equals-likelihood-ratio}.

The argument relies on a useful reparameterization. 
Let $r(x) = b(x) \, S(x)$ and note that $r(x)$ is a probability density.
Indeed, $r(x) \geq 0$ since both $b$ and $S$ are nonnegative, and
$$
\int r(x) \, dx \,=\, \int b(x) \, S(x) \, dx \,=\, \mathbb{E}_{X \sim B} [ S(X) ] \,=\, \pi(S) \, = \, 1
$$
by the unit-price constraint \eqref{eq:unit-price-constraint}. 
Conversely, since we assumed $b(x) > 0$ everywhere on the support of $P$, any probability density $r$ defines a feasible contract function via $S(x) = r(x)/b(x)$.

Now substitute $S(x) = r(x)/b(x)$ into the objective in \eqref{eq:kelly-criterion}, then add and subtract $\mathbb{E}_{X \sim Q} \log q(X)$:
$$
\begin{align}
\mathbb{E}_{X \sim Q} \log S(X)
  &\,=\, \mathbb{E}_{X \sim Q} \log \frac{r(X)}{b(X)} \\
  &\,=\, \mathbb{E}_{X \sim Q} \log \frac{q(X)}{b(X)} \,-\, \mathbb{E}_{X \sim Q} \log \frac{q(X)}{r(X)} \\
  &\,=\, D_{\mathrm{KL}}(Q \,\Vert\, B) \,-\, D_{\mathrm{KL}}(Q \,\Vert\, R) .
\end{align}
$$
The first term, $D_{\mathrm{KL}}(Q \,\Vert\, B)$, does not depend on the player's choice of contract. The second term, $D_{\mathrm{KL}}(Q \,\Vert\, R)$, is non-negative by [Gibbs' inequality](https://en.wikipedia.org/wiki/Gibbs%27_inequality), with equality if and only if $R = Q$. To maximize the objective, the player should therefore choose $R = Q$, that is, $r(x) = q(x)$. Translating back to a contract function via $S = r/b$ yields
$$
S^\star(x) \,=\, \frac{q(x)}{b(x)},
$$
as claimed in \eqref{eq:betting-function-equals-likelihood-ratio}. The maximum achievable value of the objective is $D_{\mathrm{KL}}(Q \,\Vert\, B)$ --- the exponential rate at which the player anticipates their wealth will grow, recovering the Kelly-criterion interpretation discussed in the footnote at the end of "Choosing the optimal contract function."

</div>
