
from functools import partial
import pandas as pd


class DataUtils:
    @staticmethod
    def get_reader(data_format, csv_encoding = None, header = None):
        if data_format in ["xls", "xlsx"]:
            reader = partial(
                pd.read_excel,
                header = header
            )
        elif data_format == "csv":
            reader = partial(
                pd.read_csv,
                encoding = csv_encoding,
                header = header
            )
        else:
            raise NotImplementedError(f"Data type `{data_format}` NOT supported!")
        #end
        
        return reader
    #end
    
    def get_formatted_date(date_list, format_list, separator):
        datetime_date = pd.to_datetime(
            separator.join(date_list),
            format = separator.join(format_list)
        )
        return datetime_date
    #end
#end


