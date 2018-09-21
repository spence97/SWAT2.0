from django.db import models
from django.core.files import File
from tethys_sdk.services import get_spatial_dataset_engine
from .config import temp_workspace, data_path, geoserver, watershed_xml_path, WORKSPACE, GEOSERVER_URI, nasaaccess_path, nasaaccess_temp
from .outputs_config import *
from dbfread import DBF
from shutil import copyfile
from osgeo import gdal
from datetime import datetime
from dateutil import relativedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import OrderedDict
import numpy as np
import pandas as pd
import xml.etree.cElementTree as ET
import os, subprocess, requests, smtplib, fiona, json, zipfile

def extract_monthly_rch(watershed, start, end, parameters, reachid):

    monthly_rch_path = os.path.join(data_path, watershed, 'Outputs', 'output_monthly.rch')

    dt_start = datetime.strptime(start, '%B %Y')
    dt_end = datetime.strptime(end, '%B %Y')

    year_start = dt_start.year
    year_end = dt_end.year

    delta = relativedelta.relativedelta(dt_end, dt_start)
    total_months = delta.years * 12 + delta.months

    start_index = relativedelta.relativedelta(dt_start, datetime.strptime(str(year_start) + '-01', '%Y-%m')).months
    end_index = start_index + total_months + 1

    daterange = pd.date_range(start, end, freq='1M')
    daterange = daterange.union([daterange[-1] + 1])
    daterange_str = [d.strftime('%b %y') for d in daterange]
    daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]



    f = open(monthly_rch_path)
    for skip_line in f:
        if 'REACH' in skip_line:
            break
    for num, line in enumerate(f, 1):
        line = line.strip()
        columns = line.split()
        if len(columns[3]) > 3:
            first_year = columns[3]
            break



    rchDict = {'Watershed': watershed,
               'Dates': daterange_str,
               'ReachID': reachid,
               'Parameters': parameters,
               'Values':{}, 'Names': [],
               'Timestep': 'Monthly',
               'FileType': 'rch'}
    for x in range(0,len(parameters)):
        param_index = rch_param_vals.index(parameters[x])
        param_name = rch_param_names[parameters[x]]
        data = []
        f = open(monthly_rch_path)
        start_year_str = ' ' + str(year_start-1) + ' '
        end_year_str = str(year_end)
        for skip_line in f:
            if 'RCH' in skip_line:
                break

        if str(year_start) == first_year:
            for num, line in enumerate(f,1):
                line = line.strip()
                columns = line.split()
                if columns[1] == str(reachid) and 1 <= float(columns[3]) <= 12:
                    data.append(float(columns[param_index]))
                elif columns[3] == end_year_str:
                    break

            f.close()
        else:
            for skip_line in f:
                if start_year_str in skip_line:
                    break

            for num, line in enumerate(f,1):
                line = line.strip()
                columns = line.split()
                if columns[1] == str(reachid) and 1 <= float(columns[3]) <= 12:
                    data.append(float(columns[param_index]))
                elif columns[3] == end_year_str:
                    break

            f.close()

        ts = []
        data = data[start_index:end_index]
        i = 0
        while i < len(data):
            ts.append([daterange_mil[i],data[i]])
            i += 1


        rchDict['Values'][x] = ts
        rchDict['Names'].append(param_name)

    return rchDict


