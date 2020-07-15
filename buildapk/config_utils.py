# encoding:utf-8
import os
import os.path
import file_utils
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import Element
from xml.etree.cElementTree import ElementTree

import buildapk.request_utils as request_utils
from channelsdks import game_channel_config


def get_keystore(channel):
    return get_default_keystore(channel)


def get_default_keystore(channel):
    print("channel" + channel)
    if channel.startswith('kuaiyouph'):
        config_file = file_utils.getFullPath("channelkeystore/keystore.xml")
        print("111channel" + channel + "config_file+" + config_file)
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


def request_channels_params(channel_args, game):
    lst_channels = []
    for channel_name in channel_args.split(":"):
        if channel_name is "":
            break;

        channel = {}
        channel['name'] = channel_name

        if not os.path.exists(file_utils.getFullPath("sdks/%s/sdk/%s" % (game, channel_name))) and not os.path.exists(
                file_utils.getFullPath("channelsdks/%s" % channel_name)):
            channel['sdk'] = 'stvgame'
        else:
            channel['sdk'] = channel_name
        suffix = game_channel_config.channel_suffix.get(channel_name)
        channel['suffix'] = suffix
        s = request_utils.get_channels_params(game, channel_name)
        if s is '':
            channel['params'] = []
            lst_channels.append(channel)
            continue;
        params = s['data']

        if params is not None and len(params) > 0:
            channel['params'] = []

            for key in params.keys():
                if params.get(key) is None:
                    params[key] = ""

            channel['params'].append(params)
            print(channel)
        lst_channels.append(channel)

    return lst_channels


def write_developer_properties(channel, target_file_path,game):
    target_file_path = file_utils.getFullPath(target_file_path)
    target_file_path = target_file_path.replace("\\", "/")
    pro_str = ""
    if channel['params'] is not None and len(channel['params']) > 0:
        pro_str = game_channel_config.convert_channel_key(channel)
        pro_str =pro_str+'game' + "=" + game
        # for param in channel['params']:
        #     if param['name'] and param['value'] is not None:
        #         pro_str = pro_str + param['name'] + "=" + param['value'] + "\n"
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


def write_plugin_configs_from_plubic(channel, target_file_path):
    target_file_path = file_utils.getFullPath(target_file_path)
    target_file_path = target_file_path.replace("\\", "/")
    target_tree = ElementTree()
    target_root = Element('plugins')
    target_tree._setroot(target_root)
    sdk = channel['sdk']
    login_pay_class = {}
    if sdk in game_channel_config.channel_login_pay:
            login_pay_class = game_channel_config.channel_login_pay.get(sdk)
    print('登录支付类' + str(login_pay_class) + '写入路径' + str(target_file_path))

    type_tag = 'plugin'
    if login_pay_class.get('login') is not None:
        type_name = login_pay_class.get('login')
        type_val = '1'
        plugin_node = SubElement(target_root, type_tag)
        plugin_node.set('name', type_name)
        plugin_node.set('type', type_val)
    if login_pay_class.get('pay') is not None:
        type_name = login_pay_class.get('pay')
        type_val = '2'
        plugin_node = SubElement(target_root, type_tag)
        plugin_node.set('name', type_name)
        plugin_node.set('type', type_val)

    target_tree.write(target_file_path, 'UTF-8')
