#!/usr/bin/python
# coding=utf-8
import multiprocessing
import socket
from http.server import SimpleHTTPRequestHandler, HTTPServer

import qrcode as qrcode
from PIL import Image, ImageTk
from biplist import *
import os
import shutil
import zipfile
from tkinter import filedialog
from tkinter import messagebox
import tkinter
from bottle import template


def startZipAndroid():
    if not entry.get():
        messagebox.showerror(title="错误", message="请选择apk包文件")
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

    # 创建数组下载对象
    listDownLoad = []
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
        if src_apk_extension == '.apk':
            # android的超链接
            listDownLoad.append(('渠道' + target_channel + '点击下载', get_host_ip() + target_apk))
        elif src_apk_extension == '.ipa':
            # ios itms-services://?action=download-manifest&url=https://www.fs4ss.com/lib/vshow1.5.4.plist
            # 1.先生成plist
            plistItem = {
                'items': [
                    {
                        'assets': [
                            {
                                'kind': 'software-package',
                                'url': get_host_ip() + target_apk
                            },
                            {
                                'kind': 'display-image',
                                'url': ''
                            },
                            {
                                'kind': 'full-size-image',
                                'url': ''
                            }
                        ],
                        'metadata': {
                            'bundle-identifier': '',
                            'bundle-version': '2',
                            'kind': 'software',
                            'title': ''
                        }
                    }
                ]
            }
            plistItemFileName = output_dir + target_channel + 'do.plist'
            writePlist(plistItem, plistItemFileName, )
            listDownLoad.append(('渠道' + target_channel + '点击下载',
                                 'itms-services://?action=download-manifest&url=' + get_host_ip() + plistItemFileName))
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
            target_channel_file = zipped.namelist()[2] + src_temp_file
            zipped.write(src_temp_file, target_channel_file)
        # 关闭zip流
        zipped.close()

    # 删除临时文件
    os.remove(src_temp_file)
    messagebox.showinfo(title="成功", message="签名成功")
    html = createHtml(listDownLoad)
    htmlFilePath = output_dir + 'download.html'
    with open(htmlFilePath, 'w', encoding='utf-8') as s:
        s.write(html)
    createQRServer(filepath=output_dir, html=htmlFilePath)


def createQRServer(filepath, html):
    server_address = ('0.0.0.0', 9999)
    SimpleHTTPRequestHandler.protocol_version = "HTTP/1.0"
    SimpleHTTPRequestHandler.path = os.path.abspath('.') + filepath

    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    # httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True,
    #                                certfile='server.pem')
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    url = get_host_ip() + html
    print(url)
    image = createQr(url)
    image_resized = resize(120, 120, image)
    phimage = ImageTk.PhotoImage(image_resized)
    labelFex = tkinter.Label(root, text="扫描二维码下载安装测试", foreground='red')
    labelFex.pack_configure()
    btnShow = tkinter.Button(root, text="打开生成文件目录", foreground='red', command=lambda: showFiles(filepath))
    btnShow.pack_configure()
    # 下载二维码
    qeCanvas = tkinter.Canvas(root, width=120, height=120)
    qeCanvas.create_image(0, 0, anchor=tkinter.NW, image=phimage)
    qeCanvas.pack_configure(anchor=tkinter.CENTER)
    # 起线程会卡一下，进程就不会
    # _thread.start_new_thread(startServer, (httpd,))
    # # 创建进程，target：调用对象，args：传参数到对象
    p = multiprocessing.Process(target=startServer, args=(httpd,))
    p.start()  # 开启进程

    root.mainloop()


def showFiles(path):
    # 打开指定文件夹
    file_opt = options = {}
    options['initialdir'] = path
    options['title'] = '已生成的文件'
    filedialog.askopenfilename(**options)


