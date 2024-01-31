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

def gantt_2(dag_model, ax=None):
    if ax is None:
        _, ax = plt.subplots()
    
    wstride = 10
    hstride = 10

    def gantt_iter(products, ax, depth=0, y=0):
        max_depth = depth
        total_dy = 0
        names = []
        for prod in products:
            xpos = depth * wstride
            ypos = y * hstride
            rect = patches.Rectangle((xpos, ypos),
                                    wstride,
                                    hstride,
                                    linewidth=1,
                                    edgecolor='w',
                                    facecolor='ryg'[prod.status.value])
            ax.add_patch(rect)
            max_d, dy, new_names = gantt_iter(dag_model.get_prerequisites(prod), ax, depth + 1, y + 1)
            names.append(prod.name)
            names.extend(new_names)
            max_depth = max(max_depth, max_d)
            total_dy += 1 + dy
            y += 1 + dy
        return max_depth, total_dy, names
    
    xmax, ymax, names = gantt_iter(dag_model.endpoints, ax)
    ax.set_ylim(0, ymax * hstride)
    ax.set_xlim(xmax * wstride, 0)
    ax.set_yticks(np.arange(hstride / 2, ymax * hstride, hstride), names)

    return ax