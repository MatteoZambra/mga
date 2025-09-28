
from dataclasses import dataclass
import os

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils import DataUtils
from src.simutools import SimulationTools


@dataclass
class CapitalLinearModelParams:
    """
    Dataclass to store the parameters of capital linear growth.
    The assumption is that of linear capital increase.
    """
    slope: float
    intercept: float
    
    def __call__(self):
        return self.slope, self.intercept
    #end
#end

class Movements:
    """
    Base class to contain data and methods to process annual income and
    expenses. This class contains the attributes common to the two 
    derived classes. 
    """
    def __init__(self, config):
        """
        Initialization.
        
        Parameters
        ----------
        config : ``src.config.Constants``
            The configuration class used.
        """
        self.config = config
        
        # Save Jan 1st and Dec 31st, may be handy
        self.define_year_extremes()
    #end

    def get_raw_data(self, path_data):
        """
        Read the raw data and preprocess the table.
        
        Parameters
        ----------
        
        path_data : ``string``
            Path of the raw source data to process.
        """
        raw_data = (
            # Operations concatenation
            DataUtils
            
            # --- Read data, pass the data reader arguments
            .get_reader(
                data_format = self.config.DATA_FORMAT,
                csv_encoding = self.config.CSV_ENCODING,
                header = self.config.HEADER
            ) (path_data)
            
            # --- Select the columns to keep
            [self.config.COLUMNS]
            
            # --- Take care of datetime column
            .assign(
                Date = lambda x: (
                    pd.to_datetime(
                        x["Date"].values,
                        format = self.config.DATE_SEPARATION.join(
                            # ("%d", "%m", "%Y")
                            tuple(self.config.DATE_FORMAT)
                        )
                    )
                )
            )
            
            # --- Sort values and reset indices
            .sort_values(by = "Date")
            .reset_index(drop = True)
        )
        
        return raw_data
    #end
    
    def define_year_extremes(self):
        """
        Helper methods to retrieve the start and end dates of the period 
        considered. If not specified in the configuration file, the dates 
        January 1st and December 31st are assumed as period limits.
        
        This is used to impose these date boundaries if not present in the 
        source data.
        """
        
        # Start date
        if not self.config.START_DATE:
            # If end date is not given, defaults to 1st January
            self.start_date = DataUtils.get_formatted_date(
                date_list = ["01", "01", str(self.config.YEAR)],
                format_list = ["%d", "%m", "%Y"],
                separator = self.config.DATE_SEPARATION
            )
        else:
            # Otherwise, parse the date given in config.json
            self.start_date = DataUtils.get_formatted_date(
                self.config.START_DATE.split(self.config.DATE_SEPARATION)
                + [str(self.config.YEAR)],
                format_list = ["%d", "%m", "%Y"],
                separator = self.config.DATE_SEPARATION
            )
        
        # End date
        if not self.config.END_DATE:
            # If end date is not given, defaults to 31st December
            self.end_date = DataUtils.get_formatted_date(
                date_list = ["31", "12", str(self.config.YEAR)],
                format_list = ["%d", "%m", "%Y"],
                separator = self.config.DATE_SEPARATION
            )
        else:
            # Ibid.
            self.end_date = DataUtils.get_formatted_date(
                date_list = self.config.END_DATE.split(self.config.DATE_SEPARATION)
                + [str(self.config.YEAR)],
                format_list = ["%d", "%m", "%Y"],
                separator = self.config.DATE_SEPARATION
            )
    #end
#end


