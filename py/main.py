# encoding: utf-8
import os
import os.path
import shutil
import zipfile
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, ElementTree
import os
import re
import time
import datetime
from configobj import ConfigObj
import apk_utils
import config_utils
import file_utils
from apk_utils import androidNS
import sys, getopt
import game_channel_package_config

# sys.path.append('C:/BatTools')
absPath = os.path.abspath(__file__)   #返回代码段所在的位置，肯定是在某个.py文件中
temPath = os.path.dirname(absPath)    #往上返回一级目录，得到文件所在的路径
temPath = os.path.dirname(temPath)    #在往上返回一级，得到文件夹所在的路径
sys.path.append(temPath)              # 就是为了把battools 这个目录加到 执行目录里面

from channelsdks import game_channel_config
from buildapk import new_main

generate_new_r_file_use_aapt2 = {'sd', 'hlxd'}
recompile_use_new_apktool = {'skzl','wysj','mbzj','jjdg'}


def main(argv):
    pack_all_channels(argv)


def delete_systemui_string(dec_dir, dir, channel, package_str, game):
    print('delete_systemui_string package_str = %s' % package_str)
    new_so_file = file_utils.getFullPath("sdks/%s/so/libunity.so" % game)
    if os.path.exists(new_so_file):
        print('delete_systemui_string copy new_so_file = %s' % new_so_file)
        old_so_file = os.path.join(dec_dir, "lib/armeabi-v7a/libunity.so")
        if os.path.exists(old_so_file):
            os.remove(old_so_file)
            print('delete_systemui_string copy old_so_file = %s' % old_so_file)
            shutil.copy(new_so_file, os.path.join(dec_dir, "lib/armeabi-v7a/"))

    modify_file_index = 0
    for fpathe, dirs, fs in os.walk(dir):

        for f in fs:
            smali_path = os.path.join(fpathe, f)
            smali_text = open(smali_path, encoding='UTF-8').read()
            # a = smali_file
            set_system_ui_key = 'android/view/View;->setSystemUiVisibility'
            set_system_ui_key_two = '\"setSystemUiVisibility\"'
            # r_res_text_key = 'com/stvgame/atm/R'
            system_index = smali_text.find(set_system_ui_key)
            system_index_two = smali_text.find(set_system_ui_key_two)
            if system_index_two > -1:
                replace_after = smali_text.replace(set_system_ui_key_two, "\"\"")
                with open(smali_path, 'w') as w:
                    w.write(replace_after)

            if system_index > -1:  # 删除 setSystemui的代码,解决下拉弹窗的问题.
                modify_file_index += 1
                print("modify_file = %s" % f)
                with open(smali_path, 'r') as r:
                    lines = r.readlines()
                with open(smali_path, 'w') as w:
                    for l in lines:
                        if set_system_ui_key not in l:
                            # print("modify_line = %s" % l)
                            w.write(l)

            new_r_pat = r'%s/R' % package_str.replace('.', "/")
            pat_pattern = ''

            if channel == 'wangsu' or channel == "yiqitvpay":
                pat_pattern = r'com/stvgame/sango2/R|com/stvgame/atm/R'

            if channel == "lerong":
                pat_pattern = r'com/letv/tvos/intermodal/R'

            if channel == "kangjia":
                pat_pattern = r'com/konka/kkuserpay/R'

            if channel == "tcl":
                pat_pattern = r'com/stvgame/pay/realize/R'

            if channel == "alitv":
                pat_pattern = r'com/yunos/tv/apppaysdk/R'

            if pat_pattern != '' and re.search(pat_pattern, smali_text):
                print("smali_path = %s" % smali_path)
                smali_text = re.sub(pat_pattern, new_r_pat, smali_text)
                with open(smali_path, 'w') as w:
                    w.write(smali_text)

    print("modify_file_index = %s" % modify_file_index)


def delete_sign_dir(game, dec_dir, smali_dir):
    print('delete_sign_dir dec_dir = %s,smali_dir = %s ' % (dec_dir, smali_dir))
    sign_dir = os.path.join(dec_dir, "original\META-INF")
    if os.path.exists(sign_dir):
        print('delete_sign_dir exist')
        shutil.rmtree(sign_dir)
        print('delete_sign_dir exist remove done')
    if game not in generate_new_r_file_use_aapt2:
        sign_dir_two = os.path.join(dec_dir, "unknown")
        if os.path.exists(sign_dir_two):
            print('sign_dir_two exist')
            shutil.rmtree(sign_dir_two)
            print('sign_dir_two exist remove done')


