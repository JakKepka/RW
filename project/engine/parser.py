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
        
        # Initial state declaration
        self.initially_stmt = Group(
            Literal("initially") +
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
            self.always_stmt |
            self.initially_stmt
        )
    
    def parse_statement(self, text: str) -> dict:
        """Parse a statement and return a dictionary with its components"""
        try:
            result = self.statement.parseString(text, parseAll=True)[0]
            
            # Convert parse result to dictionary
            stmt_dict = {}
            
            if result[0] == "initially":
                stmt_dict["type"] = "initially"
                stmt_dict["fluents"] = []
                for fluent in result[1:]:
                    if len(fluent) == 2 and fluent[0] == "not":
                        stmt_dict["fluents"].append(("not", fluent[1]))
                    else:
                        stmt_dict["fluents"].append(("pos", fluent[0]))
                return stmt_dict
            
            elif result[0] == "causes":
                stmt_dict["type"] = "causes"
                stmt_dict["action"] = result[1]
                stmt_dict["effect"] = result[2]
                if len(result) > 3 and result[3][0] == "if":
                    stmt_dict["conditions"] = result[3][1:]
                else:
                    stmt_dict["conditions"] = []
                    
            elif result[0] == "impossible":
                stmt_dict["type"] = "impossible"
                stmt_dict["action"] = result[1]
                if len(result) > 2 and result[2][0] == "if":
                    stmt_dict["conditions"] = result[2][1:]
                else:
                    stmt_dict["conditions"] = []
                    
            elif result[0] == "always":
                stmt_dict["type"] = "always"
                stmt_dict["effect"] = result[1]
                
            return stmt_dict
            
        except ParseException as e:
            raise ValueError(f"Invalid statement syntax: {str(e)}")
    
    def parse_query(self, text):
        """Parse a query"""
        # For now, just return the text as is
        return text 