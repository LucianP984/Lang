"""
Token type definitions for the lexer.
"""
from enum import Enum, auto

class TokenType(Enum):
    """Enum representing the different types of tokens in the language"""
    # Single-character tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SLASH = auto()
    STAR = auto()
    COLON = auto()

    # One or two character tokens
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    MODULO = auto()
    EXPODENT = auto() 

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    AND = auto()
    ELSE = auto()
    FALSE = auto()
    FUNCTION = auto()
    IF = auto()
    INPUT = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    TRUE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()

    #Class Token
    CLASS = auto()
    SUPER = auto()
    THIS = auto()
    NEW=auto()

    # End of file
    EOF = auto()

class Token:
    """Class representing a token in the language"""
    def __init__(self, token_type, lexeme, literal=None, line=1):
        self.type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __str__(self):
        if self.literal is not None:
            return f"{self.type}: '{self.lexeme}' {self.literal}"
        return f"{self.type}: '{self.lexeme}'"