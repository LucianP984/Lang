"""
Abstract Syntax Tree (AST) node definitions.
These represent the parsed structure of the program.
"""

# Base classes for expressions and statements
class Expr:
    """Base class for all expressions."""
    pass

class Stmt:
    """Base class for all statements."""
    pass

# --- Expression nodes ---

class Binary(Expr):
    """A binary expression like 'a + b'."""
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_binary_expr(self)

class Grouping(Expr):
    """A grouping expression like '(expr)'."""
    def __init__(self, expression):
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_grouping_expr(self)

class Literal(Expr):
    """A literal value like '123' or 'hello'."""
    def __init__(self, value):
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_literal_expr(self)

class Unary(Expr):
    """A unary expression like '!expr' or '-expr'."""
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
    
    def accept(self, visitor):
        return visitor.visit_unary_expr(self)

class Variable(Expr):
    """A variable reference like 'fun'."""
    def __init__(self, name):
        self.name = name
    
    def accept(self, visitor):
        return visitor.visit_variable_expr(self)

class Assign(Expr):
    """An assignment expression like 'fun = bar'."""
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_assign_expr(self)

class Call(Expr):
    """A function call like 'fun(1, 2)'."""
    def __init__(self, callee, paren, arguments):
        self.callee = callee      
        self.paren = paren        
        self.arguments = arguments
    
    def accept(self, visitor):
        return visitor.visit_call_expr(self)

class Get(Expr):
    """A property access like 'fun.bar'."""
    def __init__(self, object, name):
        self.object = object
        self.name = name
        
    
    def accept(self, visitor):
        return visitor.visit_get_expr(self)
    
class Set(Expr):
    def __init__(self, object, name, value):
        self.object = object  # Expression
        self.name = name  # Token 
        self.value = value  

    def accept(self, visitor):
        return visitor.visit_set_expr(self)

class List(Expr):
    """A list literal like '[1, 2, 3]'."""
    def __init__(self, elements):
        self.elements = elements
    
    def accept(self, visitor):
        return visitor.visit_list_expr(self)

class Index(Expr):
    """An index expression like 'array[0]'."""
    def __init__(self, object, index):
        self.object = object
        self.index = index
    
    def accept(self, visitor):
        return visitor.visit_index_expr(self)
    
class IndexAssign:
    def __init__(self, object, index, value):
        self.object = object
        self.index = index
        self.value = value

    def accept(self, visitor):
        return visitor.visit_index_assign_expr(self)

class Dictionary(Expr):
    """A dictionary literal like '{"a": 1, "b": 2}'."""
    def __init__(self, keys, values):
        self.keys = keys
        self.values = values
    
    def accept(self, visitor):
        return visitor.visit_dictionary_expr(self)

# --- Statement nodes ---

class ExpressionStmt(Stmt):
    """An expression statement like 'fun;'."""
    def __init__(self, expression):
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)

class PrintStmt(Stmt):
    """A print statement like 'print expr;'."""
    def __init__(self, expression):
        self.expression = expression
    
    def accept(self, visitor):
        return visitor.visit_print_stmt(self)

class InputStmt(Stmt):
    """An input statement like 'input x;' or 'input(prompt) x;'."""
    def __init__(self, variable, prompt=None):
        self.variable = variable
        self.prompt = prompt
    
    def accept(self, visitor):
        return visitor.visit_input_stmt(self)

class BlockStmt(Stmt):
    """A block statement like '{ stmt1; stmt2; }'."""
    def __init__(self, statements):
        self.statements = statements
    
    def accept(self, visitor):
        return visitor.visit_block_stmt(self)

class IfStmt(Stmt):
    """An if statement like 'if (cond) { then_stmt } else { else_stmt }'."""
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
    
    def accept(self, visitor):
        return visitor.visit_if_stmt(self)

class WhileStmt(Stmt):
    """A while statement like 'while (cond) { body }'."""
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_while_stmt(self)

class FunctionStmt(Stmt):
    """A function declaration like 'function fun(a, b) { body }'."""
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body
    
    def accept(self, visitor):
        return visitor.visit_function_stmt(self)

class ReturnStmt(Stmt):
    """A return statement like 'return expr;'."""
    def __init__(self, keyword, value=None):
        self.keyword = keyword  
        self.value = value
    
    def accept(self, visitor):
        return visitor.visit_return_stmt(self)
    

class Logical:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor):
        return visitor.visit_logical_expr(self)
    

class ForEach:
    def __init__(self, variable, iterable, body):
        self.variable = variable  
        self.iterable = iterable  
        self.body = body          

    def accept(self, visitor):
        return visitor.visit_foreach_stmt(self)
    

class Class:
    def __init__(self, name, superclass, methods):
        self.name = name  # Token
        self.superclass = superclass  # Variable expression or None
        self.methods = methods  # List of Function statements

    def accept(self, visitor):
        return visitor.visit_class_stmt(self)


class This:
    def __init__(self, keyword):
        self.keyword = keyword  # Token

    def accept(self, visitor):
        return visitor.visit_this_expr(self)

class Super:
    def __init__(self, keyword, method):
        self.keyword = keyword  # Token
        self.method = method  # Token (method name)

    def accept(self, visitor):
        return visitor.visit_super_expr(self)
    
class New(Expr):
    """A new expression like 'new ClassName(args)'."""
    def __init__(self, class_name, arguments):
        self.class_name = class_name  # Token or Variable
        self.arguments = arguments    # List of expressions
    
    def accept(self, visitor):
        return visitor.visit_new_expr(self)