def extract_daily_rch(watershed, start, end, parameters, reachid):

    daily_rch_path = os.path.join(data_path, watershed, 'Outputs', 'output_daily.rch')

    param_vals = ['']
    with open(daily_rch_path) as f:
        for line in f:
            if 'RCH' in line:
                paramstring = line.strip()
                for i in range(0, len(paramstring)-1):
                    if paramstring[i].islower() and paramstring[i+1].isupper() and paramstring[i] != 'c':
                        paramstring = paramstring[0:i+1] + ' ' + paramstring[i+1:]
                param_vals = param_vals + paramstring.split()
                for i in range(0,len(param_vals)-3):
                    if param_vals[i] == 'TOT':
                        new_val = param_vals[i]+param_vals[i+1]
                        param_vals[i] = new_val
                        param_vals.pop(i+1)

                break

    dt_start = datetime.strptime(start, '%B %d, %Y')
    dt_end = datetime.strptime(end, '%B %d, %Y')

    year_start = str(dt_start.year)
    month_start = str(dt_start.month)
    day_start = str(dt_start.day)

    if len(day_start) == 1:
        day_start = '  ' + day_start + ' '
    if len(day_start) == 2:
        day_start = ' ' + day_start + ' '

    date_str = month_start + day_start + year_start

    daterange = pd.date_range(start, end, freq='1d')
    daterange = daterange.union([daterange[-1]])
    daterange_str = [d.strftime('%b %d, %Y') for d in daterange]
    daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]

    rchDict = {'Watershed': watershed,
               'Dates': daterange_str,
               'ReachID': reachid,
               'Parameters': parameters,
               'Values': {},
               'Names': [],
               'Timestep': 'Daily',
               'FileType': 'rch'}

    for x in range(0, len(parameters)):

        param_index = param_vals.index(parameters[x])
        param_name = rch_param_names[parameters[x]]

        data = []
        f = open(daily_rch_path)

        for skip_line in f:
            if date_str in skip_line:
                break

        for num, line in enumerate(f,1):
            line = line.strip()
            columns = line.split()
            date = datetime.strptime(columns[3] + '/' + columns [4] + '/' + columns[5], '%m/%d/%Y')
            if columns[1] == str(reachid) and dt_start <= date <= dt_end:
                data.append(float(columns[param_index]))
            elif date > dt_end:
                break

        f.close()
        ts = []
        i = 0
        while i < len(data):
            ts.append([daterange_mil[i],data[i]])
            i += 1


        rchDict['Values'][x] = ts
        rchDict['Names'].append(param_name)


    return rchDict

def extract_sub(watershed, start, end, parameters, subid):
    #function to access timeseries data from output.sub file using user specified variables and date range
    sub_path = os.path.join(data_path, watershed, 'Outputs', 'output.sub') #path to output.sub file in server

    #read in start and end dates
    dt_start = datetime.strptime(start, '%B %d, %Y')
    dt_end = datetime.strptime(end, '%B %d, %Y')


    year_start = str(dt_start.year)
    month_start = str(dt_start.month)
    day_start = str(dt_start.day)

    #format start date into string to match format in output.sub file. this will be used to skip all unnecessary lines
    if len(day_start) == 1:
        day_start = '  ' + day_start + ' '
    if len(day_start) == 2:
        day_start = ' ' + day_start + ' '
    date_str = month_start + day_start + year_start

    #create daterange in milliseconds to be used by highcharts javascript API
    daterange = pd.date_range(start, end, freq='1d')
    daterange = daterange.union([daterange[-1]])
    daterange_str = [d.strftime('%b %d, %Y') for d in daterange]
    daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]

    #initiate dictionary that AJAX will pass back to javascript for data visualization
    subDict = {'Watershed': watershed,
               'Dates': daterange_str,
               'ReachID': subid,
               'Parameters': parameters,
               'Values':{},
               'Names': [],
               'Timestep': 'Daily',
               'FileType': 'sub'}


    for x in range(0, len(parameters)):     #loop through all user-selected variables
        param_index = sub_param_vals.index(parameters[x])   #get the column index for the variable in output.sub
        param_name = sub_param_names[parameters[x]]     #get the human readable name for the variable
        data = []   #initiate array that will contain all values within daterange
        f = open(sub_path)

        for skip_line in f:     #skip all unnecessary lines
            if date_str in skip_line:
                break

        for num, line in enumerate(f,1):    #loop through all lines in file that might have requested data in it
            line = str(line.strip())
            columns = line.split()
            if columns[0] != 'BIGSUB':
                split = columns[0]
                columns[0] = split[:6]
                columns.insert(1, split[6:])
            date = datetime.strptime(columns[3] + '/' + columns [4] + '/' + columns[5], '%m/%d/%Y')
            if columns[1] == str(subid) and dt_start <= date <= dt_end:
                data.append(float(columns[param_index]))    #add data to data array
            elif date > dt_end:
                break

        f.close()
        ts = [] #initiate array that will contain (time, data) tuples to be plotted by highcharts
        i = 0
        while i < len(data):
            ts.append([daterange_mil[i],data[i]])
            i += 1


        subDict['Values'][x] = ts   #add ts array to the dictionary
        subDict['Names'].append(param_name)     #add variable name to the dictionary


    return subDict

