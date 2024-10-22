import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import random


######################## Monte Carlo Functions ########################
def monte_carlo_simulation(data: pd.DataFrame, total_beds: int, average_stay: int, num_simulations: int, post: str, weekend: bool = False, predictions: bool = False, year: int = 2024, scenario: str = None):
    '''
    Function to perform monte carlo simulations to simulate the demand side.

    params:
            data: Expected value pandas dataframe. Full dataset to be filtered
            
            total_beds: Expected value integer. The total number of beds at the hospitaal dept. post. 
            
            average_stay: Expected value integer. The average stay (in days) of the patients in the post. 
            
            num_simulations: Expected value integer. The number of monte carlo simulations to be ran be the function. 
            
            post: Expected string value. The post at the hospital to filter on
            
            weekend: Expected boolean value. Default False, if True -> filter dataset by weekend values
            
            predictions: Expected boolean value. Default False, if True -> filter dataset on future forecasted values only
            
            year: Expected value integer. Default value 2024, if else -> filter by year of choice
            
            scenario: Expected string value. Default None, if else -> filter values on the scenario of choice

    output: returns information from the simulation. 
    '''
    
    if post == "medisinsk":
        df_fin = data[data["post"] == "medisinsk"]
    elif post == "kirurgisk":
        df_fin = data[data["post"] == "kirurgisk"]
    
    if weekend == True:
        df_fin = df_fin[df_fin["helg"] == 1]
    else:
        df_fin = df_fin[df_fin["helg"] == 0]

    if predictions == True:
        df_fin = df_fin[df_fin["År"] == 2025]
        df_fin["Antall inn på post"] = df_fin["Prediksjoner pasientstrøm"]
        df_fin["Belegg pr. dag"] = df_fin["Prediksjoner belegg"]
    else:
        df_fin = df_fin[df_fin["År"] == year]

    
    if scenario == "helligdag":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "høytid":
        if df_fin["Antall inn på post"] >=2:
            df_fin["Antall inn på post"] = df_fin["Antall inn på post"] - 2
            df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] - 2

    elif scenario == "ulykke":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "krig":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 30
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 30

    
    if year == 2024:
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"].fillna(df_fin["Prediksjoner pasientstrøm"])
    df_fin = df_fin.reset_index()
    df_index = df_fin.index.values
    df_index = [x +1 for x in df_index]
    df_fin["day of year"] = df_index
    
    

    total_bed_occupancy_overall = 0
    total_overloaded_days = 0
    total_patients_waiting = 0
    total_patients_admitted = 0
    
    # For visualiseringen
    all_overload_days = [] 
    all_occupancy_percents = []
    
    for sim in range(num_simulations):
        beds_occupied = []
        daily_overload = 0  # dager med overbelastning
        bed_occupancy = 0   # belegget
        
        # For visualiseringer
        if sim == 0:  
            daily_occupancy_record = []  
        
        for index, row in df_fin.iterrows(): 
            beds_occupied = [stay for stay in beds_occupied if stay > row["day of year"]] # Oppdater senger
            new_patients = row["Antall inn på post"]
            total_patients_admitted += int(new_patients)


            overload_today = False

            # Sjekk om det er en ledig seng
            for _ in range(int(new_patients)):
                if len(beds_occupied) < total_beds:

                    # Tildel en seng og definer hvor lenge de vil ligge inne
                    stay_duration = max(1, int(np.random.normal(average_stay, 2)))  # Normalfordeling
                    beds_occupied.append(row["day of year"] + stay_duration)
                else:
                    # Overbelastning, pasient må vente
                    overload_today = True
                    total_patients_waiting += 1
            if overload_today:
                daily_overload += 1
            
            bed_occupancy += len(beds_occupied) / total_beds

            if sim == 0:
                daily_occupancy_record.append(len(beds_occupied) / total_beds)

        total_overloaded_days += daily_overload
        total_bed_occupancy_overall += bed_occupancy / df_fin["day of year"].max()
        all_overload_days.append(daily_overload)
        
        if sim == 0:
            all_occupancy_percents = daily_occupancy_record

    # Beregn gjennomsnittlig overbelastning, beleggsprosent og sannsynlighet
    avg_overload_days = total_overloaded_days / num_simulations
    avg_occupancy_percentage = (total_bed_occupancy_overall / num_simulations) * 100
    waiting_probability = total_patients_waiting / total_patients_admitted
    
    return df_fin, avg_overload_days, avg_occupancy_percentage, waiting_probability, all_overload_days, all_occupancy_percents


