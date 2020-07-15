# encoding: utf-8
from configobj import ConfigObj


class BuildProperty:
    def __init__(self, proj_conf_file):
        proj_conf = ConfigObj(proj_conf_file)
        self.proj_ver_code = proj_conf['proj_ver_code']
        self.proj_ver_name = proj_conf['proj_ver_name']
        self.proj_pkg_name = proj_conf['proj_pkg_name']
        self.proj_app_name = proj_conf['proj_app_name']
        self.proj_ver_code_pattern = r'android:versionCode=(\'|")(.*?)(\'|")'
        self.proj_ver_code_text = 'android:versionCode="%s"' % \
                                  self.proj_ver_code
        self.proj_ver_name_pattern = r'android:versionName=(\'|")(.*?)(\'|")'
        self.proj_ver_name_text = 'android:versionName="%s"' % \
                                  self.proj_ver_name
        self.proj_app_name_pattern = r'<string name="app_name">.*?</string>'
        self.proj_app_name_text = '<string name="app_name">%s</string>' % \
                                  self.proj_app_name
        self.proj_pkg_name_pattern = r'package="(.*?)"'
        self.proj_pkg_name_text = 'package="%s"' % \
                                  self.proj_pkg_name
