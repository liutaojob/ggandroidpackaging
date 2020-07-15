#!/usr/bin/env Python
# coding=utf-8
import os
import os.path
import zipfile
import file_utils as file_operate
import config_utils
import shutil
import main
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import SubElement

androidNS = 'http://schemas.android.com/apk/res/android'


def dex2smali(dex_file, target_dir, dextool="baksmali.jar"):
    if not os.path.exists(dex_file):
        file_operate.printF("dex2smali : the dexFile is not exit. path:%s", dex_file)
        return
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    dex_file = file_operate.getFullPath(dex_file)
    smali_tool = file_operate.getFullToolPath(dextool)
    target_dir = file_operate.getFullPath(target_dir)

    cmd = '"%s" -jar "%s" -o "%s" "%s"' % (file_operate.getJavaCMD(), smali_tool, target_dir, dex_file)

    ret = file_operate.exec_format_cmd(cmd)

    return ret


def decompile_apk(game, source, target_dir, apktool="apktool.jar"):
    apkfile = file_operate.getFullPath(source)
    target_dir = file_operate.getFullPath(target_dir)

    apktool = file_operate.getFullToolPath(apktool)
    if os.path.exists(target_dir):
        file_operate.del_file_folder(target_dir)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    cmd = '"%s" -jar "%s" d -f "%s" -o "%s"' % (file_operate.getJavaCMD(), apktool, apkfile, target_dir)

    ret = file_operate.exec_format_cmd(cmd)
    return ret


def rename_package_name(decompile_dir, old_package_name, new_package_name):
    print('rename_package_name decompile_dir : %s, new_package_name : %s' % (decompile_dir, new_package_name))

    package = old_package_name

    old_package_name = package

    if new_package_name[0:1] == '.':
        new_package_name = old_package_name + new_package_name

    # now to check activity or service
    manifest_file = decompile_dir + "/AndroidManifest.xml"
    manifest_file = file_operate.getFullPath(manifest_file)
    ET.register_namespace('android', androidNS)
    tree = ET.parse(manifest_file)
    root = tree.getroot()
    app_node = root.find('application')
    if app_node is not None:
        activity_list = app_node.findall('activity')
        key = '{' + androidNS + '}name'
        if activity_list is not None and len(activity_list) > 0:
            for aNode in activity_list:
                activity_name = aNode.attrib[key]
                if activity_list[0:1] == '.':
                    activity_name = old_package_name + activity_name
                elif activity_name.find('.') == -1:
                    activity_name = old_package_name + "." + activity_name
                aNode.attrib[key] = activity_name

        service_lst = app_node.findall('service')
        key = '{' + androidNS + '}name'
        if service_lst is not None and len(service_lst) > 0:
            for sNode in service_lst:
                service_name = sNode.attrib[key]
                if service_name[0:1] == '.':
                    service_name = old_package_name + service_name
                elif service_name.find('.') == -1:
                    service_name = old_package_name + '.' + service_name
                sNode.attrib[key] = service_name

        # 专门替换小y FileProvider的 authorities
        provider_lst = app_node.findall('provider')
        key = '{' + androidNS + '}authorities'
        if provider_lst is not None and len(provider_lst) > 0:
            for sNode in provider_lst:
                print('rename_package_name sNode : %s , androidNS = %s , sNode.attrib[key] = %s' % (
                sNode, androidNS, sNode.attrib[key]))
                provider_authorities = sNode.attrib[key]
                if provider_authorities.find(old_package_name) == 0:
                    provider_authorities = provider_authorities.replace(old_package_name, new_package_name)
                sNode.attrib[key] = provider_authorities

    root.attrib['package'] = new_package_name
    tree.write(manifest_file, 'UTF-8')
    print('rename_package_name manifest_file : %s, new_package_name : %s' % (manifest_file, new_package_name))
    package = new_package_name
    return package


