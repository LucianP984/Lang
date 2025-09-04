"""
Lexical analyzer (scanner/tokenizer) for the language.
Converts source code into tokens.
"""
from .token_types import TokenType, Token

class Lexer:
    """Lexical analyzer that converts source code to tokens."""

    def __init__(self, source):
        self.source = source
        self.tokens = []
        self.start = 0
        self.current = 0
        self.line = 1

        # Map keywords to their token types
        self.keywords = {
            "and": TokenType.AND,
            "else": TokenType.ELSE,
            "false": TokenType.FALSE,
            "function": TokenType.FUNCTION,
            "if": TokenType.IF,
            "input": TokenType.INPUT,
            "or": TokenType.OR,
            "print": TokenType.PRINT,
            "return": TokenType.RETURN,
            "true": TokenType.TRUE,
            "while": TokenType.WHILE,
            "for" : TokenType.FOR,
            "in" :TokenType.IN,
            "class": TokenType.CLASS,
            "this": TokenType.THIS,
            "super": TokenType.SUPER,
            "new": TokenType.NEW
        }

    def scan_tokens(self):
        """Scan the source code and produce a list of tokens."""
        while not self.is_at_end():
            
            self.start = self.current
            self.scan_token()

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))
        return self.tokens

    def is_at_end(self):
        """Check if we've reached the end of the source code."""
        return self.current >= len(self.source)

    def scan_token(self):
        """Scan a single token."""
        c = self.advance()

        # Single-character tokens
        if c == '(': self.add_token(TokenType.LEFT_PAREN)
        elif c == ')': self.add_token(TokenType.RIGHT_PAREN)
        elif c == '{': self.add_token(TokenType.LEFT_BRACE)
        elif c == '}': self.add_token(TokenType.RIGHT_BRACE)
        elif c == '[': self.add_token(TokenType.LEFT_BRACKET)
        elif c == ']': self.add_token(TokenType.RIGHT_BRACKET)
        elif c == ',': self.add_token(TokenType.COMMA)
        elif c == '.': self.add_token(TokenType.DOT)
        elif c == '-': self.add_token(TokenType.MINUS)
        elif c == '+': self.add_token(TokenType.PLUS)
        elif c == ':': self.add_token(TokenType.COLON)
        elif c == '*': self.add_token(TokenType.STAR)
        elif c == '%': self.add_token(TokenType.MODULO)
        elif c == '^': self.add_token(TokenType.EXPODENT)
        

        
        elif c == '!': self.add_token(TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG)
        elif c == '=': self.add_token(TokenType.EQUAL_EQUAL if self.match('=') else TokenType.EQUAL)
        elif c == '<': self.add_token(TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS)
        elif c == '>': self.add_token(TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER)

        # Division or comment
        elif c == '/':
            if self.match('/'):
                # Comment goes until the end of line
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.SLASH)

        # Whitespace (ignore)
        elif c in [' ', '\r', '\t']:
            pass

        # Newline
        elif c == '\n':
            self.line += 1

        # String literals
        elif c == '"':
            self.string()

        # Number literals
        elif self.is_digit(c):
            self.number()

        # Identifiers and keywords
        elif self.is_alpha(c):
            self.identifier()

        # Unexpected character
        else:
            self.error(f"Unexpected character: '{c}'")

    def error(self, message):
        """Report an error at the current position."""
        print(f"Error (line {self.line}): {message}")

    def advance(self):
        """Consume the next character and return it."""
        char = self.source[self.current]
        self.current += 1
        return char

    def match(self, expected):
        """Check if the current character matches the expected one."""
        if self.is_at_end() or self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def peek(self):
        """Look at the current character without consuming it."""
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self):
        """Look at the next character without consuming it."""
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def string(self):
        """Process a string literal."""
        # Keep consuming until we find the closing quote
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        # Unterminated string
        if self.is_at_end():
            self.error("Unterminated string.")
            return

        # Consume the closing quote
        self.advance()

        # Extract the string value (without quotes)
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def number(self):
        """Process a number literal."""
        # Consume all digits
        while self.is_digit(self.peek()):
            self.advance()

        # Look for a decimal part
        if self.peek() == '.' and self.is_digit(self.peek_next()):
            # Consume the '.'
            self.advance()

            # Consume the fractional part
            while self.is_digit(self.peek()):
                self.advance()

        # Parse the number
        value = float(self.source[self.start:self.current])
        # Convert to integer if it's a whole number
        if value.is_integer():
            value = int(value)
        self.add_token(TokenType.NUMBER, value)

    def identifier(self):
        """Process an identifier or keyword."""
        # Consume all alphanumeric characters
        while self.is_alphanumeric(self.peek()):
            self.advance()

        # Get the lexeme
        text = self.source[self.start:self.current]

        # Check if it's a keyword
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)

        # Add the token
        if token_type == TokenType.TRUE:
            self.add_token(token_type, True)
        elif token_type == TokenType.FALSE:
            self.add_token(token_type, False)
        else:
            self.add_token(token_type)

    def is_digit(self, c):
        """Check if a character is a digit."""
        return '0' <= c <= '9'

    def is_alpha(self, c):
        """Check if a character is alphabetic."""
        return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '_'

    def is_alphanumeric(self, c):
        """Check if a character is alphanumeric."""
        return self.is_alpha(c) or self.is_digit(c)

    def add_token(self, token_type, literal=None):
        """Add a token to the list."""
        text = self.source[self.start:self.current]
        self.tokens.append(Token(token_type, text, literal, self.line))