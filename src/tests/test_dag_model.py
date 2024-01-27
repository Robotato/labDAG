import unittest
from datetime import datetime

from src.dag_model import DAGModel, Product, CycleError

class TestDAGModel(unittest.TestCase):
    def setUp(self):
        self.dag_model = DAGModel()
        self.product1 = Product("Plasmid1", set(), notes="Notes1", target=datetime(2024, 1, 30))
        self.product2 = Product("Plasmid2", {self.product1}, notes="Notes2", target=datetime(2024, 2, 15))
        self.product3 = Product("Plasmid3", {self.product2}, notes="Notes3", target=datetime(2024, 3, 20))
        self.product4 = Product("Plasmid4")

    def test_add_product(self):
        self.dag_model.add_product(self.product1)
        self.assertIn(self.product1.uuid, self.dag_model._nodes)
        self.assertEqual(self.product1, self.dag_model._nodes[self.product1.uuid])

    def test_remove_product(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.remove_product(self.product1)
        self.assertNotIn(self.product1.uuid, self.dag_model._nodes)

    def test_get_products_by_name(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product2)
        products = self.dag_model.get_products_by_name("Plasmid1")
        self.assertIn(self.product1, products)
        self.assertNotIn(self.product2, products)

    def test_order_property(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product2)
        self.dag_model.add_product(self.product3)
        ordered_products = self.dag_model.order
        
        self.assertEqual((self.product1, self.product2, self.product3), ordered_products)

        self.product1.prerequisites = {self.product3}
        self.dag_model.add_product(self.product1)
        with self.assertRaises(CycleError):
            _ = self.dag_model.order
    
    def test_all_prerequisites(self):
        # Set up dependencies
        self.dag_model.add_dependency(self.product4, self.product3, self.product2)
        self.dag_model.add_dependency(self.product3, self.product2)
        self.dag_model.add_dependency(self.product2, self.product1)

        # Get all prerequisites for product4
        prerequisites = set(self.dag_model.all_prerequisites(self.product4))

        # Check that all prerequisites are correctly identified
        expected_prerequisites = {self.product1, self.product2, self.product3}
        self.assertEqual(prerequisites, expected_prerequisites)

        # Test with a product that has no prerequisites
        prerequisites_no_deps = set(self.dag_model.all_prerequisites(self.product1))
        self.assertEqual(prerequisites_no_deps, set())


if __name__ == '__main__':
    unittest.main()