class Operations(Movements):
    def __init__(self, config):
        super().__init__(config)
    #end
    
    def setup(self, data = None):
        r"""
        This function sets up the data for the operations analysis. 
        
        Actions performed:
            1. Load data, if not given
            2. Aggregate the operation categories on monthly bases
               Prepare these categories as ``dictionary``
            3. For each category, obtain the array of expense items
            4. FRom the latter, compute the monthly and yearly means
            5. Estimate the expected end-of-month delta, that is the 
               approximation of the operator :math:`\Phi`, according to 
               the expression
               
                   .. math::
                       \mathbf{x}_{t+1} = \mathbf{x}_t + \Phi(\mathbf{x}_t)
            
            This recipe allows to visualize the volumes of the expense items
            for each month. That is, it allows to estimate the lifestyle cost.
            
        **NOTE** that this estimation depends on the analyzed year.

        Parameters
        ----------
        data : ``pandas.DataFrame``, optional
            The source data file. Default is ``None``. If not given, the 
            method used the class method ``get_raw_data`` to retrieve 
            the input spreadsheet.
        """
        # Get raw data
        if isinstance(data, pd.DataFrame):
            ops_sheet = data.copy()
        else:
            ops_sheet = self.get_raw_data(self.config.PATH_RAW_DATA)
        
        # For each month, aggregate the expenses
        # associated to each expense item
        ops_dict = self.get_monthly_aggregated_categories_expanses(ops_sheet)
        
        # Create vectors of monthly expenses for each expense item
        expese_items = self.get_categories_expanses_monthly(
            ops_dict, categories = list(ops_sheet["Category"].unique())
        )
        
        # Get the means month- and year-wise
        # This allows to evaluate lifestyle cost
        month_means, year_means = self.get_monthly_yearly_means(expese_items)
        self.month_means = month_means
        self.year_means = year_means
        
        # Get the capital growth slope
        self.expected_delta = self.growth_coefficient(year_means)
    #end
    
    def print_expected_delta(self):
        r"""
        Print the estimation of the delta :math:`\Phi`.
        """
        try:
            print(f"Expected Delta = {self.expected_delta:.2f} EUR / Month")
        except AttributeError:
            raise AttributeError("It seems that you did not compute"
                                 "the Expected Delta yet.\n"
                                 "Run `Operations.setup()` to compute it.")
        finally:
            return
    #end
    
    def get_monthly_aggregated_categories_expanses(self, ops_sheet):
        """
        For all the months, aggregate (sum) the expense item.
        
        Parameters
        ----------
        
        ops_sheet : ``pandas.DataFrame``
            The operations spreadsheet. This is the raw data file.
        
        Returns
        -------
        
        ops_dict : ``dictionary`` of ``pandas.Series``
            The overall operations for each expense item. Sorted
            chronologically but not spaced according to the daily grid.
        """
        ops_dict = {
            month : (
                ops_sheet[ops_sheet["Date"].dt.month == month_idx]
                .groupby(["Category"])["Amount"]
                .apply("sum")
                .reset_index(drop = False)
            )
            for month, month_idx in self.config.MONTHS.items()
        }
        return ops_dict
    #end
    
    def get_categories_expanses_monthly(self, ops_dict, categories):
        """
        Get the yearly view. For each expanse items category, get the
        12 values, each for each month.
        
        Parameters
        ----------
        
        ops_dict : ``dictionary`` of ``pandas.Series``
            Dictionary with the aggregated expense items for each category.
        categories: ``list``
            All the categories found in the raw data file.
        
        Returns
        -------
        
        expense_items : ``dictionary`` of ``numpy.ndarray``
            For each category, the expense items for each month. So the array
            has as many entries as the months, that is 12.
        """
        expense_items = {
            category : np.zeros(len(self.config.MONTHS.keys()))
            for category in categories
        }
        
        for category in categories:
            for month_idx, (month, df_month) in enumerate(ops_dict.items()):
                value = (
                    ops_dict[month]
                    .loc[ops_dict[month]["Category"] == category, "Amount"]
                )
                if len(value) > 0:
                    value = float(value.iloc[0])
                elif len(value) == 0:
                    value = np.nan
                else:
                    raise ValueError(
                        "In `Operations.get_categories_expanses_monthly`"
                        "Length of item to set > 1. Tertium non datur.")
                expense_items[category][month_idx] = value
            #end
        #end
        
        return expense_items
    #end
    
    def get_monthly_yearly_means(self, expense_items):
        """
        Given the dictionary of expense items throught the year, we
        may calculate the averages on both months and the year.
        This allows us to evaluate the lifestyle cost and what categories
        of expenses cost most on the overall input/output flow.
        
        Parameters
        ----------
        
        expense_items : ``dictionary`` of ``numpy.ndarray``
            It is the output of the ``get_categories_expanses_monthly`` method.
        
        Returns
        -------
        
        month_means : ``dictionary`` of ``float``
            The monthly means of each category of expense items.
        year_means : ``dictionary`` of ``float``
            The yearly means of same same categories.
        """
        month_means = {
            category : np.nanmean(expense_items[category])
            for category in expense_items.keys()
        }
        year_means = {
            category : (
                np.nansum(expense_items[category]) / len(self.config.MONTHS)
            )
            for category in expense_items.keys()
        }
        
        return month_means, year_means
    #end
    
    def growth_coefficient(self, year_means):
        r"""
        Get the capital growth coefficient as the difference between the 
        total incomes and the total expenses. These numbers refer to the
        yearly means. The yearly means are intended to be the year-average
        of the monthly average items for each category. In other words, this
        method returns the expected capital variation.
        
        Parameters
        ----------
        
        year_means : ``dictionary`` of ``float``
            The second output of the ``get_monthly_yearly_means`` method.
        
        Returns
        -------
        
        growth_slope : ``float``
            The estimated :math:`\Phi`, that is the end-of-month delta.
        """
        year_means_expenses = year_means.copy()
        
        income_sources = np.zeros(len(self.config.CATEGORIES_INCOME))
        for i, income_item in enumerate(self.config.CATEGORIES_INCOME):
            income_source = year_means_expenses.pop(income_item)
            income_sources[i] = income_source
        #end
        
        expenses = np.array(list(year_means_expenses.values()))
        
        growth_slope = income_sources.sum() + expenses.sum()
        return growth_slope
    #end
