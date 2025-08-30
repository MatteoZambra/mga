
from config import config
from src.movements import Operations, Timeseries
from src.utils import Plots

if __name__ == "__main__":

    # Instantiate configuration
    cfg = config.Constants()
    
    # Instantiate operations class
    if True:
        operations = Operations(cfg.PATH_RAW_DATA, cfg)
        operations.setup()
        operations.print_expected_delta()
    
    # Instantiate timeseries class
    if True:
        timeseries = Timeseries(cfg.PATH_RAW_DATA, cfg)
        inout_sheet = timeseries.setup()
        
        # Plot
        Plots.plot_trend(timeseries)