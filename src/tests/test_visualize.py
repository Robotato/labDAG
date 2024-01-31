import unittest

import matplotlib.pyplot as plt
from datetime import datetime
from src.dag_model import DAGModel, Product, Status
from src.visualize import gantt

class TestVisualize(unittest.TestCase):
    def setUp(self):
        self.dag_model = DAGModel()
        self.product1 = Product("Plasmid1", notes="Notes1", target=datetime(2024, 1, 30), status=Status.IN_PROGRESS)
        self.product2 = Product("Plasmid2", notes="Notes2", target=datetime(2024, 2, 15), status=Status.DONE)
        self.product3 = Product("Plasmid3", notes="Notes3", target=datetime(2024, 3, 20), status=Status.DONE)
        self.product4 = Product("Plasmid4", status=Status.TO_DO)

        self.dag_model.add_product(self.product1, self.product2, self.product3)
        self.dag_model.add_product(self.product4)

    def test_gantt(self):
        _, ax = plt.subplots()
        gantt(self.dag_model, ax)
        plt.show()


if __name__ == '__main__':
    unittest.main()
