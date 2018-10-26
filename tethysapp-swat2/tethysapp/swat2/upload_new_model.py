import os
import re
import psycopg2
import datetime
import requests
from dbfread import DBF


# User specified options
watershed_name = 'lower_mekong' #name of watershed to be used throughout the app (needs to be different from pre-existing watershed names)
data_path = '/home/ubuntu/swat_data/lower_mekong/' #path to folder containing all data for new model
sub_vars = ['PRECIPmm', 'PETmm', 'ETmm','SURQmm', 'GW_Qmm'] #vars from output.sub file to upload to db
rch_vars = ['FLOW_OUTcms', 'SEDCONCmg/kg', 'NO3_OUTkg', 'ORGP_OUTkg'] #vars from output.rch file to upload to db

#database specs
db = {'name': 'swat2_swat_db',
            'user':'tethys_super',
            'pass':'pass',
            'host':'localhost',
            'port':'5435'}

#geoserver specs
geoserver = {'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
             'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
             'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
             'user':'admin',
             'password':'geoserver',
             'workspace':'swat'}

# list of variables in SWAT output files used to index columns
sub_column_list = ['', 'SUB', 'GIS', 'MO', 'DA', 'YR', 'AREAkm2', 'PRECIPmm', 'SNOMELTmm', 'PETmm', 'ETmm', 'SWmm', 'PERCmm',
              'SURQmm', 'GW_Qmm', 'WYLDmm', 'SYLDt/ha', 'ORGNkg/ha', 'ORGPkg/ha', 'NSURQkg/ha', 'SOLPkg/ha',
              'SEDPkg/ha', 'LATQmm', 'LATNO3kg/ha', 'GWNO3kg/ha', 'CHOLAmic/L', 'CBODUmg/L', 'DOXQmg/L', 'TNO3kg/ha']
rchmonth_column_list = ['', 'RCH', 'GIS', 'MON', 'AREAkm2', 'FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'TLOSScms', 'SED_INtons',
                  'SED_OUTtons', 'SEDCONCmg/kg', 'ORGN_INkg', 'ORGN_OUTkg', 'ORGP_INkg', 'ORGP_OUTkg', 'NO3_INkg',
                  'NO3_OUTkg', 'NH4_INkg', 'NH4_OUTkg', 'NO2_INkg', 'NO2_OUTkg', 'MINP_INkg', 'MINP_OUTkg',
                  'CHLA_INkg', 'CHLA_OUTkg', 'CBOD_INkg', 'CBOD_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg', 'SOLPST_INmg',
                  'SOLPST_OUTmg', 'SORPST_INmg', 'SORPST_OUTmg', 'REACTPSTmg', 'VOLPSTmg', 'SETTLPSTmg', 'RESUSP_PSTmg',
                  'DIFFUSEPSTmg', 'REACBEDPSTmg', 'BURYPSTmg', 'BED_PSTmg', 'BACTP_OUTct', 'BACTLP_OUTct', 'CMETAL#1kg',
                  'CMETAL#2kg', 'CMETAL#3kg', 'TOTNkg', 'TOTPkg', 'NO3ConcMg/l', 'WTMPdegc']
rchday_column_list = ['', 'RCH', 'GIS', 'MO', 'DA', 'YR', 'AREAkm2', 'FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'TLOSScms', 'SED_INtons',
                  'SED_OUTtons', 'SEDCONCmg/kg', 'ORGN_INkg', 'ORGN_OUTkg', 'ORGP_INkg', 'ORGP_OUTkg', 'NO3_INkg',
                  'NO3_OUTkg', 'NH4_INkg', 'NH4_OUTkg', 'NO2_INkg', 'NO2_OUTkg', 'MINP_INkg', 'MINP_OUTkg',
                  'CHLA_INkg', 'CHLA_OUTkg', 'CBOD_INkg', 'CBOD_OUTkg', 'DISOX_INkg', 'DISOX_OUTkg', 'SOLPST_INmg',
                  'SOLPST_OUTmg', 'SORPST_INmg', 'SORPST_OUTmg', 'REACTPSTmg', 'VOLPSTmg', 'SETTLPSTmg', 'RESUSP_PSTmg',
                  'DIFFUSEPSTmg', 'REACBEDPSTmg', 'BURYPSTmg', 'BED_PSTmg', 'BACTP_OUTct', 'BACTLP_OUTct', 'CMETAL#1kg',
                  'CMETAL#2kg', 'CMETAL#3kg', 'TOTNkg', 'TOTPkg', 'NO3ConcMg/l', 'WTMPdegc']

#data upload functions
def new_watershed(db, watershed_name):
    print('Creating new watershed in database')
    conn = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3} port={4}'
            .format(db['name'], db['user'], db['pass'], db['host'], db['port'])
    )
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()

    if len(records) > 0:
        print('This watershed name already exists. Please specify a new name that is not already being used in the database')
        return 1
    else:
        cur.execute("""INSERT INTO watershed (name) VALUES ('{0}')""".format(watershed_name))

        conn.commit()
        return 0

