import cmd
from src.dag_model import DAGModel, Product, Status

def select_match(options, prompt=None):
    if prompt is not None:
        print(prompt)
    
    for i, option in enumerate(options):
        print(f"\t{i+1}. {option}")
    
    

    while True:
        choice = input(f"Enter your selection (1 - {len(options)}): ")

        try:
            choice = int(choice)
            return options[choice - 1]
        except:
            pass


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
        return self.dag_model

    
    def do_show(self, arg):
        'Show the current DAG: show'
        try:
            print(self.dag_model)
        except Exception as e:
            print(f"Error showing DAG: {e}")


    def do_add(self, arg):
        'Add a new product: add <name> [prereq1 prereq2 ...]'
        try:
            args = arg.split()
            if not args:
                print("Please provide a product name.")
                return

            product_name = args[0]
            prerequisite_names = args[1:]

            prerequisites = []
            for prereq_name in prerequisite_names:
                matches = self.dag_model.get_products_by_name(prereq_name)

                if len(matches) == 0:
                    match = Product(prereq_name)
                elif len(matches) == 1:
                    match = matches[0]
                else:
                    match = select_match(matches, f"Multiple products named {prereq_name} found: ")

                prerequisites.append(match)

            new_product = Product(name=product_name)
            self.dag_model.add_product(new_product, *prerequisites)

            print(f"Product '{product_name}' added", end="")
            if len(prerequisites) > 0:
                print(f" with prerequisites: {', '.join(prerequisite_names)}")
            else:
                print(".")
        except Exception as e:
            print(f"Error adding product: {e}")


    def do_mark(self, arg):
        'Mark a product with a specific status: mark <product> <status>'
        try:
            product_name, status = arg.split()

            # Get product, since multiple products can have same name
            matches = self.dag_model.get_products_by_name(product_name)
            if len(matches) == 0:
                print(f"Product {product_name} not found!")
                return
            elif len(matches) == 1:
                product = matches[0]
            else:
                product = select_match(matches, prompt=f"Multiple products named {product_name} found:")

            product.status = Status.from_string(status)
            print(f"Marked {product_name} as {status}")

        except ValueError:
            print("Invalid arguments. Usage: mark <product> <status>")


    def do_save(self, arg):
        'Save the current DAG model to an XML file: save <file>'
        try:
            self.dag_model.to_xml(arg)
            print(f"DAG model saved to {arg}")
        except Exception as e:
            print(f"Error saving file: {e}")


    def do_exit(self, _):
        'Exit the shell'
        print("Goodbye!")
        return True

if __name__ == '__main__':
    LabManagementShell().cmdloop()
