import pandas as pd
import os
from openpyxl.styles import PatternFill
import numpy as np

### Functions Definition ###

def read_gtfs(file_path, tables=None, calendar_dates_start_date=None, calendar_dates_end_date=None):
    if not tables:
        tables = ['stops', 'routes', 'trips', 'stop_times', 'shapes', 'calendar_dates','agency']

    gtfs_data = {}
    
    for table in tables:
        file_name = f"{table}.txt"
        file_path_table = os.path.join(file_path, file_name)
        print(os.path.exists(file_path_table))

        # Specify dtype for 'stop_id' if reading 'stops' or 'stop_times' table
        dtype = {'stop_id': str} if table in ['stops', 'stop_times'] else None

        # Read the CSV file
        print(f"A ler ficheiro: {table}")
        if table == 'calendar_dates' and calendar_dates_start_date is not None and calendar_dates_end_date is not None:
            # Filter calendar_dates based on the start and end dates
            gtfs_data[table] = pd.read_csv(file_path_table, dtype=dtype)
            gtfs_data[table]['date'] = pd.to_datetime(gtfs_data[table]['date'], format='%Y%m%d')
            gtfs_data[table] = gtfs_data[table][(gtfs_data[table]['date'] >= calendar_dates_start_date) & (gtfs_data[table]['date'] <= calendar_dates_end_date)]
    
        else:
            
            gtfs_data[table] = pd.read_csv(file_path_table, dtype=dtype, encoding='utf-8')

    return gtfs_data

#DEFINITION OF CONTRACT VKM - BASE OFFER FOR EACH CONTRACT
def process_agency_file(agency_path):
    
    vkm_contrato=None
    if (agency_path['agency_id']==41).any():
        vkm_contrato = 28527689
    elif (agency_path['agency_id'] == 42).any():
        vkm_contrato = 25799790
    elif (agency_path['agency_id'] == 43).any():
        vkm_contrato = 19004512
    elif (agency_path['agency_id'] == 44).any():
        vkm_contrato = 15128877
    return vkm_contrato

def add_alert(plan, error_type, grav, description, path):
    global alerts_df

    # Creates a new DataFrame with the data provided
    new_alert = pd.DataFrame({
        'Plano': [plan],
        'Tipo de erro': [error_type],
        'Gravidade': [grav],
        'Descrição': [description],
        'Percurso': [path]
    })

    # Check if alerts_df already exists; if not, create it as an empty DataFrame
    if 'alerts_df' not in globals():
        alerts_df = pd.DataFrame(columns=new_alert.columns)

    # Concatenates the new DataFrame with the global DataFrame
    alerts_df = pd.concat([alerts_df, new_alert], ignore_index=True)

# Example
add_alert('Plano A', 'Erro X', 'Alta', 'Descrição do erro X', '/caminho/para/erro')
print(alerts_df)

#TRIPS PER DATE
def trips_per_date(calendar_dates, trips, start_date, end_date):
    # Merge the trips and calendar_dates dataframes on 'service_id'
    merged = pd.merge(trips, calendar_dates, on='service_id')

    # Convert 'date' column to datetime format
    merged['date'] = pd.to_datetime(merged['date'], format='%Y%m%d')

    merged = merged[(merged['date'] >= start_date) & (merged['date'] <= end_date)]

    # Count the number of unique trips per pattern per date
    trip_counts = merged.groupby(['pattern_id', 'date'])['trip_id'].nunique()

    # Pivot the trip counts to create a table with 'pattern_id' as rows and dates as columns
    trip_counts = trip_counts.reset_index().pivot(index='pattern_id', columns='date', values='trip_id').fillna(0)

    # Create a date range from start_date to end_date and ensure all dates are included as columns
    all_dates = pd.date_range(start=start_date, end=end_date)

    # Reindex the pivoted DataFrame to include all dates in the range, filling missing values with 0
    trip_counts = trip_counts.reindex(columns=all_dates, fill_value=0)

    # Reset index to make 'pattern_id' a column
    trip_counts.reset_index(inplace=True)

    # Format the date columns to '%d/%m/%Y'
    trip_counts.columns = ['pattern_id'] + all_dates.strftime('%d/%m/%Y').tolist()

    return trip_counts

