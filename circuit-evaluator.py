# circuit_validator.py

from z3 import *
import sys

def build_z3_expr(circuit, z3_vars):
    """
    Convert a circuit definition into Z3 expressions with variables for all signals.
    
    :param circuit: Dictionary representing the circuit.
    :param z3_vars: Dictionary mapping variable names to Z3 Bool variables.
    :return: Tuple containing:
             - Dictionary mapping gate/output names to Z3 expressions.
             - List of Z3 constraints defining gate operations.
    """
    expr_map = {}
    gate_names = set()
    constraints = []

    print(f"Building expressions for the circuit.")
    print(f"Inputs: {circuit['inputs']}")
    print(f"Gates: {[gate['name'] for gate in circuit['gates']]}")
    print(f"Outputs: {circuit['outputs']}")

    # Initialize input variables
    for inp in circuit['inputs']:
        if inp not in z3_vars:
            z3_vars[inp] = Bool(inp)
        expr_map[inp] = z3_vars[inp]
        print(f"Added input {inp} to expr_map")

    # Process gates
    for gate in circuit['gates']:
        gate_name = gate['name']
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

        # Create a new Z3 variable for the gate's output
        if gate_name not in z3_vars:
            z3_vars[gate_name] = Bool(gate_name)
        gate_output = z3_vars[gate_name]

        # Create expressions based on gate type and add constraints
        if gate_type == 'AND':
            constraint = gate_output == And([expr_map[sig] for sig in gate_inputs])
        elif gate_type == 'OR':
            constraint = gate_output == Or([expr_map[sig] for sig in gate_inputs])
        elif gate_type == 'NOT':
            if len(gate_inputs) != 1:
                raise ValueError(f"NOT gate '{gate_name}' must have exactly one input.")
            constraint = gate_output == Not(expr_map[gate_inputs[0]])
        elif gate_type == 'NAND':
            constraint = gate_output == Not(And([expr_map[sig] for sig in gate_inputs]))
        elif gate_type == 'NOR':
            constraint = gate_output == Not(Or([expr_map[sig] for sig in gate_inputs]))
        elif gate_type == 'XOR':
            if len(gate_inputs) != 2:
                raise ValueError(f"XOR gate '{gate_name}' must have exactly two inputs.")
            constraint = gate_output == (expr_map[gate_inputs[0]] ^ expr_map[gate_inputs[1]])
        elif gate_type == 'XNOR':
            if len(gate_inputs) != 2:
                raise ValueError(f"XNOR gate '{gate_name}' must have exactly two inputs.")
            constraint = gate_output == Not(expr_map[gate_inputs[0]] ^ expr_map[gate_inputs[1]])
        else:
            raise ValueError(f"Unsupported gate type: {gate_type}")

        # Add the constraint to the list
        constraints.append(constraint)
        expr_map[gate_name] = gate_output
        print(f"Added gate {gate_name} to expr_map with constraint {constraint}")

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

    return output_expr, constraints

