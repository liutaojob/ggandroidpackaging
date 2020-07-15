# encoding:utf-8
import subprocess
import os
import sys
import os.path
import shutil
from configobj import ConfigObj


def printF(logstr, logarg1):
    print(logstr % (logarg1))


def getCurrDir():
    #print("os.getcwd()"+os.getcwd())
    #print("sys.path[0]"+sys.path[0])
    #print("sys.argv[0]"+sys.argv[0])
    #print("os.path.realpath(__file__)" + os.path.realpath(__file__))
    local_conf = ConfigObj(sys.path[0] + '/local.properties')
    currDir = local_conf['current_dir']
    return currDir


def getFullPath(workDir):
    rootDir = getCurrDir()
    fullPath = os.path.join(rootDir, workDir)
    fullPath.replace("\\", "/")
    return fullPath


def del_file_folder(workDir):
    if not os.path.exists(workDir):
        return
    filelist = []
    filelist = os.listdir(workDir)
    for f in filelist:
        filepath = os.path.join(workDir, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
            print(filepath + " removed!")
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath, True)
            print("dir " + filepath + " removed!")


def getFullOutputPath(output_path):
    rootDir = getCurrDir()
    outPutPath = os.path.join(rootDir, "packages")
    if os.path.exists(output_path):
        return output_path
    else:
        return outPutPath




def getToolBasePath():
    currDir = getCurrDir()
    basePath = os.path.join(currDir, "bin")
    return basePath


def getFullToolPath(toolStr):
    basePath = getToolBasePath()
    toolPath = os.path.join(basePath, toolStr)
    return toolPath


def log(message, write_console=True):
    # file.write(message + '\r\n')
    if write_console:
        print(message)


def getJavaCMD():
    local_conf = ConfigObj(sys.path[0] + '/local.properties')
    javaDir = local_conf['java_dir']
    return javaDir


def exec_format_cmd(cmd):
    try:
        print("execFormatCmd : %s" % cmd)
        output = subprocess.check_output(cmd)
        # log(output.decode("utf-8"), False)
    except Exception as e:
        log(e.__str__())
        print(e.__str__())
        raise e


def copy_file(sourceDir, destDir):
    if not os.path.exists(sourceDir):
        print("The " + sourceDir + " is not exites")
        return
    shutil.copy(sourceDir, destDir)


def copy_files(sourceDir, destDir):
    if not os.path.exists(sourceDir):
        print("The " + sourceDir + " is not exites")
        return
    os.chmod(sourceDir, 0o777)
    print("copy_files sourceDir=%s, destDir=%s" %(sourceDir, destDir))
    shutil.copytree(sourceDir, destDir)


def getJavaBinDir():
    local_conf = ConfigObj(sys.path[0] + '/local.properties')
    java_bin_dir = local_conf['java_bin_dir']
    return java_bin_dir


def read_file(file_path):
    rf = open(file_path, 'r')
    text = rf.read()
    return text


def write_file(file_path, text):
    rf = open(file_path, 'w')
    rf.write(text)
    rf.close()


def log(message, write_console=True):
    # file.write(message + '\r\n')
    if write_console:
        print(message)
def read_file_write(file_path,old_file,new_file):
    # 读取文件内容
    with open(file_path, encoding="UTF-8") as file_obj:
        content = file_obj.read()
        print(content)
        f=open(file_path, "r+")
        for line in f.readlines():
            if line.find(old_file) >= 0:
                new_content=content.replace(line,new_file+'\n')
                print(new_content)
        f.close()
    # 内容文本内容
    # new_content = content.replace()

    # 将修改后的内容 写入文件
    with open(file_path, 'w', encoding="UTF-8") as file_object:
        file_object.write(new_content)