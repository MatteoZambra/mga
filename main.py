
from src import config
from src.movements import (
    Movements,
    Operations,
    Timeseries,
    SpendingPatterns
)
from src.graphics import Plots


if __name__ == "__main__":
    
    # Instantiate configuration
    cfg = config.Constants("./config/config.json")
    ops_sheet = Movements(cfg).get_raw_data(cfg.PATH_RAW_DATA)
    
    # Hind-casting
    if True:
        # --- Operations ---
        ## Instantiate and set up operations class
        operations = Operations(cfg)
        operations.setup()
        
        ## Print the expected monthly delta
        operations.print_expected_delta()
        
        ## Plot the income/expense voices
        _,_ = Plots.plot_expense_items(operations)
        
        # --- Time series reconstruction ---
        ## Instantiate and set up timeseries class
        timeseries = Timeseries(cfg)
        timeseries.setup()
        
        ## Fit the trendline coefficients
        timeseries.fit_trendline_coefficients()
        
        ## Print yearly statistics
        timeseries.sumup_printout(save_file = True)
        
        ## Plot the timeseries reconstruction
        _ = Plots.plot_trend(timeseries)
    
    
    # Forecasting
    if False:
        # --- Extrapolate the spending patterns of the selected year
        spending_patterns = SpendingPatterns(cfg)
        spending_patterns.fit()
        
        ## Perform and ahead-in-time simulation
        ## Note: We require the first argument of the method call. The
        ## first argument would be the simulated raw input/output logs.
        ## Which are not interesting for the timeseries visualization
        _, simulated_timeseries = spending_patterns.simulate_yearly_expenses(
                rules = cfg.SIMULATION_COLUMNS_CONSTANTS,
        )
        
        ## Plot the simulation runs
        _ = Plots.plot_simulation_runs(
            simulated_timeseries,
            trendline_params = timeseries.estimated_lm_params,
            plot_trend_line = True
        )