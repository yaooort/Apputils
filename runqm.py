#!/usr/bin/python
# coding=utf-8
import base64
from tkinter.font import Font

from biplist import *
import os
import shutil
import zipfile
from tkinter import filedialog, messagebox
import tkinter

from icon import img


def startZipAndroid():
    if not entry.get():
        messagebox.showerror(title="错误", message="请选择app包文件")
        return

    if not default_value.get():
        messagebox.showerror(title="错误", message="请输入代理Id")
        return
    apk_path = entry.get()
    channel_list = default_value.get()
    # 读取配置文件
    # config = ConfigParser.ConfigParser()
    # config.read("channels-config.ini")
    # apk路径
    # apk_path = config.get("Build-Config", "apk.path")
    print("src apk path=" + apk_path)
    # 渠道识别前缀
    # channel_prefix = config.get("Build-Config", "channel.prefix")
    channel_prefix = "channel-"
    print("channel prefix=" + channel_prefix)
    # 渠道列表
    # channel_list = config.get("Build-Config", "channel.list")
    print("channel list=" + channel_list)
    # 解析渠道，生成渠道数组
    channel_array = channel_list.split(',')

    src_apk = apk_path
    # file name (with extension)
    src_apk_file_name = os.path.basename(src_apk)
    # 分割文件名与后缀
    temp_list = os.path.splitext(src_apk_file_name)
    # name without extension
    src_apk_name = temp_list[0]
    # 后缀名，包含.   例如: ".apk "
    src_apk_extension = temp_list[1]

    if src_apk_extension == '.apk':
        # 空文件 便于写入此空文件到apk包中作为channel文件
        src_temp_file = 'temp_.txt'
        # 创建生成目录,与文件名相关
        output_dir = 'apks_' + src_apk_name + '/'
    elif src_apk_extension == '.ipa':
        src_temp_file = 'AppInfo.plist'
        # 创建生成目录,与文件名相关
        output_dir = 'ipas_' + src_apk_name + '/'
    else:
        messagebox.showerror(title="错误", message="请选择.apk或者.ipa文件")
        return
    # 创建一个空文件（不存在则创建）
    f = open(src_temp_file, 'w')
    f.close()

    # 目录不存在则创建
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # 遍历渠道号并创建对应渠道号的apk文件
    for line in channel_array:
        # 获取当前渠道号，因为从渠道文件中获得带有\n,所有strip一下
        target_channel = line.strip()
        # 创建苹果的plist文件并写入
        plist = {
            'channel': target_channel
        }
        # 拼接对应渠道号的apk
        target_apk = output_dir + src_apk_name + "-" + target_channel + src_apk_extension
        # 拷贝建立新apk
        shutil.copy(src_apk, target_apk)
        # zip获取新建立的apk文件
        zipped = zipfile.ZipFile(target_apk, 'a', zipfile.ZIP_DEFLATED)

        if src_apk_extension == '.apk':
            # 初始化渠道信息
            target_channel_file = "META-INF/" + channel_prefix + "{channel}".format(channel=target_channel)
            # 写入渠道信息
            zipped.write(src_temp_file, target_channel_file)
        elif src_apk_extension == '.ipa':
            writePlist(plist, src_temp_file)
            target_channel_file = zipped.namelist()[1]+'/_CodeSignature/' + src_temp_file
            zipped.write(src_temp_file, target_channel_file)
        # 关闭zip流
        zipped.close()

    # 删除临时文件
    os.remove(src_temp_file)
    messagebox.showinfo(title="成功", message="签名成功")
    btnShow = tkinter.Button(root, text="打开生成文件目录", foreground='blue', command=lambda: showFiles(output_dir))
    btnShow.pack_configure(pady=15)


def showFiles(path):
    # 打开指定文件夹
    file_opt = options = {}
    options['initialdir'] = path
    options['title'] = '已生成的文件'
    filedialog.askopenfilename(**options)


def selectFile():
    file_opt = options = {}
    options['defaultextension'] = '.apk .ipa'
    options['filetypes'] = [('all files', '.apk .ipa')]
    options['title'] = '选择app包'

    name = filedialog.askopenfilename(**file_opt)
    print(name)
    # dirname = tkinter.filedialog.askdirectory()  # 打开文件夹对话框
    entry.set(name)  # 设置变量entryvar，等同于设置部件Entry
    if not name:
        messagebox.showwarning(title="警告", message="未选择文件")  # 弹出消息提示框


def center_window():
    # get screen width and height
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    # calculate position x, y
    x = (ws / 2)
    y = (hs / 2)
    root.geometry('+%d+%d' % (x, y))


if __name__ == '__main__':
    root = tkinter.Tk(screenName="四虎渠道包", baseName="四虎渠道包", className="四虎渠道包")
    # root.iconbitmap("icon.ico")
    tmp = open("tmp.ico", "wb+")
    tmp.write(base64.b64decode(img))
    tmp.close()
    root.iconbitmap("tmp.ico")
    os.remove("tmp.ico")
    root.title = "四虎渠道包"
    # root.geometry('500x500')
    root.resizable(True, False)  # 固定窗口大小
    windowWidth = 260  # 获得当前窗口宽
    windowHeight = 300  # 获得当前窗口高
    screenWidth, screenHeight = root.maxsize()  # 获得屏幕宽和高
    geometryParam = '%dx%d+%d+%d' % (
        windowWidth, windowHeight, (screenWidth - windowWidth) / 2, (screenHeight - windowHeight) / 2)
    root.geometry(geometryParam)  # 设置窗口大小及偏移坐标
    root.wm_attributes('-topmost', 1)  # 窗口置顶

    frame_main = tkinter.Frame(root, borderwidth=10)

    frame1 = tkinter.Frame(frame_main, borderwidth=10)
    # 代理ID输入框
    entry = tkinter.StringVar()
    entry.set("")
    # 文件选择输入
    labelPath = tkinter.Entry(frame1, textvariable=entry)
    labelPath.pack_configure(anchor=tkinter.CENTER)
    # 按钮
    selectFileBtn = tkinter.Button(frame1, text="选取Apk或ipa包", foreground='black', command=selectFile)
    selectFileBtn.pack_configure(side=tkinter.RIGHT, pady=5)
    frame1.pack_configure(anchor=tkinter.NW)
    frame2 = tkinter.Frame(frame_main, borderwidth=10)
    # 代理ID输入
    default_value = tkinter.StringVar()
    default_value.set('')
    inputDaili = tkinter.Entry(frame2, textvariable=default_value)
    inputDaili.pack_configure(anchor=tkinter.CENTER)
    # 提示文字
    labelFex = tkinter.Label(frame2, text="代理Id,多个使用英文 , 分隔", foreground='black')
    labelFex.pack_configure(side=tkinter.RIGHT, pady=5)
    frame2.pack_configure(anchor=tkinter.NW)

    frame_main.pack_configure(anchor=tkinter.CENTER)
    # 运行按钮
    helv15 = Font(family='Helvetica', size=15, weight='bold')
    runQi = tkinter.Button(root, text="签名", foreground='red', font=helv15, command=startZipAndroid)
    runQi.pack_configure(ipadx=10)
    # 渲染界面
    root.mainloop()