def hrus(watershed, upstreamIDs):
    hru_options = []
    hru_info = {}
    hru_path = os.path.join(data_path, watershed, 'Outputs', 'output.hru')
    f = open(hru_path)
    for skip_line in f:
        if 'LULC' in skip_line:
            break
    for num, line in enumerate(f, 1):
        line = line.strip()
        columns = line.split()
        if int(columns[3]) in upstreamIDs:
            name_value = (columns[0] + ' (' + columns[1] + ')', columns[1])
            hru_options.append(name_value)
            hru_info['options'] = hru_options
            hru_info[columns[1]]={}
            hru_info[columns[1]]['Area_km2'] = float(columns[8])
            hru_info[columns[1]]['LULC'] = columns[0]
            hru_info[columns[1]]['MGMT'] = columns[4]
            hru_info[columns[1]]['Subbasin'] = columns[3]
        elif int(columns[3]) > max(upstreamIDs):
            break
    return hru_info


def get_upstreams(watershed, streamID):
    dbf_path = os.path.join(data_path, watershed, 'Watershed', 'Reach.dbf')
    upstreams = [int(streamID)]
    temp_upstreams = [int(streamID)]
    table = DBF(dbf_path, load=True)

    while len(temp_upstreams)>0:
        reach = temp_upstreams[0]
        for record in table:
            if record['TO_NODE'] == reach:
                temp_upstreams.append(record['Subbasin'])
                upstreams.append(record['Subbasin'])
        temp_upstreams.remove(reach)
    return upstreams


def write_shapefile(watershed, uniqueID, streamID):
    json_path = os.path.join(temp_workspace, uniqueID)

    upstream_json = json.loads(open(json_path + '/basin_upstream' + streamID + '.json').read())

    coords = []

    for i in range(0, len(upstream_json['features'])):
        coordinates = upstream_json['features'][i]['geometry']['coordinates'][0][0]
        coords.append(coordinates)

    new_json = {'type': 'Polygon', 'coordinates': coords}

    shapefile_path = os.path.join(temp_workspace, id, 'shapefile')
    os.makedirs(shapefile_path, 0777)

    shapefile_path = shapefile_path + '/basin_upstream' + streamID + '.shp'

    schema = {'geometry': 'Polygon', 'properties': {'watershed': 'str:50'}}
    with fiona.open(shapefile_path, 'w', 'ESRI Shapefile', schema) as layer:
        layer.write({'geometry': new_json, 'properties': {'watershed': watershed}})


def clip_raster(watershed, uniqueID, outletID, raster_type):
    input_json = os.path.join(temp_workspace, uniqueID, 'basin_upstream_' + outletID + '.json')
    input_tif = os.path.join(data_path, watershed, 'Land', raster_type + '.tif')
    output_tif = os.path.join(temp_workspace, uniqueID, watershed + '_upstream_'+ raster_type + '_' + outletID + '.tif')

    subprocess.call(
        'gdalwarp --config GDALWARP_IGNORE_BAD_CUTLINE YES -cutline {0} -crop_to_cutline -dstalpha {1} {2}'
            .format(input_json, input_tif, output_tif), shell=True)

    storename = watershed + '_upstream_' + raster_type + '_' + outletID
    headers = {'Content-type': 'image/tiff', }
    user = geoserver['user']
    password = geoserver['password']
    data = open(output_tif, 'rb').read()

    geoserver_engine = get_spatial_dataset_engine(name='ADPC')
    response = geoserver_engine.get_layer(storename, debug=True)
    if response['success'] == False:
        request_url = '{0}workspaces/{1}/coveragestores/{2}/file.geotiff'.format(geoserver['rest_url'],
                                                                                 geoserver['workspace'], storename)

        requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))
    else:
        print('layer already exists')


