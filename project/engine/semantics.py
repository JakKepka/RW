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
            statements = self.parser.parse_program(text)
            for stmt in statements:
                if 'causes' in stmt:
                    self._process_causes(stmt)
                elif 'releases' in stmt:
                    self._process_releases(stmt)
                elif 'impossible' in stmt:
                    self._process_impossible(stmt)
                elif 'always' in stmt:
                    self._process_always(stmt)
        except ValueError as e:
            raise ValueError(f"Error processing domain definition: {str(e)}")
    
    def _process_causes(self, stmt):
        """Process a causes statement"""
        action = self._get_action_name(stmt.action)
        effect = self._get_effect_name(stmt.effect)
        conditions = [self._get_effect_name(cond) for cond in stmt.conditions] if 'conditions' in stmt else None
        self.executor.add_causes_rule(action, effect, conditions)
    
    def _process_releases(self, stmt):
        """Process a releases statement"""
        action = self._get_action_name(stmt.action)
        fluent = stmt.fluent
        self.executor.add_releases_rule(action, fluent)
    
    def _process_impossible(self, stmt):
        """Process an impossible statement"""
        action = self._get_action_name(stmt.action)
        conditions = [self._get_effect_name(cond) for cond in stmt.conditions]
        self.executor.add_impossible_rule(action, conditions)
    
    def _process_always(self, stmt):
        """Process an always statement"""
        effect = self._get_effect_name(stmt.effect)
        self.executor.add_always_rule(effect)
    
    def _get_action_name(self, action_expr) -> str:
        """Extract action name from action expression"""
        if isinstance(action_expr, str):
            return action_expr
        return action_expr.name
    
    def _get_effect_name(self, effect_expr) -> str:
        """Extract effect name from effect expression"""
        if isinstance(effect_expr, str):
            return effect_expr
        if hasattr(effect_expr, 'negated'):
            return f"not {effect_expr.name}"
        return effect_expr.name
    
    def process_query(self, query_text: str, initial_state: Optional[State] = None) -> Tuple[bool, str]:
        """Process a query and return result with explanation"""
        try:
            print(f"Processing query: {query_text}")
            query = self.parser.parse_query(query_text)
            print(f"Parsed query: {query.dump()}")
            
            if initial_state is None:
                initial_state = State(fluents=set(), released=set())
            
            if query.getName() == "executable":
                program = [action.name for action in query.actions]
                result = self.executor.check_executable(program, initial_state)
                explanation = "Program is always executable" if result else "Program is not always executable"
            
            elif query.getName() == "accessible":
                program = [action.name for action in query.actions]
                goal_state = {self._get_effect_name(query.goal)}
                result = self.executor.check_accessible(goal_state, program, initial_state)
                explanation = "Goal state is accessible" if result else "Goal state is not accessible"
            
            elif query.getName() == "realisable":
                program = [action.name for action in query.actions]
                group = list(query.agents)
                result = self.executor.check_realisable(program, group, initial_state)
                explanation = f"Program is realisable by group {group}" if result else f"Program is not realisable by group {group}"
            
            elif query.getName() == "active":
                agent = query.agent
                action = query.action
                group = list(query.agents)
                result = self.executor.check_active(agent, action, group)
                explanation = f"Agent {agent} is active in action {action}" if result else f"Agent {agent} is not active in action {action}"
            
            else:
                raise ValueError(f"Unknown query type: {query.getName()}")
            
            print(f"Query result: {result}, Explanation: {explanation}")
            return result, explanation
            
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
        return actions 