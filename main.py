
from config import config
from src.movements import Operations, Timeseries

if __name__ == "__main__":

    # Instantiate configuration
    cfg = config.Constants()

    # Instantiate operations class
    operations = Operations(cfg.PATH_RAW_DATA, cfg)
    operations.setup()
    operations.print_expected_delta()
    
    # Instantiate timeseries class
    timeseries = Timeseries(cfg.PATH_RAW_DATA, cfg)
    timeseries.setup()