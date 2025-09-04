
"""
Main entry point for the programming language interpreter.
Reads source code from file and interprets it.
"""
import sys
import os
from lexer.lexer import Lexer
from parser.parser import Parser
from interpreter.interpreter import Interpreter


def run_file(path):
    """Execute code from a file"""
    try:
        with open(path, 'r') as file:
            source = file.read()
        run(source)
    except FileNotFoundError:
        print(f"Error: Could not find file '{path}'")
        sys.exit(1)

def run(source):
    """Execute code from a string"""
    # Lexical analysis - convert source to tokens
    lexer = Lexer(source)
    tokens = lexer.scan_tokens()

    # Parsing - convert tokens to AST
    parser = Parser(tokens)
    statements = parser.parse()

    # If parsing failed, exit
    if not statements:
        return

    # Interpretation - execute the AST
    interpreter = Interpreter()
    interpreter.interpret(statements)

def main():
    """Main function that handles command line arguments"""
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        print("Usage: python main.py <source_file>")
        sys.exit(1)

if __name__ == "__main__":
    main()