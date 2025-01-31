import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from pyomo.opt import TerminationCondition
import time 
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


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


def behovsdekning_lineplot(curr_sit:int, sim_avg_nurses:list) -> plt:
    curr_sit = curr_sit
    nurses_needed_per_shift = sim_avg_nurses
    actual_nurses = [i for i in range(max(nurses_needed_per_shift) + 6)]             
    total_shifts = len(nurses_needed_per_shift)
    staff_dict = {}

    for staffing in actual_nurses:
        understaffed_shifts = 0
        overstaffed_shifts = 0
        for nurse in sim_avg_nurses:
            if nurse > staffing:
                understaffed_shifts += 1
            elif nurse < staffing:
                overstaffed_shifts += 1


        prosent_underbemannet_skift = understaffed_shifts / total_shifts * 100
        prosent_overbemannet_skift = overstaffed_shifts / total_shifts * 100
        prosent_riktig_bemannet = 100 - (prosent_underbemannet_skift + prosent_overbemannet_skift)
        prosent_til_figur = prosent_overbemannet_skift + prosent_riktig_bemannet
        staff_dict[staffing] = prosent_til_figur

    # staff_dict = {key: value for key, value in staff_dict.items() if value > 95}
    staffing = list(staff_dict.keys())
    coverage = list(staff_dict.values())

    staffing_exceeding_90 = next(key for key, value in staff_dict.items() if value > 95)
    plt.plot(staffing, coverage, marker='x', linestyle='-', color='b')

    plt.axvline(x=curr_sit, color='r', linestyle='--', label='x=12')
    plt.axvline(x=staffing_exceeding_90, color='g', linestyle='--', label=f'Staffing > 90%: x={staffing_exceeding_90}')

    plt.xlabel('Antall ansatte')
    plt.ylabel('Behovsdekning (%)')
    plt.title('Behovsdekning ved ulike Bemanningsnivåer')
    plt.grid(False)
    plt.show()
    return staffing_exceeding_90


def verifiseringsmodellen(fin_data_hourly: pd.DataFrame, PPP: int, staff_level: int) -> plt:
    test_df = fin_data_hourly[(fin_data_hourly["År"] == 2024) & (fin_data_hourly["post"] == "medisinsk")
                    & (fin_data_hourly["skift_type"] == "kveld") & (fin_data_hourly["helg"] == 0)]

    month = ["January", "February","March", "April", "May", "June", "July", "August", "September"]
    data = test_df.query(f"Måned in {month}")


    needed_nurses_intensity = []

    belegg = data["Belegg"].tolist()
    nurses_min = [staff_level]*len(belegg)
    PPP = PPP
    for b, n_min in zip(belegg, nurses_min):
        SI = b / (n_min * PPP) 
        needed_nurses_intensity.append(SI)


    needed_nurses_intensity_rounded = [round(intensity, 2) for intensity in needed_nurses_intensity]
    avg = sum(needed_nurses_intensity_rounded)/len(needed_nurses_intensity_rounded)
    over = []
    correct = []
    for i in needed_nurses_intensity_rounded:
        if i > 1:
            over.append(i)
        else:
            correct.append(i)

    pct_over = len(over)/len(needed_nurses_intensity_rounded)*100

    print(avg)
    print(pct_over)

    plt.figure(figsize=(10, 6))
    plt.plot(needed_nurses_intensity_rounded, marker='o', color='g', linestyle='-')
    plt.title('Variasjon i skiftintensitet for post hos Finnmarksykehuset')
    plt.axhline(y=1.0, color="r", linewidth = 2, linestyle = "-")
    plt.xlabel('Time i perioden')
    plt.ylabel('Skiftintensitet')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def create_dummy_employee_data(num_emp: int, FTEs:int, num_part_time: int, num_weeks: list) -> pd.DataFrame:
    emps = num_emp +1
    employees = list(range(1, emps))

    # Stillingsprosenter
    values = [1.0] * FTEs + [0.5] * num_part_time #+ [0.5] * 2 + [0.4] * 1
    np.random.shuffle(values)

    emp_pospct_df = pd.DataFrame({
        'Ansatt': employees,
        'Stillingsprosent': values
    })

    num_weeks = num_weeks
    emp_pospct_df['Weekend_Work'] = 3
    emp_pospct_df['7Day_Working_Hours'] = 40
    emp_pospct_df["Max_Work_Hours"] = emp_pospct_df["Stillingsprosent"] * 35 * num_weeks
    
    return emp_pospct_df