# COMPARE CALENDAR FILES
def compare_calendar_dates(calendar_dates_gtfs_POferta, calendar_dates_gtfs_POperação):
    
    # Remove duplicates based on 'date', 'period', and 'day_type' for GTFS1
    unique_calendar_dates_df_gtfs_POferta = calendar_dates_gtfs_POferta['date'].drop_duplicates(keep='first')
    unique_calendar_dates_gtfs_POferta = calendar_dates_gtfs_POferta[['date', 'period', 'day_type']].drop_duplicates(keep='first')

    # Remove duplicates based on 'date', 'period', and 'day_type' for GTFS2
    unique_calendar_dates_df_gtfs_POperação = calendar_dates_gtfs_POperação['date'].drop_duplicates(keep='first')
    unique_calendar_dates_gtfs_POperação = calendar_dates_gtfs_POperação[['date', 'period', 'day_type']].drop_duplicates(keep='first')

    # Check for differences in the caracterization of each date in OFFER and OPERATION PLANS
    if len(unique_calendar_dates_df_gtfs_POferta) != len(unique_calendar_dates_gtfs_POferta):
        add_alert("PLANO DE OFERTA","Calendário", 'MUITO GRAVE', "Plano de Oferta com datas classificadas com mais do que um periodo e/ou dia tipo",'')

    if len(unique_calendar_dates_df_gtfs_POperação) != len(unique_calendar_dates_gtfs_POperação):
        add_alert("PLANO DE OPERAÇÃO", "Calendário", 'MUITO GRAVE', "Plano de Operação com datas classificadas com mais do que um periodo e/ou dia tipo",'')
        
    calendar_dates_merged = pd.concat([unique_calendar_dates_gtfs_POferta,unique_calendar_dates_gtfs_POperação])
    unique_calendar_dates_merged_date = calendar_dates_merged[['date']].drop_duplicates(keep='first')
    unique_calendar_dates_merged = calendar_dates_merged[['date', 'period', 'day_type']].drop_duplicates(keep='first')
    
    # Check for differences in the number of unique dates between OFFER PLAN and OPERATION PLAN
    if len(unique_calendar_dates_merged_date) != len(unique_calendar_dates_merged):
        add_alert("PLANO DE OPERAÇÃO","Calendário", 'MUITO GRAVE',"Plano de operação com datas com diferente caracterização do Plano de oferta",'')

    # Merge the unique calendar dates for comparison
    compare_calendars = pd.merge(unique_calendar_dates_gtfs_POferta, unique_calendar_dates_gtfs_POperação, on=['date'], how='outer')
    compare_calendars['date'] = pd.to_datetime(compare_calendars['date']).dt.strftime('%Y-%m-%d')
    
    # Create columns indicating differences in 'period' and 'day_type'
    compare_calendars['Diferenças_periodo'] = np.where(compare_calendars['period_x'] == compare_calendars['period_y'], 'IGUAL', 'DIFERENTE')
    compare_calendars['Diferenças_dia_tipo'] = np.where(compare_calendars['day_type_x'] == compare_calendars['day_type_y'], 'IGUAL', 'DIFERENTE')
    
    # Rename columns for clarity
    compare_calendars.rename(columns={'date':'Data',
                                      'period_x': 'Periodo do ano_POferta', 
                                      'day_type_x': 'Dia tipo_POferta',
                                      'period_y': 'Periodo do ano_POperação', 
                                      'day_type_y': 'Dia tipo_POperação'}, inplace=True)
    reorder =['Data', 'Periodo do ano_POferta', 'Dia tipo_POferta','Periodo do ano_POperação','Dia tipo_POperação','Diferenças_periodo','Diferenças_dia_tipo']
    
    compare_calendars= compare_calendars[reorder]

    return compare_calendars

# CHECK FOR DATES WITHOUT TRIPS 
def check_trips_for_dates(calendar_dates, trips, gtfsname):
#    # Merge calendar_dates with trips on service_id, marking all calendar_dates entries
    merged_data = pd.merge(calendar_dates, trips, on='service_id', how='left')

    filtered_data = merged_data[merged_data['service_id'] == 2]

    # Dates with associated trips 
    dates_with_trips = merged_data[merged_data['trip_id'].notnull()]['date'].unique()

    # Dates without associated trips
    dates_without_trips = merged_data[merged_data['trip_id'].isnull()]['date'].unique()
    # print(dates_without_trips)

    final_dates_without_trips = [date for date in dates_without_trips if date not in dates_with_trips]

    # Prepare to display or alert based on the results
    if len(final_dates_without_trips) > 0:
        missing_dates_formatted = ', '.join(pd.to_datetime(final_dates_without_trips).strftime('%Y-%m-%d'))
        #print(f"{gtfsname}: The following dates do NOT have associated trips: {final_dates_without_trips}")
        add_alert(f"{gtfsname}", "Número de circulações", 'MUITO GRAVE', f"As seguintes datas não têm oferta prevista: {missing_dates_formatted}", '')
    else:
         print(f"{gtfsname}: All dates have associated trips.")

    if len(dates_with_trips) > 0:
        available_dates_formatted = ', '.join(pd.to_datetime(dates_with_trips).strftime('%Y-%m-%d'))
        # print(f"{gtfsname}: The following dates have associated trips: {available_dates_formatted}")

