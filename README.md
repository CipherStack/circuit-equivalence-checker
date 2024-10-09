# Circuit Equivalence Checker

## Overview

The Circuit Equivalence Checker is a powerful Python tool designed to verify the logical equivalence of digital circuits. It uses the Z3 theorem prover to determine whether two given circuit descriptions produce identical outputs for all possible input combinations.

## Features

- Supports various logic gates: AND, OR, NOT, NAND, NOR, XOR, XNOR
- Handles circuits with multiple inputs and outputs
- Provides detailed counterexamples for non-equivalent circuits
- Robust error handling for invalid circuit descriptions
- Comprehensive unit tests to ensure reliability
- Circuit validation functionality

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/CipherStack/circuit-equivalence-checker.git
   cd circuit-equivalence-checker
   ```

2. Install the required dependencies:
   ```
   pip3 install z3-solver
   ```

## Usage

### Circuit Equivalence Checker

You can use the `check_circuit_equivalence` function in your Python scripts:

```python
from circuit_equivalence import check_circuit_equivalence

circuit1 = {
    'inputs': ['A', 'B', 'C'],
    'gates': [
        {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
        {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']}
    ],
    'outputs': ['E']
}

circuit2 = {
    'inputs': ['A', 'B', 'C'],
    'gates': [
        {'name': 'F', 'type': 'OR', 'inputs': ['A', 'C']},
        {'name': 'G', 'type': 'OR', 'inputs': ['B', 'C']},
        {'name': 'E', 'type': 'AND', 'inputs': ['F', 'G']}
    ],
    'outputs': ['E']
}

is_equiv, result = check_circuit_equivalence(circuit1, circuit2)

if is_equiv:
    print("The circuits are equivalent.")
else:
    print("The circuits are NOT equivalent.")
    if result:
        assignment, diffs = result
        print("Counterexample:", assignment)
        print("Differing outputs:", diffs)
```

### Circuit Validator

You can use the `validate_circuit` function to validate a circuit with given input assignments:

```python
from circuit_validator import validate_circuit

circuit = {
    'inputs': ['A', 'B', 'C'],
    'gates': [
        {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
        {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']}
    ],
    'outputs': ['E']
}

input_assignments = {'A': True, 'B': True, 'C': False}
is_valid, result = validate_circuit(circuit, input_assignments)

if is_valid:
    print("The input assignments are valid.")
    print(f"Outputs: {result}")
else:
    print(f"Validation failed: {result}")
```

### As Standalone Scripts

Run the scripts directly to see demonstrations:

```
python circuit_equivalence.py
python circuit_validator.py
```

## Testing

To run the unit tests:

```
python test_evaluator.py
```

## How It Works

1. The tool converts circuit descriptions into Z3 expressions.
2. For equivalence checking, it uses Z3 to check if there exists any input combination that produces different outputs for the two circuits.
3. For circuit validation, it applies the given input assignments and checks for consistency and computes outputs.
4. If a difference or contradiction is found, a counterexample or error message is provided.
5. If no such combination exists, the circuits are deemed equivalent or the validation is successful.

## Circuit Description Format

Circuits are described using Python dictionaries with the following structure:

```python
{
    'inputs': ['A', 'B', 'C', ...],
    'gates': [
        {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
        {'name': 'E', 'type': 'OR', 'inputs': ['C', 'D']},
        ...
    ],
    'outputs': ['E', ...]
}
```

## Limitations

- The tool assumes that the circuit descriptions are acyclic (no feedback loops).
- Large circuits may require significant computational resources.

## Acknowledgments

- The Z3 theorem prover team for their excellent SMT solver