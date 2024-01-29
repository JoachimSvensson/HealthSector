import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import time 
import pandas as pd 
import numpy as np
import streamlit as st

def pylice_opt_model_hard(time_t,p_shifts,demand,teamsize,cap_max,shift_cost, day_shift_match, shift_day_match_end, shift_day_match_start):
    # Creating Model instance
    model = pyo.ConcreteModel()

    ##### Sets #####
    model.setTime = pyo.Set(initialize = time_t) # time
    model.setShifts = pyo.Set(initialize = p_shifts) # Possible Combination of Shifts
    model.setDayShifts = pyo.Set(model.setTime, initialize = day_shift_match)
    model.setEndingShifts = pyo.Set(model.setTime, initialize = shift_day_match_end)
    model.setStartingShifts = pyo.Set(model.setTime, initialize = shift_day_match_start)
    ##### Parameters #####
    model.E = pyo.Param(model.setTime, initialize = demand, within = pyo.Integers)
    E = model.E

    model.TS = pyo.Param(initialize = teamsize, within = pyo.Integers)
    TS = model.TS

    model.Cap_max = pyo.Param(initialize = cap_max, within = pyo.Integers)
    Cap_max = model.Cap_max

    model.C_Shift = pyo.Param(model.setShifts, initialize = shift_cost)
    C_Shift = model.C_Shift

    ##### Decision Variables #####
    model.Allocated_Teams = pyo.Var(model.setShifts, within = pyo.Integers, bounds=(0.0, None))
    x = model.Allocated_Teams

    model.Tot_Costs = pyo.Var(within = pyo.Reals, bounds=(0.0, None))
    z = model.Tot_Costs

    model.ShiftSelect = pyo.Var(model.setShifts, within = pyo.Binary)
    y = model.ShiftSelect

    model.multiple = pyo.Var(model.setShifts, within = pyo.Integers, bounds=(0.0, None))
    q = model.multiple

    ##### Objective Function #####

    model.obj_costs = pyo.Objective(expr = z, sense = pyo.minimize)

    ##### s.t. #####

    # Team Allocation
    model.C1 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C1.add(expr = x[s] <= y[s]*Cap_max)
    model.C2 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C2.add(expr = x[s] >= y[s])
    # Make x a multiple of TS
    model.C3 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C3.add(expr = x[s] == TS * q[s]) 
    # Demand Coverage
    model.C4 = pyo.ConstraintList()
    for t in model.setTime:
        model.C4.add(expr = sum(x[s] for s in model.setDayShifts[t]) >= E[t])
    # Max Allocation
    model.C6 = pyo.ConstraintList()
    for t in model.setTime:
        model.C6.add(expr = sum(x[s] for s in model.setDayShifts[t]) <= Cap_max)
    # Cost
    model.C9 = pyo.Constraint(expr = z == sum(C_Shift[s]*x[s] for s in model.setShifts))
    return model


def optimize_hard(model):
    opt = SolverFactory('scipampl')
    status = opt.solve(model, tee=False)
    return model, status





