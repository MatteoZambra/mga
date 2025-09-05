
import pandas as pd
import numpy as np

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
        
        # Initialize mock data structure
        simulated_expenses = {}
        
        # Simulate
        for col, lags in expenses_lags.items():
            if lags.empty:
                continue
            
            if col in rules.keys():
                # Enforce the user-defined input/output rules
                # E.g. Recurrent salary input, recurrent rent expense
                simulated_expenses[col] = pd.Series(
                    data = np.array(
                        [rules[col]["Amount"]] * len(config.MONTHS)
                    ),
                    index = [
                        DataUtils.get_formatted_date(
                            date_list = [
                                f"{rules[col]['Day']}",
                                f"{month:02d}",
                                str(config.YEAR)],
                            format_list = ["%d", "%m", "%Y"],
                            separator = config.DATE_SEPARATION
                        )
                        for month in config.MONTHS.values()
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
            
            # Statistically likely sequence of occurrences for this expense item
            sampled_lags = np.random.choice(
                lags, size = n_expenses, replace = True
            )
            
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
            for lag in sampled_lags:
                date_next = sampled_dates[-1] + pd.Timedelta(days = int(lag))
                if date_next.year != config.YEAR:
                    continue
                
                sampled_dates.append(
                    sampled_dates[-1] + pd.Timedelta(days = int(lag))
                )
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


