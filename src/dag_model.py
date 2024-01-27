import uuid
from warnings import warn
from enum import Enum
from graphlib import TopologicalSorter, CycleError

class Status(Enum):
    TO_DO, IN_PROGRESS, DONE = range(3)

class Product():
    def __init__(self, name="", prerequisites=set(), status=None, target=None, notes=None):
        self.uuid=uuid.uuid4()
        self.name = name
        self.prerequisites = prerequisites
        self.status = status
        self.target = target
        self.notes = notes

class DAGModel:
    def __init__(self):
        self._nodes = {}
        self._graph = {}
        self._sorter = TopologicalSorter()

    def add_product(self, product):
        self._nodes[product.uuid] = product
        self._graph[product.uuid] = {pre.uuid for pre in product.prerequisites}
        self._sorter.add(product.uuid, *[pre.uuid for pre in product.prerequisites])
    
    def add_dependency(self, product, *prerequisites):
        product.prerequisites.update(prerequisites)
        self.add_product(product)

    def remove_product(self, product):
        # remove from nodes
        del self._nodes[product.uuid]

        # remove from graph
        for product_id, product in self._nodes.items():
            if product_id in product.prerequisites:
                product.prerequisites.remove(product_id)
                self._graph[product_id].remove(product_id)
        
        # re-create sorter
        self._sorter = TopologicalSorter(self._graph)

    def get_product_by_uuid(self, uuid):
        return self._nodes[uuid]

    def get_products_by_name(self, product_name):
        result = []
        for product in self._nodes.values():
            if product.name == product_name:
                result.append(product)

        return result
    
    def all_prerequisites(self, product):
        queue = [pre for pre in product.prerequisites]
        seen = set()
        
        while len(queue) > 0:
            pre = queue.pop()
            seen.add(pre)
            queue.extend(p for p in pre.prerequisites if p not in seen)

            yield pre

    @property
    def products(self):
        return [product for product in self._nodes.values()]

    @property
    def order(self):
        try:
            result = tuple(self._nodes[uuid] for uuid in self._sorter.static_order())
            self._sorter = TopologicalSorter(self._graph)
            return result
        except CycleError as e:
            msg = e.args[0]
            cycle_nodes = [f"{self._nodes[uuid].name} ({str(uuid)[-8:]})" for uuid in e.args[1]]
            e.args = (msg, cycle_nodes)
            raise e

    @staticmethod
    def from_file(filepath):
        pass

    def to_file(self, filepath):
        pass
