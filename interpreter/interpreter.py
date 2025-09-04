"""
Interpreter for the language.
Executes the AST.
"""
from lexer.token_types import TokenType
from parser.runtime  import LoxClass,LoxInstance

class ReturnException(Exception):
    """Exception used to handle return statements."""
    def __init__(self, value):
        self.value = value
        super().__init__(self)

class Environment:
    """Environment for storing variables."""

    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, name, value):
        """Define a variable in the current environment."""
        if isinstance(name, str):
            self.values[name] = value
        else:
            self.values[name.lexeme] = value

    def get(self, name):
        """Get a variable's value."""
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self.enclosing:
            return self.enclosing.get(name)

        raise RuntimeError(f"Undefined variable '{name.lexeme}'.")

    def assign(self, name, value):
        """Assign a new value to an existing variable."""
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing:
            self.enclosing.assign(name, value)
            return

        raise RuntimeError(f"Undefined variable '{name.lexeme}'.")

class Function:
    """Callable function object."""

    def __init__(self, declaration, closure):
        self.declaration = declaration
        self.closure = closure

    def call(self, interpreter, arguments):
        """Execute the function with the given arguments."""
        # Create a new environment with the closure as parent
        environment = Environment(self.closure)

        # Bind parameters to arguments
        for i in range(len(self.declaration.params)):
            param_name = self.declaration.params[i].lexeme
            environment.define(param_name, arguments[i])

        # Execute function body
        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnException as return_value:
            return return_value.value

        return None
    def bind(self, instance):
        """Bind this function to an instance, creating a method."""
        environment = Environment(self.closure)
        environment.define("this", instance)
        return Function(self.declaration, environment)

    def arity(self):
        """Return the number of parameters the function takes."""
        return len(self.declaration.params)

    def __str__(self):
        return f"<function {self.declaration.name.lexeme}>"

class BuiltinFunction:
    """Built-in function callable from the language."""
    
    def __init__(self, arity, fn):
        self.arity_count = arity
        self.fn = fn
    
    def call(self, interpreter, arguments):
        """Execute the built-in function with the given arguments."""
        return self.fn(arguments)
    
    def arity(self):
        """Return the number of parameters the function takes."""
        return self.arity_count
    
    def __str__(self):
        return "<native function>"

class RuntimeError(Exception):
    """Runtime error during interpretation."""
    pass



