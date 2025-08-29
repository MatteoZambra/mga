
import numpy as np
import pandas as pd
from functools import partial

class DataUtils:
    @staticmethod
    def get_reader(data_format, csv_encoding = None, header = None):
        if data_format in ["xls", "xlsx"]:
            reader = partial(
                pd.read_excel,
                header = header
            )
        elif data_format == "csv":
            reader = partial(
                pd.read_csv,
                encoding = csv_encoding,
                header = header
            )
        return reader
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
                            ("%d"," %m", "%Y")
                        ).replace(" ", "")
                    )
                )
            )
            
            # --- Sort values and reset indices
            .sort_values(by = "Date")
            .reset_index(drop = True)
        )
        
        return raw_data
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
    #end
    
    def setup(self):
        # Get raw data
        ops_sheet = self.get_raw_data()
        
        # Add relevant columns
        ops_sheet = (
            ops_sheet
            
            # --- Define input and output flows
            .assign(
                In = lambda x: x[x["Amount"] > 0]["Amount"],
                Out = lambda x: -1. * x[x["Amount"] < 0]["Amount"],
            )
            .fillna(0.)
        )
        
        return ops_sheet
    #end
#end