def copy_resource(sdk_dir, decompile_dir, channel):
    if 'ops' not in channel.keys():
        print("  没有资源需要复制或者合并 ")
        return 0
    if channel['ops'] is not None and len(channel['ops']) > 0:
        for child in channel['ops']:
            if child['type'] == 'merge':
                manifest_from = file_operate.getFullPath(os.path.join(sdk_dir, child['from']))
                manifest_to = file_operate.getFullPath(os.path.join(decompile_dir, child['to']))
                # print(" manifestFrom is :" + manifest_from + " manifestTo is :" + manifest_to)
                # merge into xml
                manifest_to = manifest_to.replace("\\", '/')
                manifest_from = manifest_from.replace("\\", "/")
                b_ret = merge_manifest(manifest_to, manifest_from)
                if b_ret:
                    print("*********** MergeManifest successfully *************")
                else:
                    print("***************** MergeManifest failed **************")

            elif child['type'] == 'copy':
                if child['from'] is None or child['to'] is None:
                    file_operate.printF("The config file is error. copyRes,need from and to attrib.sdk:%s",
                                        channel['name'])
                    return 1

                if child['to'] == 'lib':
                    # copy libs ->lib use copyLibs method. here not copy libs.
                    continue

                copy_from = file_operate.getFullPath(os.path.join(sdk_dir, child['from']))
                copy_to = file_operate.getFullPath(os.path.join(decompile_dir, child['to']))
                copy_res_to_apk(copy_from, copy_to)

    return 0


def merge_manifest(target_manifest, sdk_manifest):
    if not os.path.exists(target_manifest) or not os.path.exists(sdk_manifest):
        print("The manifest file is not exists:" + sdk_manifest)
        return False

    ET.register_namespace('android', androidNS)
    target_tree = ET.parse(target_manifest)
    target_root = target_tree.getroot()

    ET.register_namespace('android', androidNS)
    sdk_tree = ET.parse(sdk_manifest)
    sdk_root = sdk_tree.getroot()

    f = open(target_manifest,'r',encoding='utf-8')
    target_content = f.read()
    f.close()

    b_ret = False
    app_config_node = sdk_root.find('applicationConfig')
    app_node = target_root.find('application')
    if app_config_node is not None:

        proxy_application_name = app_config_node.get('proxyApplication')
        if proxy_application_name is not None and len(proxy_application_name) > 0:
            meta_node = SubElement(app_node, 'meta-data')
            key = '{' + androidNS + '}name'
            val = '{' + androidNS + '}value'
            meta_node.set(key, "XY_APPLICATION_PROXY_NAME")
            meta_node.set(val, proxy_application_name)

        app_key_word = app_config_node.get('keyword')

        if app_key_word is not None and len(app_key_word) > 0:
            key_index = target_content.find(app_key_word)
            if -1 == key_index:
                b_ret = True
                for child in list(app_config_node):
                    target_root.find('application').append(child)

    permission_config_node = sdk_root.find('permissionConfig')
    if permission_config_node is not None and len(permission_config_node) > 0:
        for child in list(permission_config_node):
            key = '{' + androidNS + '}name'
            val = child.get(key)
            if val is not None and len(val) > 0:
                attr_index = target_content.find(val)
                if -1 == attr_index:
                    b_ret = True
                    target_root.append(child)

    target_tree.write(target_manifest, 'UTF-8')

    return b_ret


def copy_res_to_apk(copy_from, copy_to):
    # print("copyResToApk copyFrom:%s , copyTo:%s" % (copy_from, copy_to))
    if not os.path.exists(copy_from):
        file_operate.printF('The copyFrom "%s" is not exit', copy_from)
        return

    if not os.path.exists(copy_to):
        os.makedirs(copy_to)

    if os.path.isfile(copy_from) and not merge_res_xml(copy_from, copy_to):
        file_operate.copyFile(copy_from, copy_to)
        return

    for f in os.listdir(copy_from):
        source_file = os.path.join(copy_from, f)
        target_file = os.path.join(copy_to, f)

        if os.path.isfile(source_file):
            if not os.path.exists(copy_to):
                os.makedirs(copy_to)

            if merge_res_xml(source_file, target_file):
                continue
            if not os.path.exists(target_file) or os.path.getsize(target_file) != os.path.getsize(source_file):
                destfilestream = open(target_file, 'wb')
                sourcefilestream = open(source_file, 'rb')
                destfilestream.write(sourcefilestream.read())
                destfilestream.close()
                sourcefilestream.close()

        if os.path.isdir(source_file):
            copy_res_to_apk(source_file, target_file)


