import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition
import time 
import pandas as pd 
import numpy as np

def labor_scheduling(df_index:list, demand:list, MaxStaff:int\
                     , patients_staff:int, availability:int, ServiceLevel:float):
    
    # Creating model instance
    model = pyo.ConcreteModel()

    #### Sets ####
    model.setShift = pyo.Set(initialize=df_index)


    #### Parameters ####
    
    # Demand of Patients
    demand_dict = {df_index[i]: demand[i] for i in range(len(df_index))}
    model.D = pyo.Param(model.setShift, initialize = demand_dict, within = pyo.Integers)
    D = model.D

    # Maximum capacity of staff for each shift
    model.MaxStaff = pyo.Param(initialize = MaxStaff, within = pyo.Integers)
    Cap = model.MaxStaff

    # Number of patients each staff can handle at the same time
    model.PatientsPerStaff = pyo.Param(initialize = patients_staff, within = pyo.Integers)
    PPS = model.PatientsPerStaff

    # Available staff at the time of an occuring shift
    availability_dict = {df_index[i]: availability for i in range(len(df_index))}
    model.AvailableStaff = pyo.Param(model.setShift, initialize = availability_dict, within = pyo.Integers)
    A = model.AvailableStaff

    # Service Level
    model.ServiceLevel = pyo.Param(initialize= ServiceLevel, within = pyo.PercentFraction)
    SL = model.ServiceLevel

    #### Decision Variables ####
    
    # Number of staff members allocated to a shift
    model.Staff_Allocated = pyo.Var(model.setShift, within = pyo.NonNegativeIntegers, bounds=(0, None))
    x = model.Staff_Allocated


    #### Objective Function ####

    # Minimize total staff allocated across all shifts
    model.obj_min_staff = pyo.Objective(expr=sum(x[s] for s in model.setShift), sense=pyo.minimize)



    #### Constraints ####

    # Demand Coverage Constraint
    model.C1 = pyo.ConstraintList()
    for s in model.setShift:
        model.C1.add(expr = x[s] >= SL*(D[s]/PPS))

    # Staff Availability
    model.C2 = pyo.ConstraintList()
    for s in model.setShift:
        model.C2.add(expr = x[s] <= A[s])

    # Capacity
    model.C3 = pyo.ConstraintList()
    for s in model.setShift:
        model.C3.add(expr = x[s] <= Cap)


    return model


def optimize_staffing(model):
    opt = SolverFactory('glpk')
    status = opt.solve(model, tee=True)

    # Check if the model was solved successfully
    if status.solver.termination_condition != TerminationCondition.optimal:
        print("Solver did not converge to an optimal solution.")
        return None, status, None, None

    # Retrieve objective value
    obj = pyo.value(model.obj_min_staff)

    # Retrieve staff allocated for each shift
    staff_allocated = [pyo.value(model.Staff_Allocated[s]) for s in model.setShift]

    return model, status, obj, staff_allocated