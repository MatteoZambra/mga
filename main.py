
from src import config
from src.movements import (
    Operations,
    Timeseries,
    TimeseriesProjection,
    SpendingPatterns
)
from src.graphics import Plots


if __name__ == "__main__":

    # Instantiate configuration
    cfg = config.Constants("./config/config.json")
    
    # Instantiate operations class
    if True:
        operations = Operations(cfg.PATH_RAW_DATA, cfg)
        operations.setup()
        operations.print_expected_delta()
        
        fig_incomes, fig_expenses = Plots.plot_expense_items(
            operations,
            backend = "matplotlib"
        )
    
    # Instantiate timeseries class
    if True:
        timeseries = Timeseries(cfg.PATH_RAW_DATA, cfg)
        timeseries.setup()
        true_inout = timeseries.get_raw_data()
        timeseries.sumup_printout(save_file = True)
        
        # Plot
        fig_timeseries = Plots.plot_trend(
            timeseries,
            backend = "matplotlib"
        )
    
    # Instantiate class to extrapolate spending patterns
    if False:
        from copy import deepcopy
        import os
        
        # Extrapolate the spending patterns of the selected year
        spending_patterns = SpendingPatterns(cfg.PATH_RAW_DATA, cfg)
        spending_patterns.fit()
        simulated_inout = (
            spending_patterns
            .simulate_yearly_expenses(
                rules = cfg.SIMULATION_COLUMNS_CONSTANTS,
                save = True
            )
        )
        
        # Edit the configuration class, as if we were to start all over
        cfg_ = deepcopy(cfg)
        cfg_.set_property("DATA_FORMAT", "xlsx")
        cfg_.set_property("PATH_RAW_DATA", os.path.join(
            cfg.PATH_DATA,
            f"Simulated_synthesis_{cfg.YEAR}.xlsx"
        ))
        cfg_.set_property("HEADER", 0)
        cfg_.set_property("DATE_FORMAT", ["%Y", "%m", "%d"])
        cfg_.set_property("DATE_SEPARATION", "-")
        
        # Let's see if there is statistical match
        # And make the future projection
        timeseries_simulated = TimeseriesProjection(cfg_.PATH_RAW_DATA, cfg_)
        timeseries_simulated.setup()
        timeseries_simulated.sumup_printout(save_file = False)
        
        fig_timeseries_simulated = Plots.plot_trend(
            timeseries_simulated,
            backend = "matplotlib",
            plot_trend_line = False
        )