def merge_res_xml(copy_from, copy_to):
    # print("merge_res_xml copyFrom:%s , copyTo:%s" % (copy_from, copy_to))
    if not os.path.exists(copy_to):
        return False

    ary_xml = ['strings.xml', 'styles.xml', 'colors.xml', 'dimens.xml', 'id.xml', 'attrs.xml', 'integers.xml',
               'arrays.xml', 'bools.xml', 'ids.xml', 'drawables.xml']
    basename = os.path.basename(copy_from)

    f = open(copy_to, 'rb')
    target_content = f.read().decode('UTF-8')
    f.close()

    if basename in ary_xml:
        from_tree = ET.parse(copy_from)
        from_root = from_tree.getroot()
        to_tree = ET.parse(copy_to)
        to_root = to_tree.getroot()
        for node in list(from_root):
            val = node.get('name')
            if val is not None and len(val) > 0:
                val_match = '"' + val + '"'
                attr_index = target_content.find(val_match)
                if -1 == attr_index:
                    to_root.append(node)
                else:
                    print("The attrib is exists already. the " + val)
        to_tree.write(copy_to, 'UTF-8')
        return True
    return False


def write_develop_info(channel, decompile_dir):
    print("write_develop_info  channel : %s" % channel)
    develop_config_file = os.path.join(decompile_dir, "assets")
    if not os.path.exists(develop_config_file):
        os.makedirs(develop_config_file)

    develop_config_file = os.path.join(develop_config_file, "developer_config.properties")
    config_utils.write_developer_properties(channel, develop_config_file)


def write_support_info(channel, decompile_dir):
    develop_config_file = os.path.join(decompile_dir, "assets")
    if not os.path.exists(develop_config_file):
        os.makedirs(develop_config_file)

    develop_config_file = os.path.join(develop_config_file, "plugin_config.xml")
    config_utils.write_plugin_configs(channel, develop_config_file)


def generate_new_r_file(game, new_package_name, decompile_dir):
    """
        Use all new resources to generate the new R.java ,and compile it,then copy it to the target smali dir
    """

    decompile_dir = file_operate.getFullPath(decompile_dir)
    temp_path = os.path.dirname(decompile_dir)
    temp_path = temp_path + "/temp"
    file_operate.printF("The temp path is %s", temp_path)
    if os.path.exists(temp_path):
        file_operate.del_file_folder(temp_path)
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    res_path = os.path.join(decompile_dir, "res")
    target_res_path = os.path.join(temp_path, "res")
    file_operate.copy_files(res_path, target_res_path)

    gen_path = os.path.join(temp_path, "gen")
    if not os.path.exists(gen_path):
        os.makedirs(gen_path)

    # aapt2_compile_dir = os.path.join(temp_path, "compile")
    # if not os.path.exists(aapt2_compile_dir):
    #    os.makedirs(aapt2_compile_dir)

    android_path = file_operate.getFullToolPath("android.jar")
    manifest_path = os.path.join(decompile_dir, "AndroidManifest.xml")

    if game in main.generate_new_r_file_use_aapt2:
        aapt_path = file_operate.getFullToolPath("aapt2")
        file_operate.printF("The generate R aapt file path is %s", aapt_path)
        aapt2_flats_folder = os.path.join(decompile_dir, "flats")
        if not os.path.exists(aapt2_flats_folder):
            os.makedirs(aapt2_flats_folder)

        aapt2_flats = os.path.join(decompile_dir, "aapt2_flats.zip")
        cmd = '"%s" compile --dir "%s" -o "%s"' % (aapt_path, target_res_path, aapt2_flats)
        ret = file_operate.exec_format_cmd(cmd)
        if ret:
            return 1
        extracting = zipfile.ZipFile(aapt2_flats)
        extracting.extractall(aapt2_flats_folder)
        aapt2_link_gen = os.path.join(decompile_dir, "aapt2_link_gen.zip")
        reses = ''
        for root, dirs, files in os.walk(aapt2_flats_folder):
            for file in files:
                reses += " -R " + os.path.join(root, file)

        cmd = '"%s" link --auto-add-overlay %s --manifest "%s" -I "%s" --java "%s" -o "%s"' % (
            aapt_path, reses, manifest_path, android_path, gen_path, aapt2_link_gen)
        ret = file_operate.exec_format_cmd(cmd)
        if ret:
            return 1
    else:
        aapt_path = file_operate.getFullToolPath("aapt")
        file_operate.printF("The generate R aapt file path is %s", aapt_path)
        cmd = '"%s" p -f -m -J "%s" -S "%s" -I %s -M "%s"' % (
            aapt_path, gen_path, target_res_path, android_path, manifest_path)
        ret = file_operate.exec_format_cmd(cmd)
        if ret:
            return 1

    r_path = new_package_name.replace('.', '/')
    r_path = os.path.join(gen_path, r_path)
    r_path = os.path.join(r_path, "R.java")

    print("file_operate.getJavaBinDir(): " + file_operate.getJavaBinDir())
    cmd = '"%sjavac" -source 1.7 -target 1.7 -encoding UTF-8 "%s"' % (file_operate.getJavaBinDir(), r_path)
    ret = file_operate.exec_format_cmd(cmd)
    if ret:
        return 1

    target_dex_path = os.path.join(temp_path, "classes.dex")
    dex_tool_path = file_operate.getFullToolPath("dx.bat")

    print("generate_new_r_file  target_dex_path : %s" % target_dex_path)
    cmd = '"%s" --dex --output="%s" "%s"' % (dex_tool_path, target_dex_path, gen_path)
    ret = file_operate.exec_format_cmd(cmd)
    if ret:
        return 1

    smali_path = os.path.join(decompile_dir, "smali")
    ret = dex2smali(target_dex_path, smali_path, "baksmali.jar")

    return ret


