/*****************************************************************************
 * FILE:    SWAT Viewer MAIN JS
 * DATE:    3/28/18
 * AUTHOR: Spencer McDonald
 * COPYRIGHT:
 * LICENSE:
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/
var LIBRARY_OBJECT = (function() {
    // Wrap the library in a package function
    "use strict"; // And enable strict mode for this library
    /************************************************************************
     *                      MODULE LEVEL / GLOBAL VARIABLES
     *************************************************************************/
    var public_interface,
        geoserver_url = 'http://216.218.240.206:8080/geoserver/wms/',
        basin_layer,
        streams_layer,
        lulc_layer,
        soil_layer,
        featureOverlayStream,
        upstreamOverlayStream,
        featureOverlaySubbasin,
        upstreamOverlaySubbasin,
        rch_map,
        sub_map,
        lulc_map,
        layers,
        wms_source,
        wms_layer,
        current_layer,
        map

    /************************************************************************
     *                    PRIVATE FUNCTION DECLARATIONS
     *************************************************************************/
    var getCookie,
        init_map,
        init_rch_map,
        init_sub_map,
        init_lulc_map,
        init_events,
        get_time_series,
        get_upstream,
        save_json,
        add_streams,
        add_basins,
        add_lulc,
        add_soil,
        clearLayers,
        toggleLayers,
        updateTab,
        updateView,
        update_selectors,
        reset_all,
        init_all

    /************************************************************************
     *                    PRIVATE FUNCTION IMPLEMENTATIONS
     *************************************************************************/
    //Get a CSRF cookie for request
    getCookie = function(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    //find if method is csrf safe
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    //add csrf token to appropriate ajax requests
    $(function() {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                }
            }
        });
    }); //document ready


    //send data to database with error messages
    function ajax_update_database(ajax_url, ajax_data) {
        //backslash at end of url is required
        if (ajax_url.substr(-1) !== "/") {
            ajax_url = ajax_url.concat("/");
        }
        //update database
        var xhr = jQuery.ajax({
            type: "POST",
            url: ajax_url,
            dataType: "json",
            data: ajax_data
        });
        xhr.done(function(data) {
            if("success" in data) {
                // console.log("success");
            } else {
                console.log(xhr.responseText);
            }
        })
        .fail(function(xhr, status, error) {
            console.log(xhr.responseText);
        });

        return xhr;
    }

    init_map = function() {
//      Initialize all the initial map elements (projection, basemap, layers, center, zoom)
        var projection = ol.proj.get('EPSG:4326');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

//        featureOverlayStream = new ol.layer.Vector({
//            source: new ol.source.Vector()
//        });
//
//        featureOverlaySubbasin = new ol.layer.Vector({
//            source: new ol.source.Vector()
//        });

        var view = new ol.View({
            center: [104.5, 17.5],
            projection: projection,
            zoom: 5.5
        });
        wms_source = new ol.source.ImageWMS();

        wms_layer = new ol.layer.Image({
            source: wms_source
        });

        layers = [baseLayer];

        map = new ol.Map({
            target: document.getElementById("map"),
            layers: layers,
            view: view
        });

        map.crossOrigin = 'anonymous';


    };

    init_rch_map = function() {
//      Initialize all the initial map elements (projection, basemap, layers, center, zoom)
        var projection = ol.proj.get('EPSG:4326');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

        featureOverlayStream = new ol.layer.Vector({
            source: new ol.source.Vector()
        });


        var view = new ol.View({
            center: [0, 0],
            projection: projection,
            zoom: 5.5
        });

        wms_source = new ol.source.ImageWMS();

        wms_layer = new ol.layer.Image({
            source: wms_source
        });

        layers = [baseLayer, featureOverlayStream];

        rch_map = new ol.Map({
            target: document.getElementById("rch_map"),
            layers: layers,
            view: view
        });

        map.crossOrigin = 'anonymous';

    };

    init_sub_map = function() {
//      Initialize all the initial map elements (projection, basemap, layers, center, zoom)
        var projection = ol.proj.get('EPSG:4326');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

        featureOverlaySubbasin = new ol.layer.Vector({
            source: new ol.source.Vector()
        });


        var view = new ol.View({
            center: [0, 0],
            projection: projection,
            zoom: 5.5
        });

        wms_source = new ol.source.ImageWMS();

        wms_layer = new ol.layer.Image({
            source: wms_source
        });

        layers = [baseLayer, featureOverlaySubbasin];

        sub_map = new ol.Map({
            target: document.getElementById("sub_map"),
            layers: layers,
            view: view
        });

        map.crossOrigin = 'anonymous';

    };

    init_lulc_map = function() {
//      Initialize all the initial map elements (projection, basemap, layers, center, zoom)
        var projection = ol.proj.get('EPSG:4326');
        var baseLayer = new ol.layer.Tile({
            source: new ol.source.BingMaps({
                key: '5TC0yID7CYaqv3nVQLKe~xWVt4aXWMJq2Ed72cO4xsA~ApdeyQwHyH_btMjQS1NJ7OHKY8BK-W-EMQMrIavoQUMYXeZIQOUURnKGBOC7UCt4',
                imagerySet: 'AerialWithLabels' // Options 'Aerial', 'AerialWithLabels', 'Road'
            })
        });

        featureOverlayStream = new ol.layer.Vector({
            source: new ol.source.Vector()
        });


        var view = new ol.View({
            center: [0, 0],
            projection: projection,
            zoom: 5.5
        });

        wms_source = new ol.source.ImageWMS();

        wms_layer = new ol.layer.Image({
            source: wms_source
        });

        layers = [baseLayer, featureOverlaySubbasin];

        lulc_map = new ol.Map({
            target: document.getElementById("lulc_map"),
            layers: layers,
            view: view
        });

        map.crossOrigin = 'anonymous';

    };

    init_events = function() {
        (function () {
            var target, observer, config;
            // select the target node
            target = $('#app-content-wrapper')[0];

            observer = new MutationObserver(function () {
                window.setTimeout(function () {
                    map.updateSize();
                }, 350);
            });
            $(window).on('resize', function () {
                map.updateSize();

            });


            config = {attributes: true};

            observer.observe(target, config);
        }());

        map.on("singleclick",function(evt){

            if (map.getTargetElement().style.cursor == "pointer") {

                if (!$('#error').hasClass('hidden')) {
                    $('#error').addClass('hidden')
                }

                reset_all();

                var store = $('#watershed_select option:selected').val()
                var reach_store_id = 'swat:' + store + '-reach'
                var basin_store_id = 'swat:' + store + '-subbasin'


                var clickCoord = evt.coordinate;
                var view = map.getView();
                var viewResolution = view.getResolution();

                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), {'INFO_FORMAT': 'application/json'}); //Get the wms url for the clicked point
                console.log(wms_url)
                if (wms_url) {
                    sessionStorage.setItem('userId', Math.random().toString(36).substr(2,5))
                    //Retrieving the details for clicked point via the url
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: 'json',
                        success: function (result) {
                            if (parseFloat(result["features"].length < 1)) {
                                $('#error').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data. Please try again</strong></p>');
                                $('#error').removeClass('hidden');
                                $('#view-reach-loading').addClass('hidden')

                                setTimeout(function () {
                                    $('#error').addClass('hidden')
                                }, 5000);
                            }
                            var streamID = parseFloat(result["features"][0]["properties"]["Subbasin"]);
                            sessionStorage.setItem('streamID', streamID)
                            var watershed = $('#watershed_select').val();
                            sessionStorage.setItem('watershed', watershed)
                            console.log(streamID, watershed)
                            $("#data-modal").modal('show');

                            get_upstream(reach_store_id, basin_store_id, watershed, streamID, sessionStorage.userId);

                        }
                    });
                }
            }
        });

        map.on('pointermove', function(evt) {
            if (evt.dragging) {
                return;
            }
            var pixel = map.getEventPixel(evt.originalEvent);
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer != layers[0]&& layer != layers[1]){
                    current_layer = layer;
                    return true;}
            });
            map.getTargetElement().style.cursor = hit ? 'pointer' : '';
        });
    }

    get_upstream = function(reach_store_id, basin_store_id, watershed, streamID, userId) {
        $.ajax({
            type: "POST",
            url: '/apps/swat2/get_upstream/',
            data: {
                'watershed': watershed,
                'streamID': streamID,
                'id': userId
            },
            success: function(data) {
                var upstreams = data.upstreams
                sessionStorage.setItem('upstreams', upstreams)
                var cql_filter
                if (upstreams.length > 376) {
                    cql_filter = 'Subbasin=' + streamID.toString();
                } else {
                    cql_filter = 'Subbasin=' + streamID.toString();
                    for (var i=1; i<upstreams.length; i++) {
                        cql_filter += ' OR Subbasin=' + upstreams[i].toString();
                    }
                }
                var reach_url = geoserver_url + 'ows?service=wfs&version=2.0.0&request=getfeature&typename=' + reach_store_id + '&CQL_FILTER=Subbasin=' + streamID + '&outputFormat=application/json&srsname=EPSG:4326&,EPSG:4326'
                var upstream_reach_url = geoserver_url + 'ows?service=wfs&version=2.0.0&request=getfeature&typename=' + reach_store_id + '&CQL_FILTER=' + cql_filter+ '&outputFormat=application/json&srsname=EPSG:4326&,EPSG:4326'

                var streamVectorSource = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: reach_url,
                    strategy: ol.loadingstrategy.bbox
                });

                featureOverlayStream = new ol.layer.Vector({
                    source: streamVectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#f44242',
                            width: 3
                        })
                    })
                });

                var upstreamStreamVectorSource = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: upstream_reach_url,
                    strategy: ol.loadingstrategy.bbox
                });

                upstreamOverlayStream = new ol.layer.Vector({
                    source: upstreamStreamVectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#42c5f4',
                            width: 2
                        })
                    })
                });


                var basin_url = geoserver_url + 'ows?service=wfs&version=2.0.0&request=getfeature&typename=' + basin_store_id + '&CQL_FILTER=Subbasin=' + streamID + '&outputFormat=application/json&srsname=EPSG:4326&,EPSG:4326'
                var upstream_basin_url = geoserver_url + 'ows?service=wfs&version=2.0.0&request=getfeature&typename=' + basin_store_id + '&CQL_FILTER=' + cql_filter + '&outputFormat=application/json&srsname=EPSG:4326&,EPSG:4326'
                var upstreamSubbasinVectorSource = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: upstream_basin_url,
                    strategy: ol.loadingstrategy.bbox
                });

                var color = '#ffffff';
                color = ol.color.asArray(color);
                color = color.slice();
                color[3] = .5;

                upstreamOverlaySubbasin = new ol.layer.Vector({
                    source: upstreamSubbasinVectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#000000',
                            width: 2
                        }),
                        fill: new ol.style.Fill({
                            color: color
                        })
                    })
                });

                var subbasinVectorSource = new ol.source.Vector({
                    format: new ol.format.GeoJSON(),
                    url: basin_url,
                    strategy: ol.loadingstrategy.bbox
                });

                var color = '#ffffff';
                color = ol.color.asArray(color);
                color = color.slice();
                color[3] = .5;

                featureOverlaySubbasin = new ol.layer.Vector({
                    source: subbasinVectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#c10000',
                            width: 3
                        }),
                        fill: new ol.style.Fill({
                            color: color
                        })
                    })
                });

                save_json(upstream_basin_url, upstream_reach_url, data);
                rch_map.addLayer(upstreamOverlayStream);
                rch_map.addLayer(featureOverlayStream);
                sub_map.addLayer(upstreamOverlaySubbasin);
                sub_map.addLayer(featureOverlaySubbasin);
                lulc_map.addLayer(upstreamOverlaySubbasin);
            }
        });
    }

    save_json = function(upstream_basin_url, upstream_reach_url, data) {
        $.getJSON(upstream_reach_url, function(data) {
            var upstreamJson = data;
            upstreamJson['uniqueId'] = sessionStorage.userId
            upstreamJson['type'] = 'reach'
            $.ajax({
                type: 'POST',
                url: "/apps/swat2/save_json/",
                data: JSON.stringify(upstreamJson),
                success: function(result){
                    var bbox = result.bbox
                    var srs = result.srs
                    var new_extent = ol.proj.transformExtent(bbox, srs, 'EPSG:4326');
                    console.log(new_extent)
                    sessionStorage.setItem('streamExtent', new_extent)
                    console.log(sessionStorage.streamExtent.split(',').map(Number))
                    var center = ol.extent.getCenter(new_extent)
                    var view = new ol.View({
                        center: center,
                        projection: 'EPSG:4326',
                        extent: new_extent,
                        zoom: 8
                    });

                    rch_map.updateSize();
                    rch_map.getView().fit(sessionStorage.streamExtent.split(',').map(Number), rch_map.getSize());

                }
            })
        })
        $.getJSON(upstream_basin_url, function(data) {
            var upstreamJson = data;
            upstreamJson['uniqueId'] = sessionStorage.userId
            upstreamJson['type'] = 'basin'
            $.ajax({
                type: 'POST',
                url: "/apps/swat2/save_json/",
                data: JSON.stringify(upstreamJson),
                success: function(result){
                    var bbox = result.bbox
                    var srs = result.srs
                    var new_extent = ol.proj.transformExtent(bbox, srs, 'EPSG:4326');
                    sessionStorage.setItem('basinExtent', new_extent)
                    var center = ol.extent.getCenter(new_extent)
                    var view = new ol.View({
                        center: center,
                        projection: 'EPSG:4326',
                        extent: new_extent,
                        zoom: 8
                    });

                    sub_map.updateSize();
                    sub_map.getView().fit(new_extent, sub_map.getSize());
                    lulc_map.updateSize();
                    lulc_map.getView().fit(new_extent, lulc_map.getSize());

                }
            })
        })
    }

    add_streams = function() {
//      add the streams for the selected watershed
        var store = $('#watershed_select option:selected').val()
        var store_id = 'swat:' + store + '-reach'

//      Set the style for the streams layer
        var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+ store_id + '</Name><UserStyle><FeatureTypeStyle><Rule>\
            <Name>rule1</Name>\
            <Title>Blue Line</Title>\
            <Abstract>A solid blue line with a 2 pixel width</Abstract>\
            <LineSymbolizer>\
                <Stroke>\
                    <CssParameter name="stroke">#1500ff</CssParameter>\
                    <CssParameter name="stroke-width">1.2</CssParameter>\
                </Stroke>\
            </LineSymbolizer>\
            </Rule>\
            </FeatureTypeStyle>\
            </UserStyle>\
            </NamedLayer>\
            </StyledLayerDescriptor>';
//      Set the wms source to the url, workspace, and store for the streams of the selected watershed
        wms_source = new ol.source.ImageWMS({
            url: geoserver_url,
            params: {'LAYERS':store_id,'SLD_BODY':sld_string},
            serverType: 'geoserver',
            crossOrigin: 'Anonymous'
        });

        streams_layer = new ol.layer.Image({
            source: wms_source
        });

//      add streams to the map
        map.addLayer(streams_layer);

    };

    add_basins = function(){
//      add the basins for the selected watershed
        var store = $('#watershed_select option:selected').val()
        var store_id = 'swat:' + store + '-subbasin'
//      Set the style for the subbasins layer
        var sld_string = '<StyledLayerDescriptor version="1.0.0"><NamedLayer><Name>'+ store_id + '</Name><UserStyle><FeatureTypeStyle><Rule>\
            <PolygonSymbolizer>\
            <Name>rule1</Name>\
            <Title>Watersheds</Title>\
            <Abstract></Abstract>\
            <Fill>\
              <CssParameter name="fill">#adadad</CssParameter>\
              <CssParameter name="fill-opacity">.3</CssParameter>\
            </Fill>\
            <Stroke>\
              <CssParameter name="stroke">#ffffff</CssParameter>\
              <CssParameter name="stroke-width">.5</CssParameter>\
            </Stroke>\
            </PolygonSymbolizer>\
            </Rule>\
            </FeatureTypeStyle>\
            </UserStyle>\
            </NamedLayer>\
            </StyledLayerDescriptor>';

//      Set the wms source to the url, workspace, and store for the subbasins of the selected watershed
        wms_source = new ol.source.ImageWMS({
            url: geoserver_url,
            params: {'LAYERS':store_id,'SLD_BODY':sld_string},
            serverType: 'geoserver',
            crossOrigin: 'Anonymous'
        });

        basin_layer = new ol.layer.Image({
            source: wms_source
        });

//      add subbasins to the map
        map.addLayer(basin_layer);

    }

    add_lulc = function(){
//      add the streams for the selected watershed
        var store = 'lmrb_2010_lulc_map1'
        var store_id = 'swat:' + store


//      Set the wms source to the url, workspace, and store for the subbasins of the selected watershed
        wms_source = new ol.source.ImageWMS({
            url: geoserver_url,
            params: {'LAYERS':store_id,'STYLES':'lulc'},
            serverType: 'geoserver',
            crossOrigin: 'Anonymous'
        });

        lulc_layer = new ol.layer.Image({
            source: wms_source
        });

//      add subbasins to the map
        map.addLayer(lulc_layer);

    }


    add_soil = function(){
//      add the streams for the selected watershed
        var store = 'lmrb_soil_hwsd1'
        var store_id = 'swat:' + store

//      Set the wms source to the url, workspace, and store for the subbasins of the selected watershed
        wms_source = new ol.source.ImageWMS({
            url: geoserver_url,
            params: {'LAYERS':store_id,'STYLE':'soil'},
            serverType: 'geoserver',
            crossOrigin: 'Anonymous'
        });

        soil_layer = new ol.layer.Image({
            source: wms_source
        });

//      add subbasins to the map
        map.addLayer(soil_layer);

    }


    clearLayers = function() {
        map.removeLayer(soil_layer);
        map.removeLayer(lulc_layer);
        map.removeLayer(basin_layer);
        map.removeLayer(streams_layer);
    }


    toggleLayers = function() {
        if (($('#lulcOption').is(':checked')) && (!$(".toggle").hasClass( "off" ))) {
            add_lulc();
            add_basins();
            add_streams();
        } else if (($('#soilOption').is(':checked')) && (!$(".toggle").hasClass( "off" ))) {
            add_soil();
            add_basins();
            add_streams();
        } else if (($('#noneOption').is(':checked')) && (!$(".toggle").hasClass( "off" ))) {
            add_basins();
            add_streams();
        } else if (($('#lulcOption').is(':checked')) && ($(".toggle").hasClass( "off" ))) {
            add_lulc();
            add_streams();
        } else if (($('#soilOption').is(':checked')) && ($(".toggle").hasClass( "off" ))) {
            add_soil();
            add_streams();
        } else if (($('#noneOption').is(':checked')) && ($(".toggle").hasClass( "off" ))) {
            add_streams();
        }

    }


    updateTab = function() {
        if ($('#rch_link').hasClass('active')) {
            $('#rch_compute').removeClass('hidden')
            rch_map.updateSize();
            rch_map.getView().fit(sessionStorage.streamExtent.split(',').map(Number), rch_map.getSize());
        } else if ($('#sub_link').hasClass('active')) {
            $('#sub_compute').removeClass('hidden')
            sub_map.updateSize();
            sub_map.getView().fit(sessionStorage.streamExtent.split(',').map(Number), sub_map.getSize());
        } else if ($('#hru_link').hasClass('active')) {
            $('#hru_compute').removeClass('hidden')
        } else if ($("#lulc_link").hasClass('active')) {
            $('#lulc_compute').removeClass('hidden')
            lulc_map.updateSize();
            lulc_map.getView().fit(sessionStorage.streamExtent.split(',').map(Number), lulc_map.getSize());
        } else if ($('#soil_link').hasClass('active')) {
            $('#soil_compute').removeClass('hidden')
        } else if ($('#nasaaccess_link').hasClass('active')) {
        }
    }


    updateView = function() {
        var store = $('#watershed_select option:selected').val()
        var store_id = 'swat:' + store + '-reach'
        if (store === 'lower_mekong') {
            var view = new ol.View({
                center: [104.5, 17.5],
                projection: 'EPSG:4326',
                zoom: 6.5
            });

            map.setView(view)
        } else {
            var layerParams
            var layer_xml
            var bbox
            var srs
            var wmsCapUrl = geoserver_url + '?service=WMS&version=1.1.1&request=GetCapabilities&'
//          Get the extent and projection of the selected watershed and set the map view to fit it
            $.ajax({
                type: "GET",
                url: wmsCapUrl,
                dataType: 'xml',
                success: function (xml) {
//                    var layers = xml.getElementsByTagName("Layer");
                    var parser = new ol.format.WMSCapabilities();
                    var result = parser.read(xml);
                    var layers = result['Capability']['Layer']['Layer']
                    for (var i=0; i<layers.length; i++) {
                        if(layers[i].Title == store + '-subbasin') {
                            layer_xml = xml.getElementsByTagName('Layer')[i+1]
                            layerParams = layers[i]
                        }
                    }

                    srs = layer_xml.getElementsByTagName('SRS')[0].innerHTML
                    bbox = layerParams.BoundingBox[0].extent
                    var new_extent = ol.proj.transformExtent(bbox, srs, 'EPSG:4326');
                    var center = ol.extent.getCenter(new_extent)
                    var view = new ol.View({
                        center: center,
                        projection: 'EPSG:4326',
                        extent: new_extent,
                        zoom: 8
                    });

                    map.setView(view)
                    map.getView().fit(new_extent, map.getSize());
                }
            });
        }
    }

    get_time_series = function(watershed, start, end, parameters, streamID, fileType) {
//      Function to pass selected dates, parameters, and streamID to the rch data parser python function and then plot the data
        var monthOrDay
        if ($(".toggle").hasClass( "off" )) {
            monthOrDay = 'Daily'
        } else {
            monthOrDay = 'Monthly'
        }
//      AJAX call to the timeseries python controller to run the rch data parser function
        $.ajax({
            type: 'POST',
            url: '/apps/swat2/timeseries/',
            data: {
                'watershed': watershed,
                'startDate': start,
                'endDate': end,
                'parameters': parameters,
                'streamID': streamID,
                'monthOrDay': monthOrDay,
                'fileType': fileType
            },
            error: function () {
                $('#error').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the data. Please try again</strong></p>');
                $('#error').removeClass('hidden');
                $('#view-reach-loading').addClass('hidden')

                setTimeout(function () {
                    $('#error').addClass('hidden')
                }, 20000);
            },
            success: function (data) {
//              Take the resulting json object from the python function and plot it using the Highcharts API
                var values = data.Values
                var dates = data.Dates
                var parameters = data.Parameters
                var names = data.Names
                var reachId = data.ReachID

                var chartContainer

                if (!data.error) {
                    if (fileType === 'rch') {
                        $('#view-reach-loading').addClass('hidden');
                        $('#rch_chart_container').removeClass('hidden');
                        chartContainer = 'rch_chart_container'
                    } else if (fileType === 'sub') {
                        $('#view-sub-loading').addClass('hidden');
                        $('#sub_chart_container').removeClass('hidden');
                        chartContainer = 'sub_chart_container'
                    }
//                    if ($("#lulcsoil_tab").hasClass('active')) {
//                        $('#lulc_compute').removeClass('hidden');
//                        $('#download_csv').addClass('hidden');
//                        $('#download_ascii').addClass('hidden');
//                    } else if ($('#reach_tab').hasClass('active')) {
//                        $('#lulc_compute').addClass('hidden');
//                        $('#download_csv').removeClass('hidden');
//                        $('#download_ascii').removeClass('hidden');
//                    }

                }
                var plot_title
                fileType = fileType.toUpperCase()
                var plot_subtitle

                if (parameters.length == 1) {
                    plot_title = 'SWAT ' + fileType.toUpperCase() + ' Data'
                    plot_subtitle = 'BasinID: ' + reachId + ', Parameter: ' + names[0]
                } else {
                    plot_title = 'SWAT ' + fileType.toUpperCase() + ' Data'
                    plot_subtitle = 'BasinID: ' + reachId + ', Parameters: ' + names.toString().split(',').join(', ')
                }

                var seriesOptions = []
                var seriesCounter = 0
                var plot_height = 100/parameters.length - 2
                var plot_height_str = plot_height + '%'
                var top = []
                var yAxes = []
                var colors = ['#002cce','#c10000', '#0e6d00', '#7400ce']
                var data_tag
                if (monthOrDay == 'Monthly') {
                   data_tag = '{point.y:,.1f}'
                } else {
                   data_tag = '{point.y:,.1f}'
                }

                $.each( names, function( i, name ) {
                    seriesOptions[i] = {
                        type: 'area',
                        name: name,
                        data: values[i],
                        yAxis: i,
                        color: colors[i],
                        lineWidth: 1
                    };

                    var plot_top = plot_height * i + 2 * i
                    top.push(plot_top +'%')

                    yAxes[i] = {
                        labels: {
                            align: 'right',
                            x: -3
                        },
                        opposite: false,
                        min: 0,
                        title: {
                          text: name
                        },
                        offset: 0,
                        top: top[i],
                        height: plot_height_str,
                        lineWidth: 1,
                        endOnTick: false,
                        gridLineWidth: 0
                    }


                    seriesCounter += 1;

                    if (seriesCounter === names.length) {
                        Highcharts.setOptions({
                            lang: {
                                thousandsSep: ','
                            }
                        });
                        Highcharts.stockChart(chartContainer, {

                            rangeSelector: {
                                enabled: false
                            },

                            title: {
                                text: plot_title
                            },

                            subtitle: {
                                text: plot_subtitle
                            },

                            xAxis: {
                                type: 'datetime',
                                startonTick: true
                            },

                            yAxis: yAxes,


                            plotOptions: {
                                series: {
                                    showInNavigator: true
                                }
                            },

                            tooltip: {
                                pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>' + data_tag + '</b>',
                                valueDecimals: 2 ,
                                split: true
                            },

                            series: seriesOptions
                        });
                    }
                });
            }
        });
    };

    function loadXMLDoc() {
        var request = new XMLHttpRequest();
        request.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                update_selectors(this);
            }
        };
        request.open("GET", "/static/swat2/watershed_data/watershed_info.xml", true);
        request.send();
    };


    update_selectors = function(xml) {
        var watershed, xmlDoc, x, i, watershed_num, start_date, end_date, params_list
        watershed = $('#watershed_select option:selected').val()
        xmlDoc = xml.responseXML;
        x = xmlDoc.getElementsByTagName('watershed');
        for (i = 0; i< x.length; i++) {
            var watershed_name = x[i].childNodes[0].innerHTML
            if (String(watershed_name) === String(watershed)) {
                watershed_num = i
            }
        }


        if ($(".toggle").hasClass( "off")) {
            start_date = xmlDoc.getElementsByTagName("day_start_date")[watershed_num].innerHTML
            end_date = xmlDoc.getElementsByTagName("day_end_date")[watershed_num].innerHTML
            var options = {
                format: 'MM d, yyyy',
                startDate: start_date,
                endDate: end_date,
                startView: 'decade',
                minViewMode: 'days',
                orientation: 'bottom auto'
            }
            $('.input-daterange input').each(function() {
                $(this).datepicker('setDate', null)
                $(this).datepicker('destroy');
                $(this).datepicker(options);
            });
        } else {
            start_date = xmlDoc.getElementsByTagName("month_start_date")[watershed_num].innerHTML;
            end_date = xmlDoc.getElementsByTagName("month_end_date")[watershed_num].innerHTML;
            var options = {
                format: 'MM yyyy',
                startDate: start_date,
                endDate: end_date,
                startView: 'decade',
                minViewMode: 'months',
                orientation: 'bottom auto'
            }
            $('.input-daterange input').each(function() {
                $(this).datepicker('setDate', null)
                $(this).datepicker('destroy');
                $(this).datepicker(options);
            });
        }
        $('#rch_start_pick').attr('placeholder', 'Start Date')
        $('#rch_end_pick').attr('placeholder', 'End Date')

    }

    reset_all = function(){
        $('#rch_var_select').val([]).trigger('change');
        $('#rch_var_select').attr('placeholder', 'Select Variable(s)')
        $('#rch_start_pick').val('')
        $('#rch_end_pick').val('')
        $('#rch_start_pick').attr('placeholder', 'Start Date')
        $('#rch_end_pick').attr('placeholder', 'End Date')
        $('#rch_chart_container').addClass('hidden');
        rch_map.removeLayer(featureOverlayStream)
        rch_map.removeLayer(upstreamOverlayStream)
        sub_map.removeLayer(featureOverlaySubbasin)
        sub_map.removeLayer(upstreamOverlaySubbasin)
    }



    init_all = function(){
        init_map();
        updateView();
        init_rch_map();
        init_sub_map();
        init_lulc_map();
        init_events();
        add_basins();
        add_streams();
    };

    /************************************************************************
     *                        DEFINE PUBLIC INTERFACE
     *************************************************************************/

    public_interface = {

    };

    /************************************************************************
     *                  INITIALIZATION / CONSTRUCTOR
     *************************************************************************/
    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading

    $(function() {
        init_all();

        $(".radio").change(function(){
            clearLayers();
            toggleLayers();
        })

        $(".monthDayToggle").change(function(){
            loadXMLDoc();
        })

        $(".basinToggle").change(function(){
            clearLayers();
            toggleLayers();
        })

        $(".nav-tabs").click(function(){
            $('#rch_compute').addClass('hidden')
            $('#sub_compute').addClass('hidden')
            $('#hru_compute').addClass('hidden')
            $('#lulc_compute').addClass('hidden')
            $('#soil_compute').addClass('hidden')
            setTimeout(updateTab, 300);
        })

        $("#rch_compute").click(function(){
            $('#view-reach-loading').removeClass('hidden')
            var watershed = sessionStorage.watershed
            var start = $('#rch_start_pick').val();
            var end = $('#rch_end_pick').val();
            var parameters = []
            $('#rch_var_select option:selected').each(function() {
                parameters.push( $( this ).val());
                console.log(parameters)
            });
            var streamID = sessionStorage.streamID
            var fileType = 'rch'
            console.log(watershed, start, end, parameters, streamID, fileType)
            get_time_series(watershed, start, end, parameters, streamID, fileType);
        })

        $("#sub_compute").click(function(){
            $('#view-sub-loading').removeClass('hidden')
            var watershed = sessionStorage.watershed
            var start = $('#sub_start_pick').val();
            var end = $('#sub_end_pick').val();
            var parameters = []
            $('#sub_var_select option:selected').each(function() {
                parameters.push( $( this ).val());
            });
            var streamID = sessionStorage.streamID
            var fileType = 'sub'
            console.log(watershed, start, end, parameters, streamID, fileType)
            get_time_series(watershed, start, end, parameters, streamID, fileType);
        })
    })
    return public_interface;

    // Initialization: jQuery function that gets called when
    // the DOM tree finishes loading

}());// End of package wrapper
// NOTE: that the call operator (open-closed parenthesis) is used to invoke the library wrapper
// function immediately after being parsed.


