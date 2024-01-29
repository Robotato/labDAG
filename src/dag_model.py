import uuid
import xml.etree.ElementTree as ET

from datetime import datetime
from enum import Enum
from graphlib import TopologicalSorter, CycleError
from warnings import warn


class Status(Enum):
    TO_DO, IN_PROGRESS, DONE = range(3)
    def to_symbol(self):
        # return "☐🧪☑"[self]
        return "⬜🚧✅"[self.value]

class Product():
    def __init__(self, name="", prerequisites=set(), status=None, target=None, notes=None):
        self._uuid=uuid.uuid4()
        self.name = name
        self.prerequisites = prerequisites
        self.status = status if status is not None else Status.TO_DO
        self.target = target
        self.notes = notes
    
    def __eq__(self, __value: object) -> bool:
        return (self._uuid == __value._uuid
                and self.name == __value.name
                and self.prerequisites == __value.prerequisites
                and self.status == __value.status
                and self.target == __value.target
                and self.notes == __value.notes)

    def __hash__(self) -> int:
        return hash((self._uuid,
                     self.name,
                     (pre for pre in self.prerequisites),
                     self.status,
                     self.target,
                     self.notes))

    def __repr__(self) -> str:
        return f"{self.name} ({str(self._uuid)[-8:]}) {self.status.to_symbol()}"

class DAGModel:
    def __init__(self):
        self._nodes = {}
        self._graph = {}
        self._sorter = TopologicalSorter()

    def add_product(self, product):
        self._nodes[product._uuid] = product
        self._graph[product._uuid] = {pre._uuid for pre in product.prerequisites}
        self._sorter.add(product._uuid, *[pre._uuid for pre in product.prerequisites])

        # Recursively add prerequisites if they are not already in the DAG
        for pre in product.prerequisites:
            if pre._uuid not in self._nodes:
                self.add_product(pre)
    
    def add_dependency(self, product, *prerequisites):
        product.prerequisites.update(prerequisites)
        self.add_product(product)

    def remove_product(self, product):
        # remove from nodes
        del self._nodes[product._uuid]

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
    def from_xml(filepath):
        dag_model = DAGModel()
        tree = ET.parse(filepath)
        root = tree.getroot()

        for product_element in root.findall('Product'):
            name = product_element.find('Name').text
            status = product_element.find('Status').text
            id = uuid.UUID(product_element.find('UUID').text)
            notes = product_element.find('Notes').text

            target_date = product_element.find('Target')
            if target_date is not None:
                target_date = datetime.strptime(target_date.text, "%Y-%m-%d")

            prereqs = set()
            for pre in product_element.find("Prerequisites"):
                prereqs.add(dag_model._nodes[uuid.UUID(pre.text)])

            product = Product(name, prerequisites=prereqs, status=status, notes=notes, target=target_date)
            product._uuid = id
            dag_model.add_product(product)

        return dag_model

    def to_xml(self, filepath):
        root = ET.Element("DAGModel")

        for product in self.order:
            product_element = ET.SubElement(root, "Product")
            ET.SubElement(product_element, "Name").text = product.name
            ET.SubElement(product_element, "Status").text = product.status
            ET.SubElement(product_element, "UUID").text = str(product._uuid)
            ET.SubElement(product_element, "Notes").text = product.notes
            if product.target:
                ET.SubElement(product_element, "Target").text = product.target.strftime("%Y-%m-%d")

            prereqs_element = ET.SubElement(product_element, "Prerequisites")
            for pre in product.prerequisites:
                ET.SubElement(prereqs_element, "Prerequisite").text = str(pre._uuid)

            tree = ET.ElementTree(root)
            tree.write(filepath)
    
    def __eq__(self, __value: object) -> bool:
        return (self._nodes == __value._nodes
                and self._graph == __value._graph)
    
    def __str__(self) -> str:
        result = ""
        for product in self.order:
            result += f"{product.name} ({str(product._uuid)[-8:]})\n"
        return result