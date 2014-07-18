import matplotlib.pyplot as plt
import numpy as np

__author__ = 'mattdyer'

#start here when the script is launched
if (__name__ == '__main__'):
    import matplotlib.pyplot as plt
    import numpy as np
    column_labels = ['a really really really long label', 'test2', 'test3', 'test4']
    row_labels = list('WXYZ')
    data = np.random.rand(4,4)
    fig, ax = plt.subplots()
    heatmap = ax.pcolor(data, cmap=plt.cm.Blues)

    # put the major ticks at the middle of each cell
    ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False)
    ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False)

    # want a more natural, table-like display
    ax.invert_yaxis()
    ax.xaxis.tick_top()

    ax.set_xticklabels(row_labels, minor=False)
    ax.set_yticklabels(column_labels, minor=False)
    plt.show()