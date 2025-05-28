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
        
        # Action with optional agents
        self.action_with_agents = Group(
            self.action +
            Optional(
                Literal("(") +
                delimitedList(self.agent) +
                Literal(")")
            )
        )
        
        # Effect
        self.effect = Group(
            Optional(Literal("not")) +
            self.fluent
        )
        
        # Conditions
        self.conditions = Group(
            Literal("if") +
            delimitedList(self.effect, delim=",")
        )
        
        # Statement types
        self.causes_stmt = Group(
            Literal("causes") +
            self.action_with_agents +
            self.effect +
            Optional(self.conditions)
        )
        
        self.impossible_stmt = Group(
            Literal("impossible") +
            self.action_with_agents +
            Optional(self.conditions)
        )
        
        self.always_stmt = Group(
            Literal("always") +
            self.effect
        )
        
        # Complete statement
        self.statement = (
            self.causes_stmt |
            self.impossible_stmt |
            self.always_stmt
        )
    
    def parse_statement(self, text):
        """Parse a single statement"""
        try:
            # Split the line into parts
            parts = text.split()
            if not parts:
                return None
            
            # Handle different statement types
            if parts[0] == "causes":
                # Extract action
                action = parts[1]
                # Extract effect
                effect = parts[2]
                # Extract conditions if present
                conditions = []
                if "if" in parts:
                    if_index = parts.index("if")
                    conditions = [c.strip() for c in " ".join(parts[if_index + 1:]).split(",")]
                
                return {
                    "type": "causes",
                    "action": action,
                    "effect": effect,
                    "conditions": conditions
                }
                
            elif parts[0] == "impossible":
                # Extract action
                action = parts[1]
                # Extract conditions if present
                conditions = []
                if "if" in parts:
                    if_index = parts.index("if")
                    conditions = [c.strip() for c in " ".join(parts[if_index + 1:]).split(",")]
                
                return {
                    "type": "impossible",
                    "action": action,
                    "conditions": conditions
                }
                
            elif parts[0] == "always":
                # Extract effect
                effect = " ".join(parts[1:])
                return {
                    "type": "always",
                    "effect": effect
                }
            
            return None
            
        except Exception as e:
            raise ValueError(f"Error parsing statement: {str(e)}")
    
    def parse_query(self, text):
        """Parse a query"""
        # For now, just return the text as is
        return text 