#CHECK IF ALL DATES BETWEEN THE DEFINED INTERVAL ARE PRESENT IN CALENDAR_DATES
def check_dates_in_interval(calendar_dates, start_date, end_date, gtfsname):
    # Convert date columns to datetime objects
    calendar_dates['date'] = pd.to_datetime(calendar_dates['date'])
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filter calendar_dates within the specified interval
    dates_in_interval = calendar_dates[(calendar_dates['date'] >= start_date) & (calendar_dates['date'] <= end_date)]['date']
    # print(dates_in_interval)

    # Check if all dates within the interval are present
    missing_dates = set(pd.date_range(start=start_date, end=end_date).date) - set(dates_in_interval.dt.date)
    
    if len(missing_dates) == 0:
        print("All dates within the specified interval are present in calendar_dates.")
    else:
        missing_dates = [date.strftime('%Y-%m-%d') for date in missing_dates]
        add_alert(f"{gtfsname}","Número de circulações", 'MUITO GRAVE',f"Estão em falta as seguintes datas para o período definido:{list(missing_dates)}",'')

# COMPARE STOP SEQUENCES WITHIN OFFER AND OPERATION PLANS
def merge_and_check_stop_sequences(gtfs_trips, gtfs_stop_times, gtfs_stops, gtfs_name):
    # Merge relevant tables
    merged_data = pd.merge(gtfs_trips, gtfs_stop_times, on='trip_id')

    merged_data = merged_data.sort_values(by=['pattern_id', 'trip_id', 'stop_sequence'])
    # Save stop_sequences per pattern_id
    stop_sequence_perpattern = merged_data[['pattern_id', 'stop_id', 'stop_sequence']].drop_duplicates(keep='first')

    # Verify consistent stop sequences per pattern_id
    inconsistent_stop_sequences = []
    for pattern_id, group in merged_data.groupby(['pattern_id']):
        unique_stop_sequences = group.groupby('trip_id')[['stop_sequence', 'stop_id']].apply(lambda x: tuple(map(tuple, x.values))).unique()
        if len(unique_stop_sequences) > 1:
            inconsistent_stop_sequences.append((pattern_id, unique_stop_sequences))
            
            add_alert(f"{gtfs_name}","Sequência de paragens",'MUITO GRAVE',f"Múltiplas sequências de paragens para os percursos", f'{pattern_id}')
            
        
    # Group by pattern_id and count unique stops
    stops_count = stop_sequence_perpattern.groupby('pattern_id')[['stop_id','stop_sequence']].count().reset_index()

    return stops_count, stop_sequence_perpattern

#COMPARE STOP SEQUENCES BETWEEN OFFER AND OPERATION PLANS
def merge_and_check_stop_sequences_between_plans(gtfs_trips_POferta, gtfs_trips_POperação, gtfs_stop_times_POferta, gtfs_stop_times_POperação):
    # Merge relevant tables
    merged_data_POferta = pd.merge(gtfs_trips_POferta, gtfs_stop_times_POferta, on='trip_id')
    merged_data_POperação = pd.merge(gtfs_trips_POperação, gtfs_stop_times_POperação, on='trip_id')   
    merged_data_POferta = merged_data_POferta.sort_values(by=['pattern_id', 'trip_id', 'stop_sequence'])
    merged_data_POperação = merged_data_POperação.sort_values(by=['pattern_id', 'trip_id', 'stop_sequence'])

    merged_data =pd.concat([merged_data_POferta,merged_data_POperação])
    
    inconsistent_stop_sequences = []

    for pattern_id, group in merged_data.groupby(['pattern_id']):
        unique_stop_sequences = group.groupby('trip_id')[['stop_sequence', 'stop_id']].apply(lambda x: tuple(map(tuple, x.values))).unique()
        if len(unique_stop_sequences) > 1:
            inconsistent_stop_sequences.append((pattern_id, unique_stop_sequences))
            #add_alert("PLANO DE OPERAÇÃO","Sequência de paragens",'MUITO GRAVE',"Sequência de paragens diferente do Plano de Oferta nos percursos:", f'{pattern_id}')
            add_alert("PLANO DE OPERAÇÃO",
                     "Sequência de paragens", 'MUITO GRAVE',
                    "Sequência de paragens diferente do Plano de Oferta nos percursos:", pattern_id)