def create_df(sim_avg_nurses: list, function) -> pd.DataFrame:
    datetime_range = pd.date_range(start='2024-01-01 00:00', end='2024-02-28 23:00', freq='H')
    df = pd.DataFrame({'Datetime': datetime_range})
    df["År"] = df['Datetime'].dt.year
    df["Måned"] = df['Datetime'].dt.month_name()
    df["Dag"] = df["Datetime"].dt.day_name()
    df["Uke"] = df["Datetime"].dt.isocalendar().week
    df['helg'] = df['Datetime'].dt.weekday.apply(lambda x: 1 if x >= 5 else 0)
    df["Timer"] =df['Datetime'].dt.hour
    df["Timer"] = df["Timer"].astype(int)
    df["skift_type"] = df.apply(function, axis=1)

    # sim_avg_nurses +=[5,4,3,6,5,4]*4
    df['demand'] = sim_avg_nurses
    df['dato'] = df['Datetime'].dt.date
    df['day_of_year'] = df['Datetime'].dt.dayofyear
    result = df.groupby(['dato',"Uke","day_of_year", 'Dag', 'skift_type'])['demand'].max().reset_index()

    num_weeks = max(df["Uke"].tolist())

    return result, num_weeks


def update_demand(row):
    if row['Dag'] in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]: 
        if row['skift_type'] == 'dag':
            return 7
        elif row['skift_type'] == 'kveld':
            return 7
        elif row['skift_type'] == 'natt':
            return 3
    elif row['Dag'] in ["Saturday", "Sunday"]:
        if row['skift_type'] == 'dag':
            return 4
        elif row['skift_type'] == 'kveld':
            return 5
        elif row['skift_type'] == 'natt':
            return 2
    return row['demand']


from collections import OrderedDict, defaultdict

