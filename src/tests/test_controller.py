import pathlib
import unittest
import uuid
from unittest.mock import patch, MagicMock
from src.dag_model import DAGModel, Product, Status
from src.dag_controller import LabManagementShell


class TestLabManagementShell(unittest.TestCase):

    def setUp(self):
        self.shell = LabManagementShell()
        self.shell.dag_model = MagicMock()

    def test_load_command(self):
        test_filepath = 'src/tests/test_read.xml'

        real_from_xml = DAGModel.from_xml
        def from_xml_wrapper(filepath):
            # check called with correct arguments
            self.assertEqual(filepath, test_filepath)
            return real_from_xml(filepath)

        # test load command
        with patch("src.dag_model.DAGModel.from_xml") as mock_from_xml:
            mock_from_xml.side_effect = from_xml_wrapper
            self.shell.onecmd(f"load {test_filepath}")

            # Check DAG has expected products/names
            expected_products = {
                uuid.UUID("ab06ccdf-8887-4c4c-acbe-1915dcca668d"): "Plasmid1",
                uuid.UUID("2d4d755c-a950-459f-a870-d49c0cc6adb1"): "Plasmid2",
                uuid.UUID("a4e42686-2137-418b-80c0-55ccdffbe26d"): "Plasmid3",
                uuid.UUID("a1e799ff-d635-46c5-9451-ae23ddcef573"): "Plasmid4",
            }
            for prod_id, name in expected_products.items():
                self.assertIn(prod_id, self.shell.dag_model._nodes)
                self.assertEqual(
                    name, self.shell.dag_model._nodes[prod_id].name)

            # Check that relationships are correct
            expected_dependencies = {
                "Plasmid1": [],
                "Plasmid2": ["Plasmid1"],
                "Plasmid3": ["Plasmid2"],
                "Plasmid4": ["Plasmid2", "Plasmid3"]
            }
            for prod_name, dependencies in expected_dependencies.items():
                prod = self.shell.dag_model.get_products_by_name(prod_name)[0]
                self.assertListEqual(dependencies,
                                     list(p.name for p in self.shell.dag_model.get_prerequisites(prod)))
    

    def test_save_command(self):
        test_filepath = "src/tests/test_save.xml"

        # replace Mock DAGModel with real
        self.shell.dag_model = DAGModel()

        real_to_xml = self.shell.dag_model.to_xml
        def to_xml_wrapper(filepath):
            self.assertEqual(filepath, test_filepath)
            return real_to_xml(filepath)
        
        with patch.object(DAGModel, "to_xml", side_effect=to_xml_wrapper) as mock_save:
            self.shell.onecmd(f"save {test_filepath}")

        # Check that file exists
        self.assertTrue(pathlib.Path(test_filepath).exists())

        # Delete file
        pathlib.Path(test_filepath).unlink()

        # Check that file was deleted successfully
        self.assertFalse(pathlib.Path(test_filepath).exists())


    def test_mark_command(self):
        product_name = 'Plasmid1'
        status = "Done"
        self.shell.dag_model.get_product_by_name.return_value = MagicMock(
            name=product_name)

        self.shell.onecmd(f'mark {product_name} {status}')

        self.shell.dag_model.get_product_by_name.assert_called_with(
            product_name)
        self.assertTrue(
            self.shell.dag_model.get_product_by_name.return_value.status == Status.DONE)


if __name__ == '__main__':
    unittest.main()