#end


class Timeseries(Movements):
    def __init__(self, config):
        super().__init__(config)
        self.stock_init = np.loadtxt(self.config.PATH_INIT_VALUE)
    #end
    
    def setup(self, data = None):
        """
        Set up the data for the timeseries inspection.
        
        The actions are the following:
            1. Get data, if not provided as argument
            2. Rearrange the source data in chronological, daily-resoluted way 
               If necessary, aggregating the input/output fluxes. Note: inputs
               are all aggregated, outputs are all aggregated, regardless of
               the category associated to each movement
            3. Obtain the net differences between each month
        
        Parameters
        ----------
        
        data : ``pandas.DataFrame``, optional
            The raw source data spreadsheet. Default is ``None``. If not 
            given, the data is fetched from the source directory.
        """
        # Get raw data
        if isinstance(data, pd.DataFrame):
            ops_sheet = data.copy()
        else:
            ops_sheet = self.get_raw_data(self.config.PATH_RAW_DATA)
        
        # Prepare the input-output movements sheet,
        # with chronological order
        inout_sheet = self.create_timeseries_worksheet(ops_sheet)
        self.inout_sheet = inout_sheet
        
        # Aggregate monthly operations
        self.monthly_deltas = self.get_monthly_operations_aggregates(inout_sheet)
    #end
    
    def create_timeseries_worksheet(self, ops_sheet):
        r"""
        This function absorbs the raw movements sheet `ops_sheet` and
        and returns the chronologically ordered table of the fluxes:
            - Input (istantaneous)
            - Output (istantaneous)
            - Cumulative input
            - Cumulative output
            - Availability (istantaneous)
        
        ---
        
        The availability is evaluated as the sum
        
            .. math::
                \mathrm{Available}(t) = \sum_{k = 0}^{t}
                \mathrm{Available}(k) + \mathrm{Input}(k) - \mathrm{Output}(k)
        
        At the end of this method, we shall have a table with as many rows
        as the days in the year, and the aforementioned columns. This helps 
        in evaluating the average spending volume (aggregated) for each month
        and to modellize the capital evolution.
        
        Parameters
        ----------
        
        ops_sheet : ``pandas.DataFrame``
            The source data spreadsheet.
        
        Returns
        -------
        
        ops_sheet : ``pandas.DataFrame``
            The data, transformed in chronological daily-resoluted format. The
            columns mentioned above are created and populated.
        """
        
        def _complete_with_first_and_last_day(df_sheet):
            """
            This local method sets the initial and final dates of the 
            year, if these dates are not recorded (no input/output) in
            these dates in the raw movements data.
            
            Parameters
            ----------
            
            df_sheet : ``pandas.DataFrame``
                The source data, possibly with no extrema (01-01 and 31-12).
            
            Returns
            -------
            
            df_sheet : ``pandas.DataFrame``
                The same data structure, but with the addition of extrema.
                These extrema, if not originally present, are populated with
                zeros.
            """
            # Mock data to place Jan 1st and Dec 31st
            fill_data = {
                "Category": [None],
                "Amount": [0.],
                "In": [0.],
                "Out": [0.]
            }
            if not self.start_date in df_sheet["Date"]:
                row_start_date = pd.DataFrame(
                    data = {"Date": self.start_date} | fill_data
                )
                df_sheet = pd.concat([row_start_date, df_sheet], axis = 0)
            if not self.end_date in df_sheet["Date"]:
                row_end_date = pd.DataFrame(
                    data = {"Date": self.end_date} | fill_data
                )
                df_sheet = pd.concat([df_sheet, row_end_date], axis = 0)
            return df_sheet
        #end
        
        # Add relevant columns
        ops_sheet = (
            ops_sheet
            # --- Define input and output flows
            .assign(
                In = lambda x: x[x["Amount"] > 0]["Amount"],
                Out = lambda x: -1. * x[x["Amount"] < 0]["Amount"]
            )
            .fillna(0.)
        )
        
        # Complete the dataframe with Jan 1st and Dec 31st, if missing
        ops_sheet = _complete_with_first_and_last_day(ops_sheet)
        
        # Resample, aggregate and define cumulative fluxes
        ops_sheet = (
            ops_sheet
            # --- Group by day
            .groupby("Date")[["In", "Out"]]
            .apply("sum")
            
            # --- Resample to obtain evenly spaced data
            .resample(rule = pd.Timedelta("1day"))
            .sum()
            
            # --- Define cumulative inputs and outputs
            .assign(
                CumulativeIn = lambda x: x["In"].cumsum(),
                CumulativeOut = lambda x: x["Out"].cumsum()
            )
        )
        
        # Initialize the available array, to be set a ops_sheet column
        available = np.zeros(len(ops_sheet))
        available[0] = self.stock_init
        ops_sheet["Available"] = available
        
        # Availability = Cumulative input - cumulative output at a given time
        ops_sheet["Available"] = (
            ops_sheet["Available"].cumsum()
            + ops_sheet["CumulativeIn"]
            - ops_sheet["CumulativeOut"]
        )
        
        return ops_sheet
    #end
    
    def get_monthly_operations_aggregates(self, inout_sheet):
        """
        Obtain the net difference between the total input and total
        output for each month in the year.
        
        Parameters
        ----------
        
        inout_sheet : ``pandas.DataFrame``
            The refined data structure in chronological daily-resoluted format.
        
        Returns
        -------
        
        monthly_deltas : ``pandas.Series``
            A series with the end-of-month delta for each month.
        """
        monthly_deltas = (
            inout_sheet
            .reset_index()
            .assign(
                Month = lambda x: x["Date"].dt.month
            )
            .groupby("Month")
            [["In", "Out"]]
            
            # --- Sum the input and output fluxes: end-of-month delta
            .apply(lambda x: x["In"].sum() - x["Out"].sum())
            .to_frame(name = "Monthly Deltas")
            .reset_index()
        )
        
        return monthly_deltas
    #end
    
    def fit_trendline_coefficients(self, monthly_deltas = None):
        """
        Estimation: average the monthly delta and divide for the 
        number of month days in this year. Gives an estimate of 
        istantaneous growth. Ie: On daily basis, which is the 
        increase in capital, given the overall lifestyle cost, income ...
        The intercept is simply the initial stock value.
        
        Parameters
        ----------
        
        monthly_deltas : ``pandas.Series``
            Data structure containing the end-of-month deltas.
        """
        # If not provided, get the data saved as class attribute
        if not monthly_deltas:
            try:
                monthly_deltas = self.monthly_deltas
            except:
                AttributeError("Attribute `monthly_deltas` not found\n"
                               "Likely not saved as class attribute")
        
        # Slope
        estimated_slope = np.divide(
            
            # Average monthly delta
            monthly_deltas["Monthly Deltas"]
            .values
            .mean(),
            
            # Average number of month days in this year
            pd.date_range(
                start = f"{self.config.YEAR}-01-01",
                end = f"{self.config.YEAR}-12-31",
                freq = "MS"
            )
            .days_in_month
            .values
            .mean()
        )
        
        # Save params
        self.estimated_lm_params = CapitalLinearModelParams(
            estimated_slope, self.stock_init
        )
    #end
    
    def compute_summary_statistics(self):
        """
        If necessary, evaluate the average stock and the available
        stock at the end of the year, ie on Dec 31st.
        """
        self.average_stock = self.inout_sheet["Available"].mean()
        self.stock_at_enddate = self.inout_sheet.loc[self.end_date, "Available"]
    #end
    
    def sumup_printout(self, save_file = False):
        """
        Print summary statistics of the year. Namely
            1. Initial stock. Availability at January 1st
            2. Final stock. Availability at December 31st
            3. Average stock. Is the yearly average of the available stock
            4. Estimated growth trendline slope. That is the net daily gain

        Parameters
        ----------
        save_file : ``bool``, optional
            Whether to save the summary table or not. The default is False.
        """
        # Evaluate summary statistics
        self.compute_summary_statistics()
        
        stats = pd.DataFrame(
            data = [
                f"{self.stock_init:.2f}",
                f"{self.stock_at_enddate:.2f}",
                f"{self.average_stock:.2f}",
                f"{self.estimated_lm_params.slope:.2f}"
            ],
            columns = ["Amount (EUR)"],
            index = [
                f"Initial stock (at {str(self.start_date.date())})",
                f"Final stock (at {str(self.end_date.date())})",
                "Average stock",
                "Estimated daily capital growth"
            ]
        ).reset_index().rename(
            columns = {"index" : f"Summary statistic year {self.config.YEAR}"}
        )
        
        if save_file:
            stats.to_csv(
                os.path.join(
                    self.config.PATH_DATA,
                    f"summary_metrics_{self.config.YEAR}.csv"
                ),
                index = False
            )
        
        print("\n", stats)
    #end
