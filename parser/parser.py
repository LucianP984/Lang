"""
Parser for the language. 
Converts tokens into an Abstract Syntax Tree (AST).
"""
from .ast import (Binary, Unary, Literal, Grouping, Variable, Assign, Call, Get,Set,
                 Index, List, Dictionary, ExpressionStmt, PrintStmt, ReturnStmt,
                 FunctionStmt, IfStmt, WhileStmt, BlockStmt, InputStmt,IndexAssign,Logical,Class,This,Super,New,ForEach)
from lexer.token_types import TokenType

class ParseError(Exception):
    """Exception raised when a parsing error occurs."""
    pass

class Parser:
    """Parser for the language."""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        """Parse a list of tokens into an AST."""
        statements = []
        while not self.is_at_end():
            statements.append(self.declaration())
        
        return statements
    
    # --- Statement parsing ---
    
    def declaration(self):
        """Parse a declaration."""
        try:
            if self.match(TokenType.FUNCTION):
                return self.function_declaration("function")
            if self.match(TokenType.CLASS):
                return self.class_declaration()
                
            return self.statement()
        except ParseError:
            self.synchronize()
            return None
    
    def function_declaration(self, kind):
        """Parse a function declaration."""
        name = self.consume(TokenType.IDENTIFIER, f"Expect {kind} name.")

        self.consume(TokenType.LEFT_PAREN, f"Expect '(' after {kind} name.")
        parameters = []

        if not self.check(TokenType.RIGHT_PAREN):
            # Parse parameters
            parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))

            while self.match(TokenType.COMMA):
                if len(parameters) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 parameters.")

                parameters.append(self.consume(TokenType.IDENTIFIER, "Expect parameter name."))

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after parameters.")

        # Parse function body
        self.consume(TokenType.LEFT_BRACE, f"Expect '{{' before {kind} body.")
        body = self.block()

        return FunctionStmt(name, parameters, body)
    
    def class_declaration(self):
        """Parse a class declaration."""
        name = self.consume(TokenType.IDENTIFIER, "Expect class name.")

        # Handle inheritance
        superclass = None
        if self.match(TokenType.LESS):
            self.consume(TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = Variable(self.previous())

        self.consume(TokenType.LEFT_BRACE, "Expect '{' before class body.")

        methods = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self.function_declaration("method"))

        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after class body.")

        return Class(name, superclass, methods)
        
    def statement(self):
        """Parse a statement."""
        if self.match(TokenType.IF):
            return self.if_statement()
        
        if self.match(TokenType.RETURN):
            return self.return_statement()
        
        if self.match(TokenType.WHILE):
            return self.while_statement()
        
        if self.match(TokenType.LEFT_BRACE):
            return BlockStmt(self.block())
        
        if self.match(TokenType.PRINT):
            return self.print_statement()
        
        if self.match(TokenType.INPUT):
            return self.input_statement()
        if self.match(TokenType.FOR):
            return self.for_statement()
        if self.match(TokenType.CLASS):
            return self.class_declaration()
        
        return self.expression_statement()
    
    def if_statement(self):
        """Parse an if statement."""
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")
        
        then_branch = self.statement()
        else_branch = None
        
        if self.match(TokenType.ELSE):
            else_branch = self.statement()
        
        return IfStmt(condition, then_branch, else_branch)
    
    def return_statement(self):
        """Parse a return statement."""
        keyword = self.previous()
        
        value = None
        if not self.check(TokenType.RIGHT_BRACE):
            value = self.expression()
        
        return ReturnStmt(keyword, value)
    
    def while_statement(self):
        """Parse a while statement."""
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after condition.")
        
        body = self.statement()
        
        return WhileStmt(condition, body)
    
    def for_statement(self):
        """Parse a for-each loop."""
        # Parse: for (var in iterable) { body }
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        # Get variable
        var_name = self.consume(TokenType.IDENTIFIER, "Expect variable name.")

        # Expect 'in'
        self.consume(TokenType.IN, "Expect 'in' after variable name.")

        # Get iterable expression
        iterable = self.expression()

        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for loop header.")

        # Get body
        body = self.statement()

        return ForEach(var_name, iterable, body)
    
    def block(self):
        """Parse a block of statements."""
        statements = []
        
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.declaration())
        
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements
    
    def print_statement(self):
        """Parse a print statement."""
        value = self.expression()
        return PrintStmt(value)
    
    def input_statement(self):
        """Parse an input statement."""
        prompt = None
        
        if self.match(TokenType.LEFT_PAREN):
            prompt = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after input prompt.")
        
        variable = self.consume(TokenType.IDENTIFIER, "Expect variable name after input.")
        
        return InputStmt(variable, prompt)
    
    def expression_statement(self):
        """Parse an expression statement."""
        expr = self.expression()
        return ExpressionStmt(expr)
    
    # --- Expression parsing ---
    
    
    
    def equality(self):
        """Parse an equality expression."""
        expr = self.comparison()
        
        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)
        
        return expr
    
    def comparison(self):
        """Parse a comparison expression."""
        expr = self.addition()
        
        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL,
                        TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.addition()
            expr = Binary(expr, operator, right)
        
        return expr
    
    def addition(self):
        """Parse an addition expression."""
        expr = self.multiplication()
        
        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous()
            right = self.multiplication()
            expr = Binary(expr, operator, right)
        
        return expr
    
    def multiplication(self):
        
        
        """Parse a factor expression (multiplication, division, modulo)."""
        expr = self.exponentiation()

        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.MODULO):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)

        return expr
    
    def exponentiation(self):
        """Parse an exponentiation expression."""
        expr = self.unary()
        
        while self.match(TokenType.EXPODENT):
            operator = self.previous()
            right = self.exponentiation()  # Right-associative
            expr = Binary(expr, operator, right)
            
        return expr
   
    
    def unary(self):
        """Parse a unary expression."""
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        
        return self.call()
    
    def call(self):
        """Parse a function call."""
        expr = self.primary()
        
        while True:
            if self.match(TokenType.LEFT_PAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.DOT):
                name = self.consume(TokenType.IDENTIFIER, "Expect property name after '.'.")
                expr = Get(expr, name)
            elif self.match(TokenType.LEFT_BRACKET):
                index = self.expression()
                self.consume(TokenType.RIGHT_BRACKET, "Expect ']' after index.")
                expr = Index(expr, index)
            else:
                break
        
        return expr
    
    def finish_call(self, callee):
        """Finish parsing a function call."""
        arguments = []
        
        if not self.check(TokenType.RIGHT_PAREN):
            arguments.append(self.expression())
            
            while self.match(TokenType.COMMA):
                if len(arguments) >= 255:
                    self.error(self.peek(), "Cannot have more than 255 arguments.")
                
                arguments.append(self.expression())
        
        paren = self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
        
        return Call(callee, paren, arguments)
    
    def primary(self):
        """Parse a primary expression."""
        # Literals
        if self.match(TokenType.FALSE): return Literal(False)
        if self.match(TokenType.TRUE): return Literal(True)
         
        if self.match(TokenType.THIS):return This(self.previous())
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous().literal)
        
        if self.match(TokenType.NEW):
            # Parse the class name
            class_name = self.consume(TokenType.IDENTIFIER, "Expect class name after 'new'.")
            
            # Parse constructor arguments
            self.consume(TokenType.LEFT_PAREN, "Expect '(' after class name.")
            arguments = []
            
            if not self.check(TokenType.RIGHT_PAREN):
                arguments.append(self.expression())
                
                while self.match(TokenType.COMMA):
                    if len(arguments) >= 255:
                        self.error(self.peek(), "Cannot have more than 255 arguments.")
                    
                    arguments.append(self.expression())
            
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after arguments.")
            
            return New(class_name, arguments)
        # Lists
        if self.match(TokenType.LEFT_BRACKET):
            elements = []
            
            if not self.check(TokenType.RIGHT_BRACKET):
                elements.append(self.expression())
                
                while self.match(TokenType.COMMA):
                    elements.append(self.expression())
            
            self.consume(TokenType.RIGHT_BRACKET, "Expect ']' after list elements.")
            return List(elements)
        
        # Dictionaries
        if self.match(TokenType.LEFT_BRACE):
            # Empty dictionary
            if self.check(TokenType.RIGHT_BRACE):
                self.advance()
                return Dictionary([], [])
                
            keys = []
            values = []
            
            # First key-value pair
            key = self.expression()
            self.consume(TokenType.COLON, "Expect ':' after dictionary key.")
            value = self.expression()
            
            keys.append(key)
            values.append(value)
            
            # Remaining key-value pairs
            while self.match(TokenType.COMMA):
                key = self.expression()
                self.consume(TokenType.COLON, "Expect ':' after dictionary key.")
                value = self.expression()
                
                keys.append(key)
                values.append(value)
            
            self.consume(TokenType.RIGHT_BRACE, "Expect '}' after dictionary.")
            return Dictionary(keys, values)
        
        # Variable
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous())
        
        if self.match(TokenType.SUPER):
            keyword = self.previous()
            self.consume(TokenType.DOT, "Expect '.' after 'super'.")
            method = self.consume(TokenType.IDENTIFIER, "Expect superclass method name.")
            return Super(keyword, method)
        # Grouping
        if self.match(TokenType.LEFT_PAREN):
            expr = self.expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)
        
        raise self.error(self.peek(), "Expect expression.")
    
    
    # --- Helper methods ---
    
    def match(self, *types):
        """Check if the current token is any of the given types."""
        for type in types:
            if self.check(type):
                self.advance()
                return True
        
        return False
    
    def check(self, type):
        """Check if the current token is of the given type."""
        if self.is_at_end():
            return False
        return self.peek().type == type
    
    def advance(self):
        """Advance to the next token."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()
    
    def is_at_end(self):
        """Check if we're at the end of the token stream."""
        return self.peek().type == TokenType.EOF
    
    def peek(self):
        """Get the current token."""
        return self.tokens[self.current]
    
    def previous(self):
        """Get the previous token."""
        return self.tokens[self.current - 1]
    
    def consume(self, type, message):
        """Consume the current token if it's of the given type."""
        if self.check(type):
            return self.advance()
        
        raise self.error(self.peek(), message)
    
    def error(self, token, message):
        """Report a parsing error."""
        if token.type == TokenType.EOF:
            print(f"Error at end: {message}")
        else:
            print(f"Error at '{token.lexeme}' (line {token.line}): {message}")
        
        return ParseError()
    
    def synchronize(self):
        """Synchronize the parser after an error."""
        self.advance()
        
        while not self.is_at_end():
            # Try to find a statement boundary
            if self.previous().type == TokenType.RIGHT_BRACE:
                return
            
            if self.peek().type in [
                TokenType.FUNCTION,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.PRINT,
                TokenType.RETURN,
            ]:
                return
            
            self.advance()


    def expression(self):
        """Parse an expression."""
        return self.assignment()  # Start with assignment as the entry point

    # Add handling for property assignment in the assignment method
    def assignment(self):
        """Parse an assignment expression."""
        expr = self.logical_or()

        if self.match(TokenType.EQUAL):
            equals = self.previous()
            value = self.assignment()

            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            elif isinstance(expr, Get):
                # This is a property assignment (obj.prop = value)
                return Set(expr.object, expr.name, value)
            elif isinstance(expr, Index):
                # Handle array/dictionary assignments
                return IndexAssign(expr.object, expr.index, value)

            self.error(equals, "Invalid assignment target.")

        return expr

    def logical_or(self):
        """Parse a logical OR expression."""
        expr = self.logical_and()

        while self.match(TokenType.OR):
            operator = self.previous()
            right = self.logical_and()
            expr = Logical(expr, operator, right)  # Use Logical not Binary

        return expr

    def logical_and(self):
        """Parse a logical AND expression."""
        expr = self.equality()

        while self.match(TokenType.AND):
            operator = self.previous()
            right = self.equality()
            expr = Logical(expr, operator, right)  # Use Logical not Binary

        return expr
    
    