# def recompile_apk(game, source_folder, apk_file, apk_tool="apktool.jar"):
def recompile_apk(game, source_folder, apk_file, apk_tool="apktool_2.1.2.jar"):
    print(" recompile_apk game :" + game)
    # os.chdir(file_operate.getCurrDir())
    if game in main.generate_new_r_file_use_aapt2 or game in main.recompile_use_new_apktool:
        apk_tool = "apktool.jar"
    source_folder = file_operate.getFullPath(source_folder)
    apk_file = file_operate.getFullPath(apk_file)
    apk_tool = file_operate.getFullToolPath(apk_tool)

    ret = 1
    if os.path.exists(source_folder):
        cmd = '"%s" -jar "%s" -q b -f "%s" -o "%s"' % (file_operate.getJavaCMD(), apk_tool, source_folder, apk_file)
        ret = file_operate.exec_format_cmd(cmd)
    return ret


def sign_apk(apk_file, channel):
    keystore = config_utils.get_keystore(channel)
    # print("The keystore file is :"+keystore['keystore'])
    sign_apk_final(apk_file, keystore['keystore'], keystore['password'], keystore['aliaskey'], keystore['aliaspwd'])


def sign_apk_final(apk_file, keystore, password, alias, alias_pwd):
    print(" signApkFinal path :" + keystore)
    if not os.path.exists(keystore):
        print(" signApkFinal path error")
        return 1
    apk_file = file_operate.getFullPath(apk_file)
    keystore = file_operate.getFullPath(keystore)
    aapt = file_operate.getFullToolPath("aapt.exe")

    listcmd = '"%s" list "%s"' % (aapt, apk_file)
    listcmd = listcmd.encode('gb2312').decode()
    output = os.popen(listcmd).read()
    for filename in output.split('\n'):
        if filename.find('META_INF') == 0:
            rmcmd = '"%s" remove "%s" "%s"' % (aapt, apk_file, filename)
            file_operate.exec_format_cmd(rmcmd)

    os.chmod(apk_file, 0o777)
    sign_cmd = '"%sjarsigner.exe" -keystore "%s" -storepass "%s" -keypass ' \
               '"%s" "%s" "%s" -sigalg SHA1withRSA -digestalg SHA1' % (
                   file_operate.getJavaBinDir(), keystore, password, alias_pwd, apk_file, alias)
    print(" sign_cmd :" + sign_cmd)
    ret = file_operate.exec_format_cmd(sign_cmd)
    # print(" sign_cmd ret :" + ret)
    return ret