def validate_circuit(circuit, input_assignments, signal_assignments=None):
    """
    Validate the circuit with given input and signal assignments and compute outputs if valid.
    
    :param circuit: Dictionary representing the circuit.
    :param input_assignments: Dictionary mapping input names to Boolean values.
    :param signal_assignments: Dictionary mapping internal signal names to Boolean values.
    :return: Tuple (is_valid, outputs or contradiction message)
    """
    # Initialize Z3 variables
    z3_vars = {}
    try:
        outputs, constraints = build_z3_expr(circuit, z3_vars)
    except ValueError as e:
        print(f"Error in circuit definition: {e}")
        return False, str(e)  # Return the error message instead of exiting

    # Debug: Print all keys in z3_vars to verify signal definitions
    print("\nCurrent Signals in z3_vars:", list(z3_vars.keys()))

    # Initialize Z3 solver
    solver = Solver()

    # Apply gate constraints
    print("\nApplying gate constraints:")
    for constraint in constraints:
        solver.add(constraint)
        print(f"  {constraint}")

    # Apply input assignments as constraints
    print("\nApplying input assignments:")
    for inp, val in input_assignments.items():
        if inp not in circuit['inputs']:
            print(f"Error: Input '{inp}' is not defined in the circuit.")
            return False, f"Input '{inp}' is not defined in the circuit."
        constraint = z3_vars[inp] if val else Not(z3_vars[inp])
        solver.add(constraint)
        print(f"  {inp} = {val}")

    # Apply signal assignments as constraints
    if signal_assignments:
        print("\nApplying signal assignments:")
        for sig, val in signal_assignments.items():
            if sig not in z3_vars:
                print(f"Error: Signal '{sig}' is not defined in the circuit.")
                return False, f"Signal '{sig}' is not defined in the circuit."
            constraint = z3_vars[sig] if val else Not(z3_vars[sig])
            solver.add(constraint)
            print(f"  {sig} = {val}")

    # Check for contradictions
    if solver.check() == sat:
        model = solver.model()
        # Extract output values
        output_values = {}
        for out in circuit['outputs']:
            output_val = model.evaluate(outputs[out], model_completion=True)
            output_values[out] = is_true(output_val)
        return True, output_values
    else:
        return False, "Contradiction detected: The input or signal assignments lead to an unsatisfiable circuit."

def main():
    """
    Main function to demonstrate circuit validation.
    """
    # Example Circuit: E = (A AND B) OR C
    circuit = {
        'inputs': ['A', 'B', 'C'],
        'gates': [
            {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
            {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']}
        ],
        'outputs': ['E']
    }

    # Test Case 1: Valid Inputs
    input_assignments_1 = {'A': True, 'B': True, 'C': False}
    print("\n=== Test Case 1: Valid Inputs ===")
    is_valid, result = validate_circuit(circuit, input_assignments_1)
    print("The input assignments are valid." if is_valid else f"Validation failed: {result}")
    if is_valid:
        print(f"Outputs: {result}")

    # Test Case 2: Contradictory Assignments to Internal Signals
    contradictory_circuit = {
        'inputs': ['A', 'B'],
        'gates': [
            {'name': 'E1', 'type': 'AND', 'inputs': ['A', 'B']},
            {'name': 'E2', 'type': 'NOT', 'inputs': ['A']},
            {'name': 'E', 'type': 'AND', 'inputs': ['E1', 'E2']}
        ],
        'outputs': ['E']
    }
    input_assignments_2 = {'A': True, 'B': True}
    signal_assignments_2 = {'E2': True}
    print("\n=== Test Case 2: Contradictory Assignments to Internal Signals ===")
    is_valid, result = validate_circuit(contradictory_circuit, input_assignments_2, signal_assignments_2)
    print("The input and signal assignments are valid." if is_valid else f"Validation failed: {result}")
    if is_valid:
        print(f"Outputs: {result}")

    # Test Case 3: Another Valid Circuit
    circuit2 = {
        'inputs': ['A', 'B', 'C'],
        'gates': [
            {'name': 'XOR1', 'type': 'XOR', 'inputs': ['A', 'B']},
            {'name': 'NOT1', 'type': 'NOT', 'inputs': ['C']},
            {'name': 'F', 'type': 'AND', 'inputs': ['XOR1', 'NOT1']}
        ],
        'outputs': ['F']
    }
    input_assignments_3 = {'A': True, 'B': False, 'C': False}
    print("\n=== Test Case 3: Another Valid Circuit ===")
    is_valid, result = validate_circuit(circuit2, input_assignments_3)
    print("The input assignments are valid." if is_valid else f"Validation failed: {result}")
    if is_valid:
        print(f"Outputs: {result}")

    # Test Case 4: All Valid Inputs
    input_assignments_4 = {'A': True, 'B': True, 'C': False}
    print("\n=== Test Case 4: All Valid Inputs ===")
    is_valid, result = validate_circuit(circuit, input_assignments_4)
    print("The input assignments are valid." if is_valid else f"Validation failed: {result}")
    if is_valid:
        print(f"Outputs: {result}")

if __name__ == "__main__":
    main()