def createHtml(listDownload):
    """
    创建一个html
    :return: 下载列表
    """
    # 一些我们需要展示的文章题目和内容
    # articles = [("渠道ID=123", "http://blog.csdn.net/reallocing1/article/details/51694967"),
    #             ("渠道ID=223", "http://blog.csdn.net/reallocing1/article/details/51694967"),
    #             ("渠道ID=323", "http://blog.csdn.net/reallocing1/article/details/51694967")]
    # 定义想要生成的Html的基本格式
    # 使用%来插入python代码
    template_demo = """
         <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>下载App</title>
        <style>
            ul {
                width: 100%;
                height: auto;
                color: #fff;
                text-align: center;
                padding: 0;
            }

            li {
                width: 100%;
                background-color: cadetblue;
                border-radius: 20px;
                list-style-type: none;
            }
            a {
                padding: 30px;
                margin: 10px;
                display: block;
                text-decoration: none;
                color: white;
            }
            div{
                padding: 30px 50px;
            }

        </style>
        </head>
        <body>

        <div>
            <ul>
                % for title,link in items:
                <li>
                    <a href={{link}}>{{title}}</a>
                </li>
                %end
            </ul>
        </div>

        </body>
        </html>

        """
    html = template(template_demo, items=listDownload)
    return html


def startServer(httpd):
    httpd.serve_forever()


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return "http://" + ip + ":9999/"


def createQr(str=""):
    """
    生成二维码
    :return:
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=4,
    )
    qr.add_data(str)
    qr.make(fit=True)

    img = qr.make_image()
    return img


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


# 对一个pil_image对象进行缩放，让它在一个矩形框内，还能保持比例

def resize(w_box, h_box, pil_image):  # 参数是：要适应的窗口宽、高、Image.open后的图片
    w, h = pil_image.size  # 获取图像的原始大小
    f1 = 1.0 * w_box / w
    f2 = 1.0 * h_box / h
    factor = min([f1, f2])
    width = int(w * factor)
    height = int(h * factor)
    return pil_image.resize((width, height), Image.ANTIALIAS)


if __name__ == '__main__':
    root = tkinter.Tk(screenName="App渠道包", baseName="App渠道包", className="App渠道包")
    root.iconbitmap("icon.ico")
    root.title = "App渠道包"
    # root.geometry('500x500')
    root.resizable(True, False)  # 固定窗口大小
    windowWidth = 400  # 获得当前窗口宽
    windowHeight = 500  # 获得当前窗口高
    screenWidth, screenHeight = root.maxsize()  # 获得屏幕宽和高
    geometryParam = '%dx%d+%d+%d' % (
        windowWidth, windowHeight, (screenWidth - windowWidth) / 2, (screenHeight - windowHeight) / 2)
    root.geometry(geometryParam)  # 设置窗口大小及偏移坐标
    root.wm_attributes('-topmost', 1)  # 窗口置顶
    # 创建顶部logo
    logo = tkinter.Canvas(root, width=120, height=120)
    pil_image = Image.open('logo.gif')  # 以一个PIL图像对象打开  【调整待转图片格式】
    pil_image_resized = resize(80, 80, pil_image)
    ph = ImageTk.PhotoImage(pil_image_resized)
    logo.create_image(20, 20, anchor=tkinter.NW, image=ph)
    logo.pack(side=tkinter.TOP)

    frame_main = tkinter.Frame(root, borderwidth=10)

    frame1 = tkinter.Frame(frame_main, borderwidth=10)
    # 代理ID输入框
    entry = tkinter.StringVar()
    entry.set("")
    # 文件选择输入
    labelPath = tkinter.Entry(frame1, textvariable=entry)
    labelPath.pack_configure(anchor=tkinter.CENTER)
    # 按钮
    selectFileBtn = tkinter.Button(frame1, text="选取Apk或ipa包", foreground='red', command=selectFile)
    selectFileBtn.pack_configure(side=tkinter.RIGHT)
    frame1.pack_configure(anchor=tkinter.NW)
    frame2 = tkinter.Frame(frame_main, borderwidth=10)
    # 代理ID输入
    default_value = tkinter.StringVar()
    default_value.set('')
    inputDaili = tkinter.Entry(frame2, textvariable=default_value)
    inputDaili.pack_configure(anchor=tkinter.CENTER)
    # 提示文字
    labelFex = tkinter.Label(frame2, text="代理Id,多个使用英文 , 分隔", foreground='red')
    labelFex.pack_configure(side=tkinter.RIGHT)
    frame2.pack_configure(anchor=tkinter.NW)

    frame_main.pack_configure(anchor=tkinter.CENTER)
    # 运行按钮
    runQi = tkinter.Button(root, text="签名", command=startZipAndroid)
    runQi.pack_configure()

    # 渲染界面
    root.mainloop()
