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
    
    @staticmethod
    def from_string(string):
        string = string.lower().strip()
        if string in {"0", "to_do", "to do"}:
            return Status.TO_DO
        elif string in {"1", "in_progress", "in progress"}:
            return Status.IN_PROGRESS
        elif string in {"2", "done"}:
            return Status.DONE
        else:
            raise ValueError(f"Unrecognized status: {string}.")

class Product():
    def __init__(self, name="", status=None, target=None, notes=None):
        self._uuid = uuid.uuid4()
        self._created = datetime.now().replace(microsecond=0)
        self.name = name
        self.status = status if status is not None else Status.TO_DO
        self.target = target
        self.notes = notes
    
    def __eq__(self, __value: object) -> bool:
        return (self._uuid == __value._uuid
                and self._created == __value._created
                and self.name == __value.name
                and self.status == __value.status
                and self.target == __value.target
                and self.notes == __value.notes)

    def __repr__(self) -> str:
        target_date_str = f" [{self.target.strftime('%d/%m/%Y')}]" if self.target is not None else ""
        return f"({str(self._uuid)[-8:]}) {self.name}{target_date_str} {self.status.to_symbol()}"

class DAGModel:
    def __init__(self):
        self._nodes = {}
        self._graph = {}
        self._sorter = TopologicalSorter()

    def add_product(self, product, *prerequisites):
        self._nodes[product._uuid] = product
        self._graph[product._uuid] = {pre._uuid for pre in prerequisites}
        self._sorter.add(product._uuid, *[pre._uuid for pre in prerequisites])

        # Recursively add prerequisites if they are not already in the DAG
        for pre in prerequisites:
            if pre._uuid not in self._nodes:
                self.add_product(pre)
    
    def add_dependency(self, product, *prerequisites):
        self.add_product(product, *prerequisites)

    def remove_product(self, product):
        # remove from nodes
        del self._nodes[product._uuid]

        # remove from graph
        for product_id, product in self._nodes.items():
            if product._uuid in self._graph[product_id]:
                self._graph[product_id].remove(product._uuid)
        
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

    def get_prerequisites(self, product):
        return [self._nodes[pre_id] for pre_id in self._graph[product._uuid]]
    
    def all_prerequisites(self, product):
        queue = [pre for pre in self.get_prerequisites(product)]
        seen = set()
        
        while len(queue) > 0:
            pre = queue.pop()
            seen.add(pre._uuid)
            queue.extend(p for p in self.get_prerequisites(pre) if p._uuid not in seen)

            yield pre

    @property
    def products(self):
        return [product for product in self._nodes.values()]

    @property
    def order(self):
        try:
            result = tuple(self._nodes[uuid] for uuid in self._sorter.static_order())
            # re-create sorter
            self._sorter = TopologicalSorter(self._graph)

            return result
        except CycleError as e:
            msg = e.args[0]
            cycle_nodes = [f"{self._nodes[uuid].name} ({str(uuid)[-8:]})" for uuid in e.args[1]]
            e.args = (msg, cycle_nodes)

            # re-create sorter
            self._sorter = TopologicalSorter(self._graph)
            raise e

    @staticmethod
    def from_xml(filepath):
        dag_model = DAGModel()
        tree = ET.parse(filepath)
        root = tree.getroot()

        for product_element in root.findall('Product'):
            name = product_element.find('Name').text

            status = product_element.find('Status').text
            if status is not None:
                status = Status(status)
            
            id = uuid.UUID(product_element.find('UUID').text)
            notes = product_element.find('Notes').text

            created = datetime.strptime(product_element.find("Created").text, "%d/%m/%Y %H:%M:%S")

            target_date = product_element.find('Target')
            if target_date is not None:
                target_date = datetime.strptime(target_date.text, "%Y-%m-%d")

            prereqs = []
            for pre in product_element.find("Prerequisites"):
                prereqs.append(dag_model._nodes[uuid.UUID(pre.text)])

            product = Product(name, status=status, notes=notes, target=target_date)
            product._uuid = id
            product._created = created
            dag_model.add_product(product, *prereqs)

        return dag_model

    def to_xml(self, filepath):
        root = ET.Element("DAGModel")

        for product in self.order:
            product_element = ET.SubElement(root, "Product")
            ET.SubElement(product_element, "Name").text = product.name
            ET.SubElement(product_element, "Status").text = product.status.value
            ET.SubElement(product_element, "UUID").text = str(product._uuid)
            ET.SubElement(product_element, "Created").text = product._created.strftime("%d/%m/%Y %H:%M:%S")
            ET.SubElement(product_element, "Notes").text = product.notes
            if product.target:
                ET.SubElement(product_element, "Target").text = product.target.strftime("%Y-%m-%d")

            prereqs_element = ET.SubElement(product_element, "Prerequisites")
            for pre in self.get_prerequisites(product):
                ET.SubElement(prereqs_element, "Prerequisite").text = str(pre._uuid)

        tree = ET.ElementTree(root)
        tree.write(filepath)
    
    def __eq__(self, __value: object) -> bool:
        return (self._nodes == __value._nodes
                and self._graph == __value._graph)
    
    def __str__(self) -> str:
        result = ""
        for product in self.order:
            result += f"{str(product)}\n"
        return result