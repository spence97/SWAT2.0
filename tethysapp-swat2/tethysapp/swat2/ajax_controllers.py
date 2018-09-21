import os, json
from .model import *
from .config import temp_workspace
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse

def get_upstream(request):
    """
    Controller to get list of all upstream reach ids and pass it to front end
    """
    watershed = request.POST.get('watershed')
    streamID = request.POST.get('streamID')
    unique_id = request.POST.get('id')
    unique_path = os.path.join(temp_workspace, unique_id)
    if not os.path.exists(unique_path):
        os.makedirs(unique_path, 0777)

    upstreams = get_upstreams(watershed, streamID)

    json_dict = JsonResponse({'watershed': watershed, 'streamID': streamID, 'upstreams': upstreams})
    return json_dict


def save_json(request):
    """
    Controller to save upstream stream and subbasin json files to user's data cart
    """
    upstream_json = json.loads(request.body)
    bbox = upstream_json['bbox']
    srs = 'EPSG:'
    srs += upstream_json['crs']['properties']['name'].split(':')[-1]
    unique_id = upstream_json['uniqueId']
    outletID = upstream_json['outletID']
    feature_type = upstream_json['featureType']

    unique_path = os.path.join(temp_workspace, unique_id)
    with open(unique_path + '/' + feature_type + '_upstream_' + outletID + '.json', 'w') as outfile:
        json.dump(upstream_json, outfile)

    json_dict = JsonResponse({'id': unique_id, 'bbox': bbox, 'srs': srs})
    if feature_type == 'basin':
        watershed = upstream_json['watershed']
        clip_raster(watershed, unique_id, outletID, 'lulc')
        clip_raster(watershed, unique_id, outletID, 'soil')
    return json_dict


def timeseries(request):
    """
    Controller for the time-series plot.
    """
    # Get values passed from the timeseries function in main.js
    watershed = request.POST.get('watershed')
    start = request.POST.get('startDate')
    end = request.POST.get('endDate')
    parameters = request.POST.getlist('parameters[]')
    streamID = request.POST.get('streamID')
    monthOrDay = request.POST.get('monthOrDay')
    file_type = request.POST.get('fileType')


    if file_type == 'rch':
        # Call the correct rch data parser function based on whether the monthly or daily toggle was selected
        if monthOrDay == 'Monthly':
            timeseries_dict = extract_monthly_rch(watershed, start, end, parameters, streamID)
        else:
            timeseries_dict = extract_daily_rch(watershed, start, end, parameters, streamID)
    elif file_type == 'sub':
        timeseries_dict= extract_sub(watershed, start, end, parameters, streamID)

    # Return the json object back to main.js for timeseries plotting
    json_dict = JsonResponse(timeseries_dict)
    print(json_dict)
    return json_dict

def coverage_compute(request):
    """
    Controller for computing the lulc or soil coverage statistics
    """
    uniqueID = request.POST.get('userID')
    outletID = str(request.POST.get('outletID'))
    print(outletID)
    watershed = request.POST.get('watershed')
    raster_type = request.POST.get('raster_type')
    # clip_raster(watershed, uniqueID, outletID, raster_type)
    coverage_dict = coverage_stats(watershed, uniqueID, outletID, raster_type)
    json_dict = JsonResponse(coverage_dict)
    return(json_dict)

def get_hrus(request):
    """
    Controller for listing all HRUs that fall within a subbasin(s) boundary
    """
    upstreams = request.POST.get('upstreams')
    watershed = request.POST.get('watershed')
    upstreamIDs = list(map(int, upstreams.split(',')))
    print(upstreamIDs)
    hru_dict = hrus(watershed, upstreamIDs)
    json_dict = JsonResponse(hru_dict)
    return(json_dict)


def save_file(request):
    data_json = json.loads(request.body)
    file_dict = write_csv(data_json)
    json_dict = JsonResponse(file_dict)
    return json_dict

def download_files(request):
    if request.method == 'POST':
        uniqueID = request.POST['userID']

        data_dir = os.path.join(temp_workspace, uniqueID)

        zipfolder(data_dir, data_dir)

        path_to_file = os.path.join(temp_workspace, uniqueID + '.zip')
        print(path_to_file)
        f = open(path_to_file, 'r')
        myfile = File(f)

        response = HttpResponse(myfile, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=' + uniqueID + '.zip'
        return response