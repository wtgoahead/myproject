'''
这是界面的控制代码
'''
from PyQt5.QtWidgets import QWidget,QApplication,QMainWindow,QMessageBox,QLabel,QFileDialog,QCheckBox,QFormLayout
# from Ui_register import *
import Ui_register
import Ui_login
import Ui_main
from PyQt5.QtCore import Qt,QRect
from PyQt5.QtGui import QIcon,QPixmap
import sys
from socket import *
import time

HOST = '176.209.102.47'
PORT = 7777
ADDR = (HOST,PORT)

#存放组件的列表
l = []

def varify_info(sockfd,username,password,mod):
    msg = mod+" %s %s"%(username,password)
    try:
        sockfd.send(msg.encode())
    except OSError:
        raise
    r = sockfd.recv(128).decode()
    return r

class Login_UI(Ui_login.Ui_MainWindow,QMainWindow):
    def __init__(self,ui_control):
        super().__init__()
        self.ui_control = ui_control
        self.setupUi(self)
        self.initUI()
    def initUI(self):
        self.btnRegister.clicked.connect(self.toRegister)
        self.btnLogin.clicked.connect(self.doLogin)
    def doLogin(self):
        # 获取用户名和密码
        self.username = self.lineUsername.text()
        self.password = self.linePassword.text()
        if not self.username or not self.password:
            QMessageBox.about(self,'警告','请填写完整信息!')
            return
        sockfd = self.ui_control.sockfd
        try:
            r = varify_info(sockfd,self.username,self.password,"L")#L代表登录
        except:
            QMessageBox.about(self,'信息','暂时无法连接服务器!')
            return
        if r == 'SUCCESS':
            # 登录成功,初始化网盘客户端界面,隐藏登录界面
            # 传递套接字和用户名
            self.hide()
            self.mainUI = Main_UI(self.ui_control.sockfd,self.username,self.password)
            self.mainUI.show()

        elif r == 'FAIL':
            # 登录失败
            QMessageBox.about(self,'信息','用户名或密码错误!')
        elif r == 'ServerError':
            QMessageBox.about(self,'信息','服务器出错!')
    def toRegister(self):
        self.hide()
        self.ui_control.show()

class Register_UI_Control(Ui_register.Ui_MainWindow,QMainWindow):
    def __init__(self):
        super().__init__()
        self.sockfd = socket()
        self.setupUi(self)
        self.initUI()
    def initUI(self):
        self.btnRegist.clicked.connect(self.doRegister)
        self.checkBox.stateChanged.connect(self.promise)
        self.btnReturnLogin.clicked.connect(self.returnLogin)
        # 初始化完成,显示界面
        self.show()
        try:
            self.sockfd.connect(ADDR)
        except:
            self.laTip.setText("无法连接服务器!")
            return
    def promise(self):
        if self.checkBox.checkState() == Qt.Checked:
            self.btnRegist.setEnabled(True)
        elif self.checkBox.checkState() == Qt.Unchecked:
            self.btnRegist.setEnabled(False)
    def returnLogin(self):
        try:
            self.login_ui.show()
            self.hide()
        except AttributeError:
            self.initLogin()
        return
    def initLogin(self):
        # 显示登录界面
        self.hide()
        # 登录界面初始化
        self.login_ui = Login_UI(self)
        self.login_ui.show()
    # 处理注册的逻辑
    def doRegister(self):
        username = self.lineUsername.text()
        password = self.linePass.text()
        password2 = self.linePass2.text()
        # 验证用户名和密码是否合法
        if " " in username or " " in password or "/" in username:
            QMessageBox.about(self,'警告','请勿使用非法字符!')
            return
        if not username or not password or not password2:
            QMessageBox.about(self,'警告','请填写完整信息!')
            return
        if  password != password2:
            QMessageBox.about(self,'警告','两次密码不一致')
            return

        r = varify_info(self.sockfd,username,password,"R")#R代表注册
        if r == 'OK':
            # 注册成功
            QMessageBox.about(self,'完成','注册成功!')
            self.returnLogin()
        elif r == "USED":
            # 用户名已存在
            QMessageBox.about(self,'警告','该用户已存在!')
            return
        else:
            # 服务器故障
            QMessageBox.about(self,'警告','服务器故障!')
            return

class Main_UI(Ui_main.Ui_MainWindow,QMainWindow):
    def __init__(self,sockfd,username,password):
        super().__init__()
        self.sockfd = sockfd
        self.username = username
        self.password = password
        self.setupUi(self)
        self.initUI()
    def initUI(self):
        # 显示用户信息至界面
        self.laUsername.setText(self.username)
        self.refreshlist()
        # 显示用户的文件列表
        self.getFileList(self.sockfd)
        # 绑定上传按钮功能
        self.btnUpload.clicked.connect(self.uploadFile)
        # 绑定下载功能按钮

    def getFileList(self,sockfd):
        pass
    def uploadFile(self):
        fileinfo = QFileDialog.getOpenFileName(self,"打开文件","./")
        fileaddr = fileinfo[0]
        self.doUpload(fileaddr)
    def doUpload(self,fileaddr):
        try:
            fd = open(fileaddr,'rb')
        except:
            print("文件打开失败")
            return
        filename = fileaddr.split("/")[-1]
        self.sockfd.send(('U '+filename+" "+self.username).encode())
        data = self.sockfd.recv(128).decode()
        if data == 'ok':
            while True:
                data = fd.read(1024)
                if not data:
                    time.sleep(0.5)
                    self.sockfd.send(b'##')
                    break
                self.sockfd.send(data)
            print("文件传输完毕")
            # 刷新客户端界面
            self.refreshlist()
        else:
            print(data)
    def refreshlist(self):
        for f in l:
            self.formLayout_3.removeRow(f)
        # 刷新后清空列表
        l.clear()
        try:
            self.sockfd.send(('F '+self.username).encode())
        except:
            print("无法连接服务器")
            return
        data = self.sockfd.recv(1024).decode()
        if data == 'ok':
            data = self.sockfd.recv(4096).decode()
            if data == "":
                return
            files = data.split('#')
            for file in files:
                if file == "":
                    continue
                self.createWidget(file)
        else:
            print(data)
        widgets = self.formLayout_3.findChild((QWidget,),"checkbox")
        print(widgets)
    def createWidget(self,filename):
        file = QCheckBox(self.formLayoutWidget)
        l.append(file)
        file.setText(filename)
        icon = QIcon()
        icon.addPixmap(QPixmap("C:/Users/tarena/Desktop/捕获.PNG"), QIcon.Normal, QIcon.Off)
        file.setIcon(icon)
        file.setObjectName("checkBox")
        # 添加组件至表单布局
        self.formLayout_3.addRow(file)
        return file

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 注册界面初始化
    register_ui = Register_UI_Control()
    sys.exit(app.exec_())