def coverage_stats(watershed, uniqueID, outletID, raster_type):
    tif_path = temp_workspace + '/' + str(uniqueID) + '/' + watershed + '_upstream_' + str(raster_type) + '_' + str(outletID) + '.tif'
    ds = gdal.Open(tif_path)
    band = ds.GetRasterBand(1)
    array = np.array(band.ReadAsArray())
    size = array.size
    unique, counts = np.unique(array, return_counts=True)
    unique_dict = dict(zip(unique, counts))

    color_key_path = os.path.join(data_path, watershed, 'Land', raster_type + '_info.txt')
    nodata_values = []
    with open(color_key_path) as f:
        for line in f:
            splitline = line.split('  ')
            if splitline[1] == 'NoData':
                nodata_values.append(splitline[0])
    for x in unique_dict:
        if str(x) in nodata_values:
            nodata_size = unique_dict[x]
            size = size - nodata_size
            unique_dict[x] = 0

    for x in unique_dict:
        if x != 127:
            unique_dict[x] = float(unique_dict[x]) / size * 100
    if raster_type == 'lulc':
        lulc_dict = {'classes': {},'classValues': {}, 'classColors': {}, 'subclassValues': {}, 'subclassColors': {}}

        for val in unique_dict:
            with open(color_key_path) as f:
                for line in f:
                    splitline = line.split('  ')
                    splitline = [x.strip() for x in splitline]
                    if str(val) not in nodata_values and str(val) in splitline[0]:
                        lulc_dict['subclassColors'][splitline[2]] = splitline[-1]
                        lulc_dict['subclassValues'][splitline[2]] = unique_dict[val]
                        lulc_dict['classes'][splitline[2]] = splitline[1]
                        if splitline[1] not in lulc_dict['classValues'].keys():
                            lulc_dict['classValues'][splitline[1]] = unique_dict[val]
                            lulc_dict['classColors'][splitline[1]] = splitline[-2]
                        else:
                            lulc_dict['classValues'][splitline[1]] += unique_dict[val]

        return(lulc_dict)

    if raster_type == 'soil':
        soil_dict = {'classValues': {}, 'classColors': {}}
        for val in unique_dict:
            with open(color_key_path) as f:
                for line in f:
                    splitline = line.split('  ')
                    splitline = [x.strip() for x in splitline]
                    if str(val) not in nodata_values and str(val) in splitline[0]:
                        soil_dict['classColors'][splitline[1]] = splitline[2]
                        soil_dict['classValues'][splitline[1]] = unique_dict[val]
        return(soil_dict)


def save_files(id):

    rch_path = os.path.join(data_path, id)
    temp_path = temp_workspace
    temp_files = os.listdir(temp_path)

    for file in temp_files:
        if file.endswith('Store'):
            temp_file_path = os.path.join(temp_path, file)
            os.remove(temp_file_path)
        if file.endswith('.rch'):
            print('saving file to app workspace')
            temp_file_path = os.path.join(temp_path, file)
            perm_file_path = os.path.join(rch_path, file)
            copyfile(temp_file_path, perm_file_path)
            os.remove(temp_file_path)
        elif file.endswith('.zip'):
            print('uploading file to geoserver')
            temp_file_path = os.path.join(temp_path, file)
            '''
            Check to see if shapefile is on geoserver. If not, upload it.
            '''
            geoserver_engine = get_spatial_dataset_engine(name='ADPC')
            response = geoserver_engine.get_layer(file, debug=True)
            if response['success'] == False:

                #Create the workspace if it does not already exist
                response = geoserver_engine.list_workspaces()
                if response['success']:
                    workspaces = response['result']
                    if WORKSPACE not in workspaces:
                        geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)

                #Create a string with the path to the zip archive
                zip_archive = temp_file_path

                # Upload shapefile to the workspaces
                if '-reach' in file or '-drainageline' in file or '-stream' in file:
                    store = id + '-reach'
                elif '-subbasin' in file or '-catch' in file or '-boundary' in file:
                    store = id + '-subbasin'
                store_id = WORKSPACE + ':' + store
                geoserver_engine.create_shapefile_resource(
                    store_id=store_id,
                    shapefile_zip=zip_archive,
                    overwrite=True
                )
            os.remove(temp_file_path)

    write_xml(id)


