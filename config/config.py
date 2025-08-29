
import os
import pandas as pd
import calendar
from dataclasses import dataclass


@dataclass
class Constants:
    YEAR = 2023                              # <--- To config.json
    TASK = "Movements"                       # <--- To config.json
    DATA_FORMAT = "xls"                      # <--- To config.json
    CSV_ENCODING = "latin-1"                 # <--- To config.json
    HEADER = 2                               # <--- To config.json
    DATE_SEPARATION = "-"                    # <--- To config.json
    CATEGORIES_INCOME = [                    # <--- To config.json
        "Paga",
        "Rimborsi",
        "Altre entrate"
    ] 
    COLUMNS = [                              # <--- To config.json
        "Date",
        "Category",
        "Amount"
    ]
    
    MONTHS = {
        month[:3] : i for i, month in enumerate(calendar.month_name) if month
    }

    def __post_init__(self):
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
        