# COMPARE THE EXTENSION CALCULATED FROM STOP_TIMES AND SHAPES FOR EACH PATTERN 
def compare_extension(gtfs_trips, gtfs_shapes, gtfs_stop_times, gtfs_name):
    # Merge relevant tables for extension comparison
    merged_data = pd.merge(gtfs_trips, gtfs_shapes, on='shape_id')
    merged_data_stop_times = pd.merge(gtfs_trips, gtfs_stop_times, on='trip_id')

    # Calculate the extension for each pattern_id
    extension = merged_data.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    
    extension[f'shape_dist_traveled'] = extension[f'shape_dist_traveled'].apply(
        lambda x: x / 1000 if x > 1000 else x
    )

    # Rename the columns to include GTFS name
    extension.columns = ['pattern_id', f'shape_dist_traveled_{gtfs_name}']

    extension_stop_times = merged_data_stop_times.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    extension_stop_times[f'shape_dist_traveled'] = extension_stop_times [f'shape_dist_traveled'].apply(
        lambda x: x / 1000 if x > 1000 else x
    )
    extension_stop_times.columns = ['pattern_id', f'dist_traveled_stops_{gtfs_name}']

    compare_extensions_in_plan = pd.merge(extension, extension_stop_times, on = 'pattern_id')
    # print(compare_extensions_in_plan)

   # Iterate over groups based on 'pattern_id'
    for pattern_id, group in compare_extensions_in_plan.groupby('pattern_id'):
        for _, row in group.iterrows():
            difference = pd.to_numeric((row[f'dist_traveled_stops_{gtfs_name}'] - row[f'shape_dist_traveled_{gtfs_name}']))
            #print(difference)
            if abs(difference) > 1:
                add_alert(f"{gtfs_name}","Extensões", 'GRAVE', "Diferença entre extensão calculada a partir de shapes e entre paragens nos percursos:", f'{pattern_id}')
                
    return extension, extension_stop_times

# COMPARE THE EXTENSION CALCULATED FROM STOP_TIMES AND SHAPES FOR EACH PATTERN 
def compare_extension(gtfs_trips, gtfs_shapes, gtfs_stop_times, gtfs_name):
    # Merge relevant tables for extension comparison
    merged_data = pd.merge(gtfs_trips, gtfs_shapes, on='shape_id')
    merged_data_stop_times = pd.merge(gtfs_trips, gtfs_stop_times, on='trip_id')

    # Calculate the extension for each pattern_id
    extension = merged_data.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    
    extension[f'shape_dist_traveled'] = extension[f'shape_dist_traveled'].apply(
        lambda x: x / 1000 if x > 1000 else x
    )

    # Rename the columns to include GTFS name
    extension.columns = ['pattern_id', f'shape_dist_traveled_{gtfs_name}']

    extension_stop_times = merged_data_stop_times.groupby('pattern_id')['shape_dist_traveled'].max().reset_index()
    extension_stop_times[f'shape_dist_traveled'] = extension_stop_times [f'shape_dist_traveled'].apply(
        lambda x: x / 1000 if x > 1000 else x
    )
    extension_stop_times.columns = ['pattern_id', f'dist_traveled_stops_{gtfs_name}']

    compare_extensions_in_plan = pd.merge(extension, extension_stop_times, on = 'pattern_id')
    # print(compare_extensions_in_plan)

   # Iterate over groups based on 'pattern_id'
    for pattern_id, group in compare_extensions_in_plan.groupby('pattern_id'):
        for _, row in group.iterrows():
            difference = pd.to_numeric((row[f'dist_traveled_stops_{gtfs_name}'] - row[f'shape_dist_traveled_{gtfs_name}']))
            #print(difference)
            if abs(difference) > 1:
                add_alert(f"{gtfs_name}","Extensões", 'GRAVE', "Diferença entre extensão calculada a partir de shapes e entre paragens nos percursos:", f'{pattern_id}')
                
    return extension, extension_stop_times

# COMPARE SCHEDULES BETWEEN OFFER AND OPERATION PLANS
def get_departure_times_for_all_patterns_and_dates(gtfs_file):
    # Load GTFS data into pandas dataframes
    stops_df = pd.read_csv(gtfs_file + '/stops.txt')
    stop_times_df = pd.read_csv(gtfs_file + '/stop_times.txt')
    trips_df = pd.read_csv(gtfs_file + '/trips.txt')
    calendar_dates_df = pd.read_csv(gtfs_file + '/calendar_dates.txt')

    # Get unique dates from calendar_dates
    unique_dates = calendar_dates_df['date'].unique()

    # Initialize an empty dataframe to store results for all patterns and dates
    all_patterns_dates_results = pd.DataFrame(columns=['date', 'pattern_id', 'departure_time', 'stop_name'])

    # Iterate through each date
    for date in unique_dates:
        # Filter trips based on service_ids for the given date
        service_ids_for_date = calendar_dates_df[calendar_dates_df['date'] == date]['service_id']
        trips_for_date_df = trips_df[trips_df['service_id'].isin(service_ids_for_date)]

        # Filter stop_times to get only the first stop for each trip
        first_stop_times_df = stop_times_df.groupby('trip_id').first().reset_index()

        # Merge first_stop_times with filtered trips to get pattern_id
        merged_df = pd.merge(first_stop_times_df, trips_for_date_df, on='trip_id')

        # Merge with stops_df to get stop_name for the first stop
        merged_with_stops_df = pd.merge(merged_df, stops_df, on='stop_id')

        # Add 'date' column
        merged_with_stops_df['date'] = date

        # Select necessary columns and sort by pattern_id and departure_time
        departure_times_for_date = merged_with_stops_df[['date', 'pattern_id', 'departure_time', 'stop_name']].sort_values(by=['pattern_id', 'departure_time'])

        # Append the result to all_patterns_dates_results dataframe
        all_patterns_dates_results = all_patterns_dates_results.append(departure_times_for_date, ignore_index=True)
    return all_patterns_dates_results

