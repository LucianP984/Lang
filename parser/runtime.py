class LoxInstance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    # Fix the get method in LoxInstance
    def get(self, name):
        # Check if name is a Token or string
        name_key = name.lexeme if hasattr(name, 'lexeme') else name

        if name_key in self.fields:
            return self.fields[name_key]

        method = self.klass.find_method(name_key)
        if method is not None:
            return method.bind(self)

        raise RuntimeError(f"Undefined property '{name_key}'.")

    # Fix the set method in LoxInstance
    def set(self, name, value):
        # Check if name is a Token or string
        name_key = name.lexeme if hasattr(name, 'lexeme') else name
        self.fields[name_key] = value

class LoxClass:
    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name):
        if name in self.methods:
            return self.methods[name]

        if self.superclass is not None:
            return self.superclass.find_method(name)

        return None

    def call(self, interpreter, arguments):
        instance = LoxInstance(self)

        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def __str__(self):
        return self.name