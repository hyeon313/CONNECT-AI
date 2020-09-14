import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QWheelEvent
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
# import Utility
import pydicom # DICOM파일(국제 표준에 따라 생성된 메디컬 이미지 파일)을 
               # 가져오기 위해 python packages 중 하나인 pydicom을 import
import numpy as np
import SimpleITK as itk # SimpleITK로부터 itk(이미지 분할 및 이미지 등록 플랫폼)을 import
import qimage2ndarray # Qimages와 numpy.ndarrays를 빠르게 변환하기위해 qimage2ndarray를 import

class MyWidget(QWidget): 
    def __init__(self): 
        super().__init__() 

        # self.lbl_original_img = QLabel()
        # self.lbl_blending_img = QLabel()
        # self.lbl_original_img.setStyleSheet("border-style: solid;""border-width: 2px;")
        self.lbl_original_img = QGraphicsScene()
        self.lbl_blending_img = QGraphicsScene()
        self.view_1 = QGraphicsView(self.lbl_original_img) 
        self.view_2 = QGraphicsView(self.lbl_blending_img) 
        self.view_1.setFixedSize(514, 514)
        self.view_2.setFixedSize(514, 514)

        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hbox = QHBoxLayout()
        # self.hbox.addWidget(self.lbl_original_img)
        # self.hbox.addWidget(self.lbl_blending_img)
        self.hbox.addWidget(self.view_1)
        self.hbox.addWidget(self.view_2)
        
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.lbl_pos)
        
        self.setLayout(self.vbox)
#         self.setGeometry(300, 100, 350, 150) # x, y, width, height 
#         self.setWindowTitle("QWidget") 
#         self.show()