def align_apk(apk_file, target_apk_file):
    align = file_operate.getFullToolPath('zipalign')
    align_cmd = '"%s" -f 4 "%s" "%s"' % (align, apk_file, target_apk_file)
    ret = file_operate.exec_format_cmd(align_cmd)
    # print(" alignApk ret :" % ret)
    return ret


def reinstall_apk(pkg_name, target_apk_path):
    uninstall_cmd = '"adb" uninstall "%s" ' % pkg_name
    ret1 = file_operate.exec_format_cmd(uninstall_cmd)

    install_cmd = '"adb" install "%s" ' % target_apk_path
    ret2 = file_operate.exec_format_cmd(install_cmd)
    if ret2 == 0:
        print(" reinstall_apk success")
    return ret1 & ret2


def jar2smali(src_dir, dst_dir, dextool="baksmali.jar"):
    print("jar2smali src_dir:%s, dst_dir:%s" % (src_dir, dst_dir))
    dex_dir = os.path.join(src_dir, "dex")
    if os.path.exists(dex_dir):
        file_operate.del_file_folder(dex_dir)
    if not os.path.exists(dex_dir):
        os.makedirs(dex_dir)
        os.chmod(dex_dir, 0o777)
    jar2dex(src_dir, dex_dir)
    ret = dex2smali(os.path.join(dex_dir, 'classes.dex'), dst_dir)
    return ret


def jar2dex(src_dir, dst_dir, dextool="baksmali.jar"):
    print("jar2dex dst_dir:%s" % dst_dir)
    """
        compile jar files to dex.
    """

    dex_tool_path = file_operate.getFullToolPath("dx.bat")

    cmd = '"%s" --dex --output="%s" ' % (dex_tool_path, dst_dir + "/classes.dex")

    for f in os.listdir(src_dir):
        if f.endswith(".jar"):
            cmd = cmd + " " + os.path.join(src_dir, f)

    if os.path.exists(src_dir + "\libs"):
        for f in os.listdir(os.path.join(src_dir, "libs")):
            if f.endswith(".jar"):
                cmd = cmd + " " + os.path.join(src_dir, "libs", f)
    else:
        print("not exists :" + src_dir + "\libs")

    file_operate.exec_format_cmd(cmd)


def copy_libs(src_dir, dst_dir):
    print("copy_libs src_dir:%s, dst_dir:%s" % (src_dir, dst_dir))
    """
        copy shared libraries
    """

    if not os.path.exists(src_dir):
        return

    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    for f in os.listdir(src_dir):
        source_file = os.path.join(src_dir, f)
        target_file = os.path.join(dst_dir, f)

        if source_file.endswith(".jar"):
            continue

        if os.path.isfile(source_file):
            if not os.path.exists(target_file) or os.path.getsize(target_file) != os.path.getsize(source_file):
                destfilestream = open(target_file, 'wb')
                sourcefilestream = open(source_file, 'rb')
                destfilestream.write(sourcefilestream.read())
                destfilestream.close()
                sourcefilestream.close()

        if os.path.isdir(source_file):
            copy_libs(source_file, target_file)

    """
        compile jar files to dex.
    """

    dex_tool_path = file_operate.getFullToolPath("dx.bat")

    cmd = '"%s" --dex --output="%s" ' % (dex_tool_path, dst_dir + "/classes.dex")

    for f in os.listdir(src_dir):
        if f.endswith(".jar"):
            cmd = cmd + " " + os.path.join(src_dir, f)
    if os.path.exists(src_dir + "\libs"):
        for f in os.listdir(os.path.join(src_dir, "libs")):
            if f.endswith(".jar"):
                cmd = cmd + " " + os.path.join(src_dir, "libs", f)
    else:
        print("not exists :" + src_dir + "\libs")
        return

    file_operate.exec_format_cmd(cmd)


def reflush_version(src_dir, dst_dir):
    print("srcDir:" + src_dir + "  dstDir:" + dst_dir)
    shutil.copy(src_dir, dst_dir)