# COMPARE ROUTE FILES BETWEEN OFFER AND OPERATION PLANS
def compare_routes(gtfs_POferta_path, gtfs_POperação_path):
    # Read routes files from both GTFS datasets
    routes_gtfs_POferta = gtfs_POferta_path
    routes_gtfs_POperação = gtfs_POperação_path

    # Extract unique route IDs from both datasets
    unique_routes_gtfs_POferta = set(routes_gtfs_POferta['route_id'])
    unique_routes_gtfs_POperação = set(routes_gtfs_POperação['route_id'])

    # Find routes that are missing in one of the datasets
    missing_routes_gtfs_POferta = unique_routes_gtfs_POperação - unique_routes_gtfs_POferta
    print(missing_routes_gtfs_POferta)
    missing_routes_gtfs_POperação = unique_routes_gtfs_POferta - unique_routes_gtfs_POperação

    # Print alerts for missing routes
    if missing_routes_gtfs_POferta:
        add_alert("PLANO DE OFERTA","Rotas",'MUITO GRAVE',f"As seguintes rotas não existem no Plano de Oferta:",f'{missing_routes_gtfs_POferta}')

    if missing_routes_gtfs_POperação:
        add_alert("PLANO DE OPERAÇÃO","Rotas", 'MUITO GRAVE', f"As seguintes rotas não existem no Plano de Operação:", f'{missing_routes_gtfs_POperação}')

    dtype_mapping = {'line_id':str, 'line_short_name':str, 'line_long_name':str, 
                     'agency_id':str, 'route_short_name':str, 'route_long_name':str,
                     'route_type':str, 'path_type':str, 'route_color':str,'route_text_color':str}
    
    routes_gtfs_POferta = routes_gtfs_POferta.astype(dtype_mapping)
    routes_gtfs_POperação = routes_gtfs_POperação.astype(dtype_mapping)

    # Merge routes data based on 'route_id'
    merged_routes = pd.merge(routes_gtfs_POferta, routes_gtfs_POperação, on='route_id', suffixes=('_POferta', '_POperação'), how='outer')
        
    fields_to_compare = ['line_id', 'line_short_name', 'line_long_name', 
                     'agency_id', 'route_short_name', 'route_long_name',
                     'route_type', 'path_type', 'route_color',
                     'route_text_color']
    
    # Iterate over each field and compare values
    for index, row in merged_routes.iterrows():
        route_id = row['route_id']
        # Skip processing if the route_id is already in the missing_routes_gtfs_POferta or missing_routes_gtfs_POperação
        if route_id in missing_routes_gtfs_POferta or route_id in missing_routes_gtfs_POperação:
            continue

        for field in fields_to_compare:
            value_POferta = str(row[f'{field}_POferta'])
            value_POperação = str(row[f'{field}_POperação'])
            
            if value_POferta != value_POperação:
                add_alert("PLANO DE OPERAÇÃO","Rotas", 'MUITO GRAVE', f"Existem diferenças nos campos {field} para as seguintes rotas:", f'{route_id}')
                
    return merged_routes

### DEFINITIONS ###
# Period of analysis
start_date = '20260116'
end_date = '20260531'

# Folder path
target_folder = r'C:\\Users\\InêsClemente\\Downloads\\A1_JANEIRO_2026\\'

# OFFER AND OPERATION PLANS
GTFS_OFFERPLAN_name='GTFS_41_REF_v29_202512091408'
GTFS_OPERATIONPLAN_name='20251215_41_YEAR_04_50_01'

# RESULT
result_name='A1_analise_plano_anual_janeiro_2026'
#result_name='A3_analise_plano_anual_dezembro_2025_v3'
#result_name='A4_analise_plano_mensal_dezembro_2025'
#result_name='A2_comparação_plano_oferta_maio_junho'
excel_file_path = target_folder+ result_name +'.xlsx'

### Read GTFS ###
print("A processar GTFS_OFFERPLAN")
gtfs_POferta = read_gtfs(os.path.join(target_folder,GTFS_OFFERPLAN_name),
                  calendar_dates_start_date=start_date, 
                  calendar_dates_end_date=end_date)

print("A processar GTFS2_OPERATIONPLAN")
gtfs_POperação = read_gtfs(os.path.join(target_folder,GTFS_OPERATIONPLAN_name),
                  calendar_dates_start_date=start_date, 
                  calendar_dates_end_date=end_date)

vkm_contrato = process_agency_file(gtfs_POperação['agency'])

# SETTING UP A TABLE TO STORE THE LIST OF ALERTS FOUND
alerts_df = pd.DataFrame(columns=['Plano', 'Tipo de erro', 'Gravidade', 'Descrição', 'Percurso'])

