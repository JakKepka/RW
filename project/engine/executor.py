from typing import Set, Dict, List, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy

@dataclass
class State:
    """Represents a state in the system"""
    fluents: Set[str]
    released: Set[str]

    def copy(self) -> 'State':
        return State(
            fluents=self.fluents.copy(),
            released=self.released.copy()
        )

class ActionExecutor:
    def __init__(self):
        self.causes_rules: Dict[str, List[Tuple[str, List[str]]]] = {}
        self.releases_rules: Dict[str, List[str]] = {}
        self.impossible_rules: Dict[str, List[List[str]]] = {}
        self.always_rules: List[str] = []
        
    def add_causes_rule(self, action: str, effect: str, conditions: Optional[List[str]] = None):
        """Add a causes rule to the system"""
        if action not in self.causes_rules:
            self.causes_rules[action] = []
        self.causes_rules[action].append((effect, conditions or []))
    
    def add_releases_rule(self, action: str, fluent: str):
        """Add a releases rule to the system"""
        if action not in self.releases_rules:
            self.releases_rules[action] = []
        self.releases_rules[action].append(fluent)
    
    def add_impossible_rule(self, action: str, conditions: List[str]):
        """Add an impossible rule to the system"""
        if action not in self.impossible_rules:
            self.impossible_rules[action] = []
        self.impossible_rules[action].append(conditions)
    
    def add_always_rule(self, effect: str):
        """Add an always rule to the system"""
        self.always_rules.append(effect)
    
    def is_action_possible(self, action: str, state: State) -> bool:
        """Check if an action is possible in the given state"""
        if action not in self.impossible_rules:
            return True
            
        for conditions in self.impossible_rules[action]:
            if all(cond in state.fluents for cond in conditions):
                return False
        return True
    
    def apply_inertia(self, old_state: State, new_state: State):
        """Apply the law of inertia to unreleased fluents"""
        for fluent in old_state.fluents:
            if fluent not in new_state.released and fluent not in new_state.fluents:
                new_state.fluents.add(fluent)
    
    def apply_always_rules(self, state: State):
        """Apply always rules to the state"""
        for effect in self.always_rules:
            if effect.startswith("not "):
                state.fluents.discard(effect[4:])
            else:
                state.fluents.add(effect)
    
    def execute_action(self, action: str, state: State) -> Optional[State]:
        """Execute an action in the given state"""
        if not self.is_action_possible(action, state):
            return None
            
        new_state = state.copy()
        
        # Apply releases
        if action in self.releases_rules:
            for fluent in self.releases_rules[action]:
                new_state.released.add(fluent)
        
        # Apply causes
        if action in self.causes_rules:
            for effect, conditions in self.causes_rules[action]:
                if all(cond in state.fluents for cond in conditions):
                    if effect.startswith("not "):
                        new_state.fluents.discard(effect[4:])
                    else:
                        new_state.fluents.add(effect)
        
        # Apply inertia and always rules
        self.apply_inertia(state, new_state)
        self.apply_always_rules(new_state)
        
        return new_state
    
    def execute_program(self, program: List[str], initial_state: State) -> List[State]:
        """Execute a program from the initial state"""
        states = [initial_state]
        current_state = initial_state
        
        for action in program:
            new_state = self.execute_action(action, current_state)
            if new_state is None:
                return []  # Program is not executable
            states.append(new_state)
            current_state = new_state
        
        return states
    
    def check_executable(self, program: List[str], initial_state: State) -> bool:
        """Check if a program is always executable from the initial state"""
        return bool(self.execute_program(program, initial_state))
    
    def check_accessible(self, goal_state: Set[str], program: List[str], initial_state: State) -> bool:
        """Check if a goal state is sometimes accessible through a program"""
        final_states = self.execute_program(program, initial_state)
        if not final_states:
            return False
            
        return all(fluent in final_states[-1].fluents for fluent in goal_state)
    
    def check_realisable(self, program: List[str], group: List[str], initial_state: State) -> bool:
        """Check if a program is realisable by a group of agents"""
        # This is a simplified implementation
        # In a real system, you would need to check agent capabilities
        return self.check_executable(program, initial_state)
    
    def check_active(self, agent: str, action: str, group: List[str]) -> bool:
        """Check if an agent is active in an action within a group"""
        # This is a simplified implementation
        # In a real system, you would need to check action requirements
        return agent in group 