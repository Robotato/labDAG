import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.dag_model import DAGModel


def gantt(dag_model, ax=None):
    if ax is None:
        _, ax = plt.subplots()
    
    wstride = 10
    hstride = 10

    end = {}
    order = dag_model.order
    N = len(order)
    names = []
    for y, product in enumerate(order):
        names.append(product.name)
        max_end = max([0] + [end.get(pre._uuid, 0) for pre in dag_model.get_prerequisites(product)])
        end[product._uuid] = max_end + 1

        # Rectangle patch
        xpos = max_end * wstride
        ypos = - (y+1) * hstride
        rect = patches.Rectangle((xpos, ypos),
                                 wstride,
                                 hstride,
                                 linewidth=1,
                                 edgecolor='w',
                                 facecolor='ryg'[product.status.value])
        ax.add_patch(rect)
    
    ax.set_xlim(0, max(end.values()) * wstride)
    ax.set_ylim(- N * hstride, 0)
    ax.set_yticks(np.arange(- hstride / 2, - N * hstride, -hstride), names)

    return ax