def printTime(tag):
    time_stamp = datetime.datetime.now()
    print(tag + time_stamp.strftime('_%Y.%m.%d-%H:%M:%S'))


def pack_all_channels(args):
    origin_args = args
    channel_args = ""
    try:
        # 这里的 h 就表示该选项无参数，i:表示 i 选项后需要有参数
        opts, args = getopt.getopt(args, "g:p:c:o:r", ["game=", "package=", "channels=", "output=", "reinstall="])
    except getopt.GetoptError:
        print('Error: test_arg.py -i <channel_args>')
        sys.exit(2)

    game_name = ""
    output_path = ""
    package_opt = ""
    reinstall = False
    for opt, arg in opts:
        if opt in ("-g", "--game"):
            # game_name = game_channel_package_config.game.get(arg)
            game_name=arg
        elif opt in ("-p", "--package"):
            package_opt = arg
            if package_opt == "":
                package_opt = 'def'
        elif opt in ("-c", "--channels"):
            channel_args = arg
        elif opt in ("-o", "--output"):
            output_path = arg
        elif opt in ("-r", "--reinstall"):
            reinstall = True

    if package_opt == "def" or package_opt == "":
        package_opt = game_name
    else:
        package_opt = "%s_%s" % (game_name, package_opt)

    print('channel_args : ', channel_args + ", package_opt :", package_opt)
    if game_name == "" or channel_args == "-o":
        print('parameter invalide! build quit!')
        return;

    if game_name not in game_channel_config.games:
        new_main.main(origin_args)
    else:
        channels = config_utils.get_all_channels(channel_args, game_name)
        print('channels : ', channels)
        if channels is not None and len(channels) > 0:
            clen = len(channels)
            print("Total " + str(clen) + " channels to package,  package_opt = %s" % package_opt)
            package_apk = file_utils.getFullPath("sdks/%s/%s.apk" % (game_name, package_opt))
            print("package_apk = %s " % package_apk)
            if not os.path.exists(package_apk):
                print("The origin apk file name must be 'sdks/%s/%s.apk'" % (game_name, package_opt))
                return
            suc_num = 0
            fal_num = 0
            for channel_args in channels:
                ret = do_pack(game_name, channel_args, package_apk, output_path, package_opt, reinstall)
                if ret:
                    fal_num = fal_num + 1
                else:
                    suc_num = suc_num + 1
            print("*********************** all complete ***********************")
            print("************ suc num: " + str(suc_num) + "  ;failed num：" + str(fal_num) + "**********")


def change_icon_if_need(game, channel_name, dec_dir, father_node):
    print("change_icon_if_need")

    channel_icon_file = file_utils.getFullPath("sdks/%s/sdk/%s/icon_%s.png" % (game, channel_name, channel_name))
    if os.path.exists(channel_icon_file):
        shutil.copy(channel_icon_file, os.path.join(dec_dir, "res/drawable"))
        del father_node.attrib['{http://schemas.android.com/apk/res/android}icon']
        father_node.attrib["android:icon"] = "@drawable/icon_%s" % channel_name
        print("change_icon_if_need after success icon = %s" % father_node.attrib["android:icon"])
    else:
        game_icon_file = file_utils.getFullPath("sdks/%s/icon_%s.png" % (game, game))
        if os.path.exists(game_icon_file):
            shutil.copy(game_icon_file, os.path.join(dec_dir, "res/drawable"))
            del father_node.attrib['{http://schemas.android.com/apk/res/android}icon']
            father_node.attrib["android:icon"] = "@drawable/icon_%s" % game
            print("change_icon_if_need after success icon = %s" % father_node.attrib["android:icon"])