def opt_staffing_model(demand: list, days: list, shifts: list, employees: list, position_percentage: list, weeks: list, day_of_year:list, shift_lengths: list, 
                       weekend_work: list, weekly_hours: list, max_workinghours: list):
    

    model = pyo.ConcreteModel()

    #### Sets ####
    model.Shift_type = pyo.Set(initialize=shifts)
    model.Employees = pyo.Set(initialize = employees)
    model.Days = pyo.Set(initialize = days)
    model.Week = pyo.Set(initialize = weeks)
    model.DoY = pyo.Set(initialize = day_of_year)



    ## Parameters ##

    # Bemanningsbehov
    behov_dict = {
        (shift, day): int(demand[(day - 1) * len(shifts) + shift_idx])
        for day in day_of_year
        for shift_idx, shift in enumerate(shifts)
    }
    behov_dict = OrderedDict(sorted(behov_dict.items(), key=lambda x: x[0][1]))
    behov_dict = dict(behov_dict)

    model.B = pyo.Param(model.Shift_type, model.DoY, initialize = behov_dict, within = pyo.Integers)
    B = model.B # Bemanningsbehov

    
    
    # Stillingsstr
    position_percentage_dict = {
    employees[i]: position_percentage[i]
    for i in range(len(employees))
    }

    model.SP = pyo.Param(model.Employees, initialize = position_percentage_dict, within = pyo.PercentFraction)
    SP = model.SP # Stillingsprosent

    
    
    # Shift varighet

    hours_dict = {}
    for shift_idx, shift in enumerate(shifts): # [:-1]
        hours_dict[shift]= shift_lengths[shift_idx]
    # hours_dict["Fri"] = 0

    model.H = pyo.Param(model.Shift_type, initialize = hours_dict, within = pyo.Integers)
    H = model.H # Hours
    

    
    # Weekend work
    weekend_work_dict = {
    employees[i]: weekend_work[i]
    for i in range(len(employees))
    }
    model.WW = pyo.Param(model.Employees, initialize = weekend_work_dict, within = pyo.Integers) 
    WW = model.WW # Weekend Work --> Brukes ikke!?



    # Maximum working hour during a week
    weekly_hours_dict = {
    employees[i]: weekly_hours[i]
    for i in range(len(employees))
    }    
    model.WH = pyo.Param(model.Employees, initialize = weekly_hours_dict, within = pyo.Integers) 
    WH = model.WH # Weekly Hours

    
    
    # Maximum working hours during planning horizon
    maxhours_dict = {
    employees[i]: max_workinghours[i]
    for i in range(len(employees))
    }
    model.MaxWH = pyo.Param(model.Employees, initialize = maxhours_dict, within = pyo.NonNegativeReals) 
    MaxWH = model.MaxWH # Maximum Working Hours --> Bruker ikke denne foreløpig?!



    # Number of weekends in period 
    model.MWEL = pyo.Param(initialize = max(weeks), within = pyo.Integers)
    MWEL = model.MWEL



    ## Decision Variables ##
    
    ## Binary variable indicating if employee e works shift type s on day of year n
    model.x = pyo.Var(model.Employees, model.Shift_type, model.DoY, within=pyo.Binary)
    x = model.x # Employee allocation variable

    # # Minimum employees needed
    model.z = pyo.Var(model.Employees, within=pyo.Binary)
    z = model.z

   # Aux variable for å lagre summen av skift for hver ansatt over en viss periode
    model.work_in_window = pyo.Var(model.Employees, model.DoY, within=pyo.NonNegativeIntegers)

   # Aux variable for å lagre summen av helgeshift for hver ansatt
    model.weekend_shifts = pyo.Var(model.Employees, model.DoY, domain=pyo.NonNegativeIntegers)
    


    ## Objective Function ##
    model.obj_min_staff = pyo.Objective(expr= sum(SP[e]*z[e] for e in model.Employees), sense=pyo.minimize)  #antall ansatte som trengs



    ## Constraints ## 

    # Demand constraint
    model.C1 = pyo.ConstraintList()
    for s in model.Shift_type:
        for n in model.DoY: 
            model.C1.add(expr = sum(x[e,s,n] for e in model.Employees) >= B[s,n])

    # Max working hours in timeperiod
    model.MaxHours = pyo.ConstraintList()
    for e in model.Employees:
        model.MaxHours.add(expr=sum(H[s]*x[e,s,n] for s in model.Shift_type for n in model.DoY) <= MaxWH[e])
    

    employees_by_contract_size = defaultdict(list)
    for e in model.Employees:
        employees_by_contract_size[SP[e]].append(e)

    # Ensure each group is sorted
    for group in employees_by_contract_size.values():
        group.sort()

    # Add symmetry-breaking constraints
    model.C_symmetry_breaking = pyo.ConstraintList()
    for c, employees in employees_by_contract_size.items():
        for i in range(1, len(employees)):
            prev_employee = employees[i - 1]
            current_employee = employees[i]
            model.C_symmetry_breaking.add(expr=z[prev_employee] <= z[current_employee])


    # Obj.fct. constraint
    M = len(demand)
    model.C2 = pyo.ConstraintList()
    for e in model.Employees:
        model.C2.add(expr=sum(x[e,s,n] for s in model.Shift_type for n in model.DoY) <= z[e]*M)

    
    # # Required Rest
    # model.C4 = pyo.ConstraintList() # denne fjernes fordi den blir dekket av påfølgende skift constraint lenger ned
    # for e in model.Employees:
    #     for n in model.DoY:
    #         # if n >= 2:
    #         model.C4.add(expr = x[e,"Natt", n] + sum(x[e,s,n] for s in model.Shift_type if s == "Dag" or s == "Kveld") <= 1)

    model.C5 = pyo.ConstraintList()
    for e in model.Employees:
        for n in model.Days:
            if n >= 2:
                model.C5.add(expr=x[e,"Kveld",n-1] + x[e,"Natt",n] <= 1)
            
    # model.C6 = pyo.ConstraintList() # denne fjernes fordi ikke lenger inkluderer "fri" som en skift type
    # for e in model.Employees:
    #     for w in model.Week:
    #         model.C6.add(expr=sum(x[e,"Fri", n] for n in model.DoY) >= 1)
    
    
    
    seven_day_windows = {n: list(range(n-6, n+1)) for n in model.DoY if n >= 7}
    
    # 7 day period working hours constraint
    model.C3 = pyo.ConstraintList()
    for e in model.Employees:
        for n, window in seven_day_windows.items(): 
            model.C3.add(
                expr=sum(H[s] * x[e, s, n_range] for s in model.Shift_type for n_range in window) <= WH[e]
            )
    
    model.C7 = pyo.ConstraintList()
    for e in model.Employees:
        for n in seven_day_windows:
            model.C7.add(expr=model.work_in_window[e, n] == sum(x[e, s, n_range] for s in model.Shift_type for n_range in seven_day_windows[n]))
            model.C7.add(expr=model.work_in_window[e, n] <= 6) 

    # # Weekends
    
    # Work sunday = work saturday
    weekend_days = {n: True for n in model.DoY if n % 7 == 0}
    model.C8 = pyo.ConstraintList()
    for e in model.Employees:
        for n in weekend_days: 
            prev_day = n - 1  
            curr_day = n      
            # Sum over alle shift typer for å sjekke at employee jobber både lør og søn
            model.C8.add(
                expr=sum(x[e, s, prev_day] for s in model.Shift_type) >= 
                sum(x[e, s, curr_day] for s in model.Shift_type)
            )

    # Tredjehver helg 
    model.C9 = pyo.ConstraintList()
    for e in model.Employees:
        for n in weekend_days:
            # Auxiliary variabel som representerer summen av shift jobbet for ansatt e på helgdag n
            model.C9.add(expr=model.weekend_shifts[e, n] == sum(x[e, s, n] for s in model.Shift_type))
    # Sørg for at hver ansatt jobber 1/3 av alle helgedager
        model.C9.add(
            expr=sum(model.weekend_shifts[e, n] for n in model.DoY if n in weekend_days) == int(MWEL / 3)
    )

    # Maks tre natt på rad
    model.C10 = pyo.ConstraintList()
    for e in model.Employees:
        for n in model.DoY:
            if n >= 4:
                model.C10.add(expr=x[e,"Natt", n] + x[e,"Natt",n-1] + x[e,"Natt",n-2] + x[e,"Natt",n-3] <= 3)

    # Påfølgende skift etter natt
    model.C11 = pyo.ConstraintList()
    for e in model.Employees:
        for n in model.DoY:
            # if n >= 2:
            model.C11.add(expr=x[e,"Natt",n] + x[e,"Dag",n] + x[e,"Kveld",n] <= 1)



    opt = SolverFactory('glpk')
    opt.options["tmlim"] = 600
    # opt.options["mipgap"] =0.05
    status = opt.solve(model, tee=True) # , keepfiles = True, logfile="glpk.log", solnfile="solution.sol"
    # model.pprint()

    if status.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]:
        print("Løsning funnet!")
        # Retrieve objective value
        obj = pyo.value(model.obj_min_staff)
        staff_allocated = {}
        for i in model.x:
            staff_allocated[i] = pyo.value(model.x[i])
        return None, status, obj, staff_allocated



    # Retrieve staff allocated for each shift
    # staff_allocated = [pyo.value(x[e,s,n]) for e in model.Employees for s in model.Shift_type for n in model.DoY]


    # Check if the model was solved successfully
    if status.solver.termination_condition != TerminationCondition.optimal:
        print("Solver did not converge to an optimal solution.")


    return None, status, None, None



