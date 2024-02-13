import cmd
import webbrowser
import matplotlib.pyplot as plt
from shlex import split, quote
from datetime import datetime
from src.dag_model import DAGModel, Product, Status
from src.visualize import gantt
from src.validate import validate_DAG

def select_match(options, prompt=None, return_index=False):
    if prompt is not None:
        print(prompt)
    
    for i, option in enumerate(options):
        print(f"\t{i+1}. {option}")
    
    while True:
        choice = input(f"Enter your selection (1 - {len(options)}): ")

        try:
            choice = int(choice)

            if not return_index:
                return options[choice - 1]
            else:
                return choice-1, options[choice - 1]
        except:
            pass


def select_product(dag_model, product_name, create_missing=True):
    matches = dag_model.get_products_by_name(product_name)

    if len(matches) == 0:
        if create_missing:
            return Product(product_name)
        else:
            raise ValueError(f"No product with name {product_name} found.")
    elif len(matches) == 1:
        return matches[0]
    else:
        return select_match(matches, f"Multiple products named {product_name} found: ")


def try_parse_datestr(datestr,
                      formats=["%m/%d/%Y",
                               "%m-%d-%Y",
                               "%m/%d/%y",
                               "%m-%d-%y",
                               ]):
    """Attempts to parse a string representing a date into a date object, using a list of possible formats.

    Args:
        datestr (str): the string to parse.
        formats (list, optional): formats that the date might be in.

    Returns:
        datetime.date or None: the parsed date if successful, else None.
    """
    for format in formats:
        try:
            return datetime.strptime(datestr, format)
        except ValueError:
            continue
    
    return None


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

    
    def do_show(self, arg):
        'Show the current DAG, or (if given) details of a product: show [product]'
        try:
            if len(arg) == 0:
                print(self.dag_model)
            else:
                product = select_product(self.dag_model, arg, create_missing=False)
                print()
                print(product)
                print(f"Created: {product._created}")
                print(f"Target: {product.target}")

                print(f"\n{product.description}\n")

                print("Resources:")
                if product.resources:
                    print("\n\t".join(f"{i}. {res}" for i, res in enumerate(product.resources)))
                else:
                    print("\tNone")
                print(f"Notes:\n{product.notes}")
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
                pre = select_product(self.dag_model, prereq_name)
                prerequisites.append(pre)

            new_product = Product(name=product_name)
            self.dag_model.add_product(new_product, *prerequisites)

            print(f"Product '{product_name}' added", end="")
            if len(prerequisites) > 0:
                print(f" with prerequisites: {', '.join(prerequisite_names)}")
            else:
                print(".")
        except Exception as e:
            print(f"Error adding product: {e}")

    
    def do_remove(self, arg):
        "Remove a product from the DAG: remove product"
        try:
            product = select_product(self.dag_model, arg)
            self.dag_model.remove_product(product)
            print(f"Removed product {arg}.")
        except Exception as e:
            print(f"Error removing product: {e}")


    def do_depends(self, arg):
        'Add one or more prerequisites to a product: depends <product> prereq1 [prereq2 prereq3 ...]'

        try:
            args = arg.split()
            if len(args) <= 1:
                print("Please provide a product name and at least 1 prerequisite.")
                return
            
            product = select_product(self.dag_model, args[0])
            prereqs = [select_product(self.dag_model, pre) for pre in args[1:]]
            self.dag_model.add_dependency(product, *prereqs)

            print(f"Added prerequisites to {args[0]}.")

        except Exception as e:
            print(f"Error adding prerequisites: {e}")


    def do_free(self, arg):
        'Remove one or more prerequisites from a product: free <product> <prereq1> [prereq2 prereq3 ...]'
        
        try:
            args = arg.split()
            if len(args) < 2:
                print("Please provide a product name and at least 1 prerequisite.")
            
            product = select_product(self.dag_model, args[0])
            prereqs = [select_product(self.dag_model, pre) for pre in args[1:]]
            self.dag_model.remove_dependencies(product, *prereqs)

            print(f"Removed prerequisites from {args[0]}: {prereqs}")

        except Exception as e:
            print(f"Error removing prerequisites: {e}")

    def do_rename(self, arg):
        'Rename a product: rename <product> <new_name>'
        try:
            args = arg.split()
            if len(args) != 2:
                print("Please provide the current name of a product, and its new name.")
            
            product = select_product(self.dag_model, args[0], create_missing=False)
            product.name = args[1]
        except Exception as e:
            print(f"Error renaming product: {e}")

    def do_mark(self, arg):
        'Mark a product with a specific status: mark <product> <status>'
        try:
            product_name, status = arg.split()

            # Get product, since multiple products can have same name
            product = select_product(self.dag_model, product_name)
            product.status = Status.from_string(status)
            print(f"Marked {product_name} as {status}")

        except ValueError:
            print("Invalid arguments. Usage: mark <product> <status>")

    
    def do_describe(self, arg):
        "Set the description of a product: describe <product> <description>"
        try:
            args = split(arg)
            if len(args) != 2:
                raise Exception(f"Expected 2 arguments, {len(args)} found (did you forget to wrap description in quotes?)")
            
            product_name, description = args
            product = select_product(self.dag_model, product_name)
            product.description = description
            print("Set description.")
        except Exception as e:
            print(f"Error setting description: {e}")
    

    def do_resource(self, arg):
        """Add, delete, or open a resource.
        Usage:
            Show resources: resource show <product>

            Add a resource: resource add <product> <value1> [value2 value3...]
            
            Delete a resource: resource remove <product>
            
            Open a resource: resource open <product>
                -w : When running in WSL, open using windows application
        """

        try:
            args = split(arg)
            subcommand = args[0]
            subargs = args[1:]
            
            match subcommand:
                case "show":
                    product = select_product(self.dag_model, subargs[0], create_missing=False)
                    print(f"Resources associated with {product}: ")
                    print("\n".join(f"\t{i+1}. {res}" for i, res in enumerate(product.resources)))
                case "add":
                    product = select_product(self.dag_model, subargs[0], create_missing=False)
                    product.resources.extend(subargs[1:])
                case "remove":
                    product = select_product(self.dag_model, subargs[0], create_missing=False)

                    match len(product.resources):
                        case 0:
                            raise Exception(f"No resources associated with {product}.")
                        case 1:
                            removed = product.resources[0]
                            product.resources = []
                        case _:
                            i, removed = select_match(product.resources, "Remove which resource?", return_index=True)
                            product.resources.pop(i)
                    
                    print(f"Removed {removed} from {product}.")
                        
                case "open":
                    product = select_product(self.dag_model, subargs[0], create_missing=False)

                    if len(product.resources) == 0:
                        print(f"No resources associated with {product}.")
                        return
                    resource = select_match(product.resources, "Open which resource?")
                    flags = subargs[2:]

                    open_in_windows = False
                    for flag in flags:
                        if flag == "-w":
                            open_in_windows = True
                    
                    if open_in_windows:
                        pass
                    else:
                        webbrowser.open(quote(resource))
                case _:
                    raise Exception(f"Unrecognized subcommand `{subcommand}`.")
        except Exception as e:
            print(f"Error adding/deleting/opening resource: {e}")

    

    def do_target(self, arg):
        'Set the target date of a product (in month/day[/year] format): target <product> <date>'
        try:
            args = arg.split()
            if len(args) < 2:
                print("Please provide a product name and date.")
                return
            
            product, date = args
            product = select_product(self.dag_model, product)

            parsed_date = try_parse_datestr(date)
            if parsed_date is None:
                # maybe date was provided without year
                parsed_date = try_parse_datestr(date, formats=["%m/%d", "%m-%d"])
                parsed_date = parsed_date.replace(year=datetime.today().year)
            if parsed_date is None:
                raise Exception(f"Could not parse {date} as a date.")
            
            product.target = parsed_date
            print(f"Set target date of {args[0]} to {product.target.strftime('%m-%d-%Y')}")

        except Exception as e:
            print(f"Error setting target date: {e}")


    def do_validate(self, arg):
        'Validate the current DAG model, reporting any cycle or date inconsistencies'
        try:
            valid, cycle, dates = validate_DAG(self.dag_model)
            if valid:
                print("No problems found.")
            else:
                print("Issues found in DAG!")
                if cycle is not None:
                    print(f"Cycle: {' -> '.join(cycle)}")
                if len(dates) > 0:
                    sep = "\n\t"
                    print(f"Products with target dates before targets of some predecessor:\n\t{sep.join([str(prod) for prod in dates])}")
        except Exception as e:
            print(f"Error validating DAG: {e}")

    
    def do_gantt(self, arg):
        'Visualize the current DAG model as a Gantt chart: gantt'
        try:
            gantt(dag_model=self.dag_model)
            plt.show()
        except Exception as e:
            print(f"Error visualizing DAG: {e}")


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

    def postcmd(self, stop: bool, line: str) -> bool:
        print()
        return super().postcmd(stop, line)

if __name__ == '__main__':
    LabManagementShell().cmdloop()
