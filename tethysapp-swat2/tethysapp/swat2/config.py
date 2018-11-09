import os
from .app import Swat2

temp_workspace = os.path.join(Swat2.get_app_workspace().path, 'swat')

data_path = os.path.join('/home/ubuntu/swat_data/')

geoserver = {'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
             'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
             'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
             'user':'admin',
             'password':'geoserver',
             'workspace':'swat'
             }

db = {'name': 'swat_db',
            'user':'tethys_super',
            'pass':'pass',
            'host':'localhost',
            'port':'5435'}

nasaaccess_path = os.path.join('/home/ubuntu/nasaaccess_data')

nasaaccess_temp = os.path.join(Swat2.get_app_workspace().path, 'nasaaccess')

nasaaccess_script = os.path.join('/home/ubuntu/subprocesses/nasaaccess.py')

nasaaccess_log = os.path.join('/home/ubuntu/subprocesses/nasaaccess.log')

gdalwarp_path = os.path.join('/home/ubuntu/tethys/miniconda/envs/tethys/bin/gdalwarp')