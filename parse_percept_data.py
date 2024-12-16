import pandas as pd
import os
import tarfile
from tqdm import tqdm
import numpy as np

'''PLEASE NOTE THIS FILE PATH CORESPONDS TO TEMP: ghcnm.tavg.v4.0.1.2024...
   THIS FILE PATH IS FOR PERCIPITATION: ghcn-m_v4.00.00_prcp...'''

class prepare_data:
    def __init__(self):
        pass

    def cat_cal(self, wind):
        if wind < 74:
            return 0
        if wind >= 74 and wind <= 95:
            return 1
        elif wind <= 110:
            return 2
        elif wind <= 129:
            return 3
        elif wind <= 156:
            return 4
        else:
            return 5

    def parse_hurdat2(self,file_path, flag):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        storm_data = []
        storm_id = None
        storm_name = None

        for i,line in enumerate(lines):
            # decide if row is data or just a header row
            if line[0].isdigit():
                details = line.split(',')
                # print()
                # print(i)
                # print(details)
                # print(details[:8])
                # print()
                date, time, _, status, lat, lon, max_wind, min_pressure = details[:8]
                storm_data.append({
                    'storm_id': storm_id,
                    'storm_name': storm_name,
                    'date': date.strip(),
                    'time': time.strip(),
                    'status': status.strip(),
                    'latitude': lat.strip(),
                    'longitude': lon.strip(),
                    'max_wind': int(max_wind.strip()),
                    'min_pressure': int(min_pressure.strip()) if min_pressure.strip() != '' else None
                })

            else:  # get header info from header line
                parts = line.split(',')
                storm_id = parts[0].strip()
                storm_name = parts[1].strip()

        data = pd.DataFrame(storm_data)

        data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
        data['category'] = data['max_wind'].apply(self.cat_cal)

        data.to_csv(f'Processed_hurricane_{flag}_data.csv', index=True)
    
    def parse_precipitation(self):
        cwd = os.getcwd()
        files_and_dirs = os.listdir(cwd)

        hawaii = []

        for file in files_and_dirs:
            if file[:4] == 'prcp':
                data = pd.read_csv(file, header = None)
                # print(file)
                # print(data.head())
                data.columns = ["Station ID", "Station Name", "Latitude", "Longitude", "Elevation", "Date", "Precipitation (mm)", "Measurement flag", "Quality control flag", "Source flag", "Source index"]
                data['Elevation'] = data['Elevation'].replace(-999.9, None)
                data['Precipitation (mm)'] = pd.to_numeric(data['Precipitation (mm)'], errors='coerce')
                data = data.dropna(subset=['Precipitation (mm)', 'Date'])
                data['Date'] = pd.to_datetime(data['Date'], format='%Y%m')
                
                if file[5] == 'A':
                    florida = data

                if file[5] == 'U':
                    hawaii.append(data)
        hawaii = pd.concat(hawaii, ignore_index = True)

        hawaii.set_index('Date', inplace=True)
        florida.set_index('Date', inplace=True)

        florida.to_csv('Processed_florida_prcp_data.csv', index=True)
        hawaii.to_csv('Processed_hawaii_prcp_data.csv', index=True)
    
    def parse_temp(self,filepath):
        column_names = ['id_str', 
                        'Value1', 'DMFlag1',
                        'Value2', 'DMFlag2',
                        'Value3', 'DMFlag3',
                        'Value4', 'DMFlag4',
                        'Value5', 'DMFlag5',
                        'Value6', 'DMFlag6',
                        'Value7', 'DMFlag7',
                        'Value8', 'DMFlag8',
                        'Value9', 'DMFlag9',
                        'Value10', 'DMFlag10',
                        'Value11', 'DMFlag11',
                        'Value12', 'DMFlag12']
        df = pd.read_csv(filepath, header=None, names=column_names, delim_whitespace=True, on_bad_lines="skip")
        df['Station ID'] = df['id_str'].str[:-8]
        df['Year'] = df['id_str'].str[-8:-4]
        df['Element'] = df['id_str'].str[-4:]
        df_florida = df[df['Station ID'] == 'USC00293225']
        df_hawaii = df[df['Station ID'].isin(['USW00022521', 'USW00022522', 'USC00511918'])]
        for i,df in enumerate([df_florida, df_hawaii]):
            df_long = df.melt(id_vars=['Station ID', 'Year', 'Element'], 
                    value_vars=[f'Value{i}' for i in range(1, 13)],
                    var_name='Month', value_name='Temperature')
            df_long['Month'] = df_long['Month'].str.extract('(\d+)').astype(int)
            df_long['Date'] = pd.to_datetime(df_long['Year'].astype(str) + '-' + df_long['Month'].astype(str), format='%Y-%m')
            df_long.set_index('Date', inplace=True)
            df_long.drop(columns=['Year', 'Month'], inplace=True)
            if i == 0:
                df_long.to_csv('Processed_florida_temp_data.csv', index = True)
            if i == 1:
                df_long.to_csv('Processed_hawaii_temp_data.csv', index = True)


# Extract correct data from prcp data
def extract_prcp_data():
    print(os.getcwd())
    filename = '/ghcn-m_v4.00.00_prcp_s16970101_e20241130_c20241205.tar.gz'
    path = os.getcwd() + filename
    print(path)
    with tarfile.open(path, "r:gz") as prcps:
        all = prcps.getmembers()
        for prcp in tqdm(all):
            # florida
            if 'ASN00048154' == prcp.name[:11]:
                print(prcp.name)
                prcps.extract(prcp.name, path=".")
                os.rename(prcp.name, 'prcp_' + prcp.name)
                print("YAY!")
            # honolulu
            elif prcp.name[:11] in ['US1HIHN0009', 'US1HIHN0010', 'US1HIHN0013', 'US1HIHN0017', 'US1HIHN0023', 'US1HIHN0031', 'US1HIHN0035' ,'US1HIHN0037', 'USW00022521', 'USW00022522']:
                print(prcp.name)
                prcps.extract(prcp.name, path=".")
                os.rename(prcp.name, 'prcp_' + prcp.name)
                print("YAY!")

                

if __name__ == "__main__":
    # extract_prcp_data()
    prepare_data = prepare_data()
    prepare_data.parse_hurdat2('HURDAT2_pacific.csv','hawaii')
    prepare_data.parse_hurdat2("HURDAT2_atlantic.csv", 'florida')
    prepare_data.parse_precipitation()
    prepare_data.parse_temp('ghcnm.tavg.v4.0.1.20241208.qcf.dat')

