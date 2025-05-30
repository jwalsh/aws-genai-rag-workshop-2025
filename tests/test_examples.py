# tests/test_examples.py

import unittest
from unittest.mock import patch
import io

from src.examples import hello_world

class TestExamples(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hello_world_output(self, mock_stdout):
        # Call the function that prints to stdout
        message = hello_world.greet("TestUser")
        
        # Check the printed output
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello, TestUser! Your Python environment is working.")
        
        # Check the returned message
        self.assertEqual(message, "Hello, TestUser! Your Python environment is working.")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_hello_world_default_output(self, mock_stdout):
        # Call the function with default argument
        message = hello_world.greet()
        
        # Check the printed output
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello, World! Your Python environment is working.")
        
        # Check the returned message
        self.assertEqual(message, "Hello, World! Your Python environment is working.")

if __name__ == '__main__':
    unittest.main()
