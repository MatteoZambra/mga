
import numpy as np

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.colors as pc


class Plots:
    @staticmethod
    def plot_trend(
            timeseries,
            backend = "matplotlib",
            plot_trend_line = True,
            save_path = None
        ):
        
        inout_sheet = timeseries.inout_sheet
        tspan = inout_sheet.index
        if plot_trend_line:
            lspan = np.linspace(0, len(tspan), len(tspan))
            real_slope, intercept = timeseries.estimated_lm_params()
            trend_line = lspan * real_slope + intercept
        
        if backend == "matplotlib":
        
            fig, ax = plt.subplots(figsize = (15,5), dpi = 100)   
            ax.plot(tspan, inout_sheet["CumulativeIn"],
                    color = 'g', lw = 2, alpha = 0.75,
                    label = 'Cumulative Income')
            ax.plot(tspan, inout_sheet["CumulativeOut"],
                    color = 'r', lw = 2, alpha = 0.75,
                    label = 'Cumulation Expanses')
            ax.plot(tspan, inout_sheet["Available"],
                    color = 'k', lw = 2, alpha = 0.75,
                    label = 'Available Capital')
            if plot_trend_line:
                ax.plot(tspan, trend_line,
                        color = 'k', lw = 2, ls = '--', alpha = 0.75,
                        label = f'Fitted Trend (empirical), slope = {real_slope:.2f}')
            ax.set_xlabel('Time', fontsize = 14, labelpad = 15)
            ax.set_ylabel('Amount [EUR]', fontsize = 14, labelpad = 15)
            ax.grid(axis = 'both', lw = 0.5)
            ax.legend()
    
        elif backend == "plotly":
            
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
    def plot_simulation_runs(
            simulated_inouts,
            trendline_params = None,
            plot_trend_line = False
        ):
        
        fig, ax = plt.subplots(figsize = (15,5))
        for inout in simulated_inouts:
            tspan = inout.index
            if plot_trend_line:
                lspan = np.linspace(0, len(tspan), len(tspan))
                real_slope, intercept = trendline_params()
                trend_line = lspan * real_slope + intercept
            ax.plot(tspan, inout["CumulativeIn"],
                    color = 'g', lw = 2, alpha = 0.5)
            ax.plot(tspan, inout["CumulativeOut"],
                    color = 'r', lw = 2, alpha = 0.5)
            ax.plot(tspan, inout["Available"],
                    color = 'k', lw = 2, alpha = 0.5)
            if plot_trend_line:
                ax.plot(tspan, trend_line,
                        color = 'k', lw = 2, ls = '--', alpha = 0.75,
                        label = f'Fitted Trend (empirical), slope = {real_slope:.2f}')
            ax.set_xlabel('Time', fontsize = 14, labelpad = 15)
            ax.set_ylabel('Amount [EUR]', fontsize = 14, labelpad = 15)
            ax.grid(axis = 'both', lw = 0.5)
        
        if trendline_params is not None and plot_trend_line:
            ax.plot(tspan, trend_line, c = "k", lw = 2, alpha = 0.85, ls = "--")
        # ax.legend()
    
    @staticmethod
    def plot_expense_items(
            operations,
            backend = "matplotlib",
            save_path = None
        ):
        
        def _get_colormap(base_cm, n_items):
            return pc.sample_colorscale(
                pc.get_colorscale(base_cm),
                [i/(n_items - 1) if n_items > 1 else 0.5 for i in range(n_items)]
            )
        #end
        
        # Differentiate inputs and outputs
        expenses_year_averages = operations.year_means
        income_items = {k: v for k, v in expenses_year_averages.items() if v > 0}
        expense_items = {k: v for k, v in expenses_year_averages.items() if v < 0}
        
        if backend == "plotly":
            def _make_pie_plot_plotly(_labels, _sizes, facecolor, title):
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
            #end
            
            # Assign the plotter function
            plotter_fnc = _make_pie_plot_plotly
        
        if backend == "matplotlib":
            def _make_pie_plot_matplotlib(_labels, _sizes, facecolor, title = None):
                # Define the plot
                fig, ax = plt.subplots(figsize = (7.5, 5.5))
                
                wedges, texts, autotexts = ax.pie(
                    _sizes,
                    autopct = "%.1f%%",
                    startangle = 90,
                    pctdistance = 1.095,
                    labeldistance = 0.5,
                    wedgeprops = dict(
                        width = 0.5,
                        edgecolor = "white",
                        # facecolor = facecolor,
                        alpha = 0.75,
                        linewidth = 2
                    )
                )
                
                # Make the legend
                ax.legend(
                    wedges,
                    _labels,
                    title="Voices",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1),
                    ncols = 2,
                    fontsize = 14
                )
                
                return fig
            #end
            
            # Assing plotter function
            plotter_fnc = _make_pie_plot_matplotlib
        #end
        
        # Make pie chart for the inputs
        fig_incomes = plotter_fnc(
            list(income_items.keys()),
            [np.abs(c.item()) for c in income_items.values()],
            facecolor = "seagreen",
            title = "Income"
        )
        
        fig_expenses = plotter_fnc(
            list(expense_items.keys()),
            [np.abs(c.item()) for c in expense_items.values()],
            facecolor = "firebrick",
            title = "Expenses"
        )
        
        return fig_incomes, fig_expenses
    #end
#end