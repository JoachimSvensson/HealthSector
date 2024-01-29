import streamlit as st 
import pandas as pd 

def horizon_timestamps(n_weeks, f):
    return list(range(60//f * 24 * 7 * n_weeks))

st.cache_data()
def create_forbidden_shifts(earliest_shift,latest_shift, f):
    forbitten_start = []
    for _ in range(7):
        forbitten_start.extend(list(map(lambda x : x + 24*(60//f)* _, range(0,earliest_shift *(60//f)))))
        forbitten_start.extend(list(map(lambda x : x + 24*(60//f)*_, range((60//f) * latest_shift+1,(23+1) * (60//f)))))
    return set(forbitten_start)

st.cache_data()
def create_possible_shifs(ts : list, forbitten_start : set, allowed_lens : set, f):
    shift_s_e = []
    possible_shifts = []
    for l in allowed_lens:
        for i in ts:
            if i in forbitten_start:
                continue
            if i + l -1 < len(ts):
                if i+l-1 in forbitten_start:
                    continue
                possible_shifts.append(ts[i:i+l])
                shift_s_e.append((i, i+l -1))
            else:
                if ((i + l) - len(ts)) -1 in forbitten_start:
                    continue
                possible_shifts.append(ts[i:] + ts[:((i + l) - len(ts))])
                shift_s_e.append((i, ((i + l) - len(ts)) -1))
    shifts = pd.DataFrame(columns = ts)
    for n, shift in enumerate(possible_shifts):
        shifts.loc[f"Shift-{n +1}", shift] = 1
    shifts.fillna(0, inplace = True)
    return shifts, shift_s_e

# st.cache_data()
def map_hours_to_period(f):
    weekend_hours = list(range(24*5*(60//f), 24 * 7*(60//f)))   
    weekday_hours = list(range(24 * 5*(60//f)))         

    late_afternoons_early_mornings_hours = [] # hours between 6-7 and 17-20 in weekdays (+12kr)
    for _ in range(5):
        late_afternoons_early_mornings_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(6*(60//f),7*(60//f)))))
    for _ in range(5):
        late_afternoons_early_mornings_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(17*(60//f),20*(60//f)))))

    night_hours = [] # hours between 0-6 and 20-23 during whole week
    for _ in range(7):
        night_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(0,6*(60//f)))))
    for _ in range(7):
        night_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(20*(60//f),(23*(60//f))+1))))
    weekday_night_hours = list(set(night_hours).intersection(set(weekday_hours))) # hours between 0-6 and 20-23 in weekdays
    weekend_night_hours = list(set(night_hours).intersection(set(weekend_hours))) # hours between 0-6 and 20-23 in weekends
    weekend_day_hours = list(set(weekend_hours).difference(set(weekend_night_hours))) # hours between 6-20 in weekends
    return late_afternoons_early_mornings_hours, weekday_night_hours, weekend_night_hours, weekend_day_hours

# st.cache_data()
def give_cost(el_h, wdn_h, wen_h, wdd_h, wed_h):
    normal_pay = 350 # kr/worked hour
    # bonus pay
    el_cost = el_h * 12 # kr/worked hour weekday
    we_cost = (wed_h + wen_h) * 52 # kr/clock hour
    n_we_cost = wen_h * (normal_pay * .45)
    n_NOTwe_cost =  wdn_h* (normal_pay * .45)
    # time conversion
    a = (wed_h + wen_h + wdn_h + wdd_h) * normal_pay
    return a + el_cost + we_cost + n_we_cost + n_NOTwe_cost

# st.cache_data()
def compute_shift_statistics(shifts,f):
    late_early, wdnh, wenh, wedh= map_hours_to_period(f)
    shift_stat = pd.DataFrame(shifts.sum(axis = 1)).rename(columns = {0: "shift_length"})

    for n,shift in shifts.iterrows():
        # check early mornings or late nights in weekdays
        shift_stat.loc[n, "early/late_hours"] = shift.loc[late_early].sum()//(60//f)
        # check for night hours 
        shift_stat.loc[n, "weekday_night_hours"] = shift.loc[wdnh].sum()//(60//f)
        shift_stat.loc[n, "weekend_night_hours"] = shift.loc[wenh].sum()//(60//f)
        # check for day weekend hours
        shift_stat.loc[n, "weekend_day_hours"] = shift.loc[wedh].sum()//(60//f)

    shift_stat["weekday_day_hours"] = shift_stat["shift_length"]//(60//f) - shift_stat[["weekday_night_hours", "weekend_night_hours", "weekend_day_hours"]].sum(axis = 1)
    shift_stat["cost"] = shift_stat.apply(lambda df: give_cost(df["early/late_hours"], df["weekday_night_hours"], df["weekend_night_hours"], df["weekday_day_hours"],  df["weekend_day_hours"]) , axis = 1)
    return shift_stat.round(2)

# st.cache_data()
def change_column_names(shifts, ts, f):
    days = {1 : "Monday", 2 : "Tuesday", 3 : "Wednesday", 4 : "Thursday", 5 : "Friday", 6 : "Saturday", 7 : "Sunday"}
    hours = list(map(lambda x : ((f*x)//60)%24, ts))
    minutes = list(map(lambda x: f*x%60, ts))
    days = list(map(lambda x: days[x//(24*60//f) + 1], ts))
    hours_of_week = []
    for _ in range(len(ts)):
        hours_of_week.append(f"{days[_]} {str(hours[_]).zfill(2)}:{str(minutes[_]).zfill(2)}:00")
    shifts.columns = hours_of_week
    return shifts

# st.cache_data()
def create_min_demand(ts, min_night_demand, min_day_demand, f):
    night_hours = [] # hours between 0-6 and 20-23 during whole week
    for _ in range(7):
        night_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(0,6*(60//f)))))
    for _ in range(7):
        night_hours.extend(list(map(lambda x : x + 24*(60//f)*_, range(20*(60//f),(23*(60//f))+1))))
    min_demand = pd.DataFrame(ts).drop(0, axis = 1)
    min_demand.loc[min_demand.index.isin(night_hours), "Staffing_level"] = min_night_demand
    min_demand.fillna(min_day_demand, inplace= True)
    return min_demand

# st.cache_data()
def create_shift_starting(time_t, shift_stats):
    shift_day_match_start = []
    for s, line in shift_stats.Start_end.items():
        shift_day_match_start.append((s, time_t[line[0]]))
    shift_day_match_start = pd.DataFrame(shift_day_match_start)
    shift_day_match_start = shift_day_match_start.groupby(1).agg({0: "unique"}).to_dict()[0]
    return shift_day_match_start

# st.cache_data()
def create_shift_ending(time_t, shift_stats):
    shift_day_match_end = []
    for s, line in shift_stats.Start_end.items():
        shift_day_match_end.append((s, time_t[line[1]]))
    shift_day_match_end = pd.DataFrame(shift_day_match_end)
    shift_day_match_end = shift_day_match_end.groupby(1).agg({0: "unique"}).to_dict()[0]
    return shift_day_match_end

# st.cache_data()
def match_starting_ending(time_t, shift_stats):
    shift_day_match_start = create_shift_starting(time_t, shift_stats)
    shift_day_match_end = create_shift_ending(time_t, shift_stats)
    match = set(shift_day_match_start.keys()) ^ set(shift_day_match_end.keys())
    for d in [shift_day_match_start, shift_day_match_end]:
        for i in match:
            if i in d.keys():
                d.pop(i)
    return shift_day_match_start, shift_day_match_end

# st.cache_data()
def create_coverage(possible_shifts):
    day_shift_match = dict()
    for t in possible_shifts.columns:
        day_shift_match[t] = possible_shifts[t].where(possible_shifts[t]>0).dropna().index.to_list()
    return day_shift_match


# big function
def optimization_preprocess(n_weeks, earliest_shift,latest_shift, allowed_lens, minimum_night, minimum_day, demand, f, progress_bar):
    progress_bar.progress(5)
    allowed_lens = set(list(map(int, allowed_lens)))
    ts = horizon_timestamps(n_weeks,f)
    progress_bar.progress(10)
    possible_shifts, starts_ends = create_possible_shifs(ts, create_forbidden_shifts(earliest_shift,latest_shift, f),allowed_lens, f)
    progress_bar.progress(25)
    shifts_info = compute_shift_statistics(possible_shifts, f)
    progress_bar.progress(30)
    shifts_info["Start_end"] = starts_ends
    possible_shifts = change_column_names(possible_shifts,ts,f)
    min_demand = create_min_demand(ts, minimum_night, minimum_day, f)
    shift_costs = shifts_info["cost"].copy(deep = True)
    shift_costs = shift_costs.to_dict()
    S = possible_shifts.index.tolist()
    ts = possible_shifts.columns.tolist()
    demand.index = ts
    min_demand.index = ts
    demand = pd.concat([demand, min_demand]).groupby(level=0).max().sort_index().to_dict()["Staffing_level"]
    progress_bar.progress(35)
    shift_day_match_start, shift_day_match_end = match_starting_ending(ts, shifts_info)
    progress_bar.progress(40)
    day_shift_match = create_coverage(possible_shifts)
    return ts, S, demand, shift_costs,day_shift_match, shift_day_match_start, shift_day_match_end, possible_shifts, shifts_info