def monte_carlo_dager_overbelastning(all_overload_days: list):
    '''
    Function to plot the overload of patients from the simulation.

    params:
            all_overload_days: All days from the simulations which indicated overload. 

    output: returns a plot. 
    '''
    # 1. antall dager med overbelastning
    plt.figure(figsize=(10, 6))
    plt.hist(all_overload_days, bins=20, color='skyblue', edgecolor='black')
    plt.title('Antall dager med overbelastning i 1000 simuleringer')
    plt.xlabel('Antall dager med overbelastning')
    plt.ylabel('Antall simuleringer')
    plt.grid(True)
    plt.show()

def monte_carlo_beleggsprosent(data: pd.DataFrame, all_occupancy_percents: list):
    '''
    Function to plot the occupancy of patients from the simulation.

    params:
            data: the data used for the plot. 
            all_occupancy_percents: All occupancy percents from the simulation output. 

    output: returns a plot. 
    '''
    # 2. daglig beleggsprosent for én simulering (visualisere årets belastning)
    plt.figure(figsize=(10, 6))
    days_in_plot = range(data["day of year"].min(), data["day of year"].max()+1)
    plt.plot(days_in_plot, np.array(all_occupancy_percents) * 100, color='blue')
    plt.title('Daglig beleggsprosent for ett år (én simulering)')
    plt.xlabel('Dag')
    plt.ylabel('Beleggsprosent (%)')
    plt.grid(True)
    plt.show()

def monte_carlo_waiting_probability(waiting_probability: float):
    '''
    Function to plot the waiting probability for patients from the simulation.

    params:
            waiting_probability: The waiting probability for patients in the simulations.  

    output: returns a plot. 
    '''
    # 3. sannsynlighet for at pasienter må vente på seng
    plt.figure(figsize=(6, 6))
    labels = ['Fikk seng umiddelbart', 'Måtte vente på seng']
    sizes = [1 - waiting_probability, waiting_probability]
    colors = ['lightgreen', 'salmon']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title('Sannsynlighet for at pasienter må vente på seng')
    plt.axis('equal')
    plt.show()