def write_csv(data):

    watershed = data['Watershed']
    watershed = watershed.replace('_', '')

    streamID = data['ReachID']

    parameters = data['Parameters']
    param_str = '&'.join(parameters)
    param_str_low = param_str.lower()
    param_str_low = ''.join(param_str.split('_'))

    timestep = data['Timestep']

    dates = data['Dates']

    values = data['Values']

    file_type = data['FileType']

    unique_id = data['userId']

    start = ''
    end = ''

    if timestep == 'Monthly':
        start = datetime.strptime(dates[0], '%b %y').strftime('%m%Y')
        end = datetime.strptime(dates[-1], '%b %y').strftime('%m%Y')
    elif timestep == 'Daily':
        start = datetime.strptime(dates[0], '%b %d, %Y').strftime('%m%d%Y')
        end = datetime.strptime(dates[-1], '%b %d, %Y').strftime('%m%d%Y')

    file_name = watershed + '_' + file_type + streamID + '_' + param_str_low + '_' + start + 'to' + end
    file_dict = {'Parameters': param_str,
                 'Start': start,
                 'End': end,
                 'FileType': file_type,
                 'TimeStep': timestep,
                 'StreamID': streamID}

    csv_path = os.path.join(temp_workspace, unique_id, file_name + '.csv')

    fieldnames = []
    if timestep == 'Monthly':
        fieldnames = ['UTC Offset (sec)', 'Date (m/y)']
    elif timestep == 'Daily':
        fieldnames = ['UTC Offset (sec)', 'Date (m/d/y)']

    fieldnames.extend(parameters)

    utc_list = []
    date_list = []
    for i in range(0, len(dates)):
        utc_list.append(values['0'][i][0]/1000)
        if timestep == 'Monthly':
            date_list.append(datetime.strptime(dates[i], '%b %y').strftime('%-m/%Y'))
        elif timestep == 'Daily':
            date_list.append(datetime.strptime(dates[i], '%b %d, %Y').strftime('%-m/%d/%Y'))
    d = OrderedDict()
    d[fieldnames[0]] = utc_list
    d[fieldnames[1]] = date_list

    for j in range(0, len(parameters)):
        value_list = []
        param = parameters[j]
        for i in range(0, len(dates)):
            value_list.append(values[str(j)][i][1])
        d[param] = value_list

    df = pd.DataFrame(data=d)

    df.to_csv(csv_path, sep=',', index=False)
    return file_dict

def write_ascii(watershed, streamID, parameters, dates, values, timestep):
    ascii_path = os.path.join(temp_workspace, 'swat_data.txt')
    f = open(ascii_path, 'w+')

    f.write('Watershed:' + str(watershed) + '\n')
    f.write('StreamID: ' + str(streamID) + '\n')

    param_str = ','.join(str(param) for param in parameters).replace(',', ', ')
    f.write('Parameters: ' + param_str + '\n')

    if timestep == 'Monthly':
        start = datetime.strptime(dates[0], '%b %y').strftime('%b %Y')
        end = datetime.strptime(dates[-1], '%b %y').strftime('%b %Y')
        head_str = 'UTCoffset(sec)   Date(m/y)'
    else:
        start = datetime.strptime(dates[0], '%b %d, %Y').strftime('%m/%d/%Y')
        end = datetime.strptime(dates[-1], '%b %d, %Y').strftime('%m/%d/%Y')
        head_str = 'UTCoffset(sec)   Date(m/d/y)'

    f.write('Dates: ' + start + ' - ' + end + '\n')

    f.write('\n')
    f.write('\n')
    f.write('\n')

    for param in parameters:
        head_str += '   ' + param
    head_str_parts = head_str.split()

    f.write(head_str + '\n')

    for i in range(0, len(dates)):
        if timestep == 'Monthly':
            row_str = str(values[0][i][0] / 1000).ljust(len(head_str_parts[0]) + 3, ' ') + \
                      str(datetime.strptime(dates[i], '%b %y').strftime('%-m/%Y')) \
                          .ljust(len(head_str_parts[1]) + 3, ' ')
        else:
            row_str = str(values[0][i][0] / 1000).ljust(len(head_str_parts[0]) + 3, ' ') + \
                      str(datetime.strptime(dates[i], '%b %d, %Y').strftime('%-m/%-d/%Y')) \
                          .ljust(len(head_str_parts[1]) + 3, ' ')
        for j in range(0, len(parameters)):
            row_str += str(values[j][i][1]).ljust(len(head_str_parts[j + 2]) + 3, ' ')
        f.write(row_str + '\n')

