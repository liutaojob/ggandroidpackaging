# encoding:utf-8
import os
import os.path
import file_utils
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import Element
from xml.etree.cElementTree import ElementTree


def get_keystore(channel):
    return get_default_keystore(channel)


def get_default_keystore(channel):
    print("channel"+channel)
    if channel.startswith('kuaiyouph'):
       config_file = file_utils.getFullPath("channelkeystore/keystore.xml")
       print("111channel" + channel+"config_file+"+config_file)
    else:
       config_file = file_utils.getFullPath("sdks/keystore.xml")
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()
    except Exception as e:
        file_utils.printF("Can not parse xml config :path:%s", config_file)
        return None
    params = root.find("default").findall("param")
    channel = {}
    for cParam in params:
        key = cParam.get('name')
        val = cParam.get('value')
        channel[key] = val
    return channel


def get_all_channels(channel_args, game):
    lst_channels = []

    for channel_name in channel_args.split(":"):
        if channel_name is "":
            break;
        config_file = file_utils.getFullPath("sdks/%s/sdk/%s/sdk_config.xml" % (game, channel_name))
        channel = {}
        channel['name'] = channel_name

        if not os.path.exists(config_file):
            config_file = file_utils.getFullPath("sdks/%s/sdk/stvgame/sdk_config.xml" % game)

        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
        except Exception as e:
            file_utils.printF("Can not parse xml config:path:%s", config_file)
            return None

        channel_nodes = root.find("channel")
        if channel_nodes is not None and len(channel_nodes) > 0:
            # channel['params'] = []
            for channelNode in channel_nodes:
                param = {}
                # param['name'] =
                # param['value'] =
                channel[channelNode.get('name')] = channelNode.get('value')

        param_nodes = root.find("params")
        if param_nodes is not None and len(param_nodes) > 0:
            channel['params'] = []
            for paramNode in param_nodes:
                param = {}
                param['name'] = paramNode.get('name')
                param['value'] = paramNode.get('value')
                channel['params'].append(param)

        operation_nodes = root.find("ops")
        if operation_nodes is not None and len(operation_nodes) > 0:
            channel['ops'] = []
            for opNode in operation_nodes:
                op = {}
                op['type'] = opNode.get('type')
                op['from'] = opNode.get('from')
                op['to'] = opNode.get('to')
                channel['ops'].append(op)

        plugin_nodes = root.find("plugins")
        if plugin_nodes is not None and len(plugin_nodes) > 0:
            channel['plugins'] = []
            for pNode in plugin_nodes:
                p = {}
                p['name'] = pNode.get('name')
                p['type'] = pNode.get('type')
                channel['plugins'].append(p)
        lst_channels.append(channel)

    return lst_channels


# def loadChannelUserConfig(channel):
#     configFile = file_utils.getFullPath("sdks/sdk/" + channel['sdk'] + "/sdk_config.xml").replace('\\', "/")
#
#     if not os.path.exists(configFile):
#         print("********** " + configFile + " no exits")
#         return 0
#     try:
#         tree = ET.parse(configFile)
#         root = tree.getroot()
#     except:
#         file_utils.printF("Can not parse xml config :path:%s", configFile)
#         return 0
#
#     configNode = root
#
#
#
#     return 1


def write_developer_properties(channel, target_file_path):
    target_file_path = file_utils.getFullPath(target_file_path)
    target_file_path = target_file_path.replace("\\", "/")
    pro_str = ""
    if channel['params'] is not None and len(channel['params']) > 0:
        for param in channel['params']:
            pro_str = pro_str + param['name'] + "=" + param['value'] + "\n"
        file_utils.printF('The developInfo is "%s"', pro_str)

    target_file = open(target_file_path, 'wb')
    pro_str = pro_str.encode('UTF-8')
    target_file.write(pro_str)
    target_file.close()


def write_plugin_configs(channel, target_file_path):
    target_file_path = file_utils.getFullPath(target_file_path)
    target_file_path = target_file_path.replace("\\", "/")
    target_tree = ElementTree()
    target_root = Element('plugins')
    target_tree._setroot(target_root)

    if "plugins" in channel:
        for plugin in channel['plugins']:
            type_tag = 'plugin'
            type_name = plugin['name']
            type_val = plugin['type']
            plugin_node = SubElement(target_root, type_tag)
            plugin_node.set('name', type_name)
            plugin_node.set('type', type_val)

    target_tree.write(target_file_path, 'UTF-8')
