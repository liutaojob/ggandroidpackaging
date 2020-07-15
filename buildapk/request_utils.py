import requests

url_comp = 'http://manage.xy51.com/dev/param/get_channel_params?appId=197444&channel=xiaomi'

url = 'http://manage.xy51.com/dev/param/get_channel_params'

import channelsdks.game_channel_config


def get_channels_params(game, channel):
    game_appid = channelsdks.game_channel_config.game_appid.get(game)
    data = {'appId': game_appid, 'channel': channel}
    print('start request_%s_%s' % (game_appid,channel))
    r = requests.get(url, params=data)
    s = r.json()
    if s['code'] == 200:
        print(s)
        return s
    else:
        print(s)
        return ''


