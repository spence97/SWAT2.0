from tethys_sdk.services import get_spatial_dataset_engine
from .config import *
from .outputs_config import *
from osgeo import gdal
from datetime import datetime
from dateutil import relativedelta
from collections import OrderedDict
import numpy as np
import pandas as pd
import os, subprocess, requests, fiona, json, zipfile, random, string, time, logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from .app import Swat2

# PostgreSQL db setup
Base = declarative_base()

class Watershed(Base):
    '''
    Watershed SQLAlchemy DB Model
    '''
    __tablename__ = 'watershed'

    # Columns
    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __init__(self, name):
        self.name = name

class Watershed_Info(Base):
    '''
    Watershed SQLAlchemy DB Model
    '''
    __tablename__ = 'watershed_info'

    # Columns
    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    rch_start = Column(Date)
    rch_end = Column(Date)
    rch_vars = Column(String)
    sub_start = Column(Date)
    sub_end = Column(Date)
    sub_vars = Column(String)
    lulc = Column(String)
    soil = Column(String)
    stations = Column(String)
    rch = Column(String)
    sub = Column(String)
    nasaaccess = Column(String)


    def __init__(self, watershed_id, rch_start, rch_end, rch_vars, sub_start, sub_end, sub_vars, lulc, soil, stations, rch, sub, nasaaccess):
        self.watershed_id = watershed_id
        self.rch_start = rch_start
        self.rch_end = rch_end
        self.rch_vars = rch_vars
        self.sub_start = sub_start
        self.sub_end = sub_end
        self.sub_vars = sub_vars
        self.lulc = lulc
        self.soil = soil
        self.stations = stations
        self.rch = rch
        self.sub = sub
        self.nasaaccess = nasaaccess

class RCH(Base):
    '''
    Region SQLAlchemy DB Model
    '''

    __tablename__ = 'output_rch'

    # Table Columns

    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    year_month_day = Column(Date)
    reach_id = Column(Integer)
    var_name = Column(String)
    val = Column(Float)

    def __init__(self, watershed_id, year_month_day, reach_id, var_name, val):
        """
        Constructor for the table
        """
        self.watershed_id = watershed_id
        self.year_month_day = year_month_day
        self.reach_id = reach_id
        self.var_name = var_name
        self.val = val

class SUB(Base):
    '''
    Region SQLAlchemy DB Model
    '''

    __tablename__ = 'output_sub'

    # Table Columns

    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    year_month_day = Column(Date)
    sub_id = Column(Integer)
    var_name = Column(String)
    val = Column(Float)

    def __init__(self, watershed_id, year_month_day, sub_id, var_name, val):
        """
        Constructor for the table
        """
        self.watershed_id = watershed_id
        self.year_month_day = year_month_day
        self.sub_id = sub_id
        self.var_name = var_name
        self.val = val

class LULC(Base):
    '''
    LULC SQLAlchemy DB Model
    '''

    __tablename__ = 'lulc'

    # Table Columns

    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    value = Column(Integer)
    lulc = Column(String)
    lulc_class = Column(String)
    lulc_subclass = Column(String)
    class_color = Column(String)
    subclass_color = Column(String)

    def __init__(self, watershed_id, value, lulc, lulc_class, lulc_subclass, class_color, subclass_color):
        """
        Constructor for the table
        """
        self.watershed_id = watershed_id
        self.value = value
        self.lulc = lulc
        self.lulc_class = lulc_class
        self.lulc_subclass = lulc_subclass
        self.class_color = class_color
        self.subclass_color = subclass_color

class SOIL(Base):
    '''
    Soil SQLAlchemy DB Model
    '''

    __tablename__ = 'soil'

    # Table Columns

    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    value = Column(Integer)
    soil_class = Column(String)
    class_color = Column(String)

    def __init__(self, watershed_id, value, soil_class, class_color):
        """
        Constructor for the table
        """
        self.watershed_id = watershed_id
        self.value = value
        self.soil_class = soil_class
        self.class_color = class_color

