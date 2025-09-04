
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.colors as pc
import src.movements as mv


class Plots:
    @staticmethod
    def plot_trend(timeseries: mv.Timeseries, save_path = None):
        
        # inout_sheet = timeseries.inout_sheet
        # tspan = inout_sheet.index
        # lspan = np.linspace(0, inout_sheet.__len__(), len(tspan))
        # real_slope, intercept = timeseries.estimated_lm_params()
        # line = lspan * real_slope + intercept
        
        # fig, ax = plt.subplots(figsize = (15,5), dpi = 100)   
        # ax.plot(tspan, inout_sheet["CumulativeIn"],
        #         color = 'g', lw = 2, alpha = 0.75,
        #         label = 'Cumulative Income')
        # ax.plot(tspan, inout_sheet["CumulativeOut"],
        #         color = 'r', lw = 2, alpha = 0.75,
        #         label = 'Cumulation Expanses')
        # ax.plot(tspan, inout_sheet["Available"],
        #         color = 'k', lw = 2, alpha = 0.75,
        #         label = 'Available Capital')
        # ax.plot(tspan, line,
        #         color = 'k', lw = 2, ls = '--', alpha = 0.75,
        #         label = f'Fitted Trend (empirical), slope = {real_slope:.2f}')
        # ax.set_xlabel('Time', fontsize = 14, labelpad = 15)
        # ax.set_ylabel('Amount [EUR]', fontsize = 14, labelpad = 15)
        # ax.grid(axis = 'both', lw = 0.5)
        # ax.legend()
        # if save_path:
        #     fig.savefig(save_path, format = "png",
        #                 dpi = 300, bbox_inches = "tight")
        # plt.show(fig)
            
        inout_sheet = timeseries.inout_sheet
        tspan = inout_sheet.index
        lspan = np.linspace(0, len(tspan), len(tspan))
        real_slope, intercept = timeseries.estimated_lm_params()
        trend_line = lspan * real_slope + intercept
    
        # --- Create figure ---
        fig = go.Figure()
    
        # Cumulative Income
        fig.add_trace(go.Scatter(
            x = tspan,
            y = inout_sheet["CumulativeIn"],
            mode = 'lines',
            name = 'Cumulative Income',
            line = dict(color = 'green', width = 2),
            hovertemplate = '%{x}<br>Cumulative Income: %{y:.2f}€<extra></extra>'
        ))
    
        # Cumulative Out
        fig.add_trace(go.Scatter(
            x = tspan,
            y = inout_sheet["CumulativeOut"],
            mode = 'lines',
            name = 'Cumulative Expenses',
            line = dict(color = 'red', width = 2),
            hovertemplate = '%{x}<br>Cumulative Expenses: %{y:.2f}€<extra></extra>'
        ))
    
        # Available
        fig.add_trace(go.Scatter(
            x = tspan,
            y = inout_sheet["Available"],
            mode = 'lines',
            name = 'Available Capital',
            line = dict(color = 'black', width = 2),
            hovertemplate = '%{x}<br>Available: %{y:.2f}€<extra></extra>'
        ))
    
        # Fitted Trend (dashed)
        fig.add_trace(go.Scatter(
            x = tspan,
            y = trend_line,
            mode = 'lines',
            name = f'Fitted Trend (slope = {real_slope:.2f})',
            line = dict(color = 'black', width = 2, dash = 'dash'),
            hovertemplate = '%{x}<br>Trend: %{y:.2f}€<extra></extra>'
        ))
    
        # --- Layout ---
        fig.update_layout(
            # title = "Financial Trend",
            xaxis_title = "Time",
            yaxis_title = "Amount [EUR]",
            template = "plotly_white",
            width = 1000,
            height = 500,
            hovermode = "x unified",
            # hoverlabel = dict(align = "left", namelength = -1)
        )
    
        return fig
    #end
    
    @staticmethod
    def plot_expense_items(operations, save_path = None):
        def _get_colormap(base_cm, n_items):
            return pc.sample_colorscale(
                pc.get_colorscale(base_cm),
                [i/(n_items - 1) if n_items > 1 else 0.5 for i in range(n_items)]
            )
        #end
            
        def _make_pie_plot(_labels, _sizes, facecolor, title):
            hover_fmt = "%{label}<br>%{value:.2f} €<extra></extra>"
            
            fig = go.Figure(
                data = [
                    go.Pie(
                        domain = dict(x = [0, 0.7], y = [0, 1]),
                        labels = _labels,
                        values = _sizes,
                        hole = 0.4,
                        marker = dict(
                            colors = [facecolor] * len(_labels),
                            line = dict(
                                color = "white",
                                width = 2
                            )
                        ),
                        hovertemplate = hover_fmt
                    )
                ]
            )
            fig.update_layout(title_text = title, height = 500, width = 600)
            return fig
        
        # Differentiate inputs and outputs
        expenses_year_averages = operations.year_means
        income_items = {k: v for k, v in expenses_year_averages.items() if v > 0}
        expense_items = {k: v for k, v in expenses_year_averages.items() if v < 0}
        
        
        # Make pie chart for the inputs
        fig_incomes = _make_pie_plot(
            list(income_items.keys()),
            [np.abs(c.item()) for c in income_items.values()],
            facecolor = "seagreen",
            title = "Income"
        )
        
        fig_expenses = _make_pie_plot(
            list(expense_items.keys()),
            [np.abs(c.item()) for c in expense_items.values()],
            facecolor = "firebrick",
            title = "Expenses"
        )
        
        return fig_incomes, fig_expenses
    #end
#end
