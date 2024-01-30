from src.dag_model import CycleError

def validate_DAG(dag_model):  
    """Validates that a DAGModel
        (1) contains no cycles, and
        (2) does not have any products with target dates before those of their prerequisites.

    Args:
        dag_model (DAGModel): the DAGModel to validate.

    Returns:
        valid (bool): whether the DAGModel is valid.
        cycle (list or None): products involved in a cycle if any, else None.
        invalid_dates (list): products whose target dates are before that of some prerequisite.
    """    

    cycle = None
    invalid_dates = []

    # Check for cycle
    try:
        _ = dag_model.order
    except CycleError as e:
        cycle = e.args[1]
    
    # Check for target date consistency
    for product in dag_model.products:
        if product.target is None:
            continue

        max_prereq_date = None
        for pre in dag_model.all_prerequisites(product):
            if pre.target is None:
                continue

            if max_prereq_date is None or max_prereq_date < pre.target:
                max_prereq_date = pre.target

        if max_prereq_date is not None and product.target < max_prereq_date:
            invalid_dates.append(product)
    
    valid = (cycle is None) and (len(invalid_dates) == 0)
    return valid, cycle, invalid_dates
