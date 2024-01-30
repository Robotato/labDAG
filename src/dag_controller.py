import cmd
from src.dag_model import DAGModel, Status

class LabManagementShell(cmd.Cmd):
    intro = 'Welcome to the LabDAG Shell. Type help or ? to list commands.\n'
    prompt = '(lab) '

    def __init__(self):
        super().__init__()
        self.dag_model = DAGModel()

    def do_load(self, arg):
        'Load a DAG model from an XML file: load <file>'
        try:
            self.dag_model = DAGModel.from_xml(arg)
            print(f"DAG model loaded from {arg}")
        except Exception as e:
            print(f"Error loading file: {e}")

    def do_mark(self, arg):
        'Mark a product with a specific status: mark <product> <status>'
        try:
            product_name, status = arg.split()
            product = self.dag_model.get_product_by_name(product_name)
            if product:
                product.status = Status.from_string(status)
                print(f"Marked {product_name} as {status}")
            else:
                print(f"Product {product_name} not found")
        except ValueError:
            print("Invalid arguments. Usage: mark <product> <status>")

    def do_save(self, arg):
        'Save the current DAG model to an XML file: save <file>'
        try:
            self.dag_model.to_xml(arg)
            print(f"DAG model saved to {arg}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def do_exit(self, arg):
        'Exit the shell'
        print("Goodbye!")
        return True

if __name__ == '__main__':
    LabManagementShell().cmdloop()
