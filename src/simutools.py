
import numpy as np
import pandas as pd
from src.utils import DataUtils


class SimulationTools:
    @staticmethod
    def simulate_expense_voice(
            expenses_volumes,
            expenses_lags,
            rules,
            config,
            day_simulation_start
        ):
        """
        **NOTE**: As now, the simulation implemented is histogram-based. 
        That is, we sample the most likely values given the observed 
        values. A more likely version is KDE sampling, so we do not sample
        observed values based on their actual occurrence frequency.
        """
        
        # Initialize mock data structure
        simulated_expenses = {}
        
        # Define the simulation horizon and the date range, and the single years
        time_horizon = day_simulation_start + pd.Timedelta(
            config.SIMULATED_YEARS * 365 - 1, "d"
        )
        dates_range = pd.date_range(day_simulation_start, time_horizon)
        years_from_config = [year.item() for year in 
                             pd.Series(dates_range).dt.year.unique()]
        
        # Simulate
        for col, lags in expenses_lags.items():
            if lags.empty:
                continue
            
            if col in rules.keys():
                # Enforce the user-defined input/output rules
                # E.g. Recurrent salary input, recurrent rent expense
                
                condition_recurrent_all_months = (
                    "Day" in rules[col].keys() and
                    not "Month" in rules[col].keys() and 
                    not "Year" in rules[col].keys()
                )
                condition_recurrent_all_years = (
                    "Day" in rules[col].keys() and 
                    "Month" in rules[col].keys() and
                    not "Year" in rules[col].keys()
                )
                condition_una_tantum = (
                    "Day" in rules[col].keys() and 
                    "Month" in rules[col].keys() and 
                    "Year" in rules[col].keys()
                )
                
                if condition_recurrent_all_months:
                    years = years_from_config
                    months = config.MONTHS.values()
                
                elif condition_recurrent_all_years:
                    years = years_from_config
                    months = [rules[col]["Month"]]
                
                elif condition_una_tantum:
                    years = [rules[col]["Year"]]
                    months = [rules[col]["Month"]]
                
                simulated_expenses[col] = pd.Series(
                    data = np.array(
                        [rules[col]["Amount"]] * len(months) * len(years)
                    ),
                    index = [
                        DataUtils.get_formatted_date(
                            date_list = [
                                f"{rules[col]['Day']}",
                                f"{month:02d}",
                                str(year)],
                            format_list = ["%d", "%m", "%Y"],
                            separator = config.DATE_SEPARATION
                        )
                        for month in months
                        for year in years
                    ]
                )
                continue
            
            # Simulate as many expense occurrences as the observed ones
            # with a dispersion of 10, if the observed expenses are more
            # than 10 in the original observed data. Otherwise, simply
            # the number of real occurrences of that item
            n_expenses = len(expenses_volumes[col].dropna())
            if n_expenses > 10:
                n_expenses = n_expenses + np.random.randint(0, 50, size = 1)
                n_expenses = np.maximum(0, n_expenses)
            
            # Set the first date and sample dates according to 
            # the previously evaluated statistics
            sampled_dates = [
                pd.Timestamp(np.random.choice(
                    pd.date_range(
                        start = day_simulation_start,
                        end = expenses_lags[col].index[0],
                        freq = "D"
                    )
                ))
            ]
            
            # Sample a set of dates
            continue_date_sample = True
            time_horizon = day_simulation_start + pd.Timedelta(
                config.SIMULATED_YEARS * 365, "d"
            )
            while continue_date_sample:
                days_forward = int(np.random.choice(lags, size = 1))
                date_next = sampled_dates[-1] + pd.Timedelta(days = days_forward)
                if date_next > time_horizon:
                    continue_date_sample = False
                else:
                    sampled_dates.append(date_next)
            #end
            
            # Simulate expense items
            simulated_expenses[col] = pd.Series(
                np.random.choice(
                    expenses_volumes[col].dropna(),
                    size = len(sampled_dates),
                    replace = True
                ),
                index = sampled_dates,
                name = col
            )
        #end
        
        # Obtain the dataframe
        simulated_expenses = pd.concat(simulated_expenses, axis = 1)
        
        # Explode columns
        simulated_inout = (
            simulated_expenses
            
            # Redefine the date as column
            .reset_index()
            .rename(columns = {"index": "Date"})
            
            # Undo the pivoting operation, drop nans
            .melt(
                id_vars = "Date",
                value_name = "Amount",
                var_name = "Category",
                
                # Note: the following operation needs to refer to the
                # variable as it was before the operations pipe, as
                # we need all and only the columns of that version
                value_vars = simulated_expenses.columns,
            )
            .dropna()
            .sort_values(by = "Date")
        )
        
        return simulated_inout
    #end
#end