def upload_swat_outputs(db, output_path, watershed_name, sub_vars, rch_vars):
    print('SWAT output files')
    conn = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3} port={4}'
            .format(db['name'], db['user'], db['pass'], db['host'], db['port'])
    )
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()
    watershed_id = records[0][0]

    for file in os.listdir(output_path):
        #upload output.sub data to PostgreSQL database
        if file.endswith('.sub'):
            print('uploading output.sub to database')
            sub_path = os.path.join(output_path, file)
            f = open(sub_path)
            for skip_line in f:
                if 'AREAkm2' in skip_line:
                    break
            for num, line in enumerate(f, 1):
                line = str(line.strip())
                columns = line.split()
                if re.match('^(?=.*[0-9]$)(?=.*[a-zA-Z])', columns[0]): #split the first column if column[0] and column[1] don't have a space between them
                    split = columns[0]
                    columns[0] = split[:6]
                    columns.insert(1, split[6:])
                for idx, item in enumerate(sub_vars):
                    sub = int(columns[1])
                    dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                    var_name = item
                    val = float(columns[sub_column_list.index(item)])
                    cur.execute("""INSERT INTO output_sub (watershed_id, year_month_day, sub_id, var_name, val)
                         VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, sub, var_name, val))

                conn.commit()

        #upload output.rch data to PostgreSQL database
        if file.endswith('.rch'):
            print('uploading output_daily.rch to database')
            if 'daily' in file:
                print('rch')
                rchday_path = os.path.join(output_path, file)
                f = open(rchday_path)
                for skip_line in f:
                    if 'AREAkm2' in skip_line:
                        break
                for num, line in enumerate(f, 1):
                    line = str(line.strip())
                    columns = line.split()
                    for idx, item in enumerate(rch_vars):
                        reach = int(columns[1])
                        dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                        var_name = item
                        val = float(columns[rchday_column_list.index(item)])
                        cur.execute("""INSERT INTO output_rch_day (watershed_id, year_month_day, reach_id, var_name, val)
                                    VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, reach, var_name, val))

                    conn.commit()

    sub_vars = ','.join(sub_vars)

    cur.execute(
        """SELECT MIN(year_month_day) FROM output_sub WHERE watershed_id={0}""".format(watershed_id)
    )
    sub_start = cur.fetchall()[0][0]

    cur.execute(
        """SELECT MAX(year_month_day) FROM output_sub WHERE watershed_id={0}""".format(watershed_id)
    )

    sub_end = cur.fetchall()[0][0]
    rch_vars = ','.join(rch_vars)

    cur.execute(
        """SELECT MIN(year_month_day) FROM output_rch_day WHERE watershed_id={0}""".format(watershed_id)
    )
    rchday_start = cur.fetchall()[0][0]

    cur.execute(
        """SELECT MAX(year_month_day) FROM output_rch_day WHERE watershed_id={0}""".format(watershed_id)
    )
    rchday_end = cur.fetchall()[0][0]

    cur.execute("""INSERT INTO watershed_info (watershed_id, rchday_start, rchday_end, rch_vars, sub_start, sub_end, sub_vars)
                VALUES ({0}, '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')""".format(watershed_id, rchday_start, rchday_end, rch_vars, sub_start, sub_end, sub_vars)
                )
    conn.commit()
    conn.close()

def upload_shapefiles(geoserver, watershed_path):
    print('Watershed Data')
    for file in os.listdir(watershed_path):
        if file.endswith('.zip'):
            path = os.path.join(watershed_path, file)
            storename = file.split('.')[0]
            print('uploading ' + storename + ' to geoserver')
            headers = {'Content-type': 'application/zip', }
            user = geoserver['user']
            password = geoserver['password']
            data = open(path, 'rb').read()

            request_url = '{0}workspaces/{1}/datastores/{2}/file.shp'.format(geoserver['rest_url'],
                                                                                     geoserver['workspace'],
                                                                                     storename)

            requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))

def upload_stream_connect(db, watershed_path, watershed_name):
    print('uploading stream connectivity information to database')
    conn = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3} port={4}'
            .format(db['name'], db['user'], db['pass'], db['host'], db['port'])
    )
    cur = conn.cursor()

    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()
    watershed_id = records[0][0]

    dbf_path = os.path.join(watershed_path, watershed_name + '-reach.dbf')

    table = DBF(dbf_path, load=True)
    for record in table:
        stream_id = int(record['Subbasin'])
        to_node = int(record['TO_NODE'])
        print(stream_id)

        cur.execute("""INSERT INTO stream_connect (watershed_id, stream_id, to_node) VALUES ({0}, {1}, {2})""".format(
            watershed_id, stream_id, to_node))

        conn.commit()
    conn.close()

