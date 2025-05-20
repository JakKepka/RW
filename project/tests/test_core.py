import pytest
from engine.parser import ActionParser
from engine.executor import ActionExecutor, State
from engine.semantics import ActionSemantics

def test_parser():
    parser = ActionParser()
    
    # Test action parsing
    action = parser.parse_action("move(driver)")
    assert action.name == "move"
    assert action.agents == ["driver"]
    
    # Test causes statement
    stmt = parser.parse_statement("causes move(driver) position_changed if engine_on")
    assert "causes" in stmt
    assert stmt.action.name == "move"
    assert stmt.effect == "position_changed"
    assert "engine_on" in stmt.conditions
    
    # Test impossible statement
    stmt = parser.parse_statement("impossible move(driver) if not engine_on")
    assert "impossible" in stmt
    assert stmt.action.name == "move"
    assert "not engine_on" in stmt.conditions
    
    # Test query parsing
    query = parser.parse_query("always executable move(driver); fire(gunner)")
    assert "executable" in query
    assert len(query.program) == 2

def test_executor():
    executor = ActionExecutor()
    
    # Setup initial state
    initial_state = State(fluents={"engine_on"}, released=set())
    
    # Add rules
    executor.add_causes_rule("move", "position_changed", ["engine_on"])
    executor.add_impossible_rule("move", ["not engine_on"])
    
    # Test execution
    result = executor.execute_action("move", initial_state)
    assert result is not None
    assert "position_changed" in result.fluents
    
    # Test impossible action
    state_no_engine = State(fluents=set(), released=set())
    result = executor.execute_action("move", state_no_engine)
    assert result is None

def test_semantics():
    semantics = ActionSemantics()
    
    # Test domain definition processing
    domain = """
    causes move(driver) position_changed if engine_on
    impossible move(driver) if not engine_on
    always not position_changed if not engine_on
    """
    semantics.process_domain_definition(domain)
    
    # Test query processing
    initial_state = State(fluents={"engine_on"}, released=set())
    result, explanation = semantics.process_query(
        "always executable move(driver)",
        initial_state
    )
    assert result is True
    assert "executable" in explanation
    
    # Test program simulation
    states = semantics.simulate_program("move(driver)", initial_state)
    assert len(states) == 2  # Initial + final state
    assert "position_changed" in states[-1]["fluents"]

def test_tank_crew_scenario():
    semantics = ActionSemantics()
    
    # Define domain
    domain = """
    causes move(driver) position_changed if engine_on
    causes start_engine(driver) engine_on
    causes stop_engine(driver) not engine_on
    causes aim(gunner) target_locked
    causes fire(gunner) target_destroyed if target_locked, ammunition_loaded
    causes load(gunner) ammunition_loaded
    causes scan(commander) target_identified
    impossible move(driver) if not engine_on
    impossible fire(gunner) if not target_locked
    always not target_destroyed if not target_identified
    always not target_locked if not target_identified
    """
    semantics.process_domain_definition(domain)
    
    # Test complete mission sequence
    initial_state = State(fluents=set(), released=set())
    program = "scan(commander); start_engine(driver); load(gunner); aim(gunner); fire(gunner)"
    states = semantics.simulate_program(program, initial_state)
    
    final_state = states[-1]["fluents"]
    assert "target_identified" in final_state
    assert "engine_on" in final_state
    assert "ammunition_loaded" in final_state
    assert "target_locked" in final_state
    assert "target_destroyed" in final_state

if __name__ == "__main__":
    pytest.main([__file__]) 