from z3 import *
import sys

def build_z3_expr(circuit, variables, z3_vars, prefix):
    """
    Convert a circuit definition into Z3 expressions with a unique prefix.
    
    :param circuit: Dictionary representing the circuit.
    :param variables: Set to collect all variable names.
    :param z3_vars: Dictionary mapping variable names to Z3 Bool variables.
    :param prefix: String prefix to uniquely identify signals from this circuit.
    :return: Dictionary mapping gate/output names to Z3 expressions.
    """
    expr_map = {}
    gate_names = set()

    print(f"Building expressions for circuit with prefix '{prefix}'")
    print(f"Inputs: {circuit['inputs']}")
    print(f"Gates: {[gate['name'] for gate in circuit['gates']]}")
    print(f"Outputs: {circuit['outputs']}")

    # Initialize input variables (shared between circuits, no prefix)
    for inp in circuit['inputs']:
        variables.add(inp)
        if inp not in z3_vars:
            z3_vars[inp] = Bool(inp)
        expr_map[inp] = z3_vars[inp]
        print(f"Added input {inp} to expr_map")

    # Process gates
    for gate in circuit['gates']:
        gate_name = gate['name']  # No prefix for internal storage
        if gate_name in gate_names:
            raise ValueError(f"Duplicate gate name '{gate_name}' in circuit.")
        gate_names.add(gate_name)

        gate_type = gate['type'].upper()
        gate_inputs = gate['inputs']

        print(f"Processing gate: {gate_name}, type: {gate_type}, inputs: {gate_inputs}")

        # Ensure input signals are already defined
        for sig in gate_inputs:
            if sig not in expr_map:
                raise ValueError(f"Signal '{sig}' used in gate '{gate_name}' is not defined.")
        
        # Create expressions based on gate type
        if gate_type == 'AND':
            expr = And([expr_map[sig] for sig in gate_inputs])
        elif gate_type == 'OR':
            expr = Or([expr_map[sig] for sig in gate_inputs])
        elif gate_type == 'NOT':
            if len(gate_inputs) != 1:
                raise ValueError(f"NOT gate '{gate_name}' must have exactly one input.")
            expr = Not(expr_map[gate_inputs[0]])
        elif gate_type == 'NAND':
            expr = Not(And([expr_map[sig] for sig in gate_inputs]))
        elif gate_type == 'NOR':
            expr = Not(Or([expr_map[sig] for sig in gate_inputs]))
        elif gate_type == 'XOR':
            if len(gate_inputs) != 2:
                raise ValueError(f"XOR gate '{gate_name}' must have exactly two inputs.")
            expr = expr_map[gate_inputs[0]] ^ expr_map[gate_inputs[1]]
        elif gate_type == 'XNOR':
            if len(gate_inputs) != 2:
                raise ValueError(f"XNOR gate '{gate_name}' must have exactly two inputs.")
            expr = Not(expr_map[gate_inputs[0]] ^ expr_map[gate_inputs[1]])
        else:
            raise ValueError(f"Unsupported gate type: {gate_type}")

        expr_map[gate_name] = expr
        variables.add(gate_name)
        print(f"Added gate {gate_name} to expr_map")

    # Map outputs
    output_expr = {}
    for out in circuit['outputs']:
        print(f"Processing output: {out}")
        if out in expr_map:
            output_expr[out] = expr_map[out]
            print(f"Output {out} found in expr_map")
        else:
            print(f"Error: Output {out} not found in expr_map")
            print(f"expr_map keys: {list(expr_map.keys())}")
            raise ValueError(f"Output signal '{out}' is not defined in the circuit.")
    
    return output_expr

