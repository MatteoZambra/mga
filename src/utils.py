
import numpy as np
import matplotlib.pyplot as plt
import src.movements as mv


class Plots:
    @staticmethod
    def plot_trend(timeseries: mv.Timeseries, save_path = None):
        
        inout_sheet = timeseries.inout_sheet
        span = np.arange(len(inout_sheet))
        lspan = np.linspace(0, inout_sheet.__len__(), 100)
        real_slope, intercept = timeseries.estimated_lm_params()
        line = lspan * real_slope + intercept
        
        fig, ax = plt.subplots(figsize = (15,5), dpi = 100)   
        ax.plot(span, inout_sheet["CumulativeIn"],
                color = 'g', lw = 2, alpha = 0.75,
                label = 'Cumulative Income')
        ax.plot(span, inout_sheet["CumulativeOut"],
                color = 'r', lw = 2, alpha = 0.75,
                label = 'Cumulation Expanses')
        ax.plot(span, inout_sheet["Available"],
                color = 'k', lw = 2, alpha = 0.75,
                label = 'Available Capital')
        ax.plot(lspan, line,
                color = 'k', lw = 2, ls = '--', alpha = 0.75,
                label = f'Fitted Trend (empirical), slope = {real_slope:.2f}')
        ax.set_xlabel('Time', fontsize = 14, labelpad = 15)
        ax.set_ylabel('Amount [EUR]', fontsize = 14, labelpad = 15)
        ax.grid(axis = 'both', lw = 0.5)
        ax.legend()
        if save_path:
            fig.savefig(save_path, format = "png",
                        dpi = 300, bbox_inches = "tight")
        plt.show(fig)
    #end
    
    @staticmethod
    def plot_expense_items():
        pass
    #end
#end
