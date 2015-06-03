# -*- coding: utf-8 -*-
"""
Created on Mon Jun 01 19:43:55 2015

@author: Laurent
"""
import pandas.core.common as com
from pandas.tools.plotting import _get_standard_colors
from pandas.compat import lrange
import numpy as np

def parallel_coordinates(frame, class_column, cols=None, ax=None, color=None,
                         use_columns=False, xticks=None, colormap=None,
                         axvlines=True, shrink=False, normalize=True,
                         bounds=None, nticks = 11, **kwds):
    """Parallel coordinates plotting.

    Parameters
    ----------
    frame: DataFrame
    class_column: str
        Column name containing class names
    cols: list, optional
        A list of column names to use
    ax: matplotlib.axis, optional
        matplotlib axis object
    color: list or tuple, optional
        Colors to use for the different classes
    use_columns: bool, optional
        If true, columns will be used as xticks
    xticks: list or tuple, optional
        A list of values to use for xticks
    colormap: str or matplotlib colormap, default None
        Colormap to use for line colors.
    axvlines: bool, optional
        If true, vertical lines will be added at each xtick
    kwds: keywords
        Options to pass to matplotlib plotting method

    Returns
    -------
    ax: matplotlib axis object

    Examples
    --------
    >>> from pandas import read_csv
    >>> from pandas.tools.plotting import parallel_coordinates
    >>> from matplotlib import pyplot as plt
    >>> df = read_csv('https://raw.github.com/pydata/pandas/master/pandas/tests/data/iris.csv')
    >>> parallel_coordinates(df, 'Name', color=('#556270', '#4ECDC4', '#C7F464'))
    >>> plt.show()
    """
    import matplotlib.pyplot as plt
    hide_yticks=False

    n = len(frame)
    classes = frame[class_column].drop_duplicates()
    class_col = frame[class_column]
            
    if cols is None:
        df = frame.drop(class_column, axis=1)
    else:
        df = frame[cols]

    used_legends = set([])

    ncols = len(df.columns)

    if shrink is True:
        df = (df-df.mean()) / (df.max() - df.min())
            
    if normalize is True:       
        if bounds is None:
            df = (df-df.min()) / (df.max() - df.min())
        else:
            lb = np.asarray(bounds[0])
            ub = np.asarray(bounds[1])
            
            df = (df-lb) / (ub - lb)

            hide_yticks=True

            #define yticks
            yticks = []
            yticks_positions = [i*1/float(nticks-1) for i in range(nticks)]
            for b in xrange(len(lb)):
                yticks.append([lb[b]+i*(ub[b]-lb[b])/float(nticks-1) for i in range(nticks)])

    # determine values to use for xticks
    if use_columns is True:
        if not np.all(np.isreal(list(df.columns))):
            raise ValueError('Columns must be numeric to be used as xticks')
        x = df.columns
    elif xticks is not None:
        if not np.all(np.isreal(xticks)):
            raise ValueError('xticks specified must be numeric')
        elif len(xticks) != ncols:
            raise ValueError('Length of xticks must match number of columns')
        x = xticks
    else:
        x = lrange(ncols)

    if ax is None:
        ax = plt.gca()

    color_values = _get_standard_colors(num_colors=len(classes),
                                        colormap=colormap, color_type='random',
                                        color=color)

    colors = dict(zip(classes, color_values))
    
    for i in range(n):
        y = df.iloc[i].values
        kls = class_col.iat[i]
        label = com.pprint_thing(kls)
        if label not in used_legends:
            used_legends.add(label)
            ax.plot(x, y, color=colors[kls], label=label, alpha=0.5, **kwds)
        else:
            ax.plot(x, y, color=colors[kls], alpha=0.5, **kwds)

    if axvlines:
        for i in x:
            ax.axvline(i, linewidth=2, color='black')
            if hide_yticks is True:
                for j in xrange(len(yticks[i])):
                    text = plt.text(i,yticks_positions[j],str(yticks[i][j]),ha='center',weight='bold')
                    text.set_bbox(dict(color='white', alpha=0.25))

    if hide_yticks is True:
        plt.setp(ax.get_yticklabels(), visible=False)

    ax.set_xticks(x)
    ax.set_xticklabels(df.columns)
    ax.set_xlim(x[0], x[-1])
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)
    ax.grid()
    return ax