# TRIPS PER DATE
pivot_dates_oferta = trips_per_date(gtfs_POferta['calendar_dates'], gtfs_POferta['trips'],start_date, end_date)
pivot_dates_operacao = trips_per_date(gtfs_POperação['calendar_dates'], gtfs_POperação['trips'], start_date, end_date)

# COMPARE CALENDAR FILES
compare_calendars=compare_calendar_dates(gtfs_POferta['calendar_dates'], gtfs_POperação['calendar_dates'])

# Read calendar_dates for day_type and period information for GTFS1
calendar_dates_POferta = gtfs_POferta['calendar_dates']

# Read calendar_dates for day_type and period information for GTFS2
calendar_dates_POperação = gtfs_POperação['calendar_dates']

# CHECK FOR DATES WITHOUT TRIPS 
check_trips_for_dates(gtfs_POperação['calendar_dates'], gtfs_POperação['trips'], 'PLANO DE OPERAÇÃO')
check_trips_for_dates(gtfs_POferta['calendar_dates'], gtfs_POferta['trips'], 'PLANO DE OFERTA')

# CHECK IF ALL DATES BETWEEN THE DEFINED INTERVAL ARE PRESENT IN CALENDAR_DATES
check_dates_in_interval(gtfs_POferta['calendar_dates'], start_date, end_date,'PLANO DE OFERTA')
check_dates_in_interval(gtfs_POperação['calendar_dates'], start_date, end_date,'PLANO DE OPERAÇÃO')

# COMPARE TOTAL NUMBER OF STOPS FOR EACH PATTERN BETWEEN OFFER AND OPERATION PLANS
stops_count_gtfs_POferta,stop_sequence_gtfs_POferta = merge_and_check_stop_sequences(gtfs_POferta['trips'], gtfs_POferta['stop_times'], gtfs_POferta['stops'], 'PLANO DE OFERTA')
stops_count_gtfs_POperação,stop_sequence_gtfs_POperação = merge_and_check_stop_sequences(gtfs_POperação['trips'], gtfs_POperação['stop_times'], gtfs_POperação['stops'], 'PLANO DE OPERAÇÃO')
# print(stops_count_gtfs_POperação)
stops_comparison_result = pd.merge(stops_count_gtfs_POferta, stops_count_gtfs_POperação, on='pattern_id', suffixes=('_count_gtfs1', '_count_gtfs2'), how='outer')
# print(stops_comparison_result)

stops_comparison_result['Diferences_numberofstops'] = np.where(stops_comparison_result['stop_id_count_gtfs1'] == stops_comparison_result['stop_id_count_gtfs2'], 'IGUAL', 'DIFERENTE')
stops_comparison_result.rename(columns={'stop_id_count_gtfs1': 'POferta_Num paragens',
                                        'stop_id_count_gtfs2': 'POperação_Num paragens'}, inplace=True)

for index, row in stops_comparison_result.iterrows():
    if row['Diferences_numberofstops'] == 'DIFERENTE':
        pattern_id = row['pattern_id']
        #print(pattern_id)
        add_alert("PLANO DE OPERAÇÃO","Número total de paragens", 'GRAVE', f'Número total de paragens diferente do Plano de Oferta nos percursos:', f'{pattern_id}')
            
# COMPARE STOP SEQUENCES BETWEEN OFFER AND OPERATION PLANS
merge_and_check_stop_sequences_between_plans(gtfs_POferta['trips'], gtfs_POperação['trips'], gtfs_POferta['stop_times'], gtfs_POperação['stop_times'])

# COMPARE THE EXTENSION CALCULATED FROM STOP_TIMES AND SHAPES FOR EACH PATTERN 
extension_gtfs_POferta, extension_stop_times_gtfs_POferta = compare_extension(gtfs_POferta['trips'], gtfs_POferta['shapes'], gtfs_POferta['stop_times'],'PLANO DE OFERTA')
extension_gtfs_POperação, extension_stop_times_gtfs_POperação = compare_extension(gtfs_POperação['trips'], gtfs_POperação['shapes'], gtfs_POperação['stop_times'],'PLANO DE OPERAÇÃO')

extension_comparison_result = pd.merge(extension_gtfs_POferta, extension_gtfs_POperação, on='pattern_id', how='outer')
extension_comparison_result = pd.merge(extension_comparison_result, extension_stop_times_gtfs_POferta, on='pattern_id', how='outer')
extension_comparison_result = pd.merge(extension_comparison_result, extension_stop_times_gtfs_POperação, on='pattern_id', how='outer')

# CALCULATE THE DIFFERENCE BETWEEN EACH METHOD (%) 
extension_comparison_result['Diferença (%)'] = round(
    ((extension_comparison_result['shape_dist_traveled_PLANO DE OPERAÇÃO'] - extension_comparison_result['shape_dist_traveled_PLANO DE OFERTA']) /
     extension_comparison_result['shape_dist_traveled_PLANO DE OFERTA']) * 100, 0
)
# RECLASSIFY DIFERENCES IN 3 CLASSES: <5%; 5 - 10%; >10%
extension_comparison_result['Classe de diferença'] = pd.cut(
    extension_comparison_result['Diferença (%)'],
    bins=[-float('inf'), 5, 10, float('inf')],
    labels=['Diferença inferior a 5%', 'Diferença entre 5 e 10%', 'Diferença superior a 10%'],
    right=False
)
# Format the 'percentage_difference' column as percentage
extension_comparison_result['Diferença (%)'] = extension_comparison_result['Diferença (%)'].astype(str) + '%'

