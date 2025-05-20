CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    domain_definition TEXT NOT NULL,
    example_queries TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tank Crew Mission
INSERT INTO problems (name, description, domain_definition, example_queries) VALUES (
    'Tank Crew Mission',
    'A tank crew consisting of a commander, gunner, and driver executing a combat mission.',
    'causes move(driver) position_changed if engine_on
causes start_engine(driver) engine_on
causes stop_engine(driver) not engine_on
causes aim(gunner) target_locked
causes fire(gunner) target_destroyed if target_locked, ammunition_loaded
causes load(gunner) ammunition_loaded
causes scan(commander) target_identified
impossible move(driver) if not engine_on
impossible fire(gunner) if not target_locked
always not target_destroyed if not target_identified
always not target_locked if not target_identified',
    'always executable move(driver); fire(gunner)
sometimes accessible target_destroyed from engine_on in scan(commander); aim(gunner); fire(gunner)
realisable scan(commander); aim(gunner); fire(gunner) by commander, gunner
active gunner in fire by commander, gunner, driver'
);

-- Football Team
INSERT INTO problems (name, description, domain_definition, example_queries) VALUES (
    'Football Team',
    'A football team executing an offensive play.',
    'causes pass(quarterback) ball_in_air
causes catch(receiver) possession if ball_in_air
causes run(runner) yards_gained if possession
causes block(lineman) protection_formed
impossible pass(quarterback) if not protection_formed
impossible catch(receiver) if not ball_in_air
always not yards_gained if not possession',
    'always executable pass(quarterback); catch(receiver)
sometimes accessible yards_gained from protection_formed in block(lineman); pass(quarterback); catch(receiver); run(runner)
realisable pass(quarterback); catch(receiver) by quarterback, receiver
active receiver in catch by quarterback, receiver, runner'
);

-- Rescue Team
INSERT INTO problems (name, description, domain_definition, example_queries) VALUES (
    'Rescue Team',
    'A rescue team responding to an emergency situation.',
    'causes assess(medic) situation_evaluated
causes treat(medic) patient_stabilized if situation_evaluated
causes secure(firefighter) area_secured
causes evacuate(firefighter) patient_evacuated if area_secured, patient_stabilized
impossible treat(medic) if not situation_evaluated
impossible evacuate(firefighter) if not area_secured
always not patient_evacuated if not patient_stabilized',
    'always executable assess(medic); treat(medic)
sometimes accessible patient_evacuated from situation_evaluated in treat(medic); secure(firefighter); evacuate(firefighter)
realisable assess(medic); treat(medic); evacuate(firefighter) by medic, firefighter
active medic in treat by medic, firefighter'
);

-- Fire Brigade
INSERT INTO problems (name, description, domain_definition, example_queries) VALUES (
    'Fire Brigade',
    'A fire brigade responding to a building fire.',
    'causes inspect(chief) risk_assessed
causes deploy(operator) hoses_ready
causes spray(firefighter) fire_contained if hoses_ready
causes ventilate(team) smoke_cleared if fire_contained
impossible deploy(operator) if not risk_assessed
impossible spray(firefighter) if not hoses_ready
always not smoke_cleared if not fire_contained',
    'always executable inspect(chief); deploy(operator)
sometimes accessible smoke_cleared from risk_assessed in deploy(operator); spray(firefighter); ventilate(team)
realisable inspect(chief); deploy(operator); spray(firefighter) by chief, operator, firefighter
active firefighter in spray by chief, operator, firefighter'
);

-- Medical Diagnosis
INSERT INTO problems (name, description, domain_definition, example_queries) VALUES (
    'Medical Diagnosis',
    'A team of doctors diagnosing and treating a patient.',
    'causes examine(physician) symptoms_identified
causes test(specialist) condition_confirmed if symptoms_identified
causes prescribe(physician) treatment_started if condition_confirmed
causes monitor(nurse) recovery_progressing if treatment_started
impossible test(specialist) if not symptoms_identified
impossible prescribe(physician) if not condition_confirmed
always not recovery_progressing if not treatment_started',
    'always executable examine(physician); test(specialist)
sometimes accessible recovery_progressing from symptoms_identified in test(specialist); prescribe(physician); monitor(nurse)
realisable examine(physician); test(specialist); prescribe(physician) by physician, specialist
active specialist in test by physician, specialist, nurse'
); 