def pylice_opt_model_soft(time_t,p_shifts,demand,teamsize,cap_max,shift_cost, day_shift_match, shift_day_match_end, shift_day_match_start, demand_weigth,over_weight = 1, under_weight = 1):
    
    # Creating Model instance
    model = pyo.ConcreteModel()

    ##### Sets #####
    model.setTime = pyo.Set(initialize = time_t) # time
    model.setShifts = pyo.Set(initialize = p_shifts) # Possible Combination of Shifts
    model.setDayShifts = pyo.Set(model.setTime, initialize = day_shift_match)
    model.setEndingShifts = pyo.Set(model.setTime, initialize = shift_day_match_end)
    model.setStartingShifts = pyo.Set(model.setTime, initialize = shift_day_match_start)
    
    
    ##### Parameters #####
    model.E = pyo.Param(model.setTime, initialize = demand, within = pyo.Integers)
    E = model.E

    model.TS = pyo.Param(initialize = teamsize, within = pyo.Integers)
    TS = model.TS

    model.Cap_max = pyo.Param(initialize = cap_max, within = pyo.Integers)
    Cap_max = model.Cap_max

    model.C_Shift = pyo.Param(model.setShifts, initialize = shift_cost)
    C_Shift = model.C_Shift

    cost_weight = 1 - demand_weigth
    demand_diff_weight = demand_weigth
    minimum_cost = 213727.5 # Max_cap = 15
    maximum_cost = 1070317.5 # Max_cap = 15
    minimum_demand_diff = 361 # Max_cap = 15
    maximum_demand_diff = 3459 # Max_cap = 15, 3459
    cost_normalization_range = maximum_cost - minimum_cost
    demand_diff_normalization_range = maximum_demand_diff - minimum_demand_diff
    
    
    ##### Decision Variables #####
    model.Allocated_Teams = pyo.Var(model.setShifts, within = pyo.Integers, bounds=(0.0, None))
    x = model.Allocated_Teams

    model.Tot_Costs = pyo.Var(within = pyo.Reals, bounds=(0.0, None))
    z = model.Tot_Costs

    model.ShiftSelect = pyo.Var(model.setShifts, within = pyo.Binary)
    y = model.ShiftSelect

    model.multiple = pyo.Var(model.setShifts, within = pyo.Integers, bounds=(0.0, None))
    q = model.multiple

    model.understaffing = pyo.Var(model.setTime, within = pyo.Integers, bounds=(0.0, None))
    us = model.understaffing
    
    model.overstaffing = pyo.Var(model.setTime, within = pyo.Integers, bounds=(0.0, None))
    os = model.overstaffing
    
    model.demand_diff = pyo.Var(within = pyo.Integers)
    demand_diff = model.demand_diff
    
    
    
    
    ##### Objective Function #####

    # First Objective Function 
    model.obj_demand = pyo.Objective(expr = sum([us[t] + os[t] for t in model.setTime]), sense = pyo.minimize)

    # Optional First Objective Functon
    model.op_obj_demand = pyo.Objective(expr = cost_weight*((z - minimum_cost)/cost_normalization_range) + demand_diff_weight*((demand_diff - minimum_demand_diff)/demand_diff_normalization_range), sense = pyo.minimize)

    # Second Objective Function
    model.obj_costs = pyo.Objective(expr = z, sense = pyo.minimize)


    ##### s.t. #####

    # Team Allocation
    model.C1 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C1.add(expr = x[s] <= y[s]*Cap_max)

    model.C2 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C2.add(expr = x[s] >= y[s])

    # Make x a multiple of TS
    model.C3 = pyo.ConstraintList()
    for s in model.setShifts:
        model.C3.add(expr = x[s] == TS * q[s]) 

    # cover all periods in horizon with at least one shift
    model.C4 = pyo.ConstraintList()
    for t in model.setTime:
        model.C4.add(expr = sum(y[s] for s in model.setDayShifts[t]) >= 1)

    # Max Allocation
    model.C5 = pyo.ConstraintList()
    for t in model.setTime:
        model.C5.add(expr = sum(x[s] for s in model.setDayShifts[t]) <= Cap_max)

    # Cost
    model.C7 = pyo.Constraint(expr = z == sum(C_Shift[s]*x[s] for s in model.setShifts))

    
    # Understaffing & Overstaffing
    model.C8 = pyo.ConstraintList()
    for t in model.setTime:
        model.C8.add(expr= sum(x[s] for s in model.setDayShifts[t]) + us[t] - os[t] == E[t])
    
    # Demand Diff
    model.C9 = pyo.Constraint(expr = demand_diff == sum([under_weight * us[t] + over_weight * os[t] for t in model.setTime]))
    
    return model


def optimize_soft(model, optimize : str):
    opt = SolverFactory('scipampl')
    if optimize.lower() == "cost":
        model.obj_demand.deactivate()
        model.op_obj_demand.deactivate()
    elif optimize.lower() == 'demand':
        model.obj_costs.deactivate()
        model.op_obj_demand.deactivate()
    else:  
        model.obj_costs.deactivate()
        model.obj_demand.deactivate()
    results = opt.solve(model, tee=False)
    return model, results

