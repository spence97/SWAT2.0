from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting

class Swat2(TethysAppBase):
    """
    Tethys app class for SWAT Data Viewer.
    """

    name = 'Lower Mekong - SWAT'
    index = 'swat2:home'
    icon = 'swat2/images/logo.png'
    package = 'swat2'
    root_url = 'swat2'
    color = '#162d51'
    description = 'Application to access and analyse the inputs and outputs of the Soil and Water Assessment Tool (SWAT)'
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
                name='update_selectors',
                url='swat2/update_selectors',
                controller='swat2.ajax_controllers.update_selectors'
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
                name='clip_rasters',
                url='swat2/clip_rasters',
                controller='swat2.ajax_controllers.clip_rasters'
            ),
            UrlMap(
                name='coverage_compute',
                url='swat2/coverage_compute',
                controller='swat2.ajax_controllers.coverage_compute'
            ),
            UrlMap(
                name='run_nasaaccess',
                url='swat2/run_nasaaccess',
                controller='swat2.ajax_controllers.run_nasaaccess'
            ),
            UrlMap(
                name='save_file',
                url='swat2/save_file',
                controller='swat2.ajax_controllers.save_file'
            ),
            UrlMap(
                name='download_files',
                url='swat2/download_files',
                controller='swat2.ajax_controllers.download_files'
            ),
        )

        return url_maps

    def persistent_store_settings(self):
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='swat_db',
                description='Primary database for SWAT Online app.',
                initializer='swat2.model.init_db',
                required=True
            ),
        )

        return ps_settings