def zipfolder(zip_name, data_dir):
    zipobj = zipfile.ZipFile(zip_name + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(data_dir) + 1
    for base, dirs, files in os.walk(data_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


def write_xml(id):
    rch_dir = os.path.join(data_path, id)
    monthly_rch_path = os.path.join(rch_dir, 'output_monthly.rch')
    daily_rch_path = os.path.join(rch_dir, 'output_daily.rch')

    month_param_vals = []
    month_years = []
    year_line_num = []
    first_line_num = ''
    with open(monthly_rch_path) as f:
        for num, line in enumerate(f,1):
            if 'RCH' in line:
                first_line_num = num
                paramstring = line.strip()
                for i in range(0, len(paramstring) - 1):
                    if paramstring[i].islower() and paramstring[i + 1].isupper() and paramstring[i] != 'c':
                        paramstring = paramstring[0:i + 1] + ' ' + paramstring[i + 1:]
                month_param_vals = month_param_vals + paramstring.split()
                for i in range(0, len(month_param_vals) - 3):
                    if month_param_vals[i] == 'TOT':
                        new_val = month_param_vals[i] + month_param_vals[i + 1]
                        month_param_vals[i] = new_val
                        month_param_vals.pop(i + 1)
            elif 'REACH' in line:
                line = line.strip()
                columns = line.split()
                if float(columns[3]) > 12 and columns[3] not in month_years:
                    year_line_num.append(num)
                    month_years.append(columns[3])


    f = open(monthly_rch_path)
    lines=f.readlines()
    month_start_month = lines[int(first_line_num)].strip().split()[3]
    month_start_date = datetime.date(int(month_years[0]), int(month_start_month), 1).strftime('%B %Y')

    month_end_month = lines[int(year_line_num[-1])-2].strip().split()[3]
    month_end_date = datetime.date(int(month_years[-1]), int(month_end_month), 1).strftime('%B %Y')


    del month_param_vals[month_param_vals.index('RCH')]
    del month_param_vals[month_param_vals.index('GIS')]
    del month_param_vals[month_param_vals.index('MON')]
    del month_param_vals[month_param_vals.index('AREAkm2')]

    month_params = ', '.join(x for x in month_param_vals)


    day_param_vals = ['']
    first_line_num = ''
    with open(daily_rch_path) as f:
        for num, line in enumerate(f,1):
            if 'RCH' in line:
                first_line_num = num
                paramstring = line.strip()
                for i in range(0, len(paramstring) - 1):
                    if paramstring[i].islower() and paramstring[i + 1].isupper() and paramstring[i] != 'c':
                        paramstring = paramstring[0:i + 1] + ' ' + paramstring[i + 1:]
                day_param_vals = day_param_vals + paramstring.split()
                for i in range(0, len(day_param_vals) - 3):
                    if day_param_vals[i] == 'TOT':
                        new_val = day_param_vals[i] + day_param_vals[i + 1]
                        day_param_vals[i] = new_val
                        day_param_vals.pop(i + 1)
                break

    f = open(daily_rch_path)
    lines=f.readlines()
    day_start_month = lines[int(first_line_num)].strip().split()[3]
    day_start_day = lines[int(first_line_num)].strip().split()[4]
    day_start_year = lines[int(first_line_num)].strip().split()[5]

    day_start_date = datetime.date(int(day_start_year), int(day_start_month), int(day_start_day)).strftime('%B %d, %Y')

    day_end_month = lines[-1].strip().split()[3]
    day_end_day = lines[-1].strip().split()[4]
    day_end_year = lines[-1].strip().split()[5]

    day_end_date = datetime.date(int(day_end_year), int(day_end_month), int(day_end_day)).strftime('%B %d, %Y')


    del day_param_vals[day_param_vals.index('')]
    del day_param_vals[day_param_vals.index('RCH')]
    del day_param_vals[day_param_vals.index('GIS')]
    del day_param_vals[day_param_vals.index('MO')]
    del day_param_vals[day_param_vals.index('DA')]
    del day_param_vals[day_param_vals.index('YR')]
    del day_param_vals[day_param_vals.index('AREAkm2')]

    day_params = ', '.join(x for x in day_param_vals)


    et = ET.parse(watershed_xml_path)
    watershed = ET.SubElement(et.getroot(), 'watershed')

    ET.SubElement(watershed, "name").text = id
    ET.SubElement(watershed, "month_start_date").text = month_start_date
    ET.SubElement(watershed, "month_end_date").text = month_end_date
    ET.SubElement(watershed, "month_params").text = month_params
    ET.SubElement(watershed, "day_start_date").text = day_start_date
    ET.SubElement(watershed, "day_end_date").text = day_end_date
    ET.SubElement(watershed, "day_params").text = day_params

    tree = ET.ElementTree(et.getroot())
    tree.write(watershed_xml_path)


def nasaaccess_run(id, functions, watershed, start, end, email):
    shp_path = os.path.join(temp_workspace, id, 'upstream.shp')
    dem_path = os.path.join(data_path, watershed, 'Land', 'dem.tif')
    unique_path = os.path.join(nasaaccess_path, 'outputs', id, 'nasaaccess_data')
    os.makedirs(unique_path, 0777)
    tempdir = os.path.join(nasaaccess_temp, id)
    os.makedirs(tempdir, 0777)
    cwd = os.getcwd()

    os.chdir(tempdir)

    for func in functions:
        if func == 'GPMpolyCentroid':
            output_path = unique_path + '/GPMpolyCentroid/'
            os.makedirs(output_path, 0777)
            print('running GPMpoly')
            GPMpolyCentroid(output_path, shp_path, dem_path, start, end)
        elif func == 'GPMswat':
            output_path = unique_path + '/GPMswat/'
            os.makedirs(output_path, 0777)
            print('running GPMswat')
            GPMswat(output_path, shp_path, dem_path, start, end)
        elif func == 'GLDASpolyCentroid':
            output_path = unique_path + '/GLDASpolyCentroid/'
            os.makedirs(output_path, 0777)
            print('running GLDASpoly')
            GLDASpolyCentroid(tempdir, output_path, shp_path, dem_path, start, end)
        elif func == 'GLDASwat':
            output_path = unique_path + '/GLDASwat/'
            os.makedirs(output_path, 0777)
            print('running GLDASwat')
            GLDASwat(output_path, shp_path, dem_path, start, end)

    from_email = 'nasaaccess@gmail.com'
    to_email = email

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Your nasaaccess data is ready'

    msg['From'] = from_email
    msg['To'] = to_email

    message = """\
        <html>
            <head></head>
            <body>
                <p>Hello,<br>
                   Your nasaaccess data is ready for download at <a href="http://tethys-servir-mekong.adpc.net/apps/nasaaccess">http://tethys-servir-mekong.adpc.net/apps/nasaaccess</a><br>
                   Your unique access code is: <strong>""" + unique_id + """</strong><br>
                </p>
            </body>
        <html>
    """

    part1 = MIMEText(message, 'html')
    msg.attach(part1)

    gmail_user = 'nasaaccess@gmail.com'
    gmail_pwd = 'nasaaccess123'
    smtpserver = smtplib.SMTP('smtp.gmail.com', 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(gmail_user, gmail_pwd)
    smtpserver.sendmail(gmail_user, to_email, msg.as_string())
    smtpserver.close()


