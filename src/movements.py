
import numpy as np
import pandas as pd
from dataclasses import dataclass
import os

from src.simutools import SimulationTools
from src.utils import DataUtils


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
    def __init__(self, path_data, config):
        self.path_data = path_data
        self.config = config
        
        # Save Jan 1st and Dec 31st, may be handy
        self.define_year_extremes()
    #end

    def get_raw_data(self):
        """
        Read the raw data and preprocess the table.
        """
        raw_data = (
            # Operations concatenation
            DataUtils
            
            # --- Read data, pass the data reader arguments
            .get_reader(
                data_format = self.config.DATA_FORMAT,
                csv_encoding = self.config.CSV_ENCODING,
                header = self.config.HEADER
            ) (self.path_data)
            
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
        # Add Jan 1st and Dec 31st, if missing
        self.jan_1st = DataUtils.get_formatted_date(
            date_list = ["01", "01", str(self.config.YEAR)],
            format_list = ["%d", "%m", "%Y"],
            separator = self.config.DATE_SEPARATION
        )
        self.dec_31st = DataUtils.get_formatted_date(
            date_list = ["31", "12", str(self.config.YEAR)],
            format_list = ["%d", "%m", "%Y"],
            separator = self.config.DATE_SEPARATION
        )
    #end
#end


class Operations(Movements):
    def __init__(
            self,
            path_data,
            config
        ):
        super().__init__(path_data, config)
    #end

    def setup(self):
        # Get raw data
        ops_sheet = self.get_raw_data()
        
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
        For all the months, aggregate (sum) the expense item
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
        12 values, each for each month
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
        of expenses cost most on the overall input/output flow
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
    def __init__(
            self,
            path_data,
            config
        ):
        super().__init__(path_data, config)
        self.stock_init = np.loadtxt(self.config.PATH_INIT_VALUE)
    #end
    
    def setup(self):
        # Get raw data
        ops_sheet = self.get_raw_data()
        
        # Prepare the input-output movements sheet,
        # with chronological order
        inout_sheet = self.create_timeseries_worksheet(ops_sheet)
        self.inout_sheet = inout_sheet
        
        # Aggregate monthly operations
        monthly_deltas = self.get_monthly_operations_aggregates(inout_sheet)
        
        # Obtain capital evolution (linear model) parameters
        self.fit_regression_coefficients(monthly_deltas)
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
        """
        
        def _complete_with_first_and_last_day(df_sheet):
            """
            This local method sets the initial and final dates of the 
            year, if these dates are not recorded (no input/output) in
            these dates in the raw movements data
            """
            
            # Mock data to place Jan 1st and Dec 31st
            fill_data = {"Category": [None], "Amount": [0.], "In": [0.], "Out": [0.]}
            if not self.jan_1st in df_sheet["Date"]:
                row_jan_1st = pd.DataFrame(
                    data = {"Date": self.jan_1st} | fill_data
                )
                df_sheet = pd.concat([row_jan_1st, df_sheet], axis = 0)
            if not self.dec_31st in df_sheet["Date"]:
                row_dec_31st = pd.DataFrame(
                    data = {"Date": self.dec_31st} | fill_data
                )
                df_sheet = pd.concat([df_sheet, row_dec_31st], axis = 0)
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
    
    def fit_regression_coefficients(self, monthly_deltas):
        """
        Estimation: average the monthly delta and divide for the 
        number of month days in this year. Gives an estimate of 
        istantaneous growth. Ie: On daily basis, which is the 
        increase in capital, given the overall lifestyle cost, income ...
        The intercept is simply the initial stock value.
        """
        
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
        self.stock_at_Dec31st = self.inout_sheet.loc[self.dec_31st, "Available"]
    #end
    
    def sumup_printout(self, save_file = False):
        # Evaluate summary statistics
        self.compute_summary_statistics()
        
        stats = pd.DataFrame(
            data = [
                f"{self.stock_init:.2f}",
                f"{self.stock_at_Dec31st:.2f}",
                f"{self.average_stock:.2f}",
                f"{self.estimated_lm_params.slope:.2f}"
            ],
            columns = ["Amount (EUR)"],
            index = [
                f"Initial stock (at {str(self.jan_1st.date())})",
                f"Final stock (at {str(self.dec_31st.date())})",
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
        
        print(stats)
    #end
#end

class SpendingPatterns(Movements):
    def __init__(self, path_data, config):
        super().__init__(path_data, config)
    #end
    
    def fit(self):
        raw_data = self.get_raw_data()
        self.extrapolate_expenses_statistics(raw_data)
    #end
    
    def extrapolate_expenses_statistics(self, ops_sheet):
        """
        Extrapolate:
            - Average lag between the same expense item instance
            - Average and std of each expense item
        
        This gives us the means to simulate synthetic data based on
        the observed year
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
    
    def simulate_yearly_expenses(self, rules, save = None):
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
        
        **NOTE**: As now, the simulation implemented is histogram-based. 
        That is, we sample the most likely values given the observed 
        values. A more likely version is KDE sampling, so we do not sample
        observed values based on their actual occurrence frequency.
        """
        
        # Get the previously obtained statistics
        expenses_lags = self.interarrival_times
        expenses_volumes = self.expenses
        
        # Get the simulated expense items
        simulated_inout = SimulationTools.simulate_expense_voice(
            expenses_volumes,
            expenses_lags,
            rules,
            self.config,
            self.jan_1st
        )
        
        # If the case, save the sheet
        if save:
            self.save_data(
                simulated_inout,
                f"Simulated_synthesis_{self.config.YEAR}"
            )
        
        # Return to the main script
        return simulated_inout
    #end
    
    def save_data(self, data, filename):
        # If the input format is `xls`, we save it as
        # and Excel-readable spreadsheet. Otherwise (e.g. `csv`)
        # we're happy with it and retain the original format       
        if self.config.DATA_FORMAT == "xls":
            data_format = "xlsx"
            data.to_excel(
                os.path.join(
                    self.config.PATH_DATA,
                    f"{filename}.xlsx"
                ),
                index = False
            )
        elif self.config.DATA_FORMAT == "csv":
            data_format = self.config.DATA_FORMAT
            data.to_csv(
                os.path.join(
                    self.config.PATH_DATA,
                    f"{filename}.{data_format}"
                ),
                index = False
            )
        else:
            raise NotImplementedError(f"Data type `{self.config.DATA_FORMAT}` "
                                      "NOT supported! Choose [xlsx | csv]")
        #end
    #end
#end
