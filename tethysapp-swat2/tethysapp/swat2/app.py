from tethys_sdk.base import TethysAppBase, url_map_maker


class Swat2(TethysAppBase):
    """
    Tethys app class for SWAT Data Viewer.
    """

    name = 'SWAT Data Viewer'
    index = 'swat2:home'
    icon = 'swat2/images/logo.png'
    package = 'swat2'
    root_url = 'swat2'
    color = '#42f498'
    description = 'Application to access and analyse inputs and outputs of the Soil and Water Assessment Tool (SWAT)'
    tags = '&quot;Hydrology&quot;, &quot;Soil&quot;, &quot;Water&quot;, &quot;Timeseries&quot;'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='swat2',
                controller='swat2.controllers.home'
            ),
            UrlMap(
                name='get_upstream',
                url='swat2/get_upstream',
                controller='swat2.ajax_controllers.get_upstream'
            ),
            UrlMap(
                name='save_json',
                url='swat2/save_json',
                controller='swat2.ajax_controllers.save_json'
            ),
            UrlMap(
                name='timeseries',
                url='swat2/timeseries',
                controller='swat2.ajax_controllers.timeseries'
            ),
            UrlMap(
                name='coverage_compute',
                url='swat2/coverage_compute',
                controller='swat2.ajax_controllers.coverage_compute'
            ),
            UrlMap(
                name='save_file',
                url='swat2/save_file',
                controller='swat2.ajax_controllers.save_file'
            ),
        )

        return url_maps