######################## Bemanningsnivå og Skiftdesign ########################
def over_under_staffed_shifts(data: pd.DataFrame, staff_needed: pd.Series, avg_length_of_stay: int, shifts_per_day: int, iterations: int, post: str, weekend: bool = False, predictions: bool = False, year: int = 2024, scenario: str = None):
    '''
    Function to perform simulations to simulate the service side and the overstaffed vs understaffed shifts/days.

    params:
            data: Expected value pandas dataframe. Full dataset to be filtered
            
            staff_needed: Expected value pandas series (a column). The optimal number of staff needed (output of the optimization model) for each day. 
            
            average_length_of_stay: Expected value integer. The average stay (in days) of the patients in the post. 
            
            shifts_per_day: Expected value integer. The number of shifts in a day. 
            
            iterations: Expected value integer. The number of monte carlo simulations to be ran be the function. 
            
            post: Expected string value. The post at the hospital to filter on
            
            weekend: Expected boolean value. Default False, if True -> filter dataset by weekend values
            
            predictions: Expected boolean value. Default False, if True -> filter dataset on future forecasted values only
            
            year: Expected value integer. Default value 2024, if else -> filter by year of choice
            
            scenario: Expected string value. Default None, if else -> filter values on the scenario of choice

    output: returns information about the simulation. 
    '''
    if post == "medisinsk":
        df_fin = data[data["post"] == "medisinsk"]
    elif post == "kirurgisk":
        df_fin = data[data["post"] == "kirurgisk"]
    
    if weekend == True:
        df_fin = df_fin[df_fin["helg"] == 1]
    else:
        df_fin = df_fin[df_fin["helg"] == 0]

    if predictions == True:
        df_fin = df_fin[df_fin["År"] == 2025]
        df_fin["Antall inn på post"] = df_fin["Prediksjoner pasientstrøm"]
        df_fin["Belegg pr. dag"] = df_fin["Prediksjoner belegg"]
    else:
        df_fin = df_fin[df_fin["År"] == year]
    
    if scenario == "helligdag":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "høytid":
        if df_fin["Antall inn på post"] >=2:
            df_fin["Antall inn på post"] = df_fin["Antall inn på post"] - 2
            df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] - 2

    elif scenario == "ulykke":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 15
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 10

    elif scenario == "krig":
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"] + 30
        df_fin["Belegg pr. dag"] = df_fin["Belegg pr. dag"] + 30

    if year == 2024:
        df_fin["Antall inn på post"] = df_fin["Antall inn på post"].fillna(df_fin["Prediksjoner pasientstrøm"])
    df_fin = df_fin.reset_index()
    df_index = df_fin.index.values
    df_index = [x +1 for x in df_index]
    df_fin["day of year"] = df_index
    df_fin["staff_needed"] = staff_needed

    understaffed_shifts = 0
    overstaffed_shifts = 0
    total_shifts = 0
    staffed_shifts_data = []

    for _ in range(iterations):
        yearly_understaffed_shifts = 0  # Teller hvor mange skift per år med underbemanning
        yearly_overstaffed_shifts = 0  # Teller hvor mange skift per år med overbemanning
        patients_on_ward = []  # Liste for å holde oversikt over pasienter som allerede ligger inne
        
        for index, row in df_fin.iterrows(): 
            new_admissions = row["Antall inn på post"]  # Simulerer nye pasienter
            lengths_of_stay = np.random.exponential(avg_length_of_stay, int(new_admissions))  # Simulerer liggetider

            # Legg til nye pasienter som skal legges inn
            patients_on_ward.extend(lengths_of_stay)
            
            # Oppdater liggetidene for pasienter som allerede er inne
            patients_on_ward = [stay - 1 for stay in patients_on_ward]  # Reduserer liggetiden med 1 for hver dag
            patients_on_ward = [stay for stay in patients_on_ward if stay > 0]  # Fjern pasienter som er utskrevet

            # Beregn total antall pasienter som trenger pleie i dag
            total_patients = len(patients_on_ward)

            # Beregn antall sykepleiere som trengs per skift
            # nurses_needed_per_shift = total_patients / patients_per_nurse / shifts_per_day
            nurses_needed_per_shift = row.staff_needed

            actual_nurses = 9  # Faktisk antall sykepleiere per skift

            # Simuler skiftene for dagen
            for shift in range(shifts_per_day):
                total_shifts += 1  # Oppdater totalt antall skift
                if nurses_needed_per_shift > actual_nurses:
                    understaffed_shifts += 1  # Underbemanning i dette skiftet
                    yearly_understaffed_shifts += 1  # Tell daglig underbemanning
                elif nurses_needed_per_shift < actual_nurses:
                    overstaffed_shifts += 1
                    yearly_overstaffed_shifts += 1
                staffed_shifts_data.append(nurses_needed_per_shift)
    return understaffed_shifts, overstaffed_shifts, total_shifts, staffed_shifts_data


def under_over_staffing_plot(staffed_shifts_data, iterations, shifts_per_day):
    '''
    Function to visualize the understaffed vs overstaffed simulated shifts.

    params:
            staffed_shifts_data: Data on how many staff is allocated each day, and whether or not it is under/overstaffed.
            iterations: number of simulations used
            shifts_per_day: number of shifts each day
    
    output: returns a plot of the simulation results. 
    '''
    # Forbered data for visualisering
    max_nurses_needed = int(max(staffed_shifts_data)) + 1  # Finn maksimum nødvendig sykepleiere
    shift_counts = [0] * max_nurses_needed  # Liste for å telle antall skift for hver sykepleier
    for nurses_needed in staffed_shifts_data:
        shift_counts[int(nurses_needed)] += 1

    # Konverter til gjennomsnitt over alle simuleringer
    average_shifts_needed = [count / iterations for count in shift_counts]

    # Visualisering av gjennomsnittlig bemanningsbehov
    plt.bar(range(max_nurses_needed), average_shifts_needed, color='orange')
    plt.xlabel('Antall sykepleiere nødvendig per skift')
    plt.ylabel('Gjennomsnittlig antall skift ila ett år')
    plt.title('Gjennomsnittlig antall skift per bemanningsbehov over ett år')
    plt.xticks(range(0, max_nurses_needed, 1))  # Vis alle unike verdier på x-aksen
    plt.ylim(0, 365 * shifts_per_day)  # Sett y-aksen opp til maksimalt antall skift i året
    plt.grid(axis='y')
    plt.show()

