
from src import config
from src.movements import (
    Movements,
    Operations,
    Timeseries,
    TimeseriesProjection,
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
        
        ## Plot
        _,_ = Plots.plot_expense_items(operations)
        
        # --- Time series reconstruction ---
        ## Instantiate and set up timeseries class
        timeseries = Timeseries(cfg)
        timeseries.setup()
        
        ## Fit the trendline coefficients
        timeseries.fit_trendline_coefficients()
        
        ## Print yearly statistics
        timeseries.sumup_printout(save_file = True)
        
        ## Plot
        _ = Plots.plot_trend(timeseries)
    
    
    # Instantiate class to extrapolate spending patterns
    if True:
        # Extrapolate the spending patterns of the selected year
        spending_patterns = SpendingPatterns(cfg)
        spending_patterns.fit()
        
        # Perform and ahead-in-time simulation
        simulated_inout = spending_patterns.simulate_yearly_expenses(
                rules = cfg.SIMULATION_COLUMNS_CONSTANTS,
        )
                
        # # And make the future projection
        timeseries_simulated = Timeseries(cfg)
        timeseries_simulated.setup(data = simulated_inout)
        
        timeseries_simulated.fit_trendline_coefficients()
        timeseries_simulated.sumup_printout(save_file = False)
        
        _ = Plots.plot_trend(timeseries_simulated, plot_trend_line = False)