#COMPARE SCHEDULES BETWEEN OFFER AND OPERATION PLANS
merged_routes = compare_routes(gtfs_POferta['routes'], gtfs_POperação['routes'])
pd.merge(gtfs_POferta['routes'], gtfs_POperação['routes'], on='route_id')

# ACESS THE NUMBER OF TRIPS PER PERIOD AND DAY TYPE FOR EACH PLAN

# Merge calendar_dates with trips to add information about period and day type
trips_calendar_POferta = pd.merge(gtfs_POferta['trips'], calendar_dates_POferta, on='service_id')
trips_calendar_POperação = pd.merge(gtfs_POperação['trips'], calendar_dates_POperação, on='service_id')

# Calculate the number of trips per pattern_id, day_type, and period for each plan
trips_per_pattern_day_type_period_POferta = trips_calendar_POferta.groupby(['pattern_id', 'service_id','period', 'day_type'])['trip_id'].nunique().reset_index()
trips_per_pattern_day_type_period_POperação = trips_calendar_POperação.groupby(['pattern_id', 'service_id','period', 'day_type'])['trip_id'].nunique().reset_index()

# Calculate the number of days per pattern_id, day_type, and period for each plan
days_per_pattern_day_type_period_POferta = trips_calendar_POferta.groupby(['pattern_id','service_id', 'period', 'day_type'])['date'].nunique().reset_index()
days_per_pattern_day_type_period_POferta.rename(columns={'date': 'days_count'}, inplace=True)
days_per_pattern_day_type_period_POperação = trips_calendar_POperação.groupby(['pattern_id','service_id', 'period', 'day_type'])['date'].nunique().reset_index()
days_per_pattern_day_type_period_POperação.rename(columns={'date': 'days_count'}, inplace=True)

# Merge days_per_pattern_day_type_period_POferta and trips_per_pattern_day_type_period_POferta
merged_result_POferta = pd.merge(days_per_pattern_day_type_period_POferta, trips_per_pattern_day_type_period_POferta, on=['pattern_id', 'service_id','period', 'day_type'], how='left')
merged_result_POperação = pd.merge(days_per_pattern_day_type_period_POperação, trips_per_pattern_day_type_period_POperação, on=['pattern_id','service_id', 'period', 'day_type'], how='left')

# Calculate the total number of trips per period and day_type
merged_result_POferta['result'] = merged_result_POferta['days_count'] * merged_result_POferta['trip_id']
merged_result_POperação['result'] = merged_result_POperação['days_count'] * merged_result_POperação['trip_id']

# CREATE TABLES WITH SUMMARY BY PLAN - NUMBER OF TRIPS PER DAY, TYPE AND PERIOD; DISTANCE BASED ON THE TWO METHODS OF CALCULATION
combined_result = pd.merge(stops_comparison_result, extension_comparison_result, on='pattern_id')
combined_result_POferta = pd.merge(combined_result, merged_result_POferta, on='pattern_id', suffixes=('_num_trips_gtfs2', '_trips2'), how='outer')
combined_result_POperação = pd.merge(combined_result, merged_result_POperação, on='pattern_id', suffixes=('_gtfs2', '_gtfs2'), how='outer')

pivot_table_gtfs_POferta = combined_result_POferta.pivot_table(index=['pattern_id', 'period', 'day_type'], values='result', aggfunc='sum')
pivot_table_gtfs_POperação = combined_result_POperação.pivot_table(index=['pattern_id', 'period', 'day_type'], values='result', aggfunc='sum')
pivot_table_gtfs_POferta = pivot_table_gtfs_POferta.reset_index()
pivot_table_gtfs_POperação = pivot_table_gtfs_POperação.reset_index()

resumo_gtfs_POperação = pd.merge(pivot_table_gtfs_POperação,stops_count_gtfs_POperação, on=['pattern_id'], how='outer')
resumo_gtfs_POperação = pd.merge(resumo_gtfs_POperação,extension_gtfs_POperação, on=['pattern_id'], how='outer')
resumo_gtfs_POperação['vkm'] = resumo_gtfs_POperação['shape_dist_traveled_PLANO DE OPERAÇÃO'] * resumo_gtfs_POperação ['result']

resumo_gtfs_POferta = pd.merge(pivot_table_gtfs_POferta,stops_count_gtfs_POferta, on=['pattern_id'], how='outer')
resumo_gtfs_POferta = pd.merge(resumo_gtfs_POferta,extension_gtfs_POferta, on=['pattern_id'], how='outer')

