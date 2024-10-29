import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition
import time 
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

#################### Optimeringsmodell ####################
def labor_scheduling(df_index:list, demand:list, MaxStaff:int\
                     , patients_staff:int, availability:int, ServiceLevel:float, night: bool):
    '''
    Function holding the actual model.

    params:
            df_index: Expected value list. The dates for each row in the dataset. 
            demand: Expected value list. The demand of incoming patients each time period.
            MaxStaff. Expected value integer. The maximum staff allowed in the post each shift/time period. 
            patients_staff: Expected value integer. Number of patients each staff can handle simultaneously. 
            availability: Expected value integer. Number of staff ready to be put into a shift. 
            ServiceLevel: Expected value float. How good should the service be? If 1 then zero waiting time for patients before getting attention. 

    output: returns the model. 
    ''' 
    # Creating model instance
    model = pyo.ConcreteModel()

    #### Sets ####
    model.setShift = pyo.Set(initialize=df_index)


    #### Parameters ####
    
    # Static variable of night vs day
    if night == True:
        need = 0.33
    else:
        need = 1

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
        model.C1.add(expr = x[s] >= need*(SL*(D[s]/PPS)))

    # Staff Availability
    model.C2 = pyo.ConstraintList()
    for s in model.setShift:
        model.C2.add(expr = x[s] <= A[s])

    # Capacity
    model.C3 = pyo.ConstraintList()
    for s in model.setShift:
        model.C3.add(expr = x[s] <= Cap)


    return model


#################### Optimeringsalgoritme ####################
def optimize_staffing(model):
    '''
    Function to run and optimize the model.

    params:
            model: The actual mathematical model to be optimized.  

    output: returns the optimized model, the status, the objective function value, and the staffed allocated each shift/time period. 
    ''' 
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


#################### Plot av Optimal bemanning ####################
def staff_opt_plot(staff_allocated: list, fin: int, siv: int, unn: int):
    '''
    Function to plot the optimized model.

    params:
            staff_allocated: Expected value list. The list of optimized staff allocated to each shift/time period. 

    output: returns a plot. 
    ''' 
    # Plot staffing requirements
    plt.figure(figsize=(10, 6))
    plt.plot(staff_allocated, marker='o', color='g', linestyle='-')
    plt.axhline(y=fin, color="r", linewidth = 2, linestyle = "-", label = "Fin")
    plt.axhline(y=siv, color="b", linewidth = 2, linestyle = "-", label = "SiV")
    plt.axhline(y=unn, color="y", linewidth = 2, linestyle = "-", label = "UNN")
    plt.title('Bemanning for post hos Finnmarksykehuset')
    plt.xlabel('Time i perioden')
    plt.ylabel('Antall nødvendig bemanning')
    plt.grid(True)
    plt.tight_layout()
    plt.legend(loc = "upper right")
    plt.show()