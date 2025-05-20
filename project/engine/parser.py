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
            self.fluent |
            Literal("not").suppress() + self.fluent
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
        # Query types
        executable = (
            Literal("always").suppress() +
            Literal("executable").suppress() +
            self.action_expr("program")
        )
        
        accessible = (
            Literal("sometimes").suppress() +
            Literal("accessible").suppress() +
            self.effect("goal") +
            Literal("from").suppress() +
            self.effect("initial") +
            Literal("in").suppress() +
            self.action_expr("program")
        )
        
        realisable = (
            Literal("realisable").suppress() +
            self.action_expr("program") +
            Literal("by").suppress() +
            Group(delimitedList(self.agent))("group")
        )
        
        active = (
            Literal("active").suppress() +
            self.agent("agent") +
            Literal("in").suppress() +
            self.action("action") +
            Literal("by").suppress() +
            Group(delimitedList(self.agent))("group")
        )
        
        query = (
            executable |
            accessible |
            realisable |
            active
        )
        
        try:
            return query.parseString(text, parseAll=True)
        except ParseException as e:
            raise ValueError(f"Invalid query syntax: {str(e)}") 