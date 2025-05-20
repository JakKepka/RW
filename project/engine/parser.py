from pyparsing import (
    Word,
    alphas,
    alphanums,
    Literal,
    Group,
    OneOrMore,
    delimitedList,
    Optional,
    Forward,
    ZeroOrMore,
    ParseException,
    White,
    restOfLine,
)

class ActionParser:
    def __init__(self):
        # Basic elements
        self.identifier = Word(alphas, alphanums + "_")
        self.agent = self.identifier.copy()
        self.fluent = self.identifier.copy()
        self.action = self.identifier.copy()
        
        # Action expressions
        self.action_expr = Forward()
        self.seq_action = Forward()
        self.nondet_action = Forward()
        
        # Basic action
        self.basic_action = Group(
            self.action("name") +
            Optional(Literal("(").suppress() +
                    delimitedList(self.agent)("agents") +
                    Literal(")").suppress())
        )
        
        # Sequential actions
        self.seq_action << (
            self.basic_action +
            Literal(";").suppress() +
            self.action_expr
        )
        
        # Non-deterministic choice
        self.nondet_action << (
            self.basic_action +
            Literal("+").suppress() +
            self.action_expr
        )
        
        # Complete action expression
        self.action_expr << (
            self.seq_action |
            self.nondet_action |
            self.basic_action
        )
        
        # Effect expressions
        self.effect = Forward()
        self.effect << (
            Literal("not").suppress() + self.fluent |
            self.fluent
        )
        
        # Causes statement
        self.causes_stmt = (
            Literal("causes").suppress() +
            self.action_expr("action") +
            self.effect("effect") +
            Optional(
                Literal("if").suppress() +
                delimitedList(self.effect)("conditions")
            )
        )
        
        # Releases statement
        self.releases_stmt = (
            Literal("releases").suppress() +
            self.action_expr("action") +
            self.fluent("fluent")
        )
        
        # Impossible statement
        self.impossible_stmt = (
            Literal("impossible").suppress() +
            self.action_expr("action") +
            Literal("if").suppress() +
            delimitedList(self.effect)("conditions")
        )
        
        # Always statement
        self.always_stmt = (
            Literal("always").suppress() +
            self.effect("effect")
        )
        
        # Complete statement
        self.statement = (
            self.causes_stmt |
            self.releases_stmt |
            self.impossible_stmt |
            self.always_stmt
        )
        
        # Complete program
        self.program = OneOrMore(self.statement)
        
        # Action sequence for queries
        self.action_sequence = delimitedList(self.basic_action, ";")("actions")
        
        # Query types
        self.executable_query = (
            Optional(Literal("always")) + 
            Literal("executable") + 
            self.action_sequence
        )("executable")
        
        self.accessible_query = (
            Optional(Literal("sometimes")) + 
            Literal("accessible") + 
            self.effect("goal") + 
            Literal("from") + 
            self.effect("initial") + 
            Literal("in") + 
            self.action_sequence
        )("accessible")
        
        self.realisable_query = (
            Literal("realisable") + 
            self.action_sequence + 
            Literal("by") + 
            delimitedList(self.agent)("agents")
        )("realisable")
        
        self.active_query = (
            Literal("active") + 
            self.agent("agent") + 
            Literal("in") + 
            self.action("action") + 
            Literal("by") + 
            delimitedList(self.agent)("agents")
        )("active")
        
        # Complete query
        self.query = (
            self.executable_query |
            self.accessible_query |
            self.realisable_query |
            self.active_query
        )
    
    def parse_action(self, text):
        """Parse an action expression"""
        try:
            return self.action_expr.parseString(text, parseAll=True)
        except ParseException as e:
            raise ValueError(f"Invalid action syntax: {str(e)}")
    
    def parse_statement(self, text):
        """Parse a single statement"""
        try:
            return self.statement.parseString(text, parseAll=True)
        except ParseException as e:
            raise ValueError(f"Invalid statement syntax: {str(e)}")
    
    def parse_program(self, text):
        """Parse a complete program"""
        try:
            return self.program.parseString(text, parseAll=True)
        except ParseException as e:
            raise ValueError(f"Invalid program syntax: {str(e)}")
    
    def parse_query(self, text):
        """Parse a query expression"""
        try:
            print(f"Parsing query: {text}")
            result = self.query.parseString(text, parseAll=True)
            print(f"Query parsed successfully: {result.dump()}")
            return result
        except ParseException as e:
            print(f"Parse error at line {e.lineno}, column {e.column}")
            print(f"Error message: {str(e)}")
            raise ValueError(f"Invalid query syntax: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise ValueError(f"Error parsing query: {str(e)}") 