class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        
        #지현
        self.window_level = 40
        self.window_width = 400


        #종엄
        self.Nx = 0 #이미지 x차원
        self.Ny = 0 #이미지 y차원
        self.NofI = 0 #이미지 개수

        # 전체 이미지 정보


        self.cur_idx = 0 #현시점 띄워줄 이미지 
        self.cur_image = [] #현재 선택된 한장의 이미지
        self.EntireImage = [] #읽어드린 이미지스택(3차원) 전체 이미지
        self.adjustedImage = []

        #영민



        self.wg = MyWidget() 
        # wg = MyWidget2() # placeholder -- QWidget 상속하여 만든것으로 추후 교체하면 됨. 
        self.setCentralWidget(self.wg) # 반드시 필요함.
        self.initUI()


        
        
    def initUI(self):
        # file open Action===> 툴바로부터 파일을 여는 액션을 생성
        openAction = QAction(QIcon('exit.png'), 'Open', self)
        openAction.triggered.connect(self.openImage)
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openAction)
        
        # dialog Button===> 원하는 이미지 번호를 받을 dialog 생성
        Dbtn = QPushButton('&ImgNum', self)
        Dbtn.move(980, 565)
        Dbtn.setCheckable(True)
        Dbtn.toggle()
        Dbtn.clicked.connect(self.showDialog)
        # previous button===> 이전 이미지로 넘어가기위한 Button 생성       
        btn1 = QPushButton('&previous', self)
        btn1.move(700, 565)
        btn1.setCheckable(True)
        btn1.toggle()
        # next button===> 다음 이미지로 넘어가기위한 Button 생성
        btn2 = QPushButton('&next', self)
        btn2.move(800, 565)
        btn1.setCheckable(True)
        btn1.toggle()
        # 단축키
        btn1.setShortcut('Ctrl+1')
        btn2.setShortcut('Ctrl+2')
        #btn1과 btn2에 각각 ~_clicked 연결하여 이벤트 발생
        btn1.clicked.connect(self.btn1_clicked)
        btn2.clicked.connect(self.btn2_clicked)
        
        self.setWindowTitle('Test Image')

        self.setGeometry(300, 300, 1100, 600)

        self.show()

    #Dbtn이 버튼 클릭으로부터 호출 할 showDialog함수 선언
    def showDialog(self):
        num, ok = QInputDialog.getInt(self, 'Input ImageNumber', 'Enter Num') #QInputDialg클래스에 getInt매소드를 이용하여 입력값을 튜플 형태로 num과ok에 넣기
        #self.label.setText("text: %s" % (text))
        self.cur_idx = num - 1 # 입력받은 num값을 cur_idx(인덱스)에 넣는다(0부터 시작해서 입력값에 1빼기)
        # if ok:
        #     self.label.setText(str(num))
        print("show image",self.cur_idx + 1)
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1 # num-1값이 NofI(이미지 전체 개수)를 넘어가면 마지막값[223]을 계속 가지게 만든다
        elif self.cur_idx < 0:
            self.cur_idx = self.NofI-224

        ###########질문########
        # if self.cur_idx == -1: #self.cur_idx가 -1,즉 num이 0을 받아온 상황에서의 조건 생성 중....
        #     QMessageBox.about(self, "메세지", "no")

        
        self.cur_image = self.EntireImage[self.cur_idx] #cur_idx값을 EntireImage를 통해 cur_image에 넣기
        
        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        # cur_image와 window_level, window_width를 AdgustPixelRange함수에 통과시켜 image에 넣기
        image = qimage2ndarray.array2qimage(image) # 통과시킨 imaeg를 Qimage로 전환
        image = QPixmap.fromImage(QImage(image)) #Qimage 형태인 image를 받아 fromImage매소드를 써서 QPixmap(이미지를 보여줄때 쓰는 객체, 포맷들을 지원)
                                #QImage=Qpaint를 사용하거나 이미지 필셀조작
                                #QPixmap= 기존 이미지를 반복해서 그릴 때
        self.wg.lbl_original_img.addPixmap(image) #original_img = 왼쪽 화면
        self.wg.lbl_blending_img.addPixmap(image) #blending_img = 오른쪽 화면
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()

    def onChanged(self,text):
        self.lbl.setText(text)
        self.lbl.adjustSize()


    def refresh(self):
        self.cur_image = self.EntireImage[self.cur_idx]

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()



    #종엄
    #btn1이 버튼 클릭으로부터 호출 할 btn1_clicked함수 선언
    def btn1_clicked(self):
        #QMessageBox.about(self, "메세지", "이전")
        self.cur_idx = self.cur_idx - 1 # 현재 인덱스에 1을 빼서 cur_idx에 넣기
                
        if self.cur_idx < 0: 
            self.cur_idx = 0 #0보다 작으면 0으로 남기
            
        print("left and image", self.cur_idx +1)


        self.cur_image = self.EntireImage[self.cur_idx]

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()

    #종엄
    #btn2이 버튼 클릭으로부터 호출 할 btn2_clicked함수 선언
    def btn2_clicked(self):
        #QMessageBox.about(self, "메세지", "다음")

        self.cur_idx = self.cur_idx + 1 # 현재 인덱스에서 1을 더해서 cur_idx에 넣기

        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1 #223보다 크면 223으로 남기

        print("right and image=", self.cur_idx +1)


        self.cur_image = self.EntireImage[self.cur_idx]

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()



    def AdjustPixelRange(self, image, level, width): #지현
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
    
        range_ratio = (Upper - Lower) / 256.0

        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)

        return image

    # def read_dicom(self, files, path):
        # return Utility.load_dicomseries(files, path)


    # #지현 예시
    # def mouseEvent():
    #     #self.EntireImage 이미지전체를 조절해줘야함.
    #     self.adjustedImage = self.AdjustPixelRange(self.EntireImage, self.window_level, self.window_width)


    
    def openImage(self):
        imagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', './')

        print("open", imagePath)

        folder_path = "C:\\Users\\yjm45\\python\\LD2HD\\L067"


        reader = itk.ImageSeriesReader() 
        # reader: 이미지시리즈를 담당하는 오브젝트를 받음.
        dicom_names = reader.GetGDCMSeriesFileNames(folder_path)
        # reader 오브젝트가 가지고 있는 멤버함수인데 파일명 리스트들 가져옴.
        print(type(dicom_names))
        reader.SetFileNames(dicom_names)
        # 파일명들을 가져올 대상으로 지정해주는 함수

        images = reader.Execute()
        #실제 이미지들을 파일명 리스트를 기반으로 읽음.
        print(type(images[0]), type(images[1]))

        ImgArray = itk.GetArrayFromImage(images)   
        self.EntireImage = np.asarray(ImgArray, dtype=np.float32) #입력 데이터를 ndarray로 변환하나 이미 ndarray일 경우 새로 메모리에 ndarray가 생성 (x)
        self.EntireImage = np.squeeze(self.EntireImage)# 차원 축소
        print(type(self.EntireImage))
        # 넘파이 이미지 (224, 512, 512)로 전체 데이터 받음.

        print(self.EntireImage.shape)# (224, 512, 512)

        self.NofI = self.EntireImage.shape[0]  #이미지 갯수
        self.Nx = self.EntireImage.shape[1] #x차원
        self.Ny = self.EntireImage.shape[2] #y차원

        self.cur_image = self.EntireImage[self.cur_idx] #현재 이미지 셋팅

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        original_img = image
        blending_img = image
        
        #왼쪽 프레임 담당
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_1.show()

        #오른쪽 프레임 담당
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_2.show()

        self.wg.view_1.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_2.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_1.setMouseTracking(True)
        self.wg.view_2.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
        self.wg.lbl_pos.setText(txt)
        self.wg.lbl_pos.adjustSize()

    def wheelEvent(self, event):
        
        n_scroll = int(event.angleDelta().y() / 120)
        
        self.cur_idx = self.cur_idx + n_scroll
        if self.cur_idx < 0:
            self.cur_idx = 0
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1

        print (self.cur_idx)
        # n_scroll = int(event.angleDelta().y() /120)
        
        
        # self.cur_idx = self.cur_idx +n_scroll
        # print(self.cur_idx)
        self.refresh()
         
        
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
