from django.shortcuts import *
from tethys_sdk.gizmos import *
from .config import data_path
from datetime import datetime
from .outputs_config import rch_options, sub_options
import os

def home(request):
    """
    Controller for the Output Viewer page.
    """
    # Get available watersheds (with rch data and wms capabilities) and set select_watershed options

    watershed_options = []
    watershed_list = os.listdir(data_path)
    for f in watershed_list:
        if f.startswith('.'):
            pass
        elif f.endswith('.xml'):
            pass
        else:
            name = f.replace('_', ' ').title()
            value = f
            if name not in watershed_options:
                watershed_options.append((name,value))


    # set the initial date picker options
    rch_start = 'January 2005'
    rch_end = 'December 2015'
    rch_format = 'MM yyyy'
    rch_startView = 'decade'
    rch_minView = 'months'

    na_start = 'Jan 01, 2000'
    na_end = datetime.now().strftime("%b %d, %Y")
    na_format = 'MM d, yyyy'
    na_startView = 'decade'
    na_minView = 'days'

    sub_start = 'January 01, 2001'
    sub_end = 'December 31, 2015'
    sub_format = 'MM d, yyyy'
    sub_startView = 'decade'
    sub_minView = 'days'

    watershed_select = SelectInput(name='watershed_select',
                                   multiple=False,
                                   original=False,
                                   options=watershed_options,
                                   initial=[('Lower Mekong', 'lower_mekong')],
                                   # select2_options={'placeholder': 'Select a Watershed to View',
                                   #                  'allowClear': False},
                                   )

    rch_start_pick = DatePicker(name='rch_start_pick',
                            autoclose=True,
                            format=rch_format,
                            min_view_mode=rch_minView,
                            start_date=rch_start,
                            end_date=rch_end,
                            start_view=rch_startView,
                            today_button=False,
                            initial='Start Date')

    rch_end_pick = DatePicker(name='rch_end_pick',
                          autoclose=True,
                          format=rch_format,
                          min_view_mode=rch_minView,
                          start_date=rch_start,
                          end_date=rch_end,
                          start_view=rch_startView,
                          today_button=False,
                          initial='End Date'
                          )

    sub_start_pick = DatePicker(name='sub_start_pick',
                                autoclose=True,
                                format=sub_format,
                                min_view_mode=sub_minView,
                                start_date=sub_start,
                                end_date=sub_end,
                                start_view=sub_startView,
                                today_button=False,
                                initial='Start Date')

    sub_end_pick = DatePicker(name='sub_end_pick',
                              autoclose=True,
                              format=sub_format,
                              min_view_mode=sub_minView,
                              start_date=sub_start,
                              end_date=sub_end,
                              start_view=sub_startView,
                              today_button=False,
                              initial='End Date'
                              )

    na_start_pick = DatePicker(name='na_start_pick',
                            autoclose=True,
                            format=na_format,
                            min_view_mode=na_minView,
                            start_date=na_start,
                            end_date=na_end,
                            start_view=na_startView,
                            today_button=False,
                            initial='Start Date')

    na_end_pick = DatePicker(name='na_end_pick',
                          autoclose=True,
                          format=na_format,
                          min_view_mode=na_minView,
                          start_date=na_start,
                          end_date=na_end,
                          start_view=na_startView,
                          today_button=False,
                          initial='End Date'
                          )

    rch_var_select = SelectInput(name='rch_var_select',
                               multiple=True,
                               original=False,
                               options=rch_options,
                               select2_options={'placeholder': 'Select Variable(s)',
                                                'allowClear': False},
                               )

    sub_var_select = SelectInput(name='sub_var_select',
                                 multiple=True,
                                 original=False,
                                 options=sub_options,
                                 select2_options={'placeholder': 'Select Variable(s)',
                                                  'allowClear': False},
                                 )



    context = {
        'rch_start_pick': rch_start_pick,
        'rch_end_pick': rch_end_pick,
        'na_start_pick': na_start_pick,
        'na_end_pick': na_end_pick,
        'sub_start_pick': sub_start_pick,
        'sub_end_pick': sub_end_pick,
        'rch_var_select': rch_var_select,
        'sub_var_select': sub_var_select,
        'watershed_select': watershed_select
    }

    return render(request, 'swat2/home.html', context)