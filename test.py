import unittest
import sys
from z3 import *
from circuit_equivalence import check_circuit_equivalence

class TestCircuitEquivalence(unittest.TestCase):
    def test_equivalent_circuits(self):
        """
        Test two circuits that are logically equivalent.
        Circuit1: E = (A AND B) OR C
        Circuit2: E = (A OR C) AND (B OR C)
        """
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
        self.assertTrue(is_equiv, "Equivalent circuits were not recognized as equivalent.")

    def test_non_equivalent_circuits(self):
        """
        Test two circuits that are not logically equivalent.
        Circuit1: E = (A AND B) OR C
        Circuit2: E = (A OR C) OR (B OR C)  # Changed AND to OR
        """
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
                {'name': 'E', 'type': 'OR', 'inputs': ['F', 'G']}  # Changed to OR
            ],
            'outputs': ['E']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertFalse(is_equiv, "Non-equivalent circuits were not recognized as non-equivalent.")
        self.assertIsNotNone(result, "Counterexample was not provided for non-equivalent circuits.")

        # Verify that the counterexample causes the outputs to differ
        assignment, diffs = result
        # Ensure that there is at least one differing output
        self.assertTrue(len(diffs) > 0, "No differing outputs found in counterexample.")
        # Optionally, check that the assignment indeed causes the outputs to differ
        # This would require re-evaluating the circuits with the assignment, which is beyond this scope

    def test_multiple_outputs_equivalent(self):
        """
        Test two circuits with multiple outputs that are equivalent.
        Circuit1: E = (A AND B) OR C, F = A OR B
        Circuit2: E = (A OR C) AND (B OR C), F = A OR B
        """
        circuit1 = {
            'inputs': ['A', 'B', 'C'],
            'gates': [
                {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']},
                {'name': 'F', 'type': 'OR', 'inputs': ['A', 'B']}
            ],
            'outputs': ['E', 'F']
        }

        circuit2 = {
            'inputs': ['A', 'B', 'C'],
            'gates': [
                {'name': 'F', 'type': 'OR', 'inputs': ['A', 'B']},
                {'name': 'G', 'type': 'OR', 'inputs': ['A', 'C']},
                {'name': 'H', 'type': 'OR', 'inputs': ['B', 'C']},
                {'name': 'E', 'type': 'AND', 'inputs': ['G', 'H']}
            ],
            'outputs': ['E', 'F']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertTrue(is_equiv, "Equivalent circuits with multiple outputs were not recognized as equivalent.")

    def test_multiple_outputs_non_equivalent(self):
        """
        Test two circuits with multiple outputs that are not equivalent.
        Circuit1: E = (A AND B) OR C, F = A OR B
        Circuit2: E = (A OR C) AND (B OR C), F = A AND B  # Changed F to AND
        """
        circuit1 = {
            'inputs': ['A', 'B', 'C'],
            'gates': [
                {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'E', 'type': 'OR', 'inputs': ['D', 'C']},
                {'name': 'F', 'type': 'OR', 'inputs': ['A', 'B']}
            ],
            'outputs': ['E', 'F']
        }

        circuit2 = {
            'inputs': ['A', 'B', 'C'],
            'gates': [
                {'name': 'F', 'type': 'AND', 'inputs': ['A', 'B']},  # Changed to AND
                {'name': 'G', 'type': 'OR', 'inputs': ['A', 'C']},
                {'name': 'H', 'type': 'OR', 'inputs': ['B', 'C']},
                {'name': 'E', 'type': 'AND', 'inputs': ['G', 'H']}
            ],
            'outputs': ['E', 'F']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertFalse(is_equiv, "Non-equivalent circuits with multiple outputs were not recognized as non-equivalent.")
        self.assertIsNotNone(result, "Counterexample was not provided for non-equivalent circuits with multiple outputs.")

        # Ensure that at least one output differs
        assignment, diffs = result
        self.assertTrue(len(diffs) > 0, "No differing outputs found in counterexample for multiple outputs.")

    def test_undefined_gate_input(self):
        """
        Test a circuit where a gate references an undefined signal.
        Circuit1: Properly defined.
        Circuit2: Gate 'E' references undefined signal 'Z'.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'D', 'type': 'OR', 'inputs': ['C', 'A']}
            ],
            'outputs': ['D']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'E', 'type': 'OR', 'inputs': ['C', 'Z']}  # 'Z' is undefined
            ],
            'outputs': ['E']
        }

        with self.assertRaises(SystemExit) as cm:
            check_circuit_equivalence(circuit1, circuit2)
        self.assertNotEqual(cm.exception.code, 0, "Script did not exit on undefined gate input.")

    def test_unsupported_gate_type(self):
        """
        Test a circuit with an unsupported gate type.
        Circuit1: Properly defined.
        Circuit2: Gate 'E' uses an unsupported 'BUFF' gate type.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'D', 'type': 'OR', 'inputs': ['C', 'A']}
            ],
            'outputs': ['D']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'E', 'type': 'BUFF', 'inputs': ['C']}  # Unsupported gate type 'BUFF'
            ],
            'outputs': ['E']
        }

        with self.assertRaises(SystemExit) as cm:
            check_circuit_equivalence(circuit1, circuit2)
        self.assertNotEqual(cm.exception.code, 0, "Script did not exit on unsupported gate type.")

    def test_invalid_not_gate(self):
        """
        Test a circuit with a NOT gate that has multiple inputs.
        Circuit1: Properly defined.
        Circuit2: NOT gate 'E' has two inputs.
        """
        circuit1 = {
            'inputs': ['A'],
            'gates': [
                {'name': 'B', 'type': 'NOT', 'inputs': ['A']}
            ],
            'outputs': ['B']
        }

        circuit2 = {
            'inputs': ['A'],
            'gates': [
                {'name': 'C', 'type': 'NOT', 'inputs': ['A', 'B']}  # NOT gate with two inputs
            ],
            'outputs': ['C']
        }

        with self.assertRaises(SystemExit) as cm:
            check_circuit_equivalence(circuit1, circuit2)
        self.assertNotEqual(cm.exception.code, 0, "Script did not exit on invalid NOT gate definition.")

    def test_no_gates(self):
        """
        Test two circuits with only inputs and no gates.
        Circuit1 and Circuit2: Outputs are direct inputs.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [],
            'outputs': ['A', 'B']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [],
            'outputs': ['A', 'B']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertTrue(is_equiv, "Circuits with only inputs were not recognized as equivalent.")

    def test_different_number_of_outputs(self):
        """
        Test two circuits with a different number of outputs.
        Circuit1: One output.
        Circuit2: Two outputs.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']}
            ],
            'outputs': ['C']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'D', 'type': 'OR', 'inputs': ['A', 'B']}
            ],
            'outputs': ['C', 'D']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertFalse(is_equiv, "Circuits with different numbers of outputs were not recognized as non-equivalent.")
        self.assertIsNone(result, "Unexpected counterexample for circuits with different number of outputs.")

    def test_duplicate_gate_names_in_same_circuit(self):
        """
        Test a circuit where two gates have the same name.
        Circuit1: Duplicate gate names.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'C', 'type': 'OR', 'inputs': ['A', 'B']}  # Duplicate gate name 'C'
            ],
            'outputs': ['C']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'D', 'type': 'AND', 'inputs': ['A', 'B']}
            ],
            'outputs': ['D']
        }

        with self.assertRaises(SystemExit) as cm:
            check_circuit_equivalence(circuit1, circuit2)
        self.assertNotEqual(cm.exception.code, 0, "Script did not exit on duplicate gate names.")

    def test_large_equivalent_circuits(self):
        """
        Test two large, complex circuits that are equivalent.
        """
        # Define a more complex equivalent circuit
        circuit1 = {
            'inputs': ['A', 'B', 'C', 'D'],
            'gates': [
                {'name': 'E', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'F', 'type': 'OR', 'inputs': ['C', 'D']},
                {'name': 'G', 'type': 'NOT', 'inputs': ['E']},
                {'name': 'H', 'type': 'AND', 'inputs': ['G', 'F']}
            ],
            'outputs': ['H']
        }

        circuit2 = {
            'inputs': ['A', 'B', 'C', 'D'],
            'gates': [
                {'name': 'E', 'type': 'OR', 'inputs': ['C', 'D']},
                {'name': 'F', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'G', 'type': 'NOT', 'inputs': ['F']},
                {'name': 'H', 'type': 'AND', 'inputs': ['G', 'E']}
            ],
            'outputs': ['H']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertTrue(is_equiv, "Large equivalent circuits were not recognized as equivalent.")

    def test_large_non_equivalent_circuits(self):
        """
        Test two large, complex circuits that are not equivalent.
        """
        # Define two complex non-equivalent circuits
        circuit1 = {
            'inputs': ['A', 'B', 'C', 'D'],
            'gates': [
                {'name': 'E', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'F', 'type': 'OR', 'inputs': ['C', 'D']},
                {'name': 'G', 'type': 'NOT', 'inputs': ['E']},
                {'name': 'H', 'type': 'AND', 'inputs': ['G', 'F']},
                {'name': 'I', 'type': 'OR', 'inputs': ['H', 'A']}
            ],
            'outputs': ['I']
        }

        circuit2 = {
            'inputs': ['A', 'B', 'C', 'D'],
            'gates': [
                {'name': 'E', 'type': 'OR', 'inputs': ['C', 'D']},
                {'name': 'F', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'G', 'type': 'NOT', 'inputs': ['F']},
                {'name': 'H', 'type': 'AND', 'inputs': ['G', 'E']},
                {'name': 'I', 'type': 'AND', 'inputs': ['H', 'A']}  # Changed to AND
            ],
            'outputs': ['I']
        }

        is_equiv, result = check_circuit_equivalence(circuit1, circuit2)
        self.assertFalse(is_equiv, "Large non-equivalent circuits were not recognized as non-equivalent.")
        self.assertIsNotNone(result, "Counterexample was not provided for large non-equivalent circuits.")

    def test_invalid_gate_input_signal(self):
        """
        Test a circuit where a gate's input is not defined.
        Circuit1: Properly defined.
        Circuit2: Gate 'E' has an undefined input 'Z'.
        """
        circuit1 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'D', 'type': 'OR', 'inputs': ['C', 'A']}
            ],
            'outputs': ['D']
        }

        circuit2 = {
            'inputs': ['A', 'B'],
            'gates': [
                {'name': 'C', 'type': 'AND', 'inputs': ['A', 'B']},
                {'name': 'E', 'type': 'OR', 'inputs': ['C', 'Z']}  # 'Z' is undefined
            ],
            'outputs': ['E']
        }

        with self.assertRaises(SystemExit) as cm:
            check_circuit_equivalence(circuit1, circuit2)
        self.assertNotEqual(cm.exception.code, 0, "Script did not exit on undefined gate input signal.")

if __name__ == '__main__':
    unittest.main()