class Interpreter:
    """Interpreter for the language."""
    
    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals
        
        # Add built-in functions
        self.define_globals()
    
    def define_globals(self):
        """Define built-in global functions."""
        # List operations
        def append(args):
            if len(args) != 2 or not isinstance(args[0], list):
                raise RuntimeError("append expects a list followed by a value")
            args[0].append(args[1])
            return args[0]
        
        self.globals.define("append", BuiltinFunction(2, append))
        
        def pop(args):
            if len(args) != 1 or not isinstance(args[0], list) or not args[0]:
                raise RuntimeError("pop expects a non-empty list")
            return args[0].pop()
        
        self.globals.define("pop", BuiltinFunction(1, pop))
        
        # String, list, dictionary length
        def length(args):
            if len(args) != 1 or not isinstance(args[0], (list, dict, str)):
                raise RuntimeError("length expects a list, dictionary, or string")
            return len(args[0])
        
        self.globals.define("length", BuiltinFunction(1, length))
        
        # TODO: Add more built-in functions as needed
    
    def interpret(self, statements):
        """Interpret a list of statements."""
        try:
            for statement in statements:
                if statement:  # Skip any None statements
                    self.execute(statement)
        except RuntimeError as error:
            print(f"Runtime error: {error}")
    
    def execute(self, stmt):
        """Execute a statement."""
        return stmt.accept(self)
    
    def execute_block(self, statements, environment):
        """Execute a block of statements in the given environment."""
        previous = self.environment
        try:
            self.environment = environment
            
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous
    
    def evaluate(self, expr):
        """Evaluate an expression."""
        return expr.accept(self)
    
    # --- Statement visitors ---
    
    def visit_block_stmt(self, stmt):
        """Execute a block statement."""
        self.execute_block(stmt.statements, Environment(self.environment))
        return None
    
    def visit_expression_stmt(self, stmt):
        """Execute an expression statement."""
        self.evaluate(stmt.expression)
        return None
    
    def visit_function_stmt(self, stmt):
        """Execute a function declaration."""
        function = Function(stmt, self.environment)
        self.environment.define(stmt.name.lexeme, function)
        return None
    
    def visit_if_stmt(self, stmt):
        """Execute an if statement."""
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
        elif stmt.else_branch:
            self.execute(stmt.else_branch)
        return None
    
    def visit_print_stmt(self, stmt):
        """Execute a print statement."""
        value = self.evaluate(stmt.expression)
        print(self.stringify(value))
        return None
    
    def visit_return_stmt(self, stmt):
        """Execute a return statement."""
        value = None
        if stmt.value:
            value = self.evaluate(stmt.value)
        
        raise ReturnException(value)
    
    def visit_while_stmt(self, stmt):
        """Execute a while statement."""
        while self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)
        return None
    
    def visit_input_stmt(self, stmt):
        """Execute an input statement."""
        prompt_text = ""
        if stmt.prompt:
            prompt_text = self.stringify(self.evaluate(stmt.prompt))
        
        user_input = input(prompt_text)
        
        # Try to parse the input as a number if it looks like one
        if user_input.isdigit():
            user_input = int(user_input)
        elif user_input.replace('.', '', 1).isdigit() and user_input.count('.') == 1:
            user_input = float(user_input)
        
        self.environment.define(stmt.variable.lexeme, user_input)
        return None
    
    # --- Expression visitors ---
    
    def visit_binary_expr(self, expr):
        """Evaluate a binary expression."""
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        
        op_type = expr.operator.type
        
        # Arithmetic operations
        if op_type == TokenType.MINUS:
            self.check_number_operands(expr.operator, left, right)
            return left - right
        elif op_type == TokenType.SLASH:
            self.check_number_operands(expr.operator, left, right)
            # Check for division by zero
            if right == 0:
                raise RuntimeError("Division by zero.")
            return left / right
        elif op_type == TokenType.STAR:
            # Number multiplication
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left * right
            # String or list repetition
            elif (isinstance(left, str) and isinstance(right, int)) or \
                 (isinstance(left, list) and isinstance(right, int)):
                return left * right
            else:
                raise RuntimeError(f"Operands must be numbers or string/list and integer: {type(left).__name__}, {type(right).__name__}")
        elif op_type == TokenType.PLUS:
            # Number addition
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            # String concatenation
            elif isinstance(left, str) and isinstance(right, str):
                return left + right
            # List concatenation
            elif isinstance(left, list) and isinstance(right, list):
                return left + right
            # Implicit conversions for concatenation
            elif isinstance(left, str):
                return left + str(right)
            elif isinstance(right, str):
                return str(left) + right
            else:
                raise RuntimeError(f"Operands must be two numbers, two strings, or two lists: {type(left).__name__}, {type(right).__name__}")
            
        elif op_type == TokenType.MODULO:
            self.check_number_operands(expr.operator, left, right)
            if right == 0:
                raise RuntimeError("Modulo by zero.")
            return left % right
        
        elif op_type == TokenType.EXPODENT:
                self.check_number_operands(expr.operator, left, right)
                return left ** right
        
        # Comparison operations
        elif op_type == TokenType.GREATER:
            self.check_comparable_operands(expr.operator, left, right)
            return left > right
        elif op_type == TokenType.GREATER_EQUAL:
            self.check_comparable_operands(expr.operator, left, right)
            return left >= right
        elif op_type == TokenType.LESS:
            self.check_comparable_operands(expr.operator, left, right)
            return left < right
        elif op_type == TokenType.LESS_EQUAL:
            self.check_comparable_operands(expr.operator, left, right)
            return left <= right
        
        # Equality operations
        elif op_type == TokenType.BANG_EQUAL:
            return not self.is_equal(left, right)
        elif op_type == TokenType.EQUAL_EQUAL:
            return self.is_equal(left, right)
        
        # Logical operations handled via short-circuit evaluation
        
        # Unreachable
        return None
    
    def visit_call_expr(self, expr):
        """Evaluate a function call."""
        callee = self.evaluate(expr.callee)
        
        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))
        
        # Check if it's a callable
        if not callable(getattr(callee, "call", None)):
            raise RuntimeError(f"Can only call functions and classes: {type(callee).__name__}")
        
        # Check arity
        function = callee
        if len(arguments) != function.arity():
            raise RuntimeError(f"Expected {function.arity()} arguments but got {len(arguments)}.")
        
        return function.call(self, arguments)
    
    def visit_get_expr(self, expr):
        """Evaluate a property access."""
        obj = self.evaluate(expr.object)
        prop_name = expr.name.lexeme
        
        # Handle built-in methods for lists, strings.
        if isinstance(obj, list):
            if prop_name == "append":
                return lambda x: obj.append(x)
            elif prop_name == "pop":
                return lambda: obj.pop() if obj else None
        
        if isinstance(obj, (list, dict, str)) and prop_name == "length":
            return len(obj)
        
        raise RuntimeError(f"No such property '{prop_name}' on {type(obj).__name__}.")
    
    def visit_dictionary_expr(self, expr):
        """Evaluate a dictionary literal."""
        result = {}
        
        for i in range(len(expr.keys)):
            key = self.evaluate(expr.keys[i])
            value = self.evaluate(expr.values[i])
            
            # Ensure key is hashable
            if isinstance(key, (list, dict)):
                raise RuntimeError("Dictionary keys must be immutable (strings, numbers, booleans).")
            
            result[key] = value
        
        return result
    
    def visit_grouping_expr(self, expr):
        """Evaluate a grouping expression."""
        return self.evaluate(expr.expression)
    
    def visit_index_expr(self, expr):
        """Evaluate an index expression."""
        obj = self.evaluate(expr.object)
        index = self.evaluate(expr.index)
        
        if isinstance(obj, list):
            if not isinstance(index, int):
                raise RuntimeError("List indices must be integers.")
            
            if index < 0 or index >= len(obj):
                raise RuntimeError(f"List index out of range: {index}")
            
            return obj[index]
        elif isinstance(obj, dict):
            if index not in obj:
                raise RuntimeError(f"Key not found in dictionary: {index}")
            
            return obj[index]
        elif isinstance(obj, str):
            if not isinstance(index, int):
                raise RuntimeError("String indices must be integers.")
            
            if index < 0 or index >= len(obj):
                raise RuntimeError(f"String index out of range: {index}")
            
            return obj[index]
        else:
            raise RuntimeError(f"Cannot index into type {type(obj).__name__}")
    
    def visit_list_expr(self, expr):
        """Evaluate a list literal."""
        elements = []
        
        for element in expr.elements:
            elements.append(self.evaluate(element))
        
        return elements
    
    def visit_literal_expr(self, expr):
        """Evaluate a literal."""
        return expr.value
    
    def visit_logical_expr(self, expr):
        left = self.evaluate(expr.left)

        # Short-circuit evaluation
        if expr.operator.type == TokenType.OR:
            if self.is_truthy(left):
                return left
        else:  
            if not self.is_truthy(left):
                return left

        return self.evaluate(expr.right)
        
    def visit_unary_expr(self, expr):
        """Evaluate a unary expression."""
        right = self.evaluate(expr.right)
        
        if expr.operator.type == TokenType.BANG:
            return not self.is_truthy(right)
        elif expr.operator.type == TokenType.MINUS:
            self.check_number_operand(expr.operator, right)
            return -right
        
        # Unreachable
        return None
    
    def visit_variable_expr(self, expr):
        """Evaluate a variable expression."""
        return self.lookup_variable(expr.name)
    
    def lookup_variable(self, name):
        """Look up a variable in the environment chain."""
        # Check all environments in the chain
        env = self.environment
        while env:
            if name.lexeme in env.values:
                return env.values[name.lexeme]
            env = env.enclosing

        raise RuntimeError(f"Undefined variable '{name.lexeme}'.")

    def visit_assign_expr(self, expr):
        """Evaluate an assignment expression."""
        value = self.evaluate(expr.value)
        self.assign_variable(expr.name, value)
        return value
    
    def assign_variable(self, name, value):

        """Assign a value to a variable in the environment chain."""
        # Check all environments in the chain
        env = self.environment
        while env:
            if name.lexeme in env.values:
                env.values[name.lexeme] = value
                return
            env = env.enclosing

        # CHANGE: If variable doesn't exist, define it in current environment
        # instead of raising an error
        self.environment.define(name.lexeme, value)


    def visit_index_assign_expr(self, expr):
        """Evaluate an index assignment expression."""
        obj = self.evaluate(expr.object)
        index = self.evaluate(expr.index)
        value = self.evaluate(expr.value)

        if isinstance(obj, list):
            if not isinstance(index, int):
                raise RuntimeError("List indices must be integers.")

            if index < 0 or index >= len(obj):
                raise RuntimeError(f"List index out of range: {index}")

            obj[index] = value
        elif isinstance(obj, dict):
            obj[index] = value
        else:
            raise RuntimeError(f"Cannot assign to index of type {type(obj).__name__}")

        return value
            
    # --- Helper methods ---
    
    def check_number_operand(self, operator, operand):
        """Check if an operand is a number."""
        if isinstance(operand, (int, float)):
            return
        raise RuntimeError(f"Operand must be a number: {type(operand).__name__}")
    
    def check_number_operands(self, operator, left, right):
        """Check if operands are numbers."""
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return
        raise RuntimeError(f"Operands must be numbers: {type(left).__name__}, {type(right).__name__}")
    
    
    def check_comparable_operands(self, operator, left, right):
        """Check if operands are comparable."""
        # Numbers can be compared
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return
        # Strings can be compared
        if isinstance(left, str) and isinstance(right, str):
            return
        # Otherwise, error
        raise RuntimeError(f"Cannot compare {type(left).__name__} and {type(right).__name__}")
    
    def is_truthy(self, value):
        """Check if a value is truthy."""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, (list, dict, str)):
            return len(value) > 0
        return True
    
    def is_equal(self, a, b):
        """Check if two values are equal."""
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b
    
    def stringify(self, value):
        """Convert a value to a string."""
        if value is None:
            return "nil"
        
        if isinstance(value, bool):
            return str(value).lower()
        
        if isinstance(value, (int, float)):
            text = str(value)
            if text.endswith(".0"):
                text = text[:-2]
            return text
        
        if isinstance(value, list):
            items = [self.stringify(item) for item in value]
            return f"[{', '.join(items)}]"
        
        if isinstance(value, dict):
            items = [f"{self.stringify(k)}: {self.stringify(v)}" for k, v in value.items()]
            return f"{{{', '.join(items)}}}"
        
        return str(value)
    

    def visit_foreach_stmt(self, stmt):
        """Execute a for-each loop."""
        # Evaluate the iterable
        iterable = self.evaluate(stmt.iterable)

        # Check if it's a valid iterable type
        if not isinstance(iterable, (list, str, dict)):
            raise RuntimeError("Can only iterate over lists, strings, and dictionaries.")

        # Convert dict to keys for iteration
        if isinstance(iterable, dict):
            iterable = list(iterable.keys())

        # Loop through each item
        for value in iterable:
            # Create a new environment for each iteration
            environment = Environment(self.environment)
            environment.define(stmt.variable.lexeme, value)

            # Execute the body with this environment
            previous_env = self.environment
            self.environment = environment

            try:
                self.execute(stmt.body)
            finally:
                # Restore the environment
                self.environment = previous_env

    def visit_class_stmt(self, stmt):
        """Execute a class declaration."""
        # Define the class in the current environment
        self.environment.define(stmt.name.lexeme, None)
        
        # Evaluate superclass if present
        superclass = None
        if stmt.superclass is not None:
            superclass = self.evaluate(stmt.superclass)
            if not isinstance(superclass, LoxClass):
                raise RuntimeError("Superclass must be a class.")
        
        # Collect methods
        methods = {}
        for method in stmt.methods:
            function = Function(method, self.environment)
            methods[method.name.lexeme] = function
        
        # Create the class
        klass = LoxClass(stmt.name.lexeme, superclass, methods)
        
        # Update the environment
        self.environment.define(stmt.name.lexeme, klass)
        
        return None

    def visit_new_expr(self, expr):
        """Evaluate a new expression."""
        # Get the class
        class_name = expr.class_name.lexeme
        
        # Look up the class in the environment
        try:
            klass = self.environment.get(expr.class_name)
        except:
            raise RuntimeError(f"Undefined class '{class_name}'.")
            
        # Evaluate arguments
        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))
            
        # Check if it's a class
        if not hasattr(klass, 'call'):
            raise RuntimeError(f"'{class_name}' is not a class.")
            
        # Create a new instance
        return klass.call(self, arguments)

    def visit_this_expr(self, expr):
        # Lookup 'this' in the environment
        return self.lookup_variable(expr.keyword, expr)
    
    def visit_get_expr(self, expr):
        """Evaluate a property access."""
        obj = self.evaluate(expr.object)
        
        # Handle built-in methods for lists, strings
        if isinstance(obj, list):
            if expr.name.lexeme == "append":
                return BuiltinFunction(1, lambda args: obj.append(args[0]))
            elif expr.name.lexeme == "pop":
                return BuiltinFunction(0, lambda args: obj.pop() if obj else None)
        
        if isinstance(obj, (list, dict, str)) and expr.name.lexeme == "length":
            return len(obj)
        
        # Handle class instances
        if isinstance(obj, LoxInstance):
            return obj.get(expr.name)
        
        raise RuntimeError(f"No such property '{expr.name.lexeme}' on {type(obj).__name__}.")
    
    def visit_set_expr(self, expr):
        """Evaluate a property assignment."""
        obj = self.evaluate(expr.object)
        value = self.evaluate(expr.value)
        
        if isinstance(obj, LoxInstance):
            obj.set(expr.name, value)
            return value
        else:
            raise RuntimeError("Only instances have fields.")
    def visit_this_expr(self, expr):
        """Resolve the 'this' keyword."""
        
        return self.lookup_variable(expr.keyword)
    def visit_super_expr(self, expr):
        """Resolve a superclass method."""
        # Get the superclass
        distance = self.locals.get(expr)
        superclass = self.environment.get_at(distance, "super")

        # Get the instance ('this') from the environment
        instance = self.environment.get_at(distance - 1, "this")

        # Find the method on the superclass
        method = superclass.find_method(expr.method.lexeme)

        if method is None:
            raise RuntimeError(f"Undefined property '{expr.method.lexeme}'.")

        return method.bind(instance)