def check_circuit_equivalence(circuit1, circuit2):
    """
    Check the equivalence of two circuits.

    :param circuit1: Dictionary representing the first circuit.
    :param circuit2: Dictionary representing the second circuit.
    :return: Tuple (is_equiv, model). is_equiv is True if equivalent, else False.
             model is the counterexample if not equivalent.
    """
    # Collect all variables
    variables = set()
    z3_vars = {}

    # Prefixes to uniquely identify each circuit's internal signals
    prefix1 = "c1_"
    prefix2 = "c2_"

    try:
        # Build expressions for both circuits
        outputs1 = build_z3_expr(circuit1, variables, z3_vars, prefix1)
        outputs2 = build_z3_expr(circuit2, variables, z3_vars, prefix2)
    except ValueError as e:
        print(f"Error in circuit definition: {e}")
        sys.exit(1)

    # Check that both circuits have the same number of outputs
    if len(outputs1) != len(outputs2):
        print("Circuits have different numbers of outputs.")
        return False, None

    # Ensure outputs correspond by order
    output_pairs = list(zip(outputs1.keys(), outputs2.keys()))
    
    # Initialize Z3 solver
    solver = Solver()

    # Assert both circuits have outputs that differ in at least one output
    diff_constraints = []
    for (out1, out2) in output_pairs:
        diff_constraints.append(outputs1[out1] != outputs2[out2])
    
    # Combine all difference constraints with OR
    solver.add(Or(diff_constraints))

    # Check satisfiability
    if solver.check() == sat:
        model = solver.model()
        # Extract input assignments only
        input_assignment = {}
        for var in circuit1['inputs']:
            if var in z3_vars:
                input_assignment[var] = is_true(model.evaluate(z3_vars[var], model_completion=True))

        # Include output differences
        differing_outputs = []
        for (out1, out2) in output_pairs:
            val1 = model.evaluate(outputs1[out1], model_completion=True)
            val2 = model.evaluate(outputs2[out2], model_completion=True)
            if is_true(val1) != is_true(val2):
                differing_outputs.append((out1, out2, is_true(val1), is_true(val2)))

        return False, (input_assignment, differing_outputs)
    else:
        return True, None

def main():
    """
    Main function to demonstrate circuit equivalence checking.
    """
    # Define Circuit 1
    # Example: Circuit1 computes E = (A AND B) OR C
    circuit1 = {
        'inputs': ['A', 'B', 'C'],
        'gates': [
            {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
            {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']}
        ],
        'outputs': ['E']
    }

    # Define Circuit 2
    # Example: Circuit2 computes E = (A OR C) AND (B OR C)
    # This is equivalent to Circuit1 via distributive law: (A AND B) OR C = (A OR C) AND (B OR C)
    circuit2 = {
        'inputs': ['A', 'B', 'C'],
        'gates': [
            {'name': 'F', 'type': 'OR', 'inputs': ['A', 'C']},
            {'name': 'G', 'type': 'OR', 'inputs': ['B', 'C']},
            {'name': 'E', 'type': 'AND', 'inputs': ['F', 'G']}
        ],
        'outputs': ['E']
    }

    # Alternatively, define non-equivalent circuits for testing
    # Uncomment below to test non-equivalence
    '''
    circuit2 = {
        'inputs': ['A', 'B', 'C'],
        'gates': [
            {'name': 'F', 'type': 'OR', 'inputs': ['A', 'C']},
            {'name': 'G', 'type': 'OR', 'inputs': ['B', 'C']},
            {'name': 'E', 'type': 'OR', 'inputs': ['F', 'G']}  # Changed from AND to OR
        ],
        'outputs': ['E']
    }
    '''

    # Check equivalence
    is_equiv, result = check_circuit_equivalence(circuit1, circuit2)

    if is_equiv:
        print("The circuits are equivalent.")
    else:
        print("The circuits are NOT equivalent.")
        if result:
            assignment, diffs = result
            print("\nCounterexample where circuits differ:")
            # Display input assignments only
            input_vars = circuit1['inputs']
            for var in input_vars:
                print(f"  {var} = {assignment[var]}")
            print("\nDiffering Outputs:")
            for (out1, out2, val1, val2) in diffs:
                print(f"  {out1} = {val1} vs {out2} = {val2}")

if __name__ == "__main__":
    main()