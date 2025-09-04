# Money, get away ...

This repo contains the source code I originally wrote to monitor bank account input and output fluxes.

Binder notebook: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/MatteoZambra/mga/HEAD?urlpath=%2Fdoc%2Ftree%2Fdemo.ipynb)

Main functionalities:
- Aggregate expense items to visualize the items' volume. Monthly and yearly averages
- Obtain a spreadsheet with cumulative and istantaneous input and output fluxes.

These functionalities allow to
- Estimate the volume of lifestyle cost
- Understand what are the items that are more costly
- Evaluate the potential end-of-month capital delta

Useful to make predictions and to evaluate potential investments allocatable volumes.

## Foundation
The following evolutionary equation is assumed

$$\mathbf{x}_t = \mathbf{x}_{t-1} + \Phi(\mathbf{x}, t)$$

The variable $\mathbf{x}_t$ is the capital volume at time $t$. The temporal resolution is assumed to be monthly.
The operator $\Phi$ is the one-step-ahead predictor of $\mathbf{x}$ and quantifies the delta between the total income and the total lifestyle cost. 

> It is important the $\Phi(\mathbf{x}, t) > 0$ strictly. In this way, capital increases in time.

