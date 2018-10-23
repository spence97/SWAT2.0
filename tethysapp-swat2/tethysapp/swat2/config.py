import os
from .app import Swat2



temp_workspace = os.path.join(Swat2.get_app_workspace().path, 'swat')

data_path = os.path.join('/home/ubuntu/swat_data/')

geoserver = {'rest_url':'http://216.218.240.206:8080/geoserver/rest/',
             'wms_url':'http://216.218.240.206:8080/geoserver/wms/',
             'wfs_url':'http://216.218.240.206:8080/geoserver/wfs/',
             'user':'admin',
             'password':'geoserver',
             'workspace':'swat'}


nasaaccess_path = os.path.join('/home/ubuntu/nasaaccess_data')

nasaaccess_temp = os.path.join(Swat2.get_app_workspace().path, 'nasaaccess')

nasaaccess_script = os.path.join('/home/ubuntu/subprocesses/nasaaccess.py')

watershed_xml_path = os.path.join('SWAT_viewer/tethysapp/swat/public/watershed_data/watershed_info.xml')

WORKSPACE = 'swat'
GEOSERVER_URI = 'http://www.example.com/swat'