class STREAM_CONNECT(Base):
    '''
    Stream connectivity SQLAlchemy DB Model
    '''

    __tablename__ = 'stream_connect'

    # Table Columns

    id = Column(Integer, primary_key=True)
    watershed_id = Column(Integer, ForeignKey('watershed.id'))
    stream_id = Column(Integer)
    to_node = Column(Integer)

    def __init__(self, watershed_id, stream_id, to_node):
        """
        Constructor for the table
        """
        self.watershed_id = watershed_id
        self.stream_id = stream_id
        self.to_node = to_node

def init_db(engine,first_time):
    Base.metadata.create_all(engine)
    if first_time:
        Session = sessionmaker(bind=engine)
        session = Session()
        session.commit()
        session.close()


# Data extraction functions
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

def extract_daily_rch(watershed, watershed_id, start, end, parameters, reachid):
    dt_start = datetime.strptime(start, '%B %d, %Y').strftime('%Y-%m-%d')
    dt_end = datetime.strptime(end, '%B %d, %Y').strftime('%Y-%m-%d')
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

    Session = Swat2.get_persistent_store_database(db['name'], as_sessionmaker=True)
    session = Session()
    for x in range(0, len(parameters)):
        param_name = rch_param_names[parameters[x]]
        rchDict['Names'].append(param_name)

        rch_qr = """SELECT val FROM output_rch WHERE watershed_id={0} AND reach_id={1} AND var_name='{2}' AND year_month_day BETWEEN '{3}' AND '{4}'; """.format(
            watershed_id, reachid, parameters[x], dt_start, dt_end)
        data = session.execute(text(rch_qr)).fetchall()

        ts = []
        i = 0
        while i < len(data):
            ts.append([daterange_mil[i], data[i][0]])
            i += 1

        rchDict['Values'][x] = ts
        rchDict['Names'].append(param_name)
    session.close()
    return rchDict

def extract_sub(watershed, watershed_id, start, end, parameters, subid):
    dt_start = datetime.strptime(start, '%B %d, %Y').strftime('%Y-%m-%d')
    dt_end = datetime.strptime(end, '%B %d, %Y').strftime('%Y-%m-%d')
    daterange = pd.date_range(start, end, freq='1d')
    daterange = daterange.union([daterange[-1]])
    daterange_str = [d.strftime('%b %d, %Y') for d in daterange]
    daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]

    subDict = {'Watershed': watershed,
               'Dates': daterange_str,
               'ReachID': subid,
               'Parameters': parameters,
               'Values': {},
               'Names': [],
               'Timestep': 'Daily',
               'FileType': 'sub'}

    Session = Swat2.get_persistent_store_database(db['name'], as_sessionmaker=True)
    session = Session()
    for x in range(0, len(parameters)):
        param_name = sub_param_names[parameters[x]]
        subDict['Names'].append(param_name)

        sub_qr = """SELECT val FROM output_sub WHERE watershed_id={0} AND sub_id={1} AND var_name='{2}' AND year_month_day BETWEEN '{3}' AND '{4}'; """.format(
            watershed_id, subid, parameters[x], dt_start, dt_end)
        data = session.execute(text(sub_qr)).fetchall()

        ts = []
        i = 0
        while i < len(data):
            ts.append([daterange_mil[i], data[i][0]])
            i += 1

        subDict['Values'][x] = ts
        subDict['Names'].append(param_name)
    session.close()
    return subDict


# geospatial processing functions
def get_upstreams(watershed_id, streamID):
    Session = Swat2.get_persistent_store_database(db['name'], as_sessionmaker=True)
    session = Session()
    upstreams = [int(streamID)]
    temp_upstreams = [int(streamID)]

    while len(temp_upstreams)>0:
        reach = temp_upstreams[0]
        upstream_qr = """SELECT stream_id FROM stream_connect WHERE watershed_id={0} AND to_node={1}""".format(watershed_id, reach)
        records = session.execute(text(upstream_qr)).fetchall()
        for stream in records:
            temp_upstreams.append(stream[0])
            upstreams.append(stream[0])
        temp_upstreams.remove(reach)
    return upstreams