def upload_tiffiles(geoserver, land_path, watershed_name):
    print('Land Data')
    for file in os.listdir(land_path):
        if file.endswith('.tif') and 'dem' not in file:
            path = os.path.join(land_path, file)
            storename = watershed_name + '-' + file.split('.')[0]
            print('uploading ' + storename + ' to geoserver')
            headers = {'Content-type': 'image/tiff', }
            user = geoserver['user']
            password = geoserver['password']
            data = open(path, 'rb').read()

            request_url = '{0}workspaces/{1}/coveragestores/{2}/file.geotiff'.format(geoserver['rest_url'],
                                                                                     geoserver['workspace'], storename)

            requests.put(request_url, verify=False, headers=headers, data=data, auth=(user, password))

def upload_lulc_key(db, land_path, watershed_name):
    print('uploading lulc_key to database')
    conn = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3} port={4}'
            .format(db['name'], db['user'], db['pass'], db['host'], db['port'])
    )
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()
    watershed_id = records[0][0]

    lulc_key_path = os.path.join(land_path, 'lulc_key.txt')
    f = open(lulc_key_path)
    for line in f:
        if 'Value' not in line:
            line = line.strip()
            line=line.strip(' ')
            columns = line.split(',')
            value = int(columns[0])
            lulc = columns[1]
            lulc_class = columns[2]
            lulc_subclass = columns[3]
            class_color = columns[4]
            subclass_color = columns[5]
            cur.execute("""INSERT INTO lulc (watershed_id, value, lulc, lulc_class, lulc_subclass, class_color, subclass_color) 
                        VALUES ({0}, {1}, '{2}', '{3}', '{4}', '{5}', '{6}')"""
                        .format(watershed_id, value, lulc, lulc_class, lulc_subclass, class_color, subclass_color))

        conn.commit()

def upload_soil_key(db, land_path, watershed_name):
    print('uploading soil_key to database')
    conn = psycopg2.connect(
        'dbname={0} user={1} password={2} host={3} port={4}'
            .format(db['name'], db['user'], db['pass'], db['host'], db['port'])
    )
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()
    watershed_id = records[0][0]

    soil_key_path = os.path.join(land_path, 'soil_key.txt')
    f = open(soil_key_path)
    for line in f:
        if 'Value' not in line:
            line = line.strip()
            line=line.strip(' ')
            columns = line.split(',')
            value = int(columns[0])
            soil_class = columns[1]
            class_color = columns[2]
            cur.execute("""INSERT INTO soil (watershed_id, value, soil_class, class_color)
                        VALUES ({0}, {1}, '{2}', '{3}')"""
                        .format(watershed_id, value, soil_class, class_color))

        conn.commit()

#Check watershed availability and run data upload functions
# if new_watershed(db, watershed_name) == 0:
#     upload_swat_outputs(db, os.path.join(data_path, 'Outputs'), watershed_name, sub_vars, rch_vars)
#     upload_shapefiles(geoserver, os.path.join(data_path, 'Watershed'))
#     upload_stream_connect(db, os.path.join(data_path, 'Watershed'), watershed_name)
#     upload_tiffiles(geoserver, os.path.join(data_path, 'Land'), watershed_name)
#     upload_lulc_key(db, os.path.join(data_path, 'Land'), watershed_name)
#     upload_soil_key(db, os.path.join(data_path, 'Land'), watershed_name)


upload_shapefiles(geoserver, os.path.join(data_path, 'Watershed'))




# if file.endswith('.hru'):
#     print('hru')
#     hru_path = os.path.join(output_path, file)
#     f = open(hru_path)
#     for skip_line in f:
#         if 'LULC' in skip_line:
#             break
#
#     for num, line in enumerate(f, 1):
#         line = str(line.strip())
#         columns = line.split()
#         if len(columns[0]) > 4:
#             split = columns[0]
#             split_parts = re.split('(\d.*)', split)
#             columns[0] = split_parts[0]
#             columns.insert(1, split_parts[1])
#         if int(columns[7]) == year_one:
#             for idx, item in enumerate(hru_vars):
#                 lulc = columns[0]
#                 hru = int(columns[1])
#                 sub = int(columns[3])
#                 dt = datetime.date(int(columns[7]), int(columns[5]), int(columns[6]))
#                 var_name = item
#                 val = float(columns[hru_column_list.index(item)])
#                 cur.execute("""INSERT INTO output_hru (watershed_id, month_day_year, sub_id, hru_id, lulc, var_name, val)
#                      VALUES ({0}, '{1}', {2}, {3}, '{4}', '{5}', {6})""".format(watershed_id, dt, sub, hru, lulc,
#                                                                                 var_name, val))
#
#             conn.commit()
#         else:
#             break