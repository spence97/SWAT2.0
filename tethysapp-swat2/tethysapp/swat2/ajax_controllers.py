import os, json
from .model import *
from .config import data_path, temp_workspace
from django.http import JsonResponse, HttpResponseRedirect

def get_upstream(request):
    """
    Controller to get list of all upstream reach ids and pass it to front end
    """
    watershed = request.POST.get('watershed')
    streamID = request.POST.get('streamID')
    unique_id = request.POST.get('id')
    unique_path = os.path.join(temp_workspace, unique_id)
    os.makedirs(unique_path, 0777)

    upstreams = get_upstreams(watershed, streamID)

    json_dict = JsonResponse({'watershed': watershed, 'streamID': streamID, 'upstreams': upstreams})
    return json_dict


def save_json(request):
    """
    Controller to clip soil and lulc rasters to upstream boundary and run raster calcs on clipped extents for basin statistics
    """
    upstream_json = json.loads(request.body)
    bbox = upstream_json['bbox']
    srs = 'EPSG:'
    srs += upstream_json['crs']['properties']['name'].split(':')[-1]
    unique_id = upstream_json['uniqueId']
    feature_type = upstream_json['featureType']
    unique_path = os.path.join(temp_workspace, unique_id)
    with open(unique_path + '/' + feature_type + '_upstream.json', 'w') as outfile:
        json.dump(upstream_json, outfile)

    json_dict = JsonResponse({'id': unique_id, 'bbox': bbox, 'srs': srs})
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
    Controller for clipping the lulc file to the upstream catchment boundary and running coverage statistics
    """
    unique_id = request.POST.get('userId')
    watershed = request.POST.get('watershed')
    raster_type = request.POST.get('raster_type')
    clip_raster(unique_id, raster_type)
    lulc_dict = coverage_stats(watershed, unique_id, raster_type)
    json_dict = JsonResponse(lulc_dict)
    return(json_dict)

def save_file(request):
    data_json = json.loads(request.body)
    file_dict = write_csv(data_json)
    json_dict = JsonResponse(file_dict)
    return json_dict