def change_logo_if_need(game, channel_name, dec_dir, father_node):
    print("change_logo_if_need")

    channel_icon_file = file_utils.getFullPath("sdks/%s/sdk/%s/logo_%s.png" % (game, channel_name, channel_name))
    if os.path.exists(channel_icon_file):
        print("change_logo_if_need exist")
        seach_dir = "%s/res" % dec_dir;
        for root, dirs, files in os.walk(seach_dir):  # path 为根目录
            print("change_logo_if_need for files = %s" % files)
            if "xiaoy_bg.jpg" in files:
                root = str(root)
                p = os.path.join(root, "xiaoy_bg.jpg")
                os.remove(p)
                shutil.copy(channel_icon_file, p)
                print("change_logo_if_need seached dir = %s" % dirs)
                print("change_logo_if_need seached p = %s" % p)
            if "xiaoy_bg.png" in files:
                root = str(root)
                dirs = str(dirs)
                p = os.path.join(root, "xiaoy_bg.png")
                os.remove(p)
                shutil.copy(channel_icon_file, p)
                print("change_logo_if_need seached dir = %s" % dirs)
                print("change_logo_if_need seached p = %s" % p)


def check_muti_dex(src_dir, dst_dir):
    print("check_muti_dex src_dir = %s, dst_dir = %s" % (src_dir,dst_dir))
    if not os.path.exists(src_dir):
        return None
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    return apk_utils.jar2smali(src_dir, dst_dir)


