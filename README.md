# MicroEconoPycs
A tool to analyze domestic finances.

This repo contains the source code I originally wrote to monitor bank account input and output fluxes.

Main functionalities:
- Aggregate expense items to visualize the items' volume. Monthly and yearly averages
- Obtain a spreadsheet with cumulative and istantaneous input and output fluxes
- Simulate future scenarios based on observed data

These functionalities allow to
- Estimate the volume of lifestyle cost
- Understand what are the items that are more costly
- Evaluate the potential end-of-month capital delta
- Make future projections based on observed spending habits

Useful to make predictions and to evaluate potential investments allocatable volumes.

> **NOTE**: The results presented are based on **synthetic data**, simulated by Google Gemini. The numbers used are random. Nothing representative of any real account.

## Foundation
The following evolutionary equation is assumed

$$\mathbf{x}_t = \mathbf{x}_{t-1} + \Phi(\mathbf{x}, t)$$

The variable $\mathbf{x}_t$ is the capital volume at time $t$. The temporal resolution is assumed to be monthly.
The operator $\Phi$ is the one-step-ahead predictor of $\mathbf{x}$ and quantifies the delta between the total income and the total lifestyle cost. 

> It is important the $\Phi(\mathbf{x}, t) > 0$ strictly. In this way, capital increases in time.

The average value of $\Phi(\mathbf{x})$ is due to the aggregated spending habits. It can be estimated from historical data. $\Phi$ can be disaggregated to visualize the volume of each expense item. See the associated notebook `demo.ipynb`, Section **Operations: Aggregated Expenses Volume**.

The same evolutionary dynamics is visualized on a time-value plane, where the cumulative incomes and expenses, as well as the istantaneous account availability, are visualized as a function of time. In this perspective, one might rescale the monthly gain $\Phi$ at daily resolution. This quantity is the slope on the trend line visualized in the **Timeseries: Deduction of the linear growth trend** Section in the notebook `demo.ipynb`.

## Simulations
The most important aspect of the tool is to sketch possible future scenarios. These projections are to be made on observed spending habits. The first and simplest way to make it is to
- choose the time horizon. That is $k$ years, **as if the current spending habits are held unchanged**
- Randomly sample the expense value **based on the observed values**, **with the same inter-arrival time**.

This allows to retain the statistics of the source data.

## Usage
### Software setup

Clone the directory in a local environment

```
git clone https://github.com/MatteoZambra/mga.git
```

Basic requirements list:
- `pandas` (2.3.1): Data manipulation
    - `xlrd` (2.0.1), `openpyxl` (3.1.5) engines required to interact with `xls`, `xlsx` spreadsheets
- `numpy` (2.3.1): Numerical computation
- `tqdm` (4.67.1): Progress bars
- `matplotlib` (3.10.5): Data visualization
- (Optional) `plotly` (6.3.0): Interactive visualization

Output of `conda env export --from-history --name mga > mga.yml`:

```
name: mga
channels:
  - defaults
dependencies:
  - spyder
  - numpy
  - pandas
  - matplotlib
  - xlrd
  - openpyxl
  - jupyterlab
  - plotly
  - tqdm
```

### Data setup
1. Create a `./data/` directory in the root directory
2. Create a directory for each one of the years to analyze. For example: `./data/2024/`
3. In this directory, place a file named `Synthesis_<YEAR>_cat.*`. It may be `csv`, `xls`, `xlsx`
4. Also in this directory, place a file named `dispo_init.csv`. This file should contain the initial stock value.

The source data file format can be specified in the configuration file.

### Data format
The expected data source file is expected to be formatted as follows

#### Source spreadsheet

| Date | Category | Amount |
| ---- | -------- | ------ |
| 2024-01-01 | Everyday life | -10.50 |
| ... | ... | ... |
| 2024-01-15 | Salary | 2000 | 
| ... | ... | ... |

> **IMPORTANT**: Expenses (outgoing fluxes) should have the *minus sign*. Incomes (incoming fluxes) are positive.

The date format, e.g. `YYYY-mm-dd`, or `dd/mm/YYYY`, must be specified in the configuration file. Note that the *date separator* must also be specified.

#### Initial stock file
The `dispo_init.csv` file must only contain a floating-point number. For example

```
5000.0
```

No spaces, units needed.

### Configuration

A core component is the `./config/config.json` file. This allows to specify
- Analyzed year
- Data file format
- Csv encoding (if applicable). E.g. `utf-8`, `latin-1`, ...
- Header: How many rows to skip before to find the table specified above in the source file
- Date format
- Date separation
- Start and end dates. If not specified, the start and end date are set to January 1st and December 31st
- Categories income: A list of strings specifying the income categories. Likely `"Salary"`, ...
- Columns: The columns of the table. If the source spreadsheet is prepared as above, specify `"Date"`, `"Category"`, `"Amount"`
- Simulation columns constants: This is a dictionary that sets the recurrent and predictable expenses
    - `"Day"` specified: Monthly recurrent.
    - `"Day"`, `"Month"` specified: Yearly recurrent.
    - `"Day"`, `"Month"`, Year: Una tantum.
- Simulated years: How many years to cover with the future forecast simulation
- Simulation runs: How many runs of the future simulation must be performed

### Run
Run it either with and IDE, a Jupyter notebook. Examples are provided both in the `main.py` and `demo.ipynb` files.

## Future work
### Future simulations
Make the future scenario simulations more realistic. Both from the expenses simulation (sampling) point of view and to give the user the possibility to enforce a variation in some spending habits. E.g. decrease the expense volume of the expense item $x$ of some chosen percentage.

### CLI
To pack the source to make a usable command line interface, so to avoid the user to set up a local environment with and IDE or Jupyter notebook/lab. 

### Interactivity
Make the visualizations interactive by leveraging the `plotly` library.
