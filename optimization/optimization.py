import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition
import time 
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

#################### Optimeringsmodell ####################
def labor_scheduling(df_index:list, demand:list, MaxStaff:int\
                     , patients_staff:int, availability:int, ServiceLevel:float):
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
def staff_opt_plot(staff_allocated: list, fin: int, siv: int, unn: int, dag: bool= True):
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
    if not dag:
        plt.axhline(y=unn, color="y", linewidth = 2, linestyle = "-", label = "UNN")
    plt.title('Bemanning for post hos Finnmarksykehuset')
    plt.xlabel('Time i perioden')
    plt.ylabel('Antall nødvendig bemanning')
    plt.grid(True)
    plt.tight_layout()
    plt.legend(loc = "upper right")
    plt.show()

#################### Calculate costs ####################
def hourly_cost_calc(row: pd.Series, weekend: bool = False) -> float:
    if row["skift_type"] == "dag":
        cost = 320
    elif row["skift_type"] == "kveld":
        cost = 320 + 20
    elif row["skift_type"] == "natt":
        cost = 320 + 100

    if weekend:
        cost *= 1.5
    
    return cost

#################### Weight nightshifts ####################
def nightshift_weight(row: pd.Series) -> pd.Series:
    if row["skift_type"] == "natt":
        row["Belegg"] = row["Belegg"]*0.25
    return row

#################### Adjust staff if 0 is needed ####################
def adjust_staff(row: pd.Series) -> pd.Series:
    if row["staff_allocated"] == 0:
        row["staff_allocated"] = 1
    return row

#################### Model for optimizing for cost ####################
def opt_cost_model(df_index:list, numEmp:list, shifts:list, shiftLengths:list, hourly_cost:list):
    # Model
    model = pyo.ConcreteModel()

    # Sets
    model.T = pyo.Set(initialize=df_index)
    model.Shifts = pyo.Set(initialize=shifts)
    model.PossibleStartTimes = pyo.RangeSet(5, 23)
    model.PossibleLengths = pyo.Set(initialize=shiftLengths) 

    # Parameters

    ## Patients at work
    emp_dict = {df_index[i]: numEmp[i] for i in range(len(df_index))}
    model.E = pyo.Param(model.T, initialize = emp_dict, within= pyo.Integers)
    E = model.E

    ## Cost of hour
    cost_dict = {df_index[i]: hourly_cost[i] for i in range(len(df_index))}
    model.C = pyo.Param(model.T, initialize = cost_dict, within= pyo.Integers)
    C = model.C


    ## Hour coverage binary parameter
    # 1 if shift s starting at `start` with `length` covers hour `t`, 0 otherwise
    delta_data = {}
    for s in model.Shifts:
        for start in model.PossibleStartTimes:
            for length in model.PossibleLengths:
                for t in model.T:
                    # Calculate whether the shift covers hour `t`
                    if (start <= t < start + length) or (start + length > 24 and (t < (start + length) % 24)):
                        delta_data[(s, start, length, t)] = 1
                    else:
                        delta_data[(s, start, length, t)] = 0

    model.z = pyo.Param(model.Shifts, model.PossibleStartTimes, model.PossibleLengths, model.T, initialize=delta_data, within=pyo.Binary)
    z = model.z


    # Decision Variables

    ## Binary variable indicating if a shift starts at a certain time with a certain length
    model.y = pyo.Var(model.Shifts, model.PossibleStartTimes, model.PossibleLengths, domain=pyo.Binary)
    y = model.y

    ## Total cost of hour
    model.x = pyo.Var(model.T, domain=pyo.NonNegativeIntegers, bounds = (0,None))
    x = model.x

    ## Total cost of selected shifts
    # model.q = pyo.Var(domain=pyo.NonNegativeIntegers, bounds = (0,None))
    # q = model.q


    # Objective function: Minimize total cost of selected shifts
    model.obj = pyo.Objective(expr=sum(x[t] for t in model.T), sense=pyo.minimize)


    # Constraints

    ## Cost of hour
    model.C1 = pyo.Constraint(rule= x[t] == sum(C[t] * E[t] for t in model.T))

    ## Coverage Hours and shifts
    # Ensure each hour `t` is covered by exactly one shift
    model.C2 = pyo.ConstraintList()
    for t in model.T:
        model.C2.add(
            sum(
                y[s, start, length] * z[s, start, length, t]
                for s in model.Shifts
                for start in model.PossibleStartTimes
                for length in model.PossibleLengths
            ) == 1
        )

    ## Hour of day coverage
    # Ensure total coverage sums to exactly 24 hours
    model.C3 = pyo.Constraint(
        expr=sum(
            y[s, start, length] * z[s, start, length, t]
            for s in model.Shifts
            for start in model.PossibleStartTimes
            for length in model.PossibleLengths
            for t in model.T
        ) == 24
    )

    ## Objective function definition
    # model.C4 = pyo.Constraint(rule= q == sum(x[t] * y[s,b,l] for t in model.T 
    #                                    for s in model.Shifts 
    #                                    for b in model.PossibleStartTimes 
    #                                    for l in model.PossibleLengths))

    # Solve
    solver = pyo.SolverFactory('glpk')
    solver.solve(model, tee=True)


    # Output results
    shift_results = []
    for s in model.Shifts:
        for start in model.PossibleStartTimes:
            for length in model.PossibleLengths:
                if pyo.value(y[s, start, length]) > 0.5:
                    shift_results.append(f"Shift {s} starts at hour {start} with length {length}")

    obj = pyo.value(model.obj)
    print(f"Total cost for optimal day: {obj}kr")

    return shift_results, obj