#end


class SpendingPatterns(Movements):
    """
    Class that performs the extrapolation of the statistics of the spending
    patterns of the observed year. This class calls the simulation of future
    scenarios. This call is delegated to antoher class, for modularity.
    """
    def __init__(self, config):
        super().__init__(config)
    #end
    
    def fit(self, data = None):
        """
        Execute the spending patterns extrapolation. This interface method
        only calls the method to learn the statistics of the inter-arrival 
        times of each input/output flux, for each category.
        
        Parameters
        ----------
        data : ``pandas.DataFrame``, optional
            The raw data source file. The default is None. If not given, it 
            will be fetched from the source directory.
        """
        if isinstance(data, pd.DataFrame):
            ops_sheet = data.copy()
        else:
            ops_sheet = self.get_raw_data(self.config.PATH_RAW_DATA)
        
        self.extrapolate_expenses_statistics(ops_sheet)
    #end
    
    def extrapolate_expenses_statistics(self, ops_sheet):
        """
        Extrapolate:
            - Average lag between the same expense item instance
            - Average and std of each expense item
        
        This gives us the means to simulate synthetic data based on
        the observed year. The following format is used. The source file is
        pivoted by the categories. This gives a table with as many rows as
        the overall days in the spreadsheet (days in which inputs/outputs)
        happened, and as many columns as the income/expense categories.
        The table obtained is sparse, the only entries being the expenses or
        incomes associated to the (day, category) accessors. This format is
        useful to
            1. Aggregate the movements for each category
            2. Evaluate the statistics of both the movements volumes and
               their inter-arrival times. 
        The second element is particularly important. A sound simulation 
        must take into account a realistic expense/income occurrence pattern.
        
        **NOTE**: The end result is:
            1. A dictionary of ``pandas.Series``, indexed by the categories.
               That is, the columns of the table explained above.
            2. A dictionary of lags. Not the columns of the table above, but
               the collection of inter-arrival times of the items of the 
               columns of the mentioned table.
        
        Parameters
        ----------
        
        ops_sheet : ``pandas.DataFrame``
            The raw source data spreadsheet.
        """
        # Pivot table: from column-expanded view, we obtain a table
        # with columns == expenses items
        ops_sheet_categories = (
            ops_sheet
            .pivot_table(
                values = "Amount",
                columns = "Category",
                index = "Date"
            )
            .resample("1D")
            .mean()
        )
        
        # Evaluate iter-arrival times, expense items averages and stds
        lags = {}
        expenses = {}
        for col in ops_sheet_categories.columns:
            # Get the inter-arrival times between the expenses
            # of this expense item
            dates = (
                ops_sheet_categories
                .index[
                    ops_sheet_categories[col]
                    .notna()
                ]
                .to_series()
                .diff()
                .dt
                .days
                .dropna()
            )
            
            # Update the associated data structures
            lags.update({col : dates})
            expenses.update({col : ops_sheet_categories[col]})
        #end
        
        # Save as class attributes, will be useful later
        self.interarrival_times = lags
        self.expenses = expenses
    #end
    
    def simulate_yearly_expenses(self, rules):
        """
        Once the statistics of expenses inter-arrival times and
        volumes are estimated, we can simulate a year similar to 
        the one observed, statistically. Useful for future projection,
        if the spending habits are constant.
        
        The ``rules`` argument, specified in the configuration file,
        needs to be given. The hypothesis is that there are constant,
        predictable expense items, such as salary and rent (if applicable)
        that are present each month. Simulating these expense items 
        may lead to unlikely results. The specification of these rules
        informs the simulation to enforce the given rules and not to
        simulate the expense items listed.
        
        Parameters
        ----------
        
        rules : ``dictionary``
            Encodes the predictable expenses and incomes.
        
        Returns
        -------
        
        simulated_inouts : ``list``
            A list with as many items as the user-defined simulation runs.
            Each element is a ``pandas.DataFrame``. This structure is generated
            to imitate the original user-given source spreadsheet.
        """
        
        # Get the previously obtained statistics
        expenses_lags = self.interarrival_times
        expenses_volumes = self.expenses
        
        # Get the simulated expense items
        simulated_inouts = []
        simulated_timeseries = []
        for run in tqdm(range(self.config.SIMULATION_RUNS)):
            # Raw source data
            simulated_inout = SimulationTools.simulate_expense_voice(
                expenses_volumes,
                expenses_lags,
                rules,
                self.config,
                self.jan_1st
            )
            
            # Timeseries-wrap. To obtain chronological time series
            timeseries = Timeseries(self.config)
            timeseries.setup(simulated_inout)
            
            # Save both the simulated raw source data and the obtained 
            # timeseries representations. Note that we save the `inout_sheet`
            # attribute of each timeseries object. We only want the prepared
            # input/output table in chronological daily order
            simulated_inouts.append(simulated_inout)
            simulated_timeseries.append(timeseries.inout_sheet)
        
        # Return to the main script
        return simulated_inouts, simulated_timeseries
    #end
#end
