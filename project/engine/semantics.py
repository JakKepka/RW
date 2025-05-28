from typing import Set, List, Dict, Optional, Tuple
from .parser import ActionParser
from .executor import ActionExecutor, State

class ActionSemantics:
    def __init__(self):
        self.parser = ActionParser()
        self.executor = ActionExecutor()
        
    def process_domain_definition(self, text: str):
        """Process a domain definition text"""
        try:
            # Split text into lines and process each line separately
            lines = text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Parse each line as a statement
                stmt = self.parser.parse_statement(line)
                
                # Process based on statement type
                if stmt["type"] == "causes":
                    action = stmt["action"][0]  # Get action name
                    if len(stmt["action"]) > 1:  # Has agents
                        action = f"{action}({','.join(stmt['action'][2:-1])})"  # Skip parentheses
                    effect = ' '.join(stmt["effect"])  # Join effect parts
                    conditions = [' '.join(cond) for cond in stmt["conditions"]]  # Join condition parts
                    self.executor.add_causes_rule(action, effect, conditions)
                    
                elif stmt["type"] == "impossible":
                    action = stmt["action"][0]  # Get action name
                    if len(stmt["action"]) > 1:  # Has agents
                        action = f"{action}({','.join(stmt['action'][2:-1])})"  # Skip parentheses
                    conditions = [' '.join(cond) for cond in stmt["conditions"]]  # Join condition parts
                    self.executor.add_impossible_rule(action, conditions)
                    
                elif stmt["type"] == "always":
                    effect = ' '.join(stmt["effect"])  # Join effect parts
                    self.executor.add_always_rule(effect)
                    
                elif 'releases' in stmt:
                    action = stmt.action.name if hasattr(stmt.action, 'name') else stmt.action
                    fluent = stmt.fluent
                    self.executor.add_releases_rule(action, fluent)
                    
        except Exception as e:
            print(f"Error processing domain definition: {str(e)}")
            raise ValueError(f"Error in domain definition: {str(e)}")
    
    def _get_action_name(self, action_expr) -> str:
        """Extract action name from action expression"""
        if isinstance(action_expr, str):
            return action_expr
        return action_expr.name if hasattr(action_expr, 'name') else str(action_expr)
    
    def _get_effect_name(self, effect_expr) -> str:
        """Extract effect name from effect expression"""
        if isinstance(effect_expr, str):
            return effect_expr
        if hasattr(effect_expr, 'negated'):
            return f"not {effect_expr.name}"
        return effect_expr.name if hasattr(effect_expr, 'name') else str(effect_expr)
    
    def process_query(self, query_text: str, initial_state: Optional[State] = None) -> Tuple[bool, str]:
        """Process a query and return result with explanation"""
        try:
            print(f"Processing query: {query_text}")
            query = self.parser.parse_query(query_text)
            
            # For now, return a dummy result
            return True, "Query processed successfully"
            
        except ValueError as e:
            print(f"Error processing query: {str(e)}")
            raise ValueError(f"Error processing query: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def simulate_program(self, program_text: str, initial_state: State) -> List[Dict[str, Set[str]]]:
        """Simulate a program execution and return state history"""
        try:
            program = self._parse_program(self.parser.parse_action(program_text))
            states = self.executor.execute_program(program, initial_state)
            
            return [
                {
                    'fluents': state.fluents,
                    'released': state.released
                }
                for state in states
            ]
            
        except ValueError as e:
            raise ValueError(f"Error simulating program: {str(e)}")
    
    def _parse_program(self, program_expr) -> List[str]:
        """Convert program expression to list of action names"""
        if isinstance(program_expr, str):
            return [program_expr]
        
        if hasattr(program_expr, 'name'):
            return [program_expr.name]
        
        actions = []
        for action in program_expr:
            if hasattr(action, 'name'):
                actions.append(action.name)
            else:
                actions.append(str(action))
        return actions 