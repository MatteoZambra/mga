
from config import config
from src.movements import Operations, Timeseries, SpendingPatterns
from src.utils import Plots

if __name__ == "__main__":

    # Instantiate configuration
    cfg = config.Constants()
    
    # Instantiate operations class
    if False:
        operations = Operations(cfg.PATH_RAW_DATA, cfg)
        operations.setup()
        operations.print_expected_delta()
    
    # Instantiate timeseries class
    if False:
        timeseries = Timeseries(cfg.PATH_RAW_DATA, cfg)
        inout_sheet = timeseries.setup()
        
        # Plot
        Plots.plot_trend(timeseries)
    
    # Instantiate class to extrapolate spending patterns
    if True:
        spending_patterns = SpendingPatterns(cfg.PATH_RAW_DATA, cfg)
        spending_patterns.fit()