def adhoc_plot(data: pd.DataFrame, tids_granulitetsniv: str = "Timer", value: str = "Demand", skift_type: str = None, aggregation_level: str = "mean"):
    # Group by timer og post, og finn gjennomsnittet av etterspørselen
    week_order = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

    if aggregation_level == "mean":
        avg_patients_per_hour = data.groupby([tids_granulitetsniv, 'post'])[value].mean().reset_index()
    elif aggregation_level == "sum":
        if tids_granulitetsniv == "Dag":
            avg_patients_per_hour = data.groupby([tids_granulitetsniv, 'post'])[value].sum().reset_index()
            avg_patients_per_hour[tids_granulitetsniv] = pd.Categorical(avg_patients_per_hour[tids_granulitetsniv], categories=week_order, ordered=True)
            avg_patients_per_hour = avg_patients_per_hour.sort_values(tids_granulitetsniv)
        else:
            avg_patients_per_hour = data.groupby([tids_granulitetsniv, 'post'])[value].sum().reset_index()
    
    if skift_type is None:
        avg = data[value].mean()    
    else:
        avg = data[data["skift_type"] == skift_type][value].mean()
    print(f"Gjennomsnittlig {value} målt i {tids_granulitetsniv}: {avg} pasienter pr {tids_granulitetsniv}")
   
    # Pivot for lettere plotting
    pivot_data = avg_patients_per_hour.pivot(index=tids_granulitetsniv, columns='post', values=value)
    pivot_data.plot(kind='bar', width=0.8, figsize=(12, 6), color=['skyblue','salmon'])
    plt.title(f"Gjennomsnittlig {value} per post i 2024")
    plt.xlabel(f"{tids_granulitetsniv} i tidsperioden")
    plt.ylabel("Gjennomsnittlig antall pasienter")
    plt.xticks(rotation=0)
    plt.legend(title="Post")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()