def clip_raster(watershed, uniqueID, outletID, raster_type):
    input_json = os.path.join(temp_workspace, uniqueID, 'basin_upstream_' + outletID + '.json')
    input_tif = os.path.join(data_path, watershed, 'Land', raster_type + '.tif')
    output_tif = os.path.join(temp_workspace, uniqueID, watershed + '_upstream_'+ raster_type + '_' + outletID + '.tif')

    def demote(user_uid, user_gid):
        def result():
            os.setgid(user_gid)
            os.setuid(user_uid)

        return result

    subprocess.call(
        'gdalwarp --config GDALWARP_IGNORE_BAD_CUTLINE YES -cutline {0} -crop_to_cutline -dstalpha {1} {2}'
            .format(input_json, input_tif, output_tif), preexec_fn=demote(1000, 1000), shell=True)

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

def coverage_stats(watershed, watershed_id, unique_id, outletID, raster_type):
    Session = Swat2.get_persistent_store_database(db['name'], as_sessionmaker=True)
    session = Session()
    tif_path = temp_workspace + '/' + str(unique_id) + '/' + watershed + '_upstream_' + str(raster_type) + '_' + str(
        outletID) + '.tif'
    ds = gdal.Open(tif_path)  # open user-requested TIFF file using gdal
    band = ds.GetRasterBand(1)  # read the 1st raster band
    array = np.array(band.ReadAsArray())  # create an array of all values in the raster
    size = array.size  # get the size (pixel count) of the raster
    unique, counts = np.unique(array, return_counts=True)  # find all the unique values in the raster
    unique_dict = dict(
        zip(unique, counts))  # create a dictionary containing unique values and the number of times each occurs
    # get "NoData" values from the {lulc or soil} Postgres table
    nodata_values = []
    nodata_qr = """SELECT value FROM {0} WHERE watershed_id={1} AND {0}_class='NoData'""".format(raster_type, watershed_id)
    records = session.execute(text(nodata_qr)).fetchall()
    for val in records:
        nodata_values.append(val[0])

    # subtract the count of "No Data" pixels in the raster from the total raster size
    for x in unique_dict:
        if x in nodata_values:
            nodata_size = unique_dict[x]
            size = size - nodata_size
            unique_dict[x] = 0

    # compute percent coverage for each unique value
    for x in unique_dict:
        if x not in nodata_values:
            unique_dict[x] = float(unique_dict[x]) / size * 100
    print(unique_dict)

    # create dictionary containing all the coverage information from the raster and info.txt file
    if raster_type == 'lulc':

        # lulc is divided into classes and subclasses for easier categorizing and visualization
        lulc_dict = {'classes': {}, 'classValues': {}, 'classColors': {}, 'subclassValues': {}, 'subclassColors': {}}

        for val in unique_dict:
            lulc_qr = """SELECT * FROM {0} WHERE watershed_id={1} AND value={2}""".format(raster_type, watershed_id, val)
            records = session.execute(text(lulc_qr)).fetchall()
            record = records[0]
            if str(val) not in nodata_values:
                lulc_dict['subclassColors'][record[5]] = record[7]
                lulc_dict['subclassValues'][record[5]] = unique_dict[val]
                lulc_dict['classes'][record[5]] = record[4]
                if record[4] not in lulc_dict['classValues'].keys():
                    lulc_dict['classValues'][record[4]] = unique_dict[val]
                    lulc_dict['classColors'][record[4]] = record[6]
                else:
                    # add all the % coverage values within a class together
                    lulc_dict['classValues'][record[4]] += unique_dict[val]
        return (lulc_dict)

    if raster_type == 'soil':
        # soil type is only divided into soil types and does not have subcategories like lulc
        soil_dict = {'classValues': {}, 'classColors': {}}

        for val in unique_dict:
            soil_qr = """SELECT * FROM {0} WHERE watershed_id={1} AND value={2}""".format(raster_type, watershed_id, val)
            records = session.execute(text(soil_qr)).fetchall()
            record = records[0]
            if str(val) not in nodata_values:
                soil_dict['classColors'][record[3]] = record[4]
                soil_dict['classValues'][record[3]] = unique_dict[val]
        return (soil_dict)


