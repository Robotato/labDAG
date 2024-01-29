import unittest
from datetime import datetime

from src.dag_model import DAGModel, Product
from src.validate import validate_DAG


class TestValidateDAG(unittest.TestCase):
    def setUp(self):
        self.dag_model = DAGModel()

        self.product1 = Product("Plasmid1", notes="Notes1", target=datetime(2024, 1, 30))
        self.product2 = Product("Plasmid2", notes="Notes2", target=datetime(2024, 2, 20))
        self.product3 = Product("Plasmid3", notes="Notes3", target=datetime(2024, 3, 20))
        self.product4 = Product("Plasmid4", notes="Notes4", target=None)

    def test_valid_dag(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product2)
        self.dag_model.add_product(self.product3)
        self.dag_model.add_dependency(self.product3, self.product2)
        self.dag_model.add_dependency(self.product2, self.product1)
        
        valid, cycles, invalid_dates = validate_DAG(self.dag_model)
        self.assertTrue(valid)
        self.assertIsNone(cycles)
        self.assertEqual(len(invalid_dates), 0)

    def test_valid_dag_with_none_target_date(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product2)
        self.dag_model.add_product(self.product4)
        self.dag_model.add_dependency(self.product4, self.product1)
        self.dag_model.add_dependency(self.product2, self.product4)
        
        valid, cycles, invalid_dates = validate_DAG(self.dag_model)
        self.assertTrue(valid)
        self.assertIsNone(cycles)
        self.assertEqual(len(invalid_dates), 0)
    
    def test_dag_with_cycle_and_none_target_date(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product4)
        self.dag_model.add_product(self.product2)
        # Create a cycle
        self.dag_model.add_dependency(self.product1, self.product4)
        self.dag_model.add_dependency(self.product4, self.product2)
        self.dag_model.add_dependency(self.product2, self.product1)

        valid, cycles, invalid_dates = validate_DAG(self.dag_model)
        self.assertFalse(valid)
        self.assertIsNotNone(cycles)
        self.assertNotEqual(len(invalid_dates), 0)

    def test_dag_with_incorrect_target_dates_and_none(self):
        self.dag_model.add_product(self.product1)
        self.dag_model.add_product(self.product2)
        self.dag_model.add_product(self.product4)
        # Set up dependencies
        self.dag_model.add_dependency(self.product1, self.product4)
        self.dag_model.add_dependency(self.product4, self.product2)

        valid, cycles, invalid_dates = validate_DAG(self.dag_model)
        self.assertFalse(valid)
        self.assertIsNone(cycles)
        self.assertNotEqual(len(invalid_dates), 0)

if __name__ == '__main__':
    unittest.main()
