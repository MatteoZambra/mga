
import os
import json
from typing import List, Dict

import pandas as pd
import calendar

from dataclasses import dataclass


@dataclass
class UserDefinedConstants:
    YEAR: int
    DATA_FORMAT: str
    CSV_ENCODING: str
    HEADER: int
    DATE_FORMAT: List[str]
    DATE_SEPARATION: str
    START_DATE: str
    END_DATE: str
    CATEGORIES_INCOME: List[str]
    COLUMNS: List[str]
    SIMULATION_COLUMNS_CONSTANTS: Dict[str, Dict[str, int]]
    SIMULATED_YEARS: int
    SIMULATION_RUNS: int
#end

@dataclass
class Constants:
    path_cfg: str
    
    def __post_init__(self):
        
        with open(self.path_cfg) as f:
            cfg_file = UserDefinedConstants(**json.load(f))
        
        self.YEAR = cfg_file.YEAR
        self.DATA_FORMAT = cfg_file.DATA_FORMAT
        self.CSV_ENCODING = cfg_file.CSV_ENCODING
        self.HEADER = cfg_file.HEADER
        self.DATE_FORMAT = cfg_file.DATE_FORMAT
        self.DATE_SEPARATION = cfg_file.DATE_SEPARATION
        self.START_DATE = cfg_file.START_DATE
        self.END_DATE = cfg_file.END_DATE
        self.CATEGORIES_INCOME = cfg_file.CATEGORIES_INCOME
        self.COLUMNS = cfg_file.COLUMNS
        self.SIMULATION_COLUMNS_CONSTANTS = cfg_file.SIMULATION_COLUMNS_CONSTANTS
        self.SIMULATED_YEARS = cfg_file.SIMULATED_YEARS
        self.SIMULATION_RUNS = cfg_file.SIMULATION_RUNS
        
        self.MONTHS = {
            month[:3] : i for i, month in enumerate(calendar.month_name) if month
        }
        
        self.YEAR_DAYS = pd.Timestamp(self.YEAR, 12, 31).dayofyear
        self.PATH_DATA = os.path.join(os.getcwd(), "data", str(self.YEAR))
        self.RAW_DATA_FILE = f"Synthesis_{str(self.YEAR)}_cat.{self.DATA_FORMAT}"
        self.INIT_VALUE_FILE = "dispo_init.csv"

        if not os.path.exists(self.PATH_DATA):
            raise OSError(f"Path: `{self.PATH_DATA}`. No such directory.")

        if not os.path.exists(os.path.join(self.PATH_DATA, self.RAW_DATA_FILE)):
            raise OSError(f"File: {self.RAW_DATA_FILE} not found but required.")
        self.PATH_RAW_DATA = os.path.join(self.PATH_DATA, self.RAW_DATA_FILE)
        
        if not os.path.join(os.path.join(self.PATH_DATA, self.INIT_VALUE_FILE)):
            raise OSError(f"File: {self.INIT_VALUE_FILE} not found but required.")
        self.PATH_INIT_VALUE = os.path.join(self.PATH_DATA, self.INIT_VALUE_FILE)
    #end
    
    def set_property(self, attr_name, attr_value):
        setattr(self, attr_name, attr_value)
    #end
#end


