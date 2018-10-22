import os
import psycopg2
import datetime
import re


output_path = '/home/ubuntu/swat_data/lower_mekong/Outputs'
watershed_name = 'lower_mekong'
hru_vars = ['PRECIPmm', 'IRRmm', 'PETmm', 'ETmm', 'SW_INITmm', 'SW_ENDmm', 'GW_Qmm']
sub_vars = ['PRECIPmm', 'PETmm', 'ETmm', 'SWmm', 'SURQmm']
rch_vars = ['FLOW_INcms', 'FLOW_OUTcms', 'EVAPcms', 'ORGN_INkg', 'ORGN_OUTkg']







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




def upload_swat_outputs(output_path, watershed_name):
    conn = psycopg2.connect('dbname=swat2_swat_db user=tethys_super password=pass host=localhost port=5435')
    cur = conn.cursor()
    cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
    records = cur.fetchall()
    

    if len(records) > 0:
        print("watershed name already exists")
    else:
        cur.execute("""INSERT INTO watershed (name) VALUES ('{0}')""".format(watershed_name))

        conn.commit()

        cur.execute("""SELECT * FROM watershed WHERE name = '{0}'""".format(watershed_name))
        records = cur.fetchall()
        print(records)
    watershed_id = records[0][0]
    print(watershed_id)
    year_one = 2001

    for file in os.listdir(output_path):
        print(file)

        if file.endswith('.sub'):
            print('sub')
            sub_path = os.path.join(output_path, file)
            f = open(sub_path)
            for skip_line in f:
                if 'AREAkm2' in skip_line:
                    break

            for num, line in enumerate(f, 1):
                line = str(line.strip())
                columns = line.split()
                if columns[0] != 'BIGSUB':
                    split = columns[0]
                    columns[0] = split[:6]
                    columns.insert(1, split[6:])
                if int(columns[5]) == year_one:
                    for idx, item in enumerate(sub_vars):
                        sub = int(columns[1])
                        dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                        var_name = item
                        val = float(columns[sub_column_list.index(item)])
                        cur.execute("""INSERT INTO output_sub (watershed_id, year_month_day, sub_id, var_name, val)
                             VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, sub, var_name, val))

                    conn.commit()

        if file.endswith('.rch'):
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
                    if int(columns[5]) == year_one:
                        for idx, item in enumerate(rch_vars):
                            reach = int(columns[1])
                            dt = datetime.date(int(columns[5]), int(columns[3]), int(columns[4]))
                            var_name = item
                            val = float(columns[rchday_column_list.index(item)])
                            cur.execute("""INSERT INTO output_rch_day (watershed_id, year_month_day, reach_id, var_name, val)
                                 VALUES ({0}, '{1}', {2}, '{3}', {4})""".format(watershed_id, dt, reach, var_name, val))

                        conn.commit()

    conn.close()



upload_swat_outputs(output_path, 'lower_mekong')

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