#nasaaccess function
def nasaaccess_run(userId, streamId, email, functions, watershed, start, end):

    logging.basicConfig(filename='/home/ubuntu/subprocesses/nasaaccess.log', level=logging.INFO)

    #identify where each of the input files are located in the server
    print('Running nasaaccess from SWAT Data Viewer application')
    logging.info('Running nasaaccess from SWAT Data Viewer application')
    shp_path = os.path.join(temp_workspace, userId, 'basin_upstream_' + streamId + '.json')
    dem_path = os.path.join(data_path, watershed, 'Land', 'dem' + '.tif')
    #create a new folder to store the user's requested data
    unique_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    unique_path = os.path.join(nasaaccess_path, 'outputs', unique_id, 'nasaaccess_data')
    #create a temporary directory to store all intermediate data while nasaaccess functions run
    tempdir = os.path.join(nasaaccess_temp, unique_id)

    functions = ','.join(functions)

    try:
        logging.info("trying to run nasaaccess functions")
        #pass user's inputs and file paths to the nasaaccess python function that will run detached from the app
        run = subprocess.call(["/home/ubuntu/tethys/miniconda/envs/nasaaccess/bin/python3", "/home/ubuntu/subprocesses/nasaaccess.py", email, functions, unique_id,
                                shp_path, dem_path, unique_path, tempdir, start, end])

        return "nasaaccess is running"
    except Exception as e:
        logging.info(str(e))
        return str(e)


# data writing functions
def write_csv(data):

    watershed = data['Watershed']
    watershed = watershed.replace('_', '')

    streamID = data['ReachID']

    parameters = data['Parameters']
    param_str = '&'.join(parameters)
    param_str_low = ''.join(param_str.lower().split('_')).replace('/','')

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
    print(file_name)
    file_name.replace('/','')
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

