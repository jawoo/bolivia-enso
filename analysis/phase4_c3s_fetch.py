#!/usr/bin/env python3
"""Fetch ECMWF SEAS5 (system 51) monthly ensemble-member anomalies over Bolivia from the CDS for the latest
available initialisation, as the forecast-conditioning layer for the Phase 4 analogue ensemble.
Writes derived/phase4/c3s/seas5_<init>_bolivia.nc. Usage: python3 analysis/phase4_c3s_fetch.py [YYYY-MM]"""
import sys, os, datetime as dt, cdsapi
ROOT = os.path.expanduser('~/Claude/bolivia-enso'); OUT = f'{ROOT}/derived/phase4/c3s'; os.makedirs(OUT, exist_ok=True)
init = sys.argv[1] if len(sys.argv) > 1 else (dt.date.today().replace(day=1) - dt.timedelta(days=1)).strftime('%Y-%m')   # previous month's init is always released
year, month = init.split('-'); path = f'{OUT}/seas5_{init}_bolivia.nc'
req = {'originating_centre': 'ecmwf', 'system': '51', 'variable': ['2m_temperature_anomaly', 'total_precipitation_anomalous_rate_of_accumulation'],
       'product_type': ['monthly_mean'], 'year': [year], 'month': [month], 'leadtime_month': ['1', '2', '3', '4', '5', '6'], 'area': [-9, -70, -23.5, -57], 'data_format': 'netcdf'}
print('requesting seasonal-postprocessed-single-levels', req, flush=True)
cdsapi.Client().retrieve('seasonal-postprocessed-single-levels', req, path); print('saved', path, os.path.getsize(path), 'bytes')
