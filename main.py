
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
        
        Plots.plot_expense_items(operations)
    
    # Instantiate timeseries class
    if True:
        timeseries = Timeseries(cfg.PATH_RAW_DATA, cfg)
        timeseries.setup()
        true_inout = timeseries.get_raw_data()
        timeseries.sumup_printout(save_file = True)
        
        # Plot
        Plots.plot_trend(timeseries)
    
    # Instantiate class to extrapolate spending patterns
    if False:
        spending_patterns = SpendingPatterns(cfg.PATH_RAW_DATA, cfg)
        spending_patterns.fit()
        simulated_inout = (
            spending_patterns
            .simulate_yearly_expenses(
                rules = cfg.SIMULATION_COLUMNS_CONSTANTS,
                save = False
            )
        )
        
        # Let's see if there is statistical match
        from copy import deepcopy
        import os
        
        cfg_ = deepcopy(cfg)
        cfg_.DATA_FORMAT = "xlsx"
        cfg_.PATH_RAW_DATA = os.path.join(
            cfg.PATH_DATA,
            f"Simulated_synthesis_{cfg.YEAR}.xlsx"
        )
        cfg_.HEADER = 0
        
        timeseries_simulated = Timeseries(cfg_.PATH_RAW_DATA, cfg_)
        timeseries_simulated.setup()
        
        Plots.plot_trend(timeseries_simulated, "./data/2023/timeseries_simulated.png")