
# Tank Crew Mission
    # Domain Editor 
        causes start_engine(driver) engine_on
        causes stop_engine(driver) engine_off
        causes move(driver) position_changed if engine_on
        causes aim(gunner) target_locked
        causes fire(gunner) target_destroyed if target_locked, ammunition_loaded
        causes load(gunner) ammunition_loaded
        causes scan(commander) target_identified
        impossible move(driver) if engine_off
        impossible fire(gunner) if target_unlocked
        always target_unlocked

    # Query
        active gunner in fire by commander, gunner, driver