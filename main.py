
from config import config
from src.movements import Operations, Timeseries, SpendingPatterns
from src.utils import Plots

if __name__ == "__main__":

    # Instantiate configuration
    cfg = config.Constants()
    
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
    if True:
        from copy import deepcopy
        import os
        
        spending_patterns = SpendingPatterns(cfg.PATH_RAW_DATA, cfg)
        spending_patterns.fit()
        simulated_inout = (
            spending_patterns
            .simulate_yearly_expenses(
                rules = cfg.SIMULATION_COLUMNS_CONSTANTS,
                save = True
            )
        )
        
        # Let's see if there is statistical match       
        cfg_ = deepcopy(cfg)
        cfg_.set_property("DATA_FORMAT", "csv")
        cfg_.set_property("PATH_RAW_DATA", os.path.join(
            cfg.PATH_DATA,
            f"Simulated_synthesis_{cfg.YEAR}.csv"
        ))
        cfg_.set_property("HEADER", 0)
        cfg_.set_property("DATE_FORMAT", ["%Y", "%m", "%d"])
        cfg_.set_property("DATE_SEPARATION", "-")
        
        timeseries_simulated = Timeseries(cfg_.PATH_RAW_DATA, cfg_)
        timeseries_simulated.setup()
        
        fig_timeseries_simulated = Plots.plot_trend(
            timeseries_simulated,
            backend = "matplotlib"
        )