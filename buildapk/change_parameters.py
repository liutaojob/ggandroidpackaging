import channelsdks.game_channel_config as game_change
import buildapk.file_utils as file_u
import buildapk.config_utils as config_utils
import buildapk.request_utils as request
import os
def change_manifest_parameters(file_path,channel,game):

    channel_sdk = channel['sdk']

    for param in channel['params']:
        appId = param['appId']
        appKey = param['appKey']
        appMd5Secret = param['appMd5Secret']
        notifyUrl = param['notifyUrl']
        gameId =param['gameId']
        mchId =param['mchId']
        appNotifyDesc =param['appNotifyDesc']

        if channel_sdk == "xiongmaowan":
            result = file_u.update_content(file_path, "client_id",appId)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "miguo" :
            file_u.update_content(file_path, "miguo_appid", appId)
            file_u.update_content(file_path, "miguo_client_id", appMd5Secret)
            result=file_u.update_content(file_path, "miguo_client_key", gameId)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "landie" :
            result =file_u.update_content(file_path, "applicationId", "com.xy51.%s"%game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk== "xiaoqi" :
            result = file_u.update_content(file_path, "applicationId", "com.xy51.%s.x7sy" % game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "jiuyao" :
            result = file_u.update_content(file_path, "applicationId", "com.xy51.%s.jyyx.game" % game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "kuaiyouph" :
            file_u.update_content(file_path, "applicationId", "com.xy51.%s.xinkuai" % game)
            file_u.update_content(file_path, "kauiyou_appid", appId)
            result=file_u.update_content(file_path, "kauiyou_key", appKey)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "lehaihai" :
            file_u.update_content(file_path, "applicationId", "com.xy51.%s.lhh" % game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "youhao" :
            file_u.update_content(file_path, "youhao_appid", appId)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "youxifan" :
            file_u.update_content(file_pathk,"ygappid",appId)
            file_u.update_content(file_pathk,"sdkappid",appKey)
            file_u.update_content(file_pathk,"gameid",gameId)
            result=file_u.update_content(file_pathk,"applicationId", "com.xy51.%s.jh" % game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "leyou" :
            file_u.update_content(file_path,"ly_appid",appId)
            file_u.update_content(file_path,"ly_appkey",appKey)
            file_u.update_content(file_path,"ly_gameid",gameId)
            result = file_u.update_content(file_pathk, "applicationId", "com.xy51.%s" % game)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "niudao" :
            file_u.update_content(file_path,"appid",appId)
            file_u.update_content(file_path,"appkey",appKey)
            result=file_u.update_content(file_path,"clientid",appMd5Secret)
            file_u.printF('替换结果是+"%s"', result)
def change_assets_parameters(file_path,channel):

    channel_sdk = channel['sdk']
    for param in channel['params']:
        appId = param['appId']
        appKey = param['appKey']
        appMd5Secret = param['appMd5Secret']
        notifyUrl = param['notifyUrl']
        gameId = param['gameId']
        mchId = param['mchId']
        appNotifyDesc = param['appNotifyDesc']
        if channel_sdk == "landie" :
            result = file_u.update_content(file_path+"/BSSDKConfig.xml", "appid", appId )
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "tt" :
            file_u.update_content(file_path+"/tt_game_sdk_opt.properties","game_id",gameId)
            result=file_u.update_content(file_path+"/TTGameSDKConfig.cfg","key",appKey)
            file_u.printF('替换结果是+"%s"', result)

        if channel_sdk == "tianyuyou" :
            file_u.update_content(file_path + "/tygrm_ak.json", '{"appid":"tianyuyou"}', appId)
            result = file_u.update_content(file_path + "/tygrm_config_p.json", '{"appkey":"tianyuyou"}',appKey)
            file_u.printF('替换结果是+"%s"', result)

def change_icon(file_icon_path,channel):
    if os.path.exists(file_icon_path + "/icon_%s.png" % channel):
        return True
    else:
        return False

def del_xml_content(file,channel) :
    channel_sdk = channel['sdk']
    if channel_sdk == "tianyuyou" :
        old_content_action = '<action android:name="android.intent.action.MAIN"/>'
        old_content_category = '<category android:name="android.intent.category.LAUNCHER"/>'
        file_u.update_content(file,old_content_action,'')
        result=file_u.update_content(file,old_content_category,'')
        file_u.printF('替换结果是+"%s"', result)

def copy_private_sdk(filepath):
    if os.path.exists(filepath + "/pay_shiboyun.jar" ):
        return True
    else:
        return False

    return False