#if 'result' not in resumo_gtfs_POferta.columns: resumo_gtfs_POferta['result'] = 1
resumo_gtfs_POferta['vkm'] = resumo_gtfs_POferta['shape_dist_traveled_PLANO DE OFERTA'] * resumo_gtfs_POferta['result']

# COMPARISON OF THE OFFER PLANNED FOR EACH PLAN
merged_all=pd.merge(resumo_gtfs_POferta,resumo_gtfs_POperação,on=['pattern_id','period','day_type'],how='outer')
merged_all.rename(columns={'pattern_id':'Percurso', 
                           'period':'Periodo do ano',
                           'day_type':'Dia tipo', 
                           'result_x':'Num total circulações ano_POferta', 
                           'stop_id_x':'Num total paragens_POferta', 
                           'stop_sequence_x':'Sequencia paragens_POferta',
                           'shape_dist_traveled_PLANO DE OFERTA':'Extensão shape_POferta',
                           'vkm_x':'VKM total ano_POferta',
                           'result_y':'Num total circulações ano_POperação', 
                           'stop_id_y':'Num total paragens_Poperação', 
                           'stop_sequence_y':'Sequencia paragens_POperação',
                           'shape_dist_traveled_PLANO DE OPERAÇÃO':'Extensão shape_POperação',
                           'vkm_y':'VKM total ano_Poperação'}, inplace=True)
# Rename columns 
extension_comparison_result.rename(columns={'pattern_id':'Percurso',
                                            'shape_dist_traveled_PLANO DE OFERTA':'Extensão shape_POferta', 
                                            'shape_dist_traveled_PLANO DE OPERAÇÃO':'Extensão shape_POperação',
                                            'dist_traveled_stops_PLANO DE OFERTA':'Extensão entre paragens_POferta', 
                                            'dist_traveled_stops_PLANO DE OPERAÇÃO':'Extensão entre paragens_POperação'}, inplace=True)

# SUMMARY TABLE WITH COMPARISON OF CONTRACT, OFFER AND OPERATION VKM
total_vkm_poferta = merged_all['VKM total ano_POferta'].sum()
total_vkm_poperação = merged_all['VKM total ano_Poperação'].sum()
total_vkm_contrato = vkm_contrato

for index, row in merged_all.iterrows():
    if row['Num total circulações ano_POferta'] != row['Num total circulações ano_POperação']:
        pattern_id = row['Percurso']
        add_alert("PLANO DE OPERAÇÃO","Número total de circulações", 'MUITO GRAVE', f'Número total de circulações diferente do Plano de Oferta nos percursos:', f'{pattern_id}')

grand_total_df = pd.DataFrame({
    '': ['Plano de Oferta', 'Plano de Operação', 'Contrato'],
    'Designação GTFS': [GTFS_OFFERPLAN_name, GTFS_OPERATIONPLAN_name, ''],
    'VKM': [total_vkm_poferta, total_vkm_poperação, total_vkm_contrato],
    'Diferença relativa ao contrato': [
        total_vkm_poferta / total_vkm_contrato,
        total_vkm_poperação / total_vkm_contrato,
        '-'
    ]
})

analysis_period_df = pd.DataFrame({
    'Período da Análise': [
        f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} a {end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    ],
    'Data da Análise': [pd.Timestamp.now().strftime('%d/%m/%Y')]
})

# SAVE THE RESULTS
with pd.ExcelWriter(excel_file_path) as writer:
    alerts_df.to_excel(writer, sheet_name='ALERTAS', index=False)
    grand_total_df.to_excel(writer, sheet_name='RESUMO', index=False, startrow=0)
    analysis_period_df.to_excel(writer, sheet_name='RESUMO', index=False, startrow=len(grand_total_df) + 2)
    merged_all.to_excel(writer, sheet_name='Total circulações e VKM', index=False)
    compare_calendars.to_excel(writer, sheet_name='Comparação calendarios', index=False)
    stops_comparison_result.to_excel(writer, sheet_name='Comparação paragens', index=False)
    extension_comparison_result.to_excel(writer, sheet_name='Comparação extensões', index=False)
    merged_routes.to_excel(writer, sheet_name='Comparação rotas', index=False)
    stop_sequence_gtfs_POferta.to_excel(writer, sheet_name='Sequencia paragens POferta', index=False)
    stop_sequence_gtfs_POperação.to_excel(writer, sheet_name='Sequencia paragens POperação', index=False)
    combined_result_POferta.to_excel(writer, sheet_name='Resumo Plano Oferta', index=False)
    combined_result_POperação.to_excel(writer, sheet_name='Resumo Plano Operação', index=False)
    pivot_dates_oferta.to_excel(writer, sheet_name='Circulações por Data POferta', index=False)
    pivot_dates_operacao.to_excel(writer, sheet_name='Circulações por Data POperação', index=False)

print(f"Results saved to {excel_file_path}")