def zipfolder(zip_name, data_dir):
    zipobj = zipfile.ZipFile(zip_name + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(data_dir) + 1
    for base, dirs, files in os.walk(data_dir):
        for file in files:
            fn = os.path.join(base, file)
            zipobj.write(fn, fn[rootlen:])


# def extract_daily_rch(watershed, start, end, parameters, reachid):
#
#     daily_rch_path = os.path.join(data_path, watershed, 'Outputs', 'output_daily.rch')
#
#     param_vals = ['']
#     with open(daily_rch_path) as f:
#         for line in f:
#             if 'RCH' in line:
#                 paramstring = line.strip()
#                 for i in range(0, len(paramstring)-1):
#                     if paramstring[i].islower() and paramstring[i+1].isupper() and paramstring[i] != 'c':
#                         paramstring = paramstring[0:i+1] + ' ' + paramstring[i+1:]
#                 param_vals = param_vals + paramstring.split()
#                 for i in range(0,len(param_vals)-3):
#                     if param_vals[i] == 'TOT':
#                         new_val = param_vals[i]+param_vals[i+1]
#                         param_vals[i] = new_val
#                         param_vals.pop(i+1)
#
#                 break
#
#     dt_start = datetime.strptime(start, '%B %d, %Y')
#     dt_end = datetime.strptime(end, '%B %d, %Y')
#
#     year_start = str(dt_start.year)
#     month_start = str(dt_start.month)
#     day_start = str(dt_start.day)
#
#     if len(day_start) == 1:
#         day_start = '  ' + day_start + ' '
#     if len(day_start) == 2:
#         day_start = ' ' + day_start + ' '
#
#     date_str = month_start + day_start + year_start
#
#     daterange = pd.date_range(start, end, freq='1d')
#     daterange = daterange.union([daterange[-1]])
#     daterange_str = [d.strftime('%b %d, %Y') for d in daterange]
#     daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]
#
#     rchDict = {'Watershed': watershed,
#                'Dates': daterange_str,
#                'ReachID': reachid,
#                'Parameters': parameters,
#                'Values': {},
#                'Names': [],
#                'Timestep': 'Daily',
#                'FileType': 'rch'}
#
#     for x in range(0, len(parameters)):
#
#         param_index = param_vals.index(parameters[x])
#         param_name = rch_param_names[parameters[x]]
#
#         data = []
#         f = open(daily_rch_path)
#
#         for skip_line in f:
#             if date_str in skip_line:
#                 break
#
#         for num, line in enumerate(f,1):
#             line = line.strip()
#             columns = line.split()
#             date = datetime.strptime(columns[3] + '/' + columns [4] + '/' + columns[5], '%m/%d/%Y')
#             if columns[1] == str(reachid) and dt_start <= date <= dt_end:
#                 data.append(float(columns[param_index]))
#             elif date > dt_end:
#                 break
#
#         f.close()
#         ts = []
#         i = 0
#         while i < len(data):
#             ts.append([daterange_mil[i],data[i]])
#             i += 1
#
#
#         rchDict['Values'][x] = ts
#         rchDict['Names'].append(param_name)
#
#
#     return rchDict


# def extract_sub(watershed, start, end, parameters, subid):
#     #function to access timeseries data from output.sub file using user specified variables and date range
#     sub_path = os.path.join(data_path, watershed, 'Outputs', 'output.sub') #path to output.sub file in server
#
#     #read in start and end dates
#     dt_start = datetime.strptime(start, '%B %d, %Y')
#     dt_end = datetime.strptime(end, '%B %d, %Y')
#
#
#     year_start = str(dt_start.year)
#     month_start = str(dt_start.month)
#     day_start = str(dt_start.day)
#
#     #format start date into string to match format in output.sub file. this will be used to skip all unnecessary lines
#     if len(day_start) == 1:
#         day_start = '  ' + day_start + ' '
#     if len(day_start) == 2:
#         day_start = ' ' + day_start + ' '
#     date_str = month_start + day_start + year_start
#
#     #create daterange in milliseconds to be used by highcharts javascript API
#     daterange = pd.date_range(start, end, freq='1d')
#     daterange = daterange.union([daterange[-1]])
#     daterange_str = [d.strftime('%b %d, %Y') for d in daterange]
#     daterange_mil = [int(d.strftime('%s')) * 1000 for d in daterange]
#
#     #initiate dictionary that AJAX will pass back to javascript for data visualization
#     subDict = {'Watershed': watershed,
#                'Dates': daterange_str,
#                'ReachID': subid,
#                'Parameters': parameters,
#                'Values':{},
#                'Names': [],
#                'Timestep': 'Daily',
#                'FileType': 'sub'}
#
#
#     for x in range(0, len(parameters)):     #loop through all user-selected variables
#         param_index = sub_param_vals.index(parameters[x])   #get the column index for the variable in output.sub
#         param_name = sub_param_names[parameters[x]]     #get the human readable name for the variable
#         data = []   #initiate array that will contain all values within daterange
#         f = open(sub_path)
#
#         for skip_line in f:     #skip all lines outside of user-defined date range
#             if date_str in skip_line:
#                 break
#
#         for num, line in enumerate(f,1):    #loop through all lines in file that might have requested data in it
#             line = str(line.strip())
#             columns = line.split()
#             if columns[0] != 'BIGSUB':
#                 split = columns[0]
#                 columns[0] = split[:6]
#                 columns.insert(1, split[6:])
#             date = datetime.strptime(columns[3] + '/' + columns [4] + '/' + columns[5], '%m/%d/%Y') #create date from current line
#             if columns[1] == str(subid) and dt_start <= date <= dt_end: #if date on current line is in user-defined date range
#                 data.append(float(columns[param_index]))    #add data to data array
#             elif date > dt_end:
#                 break
#
#         f.close()
#         ts = [] #initiate array that will contain (time, data) tuples to be plotted by highcharts
#         i = 0
#         while i < len(data):
#             ts.append([daterange_mil[i],data[i]])
#             i += 1
#
#
#         subDict['Values'][x] = ts   #add ts array to the dictionary
#         subDict['Names'].append(param_name)     #add variable name to the dictionary
#
#
#     return subDict

# def write_xml(id):
#     rch_dir = os.path.join(data_path, id)
#     monthly_rch_path = os.path.join(rch_dir, 'output_monthly.rch')
#     daily_rch_path = os.path.join(rch_dir, 'output_daily.rch')
#
#     month_param_vals = []
#     month_years = []
#     year_line_num = []
#     first_line_num = ''
#     with open(monthly_rch_path) as f:
#         for num, line in enumerate(f,1):
#             if 'RCH' in line:
#                 first_line_num = num
#                 paramstring = line.strip()
#                 for i in range(0, len(paramstring) - 1):
#                     if paramstring[i].islower() and paramstring[i + 1].isupper() and paramstring[i] != 'c':
#                         paramstring = paramstring[0:i + 1] + ' ' + paramstring[i + 1:]
#                 month_param_vals = month_param_vals + paramstring.split()
#                 for i in range(0, len(month_param_vals) - 3):
#                     if month_param_vals[i] == 'TOT':
#                         new_val = month_param_vals[i] + month_param_vals[i + 1]
#                         month_param_vals[i] = new_val
#                         month_param_vals.pop(i + 1)
#             elif 'REACH' in line:
#                 line = line.strip()
#                 columns = line.split()
#                 if float(columns[3]) > 12 and columns[3] not in month_years:
#                     year_line_num.append(num)
#                     month_years.append(columns[3])
#
#
#     f = open(monthly_rch_path)
#     lines=f.readlines()
#     month_start_month = lines[int(first_line_num)].strip().split()[3]
#     month_start_date = datetime.date(int(month_years[0]), int(month_start_month), 1).strftime('%B %Y')
#
#     month_end_month = lines[int(year_line_num[-1])-2].strip().split()[3]
#     month_end_date = datetime.date(int(month_years[-1]), int(month_end_month), 1).strftime('%B %Y')
#
#
#     del month_param_vals[month_param_vals.index('RCH')]
#     del month_param_vals[month_param_vals.index('GIS')]
#     del month_param_vals[month_param_vals.index('MON')]
#     del month_param_vals[month_param_vals.index('AREAkm2')]
#
#     month_params = ', '.join(x for x in month_param_vals)
#
#
#     day_param_vals = ['']
#     first_line_num = ''
#     with open(daily_rch_path) as f:
#         for num, line in enumerate(f,1):
#             if 'RCH' in line:
#                 first_line_num = num
#                 paramstring = line.strip()
#                 for i in range(0, len(paramstring) - 1):
#                     if paramstring[i].islower() and paramstring[i + 1].isupper() and paramstring[i] != 'c':
#                         paramstring = paramstring[0:i + 1] + ' ' + paramstring[i + 1:]
#                 day_param_vals = day_param_vals + paramstring.split()
#                 for i in range(0, len(day_param_vals) - 3):
#                     if day_param_vals[i] == 'TOT':
#                         new_val = day_param_vals[i] + day_param_vals[i + 1]
#                         day_param_vals[i] = new_val
#                         day_param_vals.pop(i + 1)
#                 break
#
#     f = open(daily_rch_path)
#     lines=f.readlines()
#     day_start_month = lines[int(first_line_num)].strip().split()[3]
#     day_start_day = lines[int(first_line_num)].strip().split()[4]
#     day_start_year = lines[int(first_line_num)].strip().split()[5]
#
#     day_start_date = datetime.date(int(day_start_year), int(day_start_month), int(day_start_day)).strftime('%B %d, %Y')
#
#     day_end_month = lines[-1].strip().split()[3]
#     day_end_day = lines[-1].strip().split()[4]
#     day_end_year = lines[-1].strip().split()[5]
#
#     day_end_date = datetime.date(int(day_end_year), int(day_end_month), int(day_end_day)).strftime('%B %d, %Y')
#
#
#     del day_param_vals[day_param_vals.index('')]
#     del day_param_vals[day_param_vals.index('RCH')]
#     del day_param_vals[day_param_vals.index('GIS')]
#     del day_param_vals[day_param_vals.index('MO')]
#     del day_param_vals[day_param_vals.index('DA')]
#     del day_param_vals[day_param_vals.index('YR')]
#     del day_param_vals[day_param_vals.index('AREAkm2')]
#
#     day_params = ', '.join(x for x in day_param_vals)
#
#
#     et = ET.parse(watershed_xml_path)
#     watershed = ET.SubElement(et.getroot(), 'watershed')
#
#     ET.SubElement(watershed, "name").text = id
#     ET.SubElement(watershed, "month_start_date").text = month_start_date
#     ET.SubElement(watershed, "month_end_date").text = month_end_date
#     ET.SubElement(watershed, "month_params").text = month_params
#     ET.SubElement(watershed, "day_start_date").text = day_start_date
#     ET.SubElement(watershed, "day_end_date").text = day_end_date
#     ET.SubElement(watershed, "day_params").text = day_params
#
#     tree = ET.ElementTree(et.getroot())
#     tree.write(watershed_xml_path)


# def hrus(watershed_id, upstreamIDs):
#     max_id = max(upstreamIDs)
#     Session = Swat2.get_persistent_store_database('swat_db', as_sessionmaker=True)
#     session = Session()
#     hru_qr =("""SELECT DISTINCT lulc FROM output_hru WHERE watershed_id={0} AND sub_id IN {1} AND sub_id < {2};""".format(
#         watershed_id, upstreamIDs, max_id))
#     hrus = session.execute(text(hru_qr)).fetchall()
#
#
#     hru_options = []
#     hru_info = {}
#
#     for x in range(0, len(hrus)):
#         name_value = (hrus[x][0], hrus[x][0])
#         hru_options.append(name_value)
#     hru_info['options'] = hru_options
#     return hru_info


# def save_files(id):
#
#     rch_path = os.path.join(data_path, id)
#     temp_path = temp_workspace
#     temp_files = os.listdir(temp_path)
#
#     for file in temp_files:
#         if file.endswith('Store'):
#             temp_file_path = os.path.join(temp_path, file)
#             os.remove(temp_file_path)
#         if file.endswith('.rch'):
#             temp_file_path = os.path.join(temp_path, file)
#             perm_file_path = os.path.join(rch_path, file)
#             copyfile(temp_file_path, perm_file_path)
#             os.remove(temp_file_path)
#         elif file.endswith('.zip'):
#             print('uploading file to geoserver')
#             temp_file_path = os.path.join(temp_path, file)
#             '''
#             Check to see if shapefile is on geoserver. If not, upload it.
#             '''
#             geoserver_engine = get_spatial_dataset_engine(name='ADPC')
#             response = geoserver_engine.get_layer(file, debug=True)
#             if response['success'] == False:
#
#                 #Create the workspace if it does not already exist
#                 response = geoserver_engine.list_workspaces()
#                 if response['success']:
#                     workspaces = response['result']
#                     if WORKSPACE not in workspaces:
#                         geoserver_engine.create_workspace(workspace_id=WORKSPACE, uri=GEOSERVER_URI)
#
#                 #Create a string with the path to the zip archive
#                 zip_archive = temp_file_path
#
#                 # Upload shapefile to the workspaces
#                 if '-reach' in file or '-drainageline' in file or '-stream' in file:
#                     store = id + '-reach'
#                 elif '-subbasin' in file or '-catch' in file or '-boundary' in file:
#                     store = id + '-subbasin'
#                 store_id = WORKSPACE + ':' + store
#                 geoserver_engine.create_shapefile_resource(
#                     store_id=store_id,
#                     shapefile_zip=zip_archive,
#                     overwrite=True
#                 )
#             os.remove(temp_file_path)
#
#     write_xml(id)


# def write_ascii(watershed, streamID, parameters, dates, values, timestep):
# ascii_path = os.path.join(temp_workspace, 'swat_data.txt')
#     f = open(ascii_path, 'w+')
#
#     f.write('Watershed:' + str(watershed) + '\n')
#     f.write('StreamID: ' + str(streamID) + '\n')
#
#     param_str = ','.join(str(param) for param in parameters).replace(',', ', ')
#     f.write('Parameters: ' + param_str + '\n')
#
#     if timestep == 'Monthly':
#         start = datetime.strptime(dates[0], '%b %y').strftime('%b %Y')
#         end = datetime.strptime(dates[-1], '%b %y').strftime('%b %Y')
#         head_str = 'UTCoffset(sec)   Date(m/y)'
#     else:
#         start = datetime.strptime(dates[0], '%b %d, %Y').strftime('%m/%d/%Y')
#         end = datetime.strptime(dates[-1], '%b %d, %Y').strftime('%m/%d/%Y')
#         head_str = 'UTCoffset(sec)   Date(m/d/y)'
#
#     f.write('Dates: ' + start + ' - ' + end + '\n')
#
#     f.write('\n')
#     f.write('\n')
#     f.write('\n')
#
#     for param in parameters:
#         head_str += '   ' + param
#     head_str_parts = head_str.split()
#
#     f.write(head_str + '\n')
#
#     for i in range(0, len(dates)):
#         if timestep == 'Monthly':
#             row_str = str(values[0][i][0] / 1000).ljust(len(head_str_parts[0]) + 3, ' ') + \
#                       str(datetime.strptime(dates[i], '%b %y').strftime('%-m/%Y')) \
#                           .ljust(len(head_str_parts[1]) + 3, ' ')
#         else:
#             row_str = str(values[0][i][0] / 1000).ljust(len(head_str_parts[0]) + 3, ' ') + \
#                       str(datetime.strptime(dates[i], '%b %d, %Y').strftime('%-m/%-d/%Y')) \
#                           .ljust(len(head_str_parts[1]) + 3, ' ')
#         for j in range(0, len(parameters)):
#             row_str += str(values[j][i][1]).ljust(len(head_str_parts[j + 2]) + 3, ' ')
#         f.write(row_str + '\n')


# def write_shapefile(watershed, uniqueID, streamID):
#     json_path = os.path.join(temp_workspace, uniqueID)
#
#     upstream_json = json.loads(open(json_path + '/basin_upstream' + streamID + '.json').read())
#
#     coords = []
#
#     for i in range(0, len(upstream_json['features'])):
#         coordinates = upstream_json['features'][i]['geometry']['coordinates'][0][0]
#         coords.append(coordinates)
#
#     new_json = {'type': 'Polygon', 'coordinates': coords}
#
#     shapefile_path = os.path.join(temp_workspace, id, 'shapefile')
#     os.makedirs(shapefile_path, 0777)
#
#     shapefile_path = shapefile_path + '/basin_upstream' + streamID + '.shp'
#
#     schema = {'geometry': 'Polygon', 'properties': {'watershed': 'str:50'}}
#     with fiona.open(shapefile_path, 'w', 'ESRI Shapefile', schema) as layer:
#         layer.write({'geometry': new_json, 'properties': {'watershed': watershed}})