def do_pack(game, channel, source_apk, output_path, package_opt, reinstall):
    print("*********************** start do_pack *********************** channel:" % channel)
    source_apk = source_apk.replace('\\', "/")
    if not os.path.exists(source_apk):
        return None

    channel_sdk = channel["sdk"]
    channel_name = channel["name"]
    work_dir = 'xywork/%s/%s' % (game, channel_sdk)
    work_dir = file_utils.getFullPath(work_dir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    file_utils.del_file_folder(work_dir)
    source_temp_apk = work_dir + "/temp.apk"
    file_utils.copy_file(source_apk, source_temp_apk)
    dec_dir = work_dir + "/decompile"
    ret = apk_utils.decompile_apk(game, source_temp_apk, dec_dir)

    if channel_sdk.startswith('kangjia') and game == "cqzhs":
        okhttp3_dir = os.path.join(dec_dir, "smali/okhttp3")
        if os.path.exists(okhttp3_dir):
            print('isexists = %s' % okhttp3_dir)
            shutil.rmtree(okhttp3_dir)

        okio_dir = os.path.join(dec_dir, "smali/okio")
        if os.path.exists(okio_dir):
            print('isexists = %s' % okio_dir)
            shutil.rmtree(okio_dir)

    if ret:
        return None

    # shutil.rmtree(os.path.join(decDir, "res/values-v14"))
    # shutil.rmtree(os.path.join(decDir, "res/values-v21"))
    sdk_source_dir = file_utils.getFullPath('sdks/%s/sdk/%s' % (game, channel_sdk))
    sdk_source_dir = sdk_source_dir.replace('\\', "/")
    smali_dir = dec_dir + "/smali"
    sdk_dest_dir = work_dir + "/sdk/" + channel_sdk

    file_utils.copy_files(sdk_source_dir, sdk_dest_dir)

    # instead the lastest plugin
    ori_plugin_dir = os.path.join(dec_dir, "assets/plugin.dat")
    if os.path.isfile(ori_plugin_dir):
        os.remove(ori_plugin_dir)
        print(ori_plugin_dir + " removed!")
    plugin_dir = file_utils.getFullPath("sdks/%s/plugin.dat" % game)
    os.chmod(plugin_dir, 0o777)
    shutil.copy(plugin_dir, os.path.join(dec_dir, "assets"))

    # instead new channel file
    channel_file = os.path.join(dec_dir, "assets/xyconfig.properties")
    if os.path.exists(channel_file):
        file_utils.read_file_write(channel_file,"channel","channel=%s" % channel_name)
    #     os.remove(channel_file)
    # f = open(channel_file, 'w')
    # f.write("channel=%s" % channel_name)
    # f.close()


    # sdk中 支付jar以及依赖jar编译成 dex
    if not channel_sdk.startswith('stvgame'):
        print("开始遍历")
        apk_utils.jar2dex((sdk_source_dir), sdk_dest_dir)

        # apk_utils.jar2dex(os.path.join(sdk_source_dir, "libs"), sdk_dest_dir)
        print("遍历lib里jar,编入apk")

        sdk_dex_file = sdk_dest_dir + "/classes.dex"
        ret = apk_utils.dex2smali(sdk_dex_file, smali_dir, "baksmali.jar")
        if ret:
            print("lib里jar未被合并")
            return None
        apk_utils.copy_libs(os.path.join(sdk_dest_dir, "libs"), os.path.join(dec_dir, "lib"))
        print("lib里jar已合并")

    # change packagename xml config and so on
    manifest_file = dec_dir + "/AndroidManifest.xml"
    manifest_file = file_utils.getFullPath(manifest_file)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    package_name = root.attrib.get('package')

    # 解决低版本apktool重编后出现新的两个元素导致无法编译的问题
    if root.attrib.get('{' + androidNS + '}' + 'compileSdkVersion') is not None:
        del root.attrib['{' + androidNS + '}' + 'compileSdkVersion']
        del root.attrib['{' + androidNS + '}' + 'compileSdkVersionCodename']

    # add versioncode and versionname [针对胡莱三国androidstudio打出的包无效]
    proj_conf = ConfigObj(file_utils.getFullPath("sdks/%s/project.properties" % game))
    proj_ver_code = proj_conf['proj_ver_code']
    proj_ver_name = proj_conf['proj_ver_name']
    root.set('android:versionCode', proj_ver_code)
    root.set('android:versionName', proj_ver_name)

    # add umeng 参数 to Manifest
    # proj_conf = ConfigObj('C:/BatTools/py/project.properties')
    # UMENG_APPKEY = proj_conf['UMENG_APPKEY']
    father_node = root.find('application')
    #
    # for child in fatherNode.findall('meta-data'):
    #     if child.attrib['{http://schemas.android.com/apk/res/android}name'] == "UMENG_APPKEY" or
    #  child.attrib['{http://schemas.android.com/apk/res/android}name'] == "UMENG_CHANNEL":
    #         fatherNode.remove(child)
    #
    # umengNode = SubElement(fatherNode, 'meta-data')
    # umengNode.set('android:name','UMENG_APPKEY')
    # umengNode.set('android:value',UMENG_APPKEY)
    # umengNode = SubElement(fatherNode, 'metzipaligna-data').

    # umengNode.set('android:name', 'UMENG_CHANNEL')

    change_icon_if_need(game, channel_name, dec_dir, father_node)
    change_logo_if_need(game, channel_name, dec_dir, father_node)
    check_muti_dex(os.path.join(sdk_source_dir, "todex"), os.path.join(dec_dir, "smali_classes2"))
    tree.write(manifest_file, 'UTF-8')

    if channel_sdk.startswith('stvgame'):
        print('is stvgame channel = %s' % channel_name)
    else:
        # unitv 调整初始化时机
        if channel_sdk.startswith('unitv'):
            if game == "atm":
                ori_code_dir = os.path.join(dec_dir, "smali/com/cocos2dx/lua/AppActivity.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/AppActivity.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/cocos2dx/lua"))
            elif game == "xjjby":
                ori_code_dir = os.path.join(dec_dir, "smali/com/openapi/template/activity/MainActivity.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/MainActivity.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/openapi/template/activity"))
            elif game == "hlsg2":
                ori_code_dir = os.path.join(dec_dir, "smali/com/hoolai/sango2/GameMainActivity.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/GameMainActivity.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/hoolai/sango2"))
            elif game == "zcry":
                ori_code_dir = os.path.join(dec_dir, "smali/com/aoshitang/sdk/XiaoySdk$1.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/XiaoySdk$1.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/aoshitang/sdk"))
            elif game == "zsjl":
                ori_code_dir = os.path.join(dec_dir, "smali/fly/fish/asdk/SkipActivity.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/SkipActivity.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/fly/fish/asdk"))
            elif game == "hlw":
                ori_code_dir = os.path.join(dec_dir, "smali/com/reign/sdk/Syhd.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/Syhd.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/reign/sdk"))
            elif game == "cqzhs":
                ori_code_dir = os.path.join(dec_dir, "smali/com/feelingtouch/idl/xiaoy/XiaoYInterface.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath("sdks/%s/sdk/%s/smali/XiaoYInterface.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/com/feelingtouch/idl/xiaoy"))
            elif game == "dldl3":
                ori_code_dir = os.path.join(dec_dir,
                                            "smali/ourpalm/android/channels/stvgame/Ourpalm_StvGame_Charging$2.smali")
                if os.path.isfile(ori_code_dir):
                    os.remove(ori_code_dir)
                code_dir = file_utils.getFullPath(
                    "sdks/%s/sdk/%s/smali/Ourpalm_StvGame_Charging$2.smali" % (game, channel_sdk))
                os.chmod(code_dir, 0o777)
                shutil.copy(code_dir, os.path.join(dec_dir, "smali/ourpalm/android/channels/stvgame"))

        if channel_sdk.startswith('kukai'):
            for child in root.iter('uses-permission'):
                if child.get('{http://schemas.android.com/apk/res/android}name') \
                        == "android.permission.RECEIVE_BOOT_COMPLETED":
                    root.remove(child)
                    tree.write(manifest_file, 'UTF-8')
                if child.get('{http://schemas.android.com/apk/res/android}name') \
                        == "android.permission.SYSTEM_ALERT_WINDOW":
                    root.remove(child)
                    tree.write(manifest_file, 'UTF-8')

        if channel_sdk.startswith('tcl'):
            shutil.copytree(file_utils.getFullPath("sdks/%s/sdk/%s/aidl/" % (game, channel_sdk)),
                            os.path.join(dec_dir, "smali/com/tcl/usercenter/aidl/"))

    suffix = ''
    if channel['suffix'] is not None and len(channel['suffix']) > 0:
        package_name = apk_utils.rename_package_name(dec_dir, package_name, channel['suffix'])
        suffix = channel['suffix'].replace('.', "")
        print("********** suffix ：" + suffix)
    ret = apk_utils.copy_resource(sdk_dest_dir, dec_dir, channel)
    if ret:
        return None

    printTime("modify smali start")
    delete_systemui_string(dec_dir, smali_dir, channel_sdk, package_name, game)
    printTime("modify smali end")
    delete_sign_dir(game, dec_dir, smali_dir)
    # return None
    #
    apk_utils.write_develop_info(channel, dec_dir)
    apk_utils.write_support_info(channel, dec_dir)

    ret = apk_utils.generate_new_r_file(game, package_name, dec_dir)
    if ret:
        return None

    target_apk = work_dir + "/target.apk"
    ret = apk_utils.recompile_apk(game, dec_dir, target_apk)
    if ret:
        return None

    ret = apk_utils.sign_apk(target_apk, channel_sdk)
    if ret:
        return None

    dest_apk_name = channel_name + '.apk'

    dest_apk_path = file_utils.getFullOutputPath(output_path)
    dest_apk_path = os.path.join(dest_apk_path, dest_apk_name)
    ret = apk_utils.align_apk(target_apk, dest_apk_path)

    if ret:
        return None


    target_apk_dir = file_utils.getFullOutputPath(output_path)
    build_time = time.strftime('%m%d%H%M', time.localtime(time.time()))
    # 拼接对应渠道号的apk
    target_apk = "%s_%s_v%s_%s.apk" % (package_opt, channel_name, proj_ver_code, build_time)
    if len(suffix) > 0:
        target_apk = "%s_%s_%s_%s_v%s.apk" % (package_opt, channel_name, suffix, proj_ver_code, build_time)
    target_apk_path = os.path.join(target_apk_dir, target_apk)
    # 拷贝建立新apk
    shutil.copy(dest_apk_path, target_apk_path)

    # channelname 编写(为了和使用xiaoy批量打包工具打出的包获取channelname的方法保持一致)
    src_empty_file = 'src.txt'
    src_empty_file = os.path.join(target_apk_dir, src_empty_file)
    # 创建一个空文件(如果不存在，则创建)
    f = open(src_empty_file, 'w')
    f.close()
    # zip获取新建立的apk文件,'a'表示打开一个zipfile，并添加内容
    zipped = zipfile.ZipFile(target_apk_path, 'a', zipfile.ZIP_DEFLATED)
    # 初始化渠道信息
    empty_channel_file = "META-INF/xy_{channel}".format(channel=channel_name)
    # 写入渠道信息MergeManifest
    zipped.write(src_empty_file, empty_channel_file)
    # 关闭zip流
    zipped.close()

    print('final apk path : ', target_apk_path)
    if reinstall:
        apk_utils.reinstall_apk(package_name, target_apk_path)

    os.remove(src_empty_file)
    os.remove(dest_apk_path)

    return 0
