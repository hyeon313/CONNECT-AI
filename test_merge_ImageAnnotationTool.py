# 2020.9.10. 
# 9.10까지 완료된 jh_ImageAnnotationTool.py과 ju_ImageAnnotationTool.py를 합친 것
# jh_ImageAnnotationTool.py
# 마우스 왼쪽 오른쪽 동시 클릭(toggle; 토글)시 첫 클릭한 좌표에서 이동한 좌표까지의 거리를 width, level적용
# 'next' or 'previous' 버튼을 누르면 전체 이미지의 width, level이 적용된 것을 확인 할 수 있음
# ju_ImageAnnotationTool.py
# 현재는 경로가 지정되어 있지만 나중에 고칠 예정
# 지정된 경로의 전체 이미지를 불러서 처음에는 0번째 이미지를 보지만 'next' or 'previous' 버튼을 누르면 이전과 이후로 넘어감
# 'next' or 'previous' 버튼을 누를 때 마지막 이미지 이거나 첫 이미지 이면 그대로 멈춤
# jh_ImageAnnotationTool.py+ju_ImageAnnotationTool.py 
# 여기까지는 합쳤음

# 추가로 합칠 예정 
# ym_ImageAnnotationTool.py
# 마스크된 이미지 띄우기 완료
# 마스크된 좌표를 1로 표시한 numpy array를 CSV파일로 저장하기 완료




import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import pydicom

import numpy as np
import SimpleITK as itk #dicom 관련
import qimage2ndarray
import math

class MyWidget(QWidget): 
    def __init__(self): 
        super().__init__() 

        self.lbl_original_img = QGraphicsScene()
        self.lbl_blending_img = QGraphicsScene()
        self.view_1 = QGraphicsView(self.lbl_original_img) 
        self.view_2 = QGraphicsView(self.lbl_blending_img) 
        self.view_1.setFixedSize(514, 514)
        self.view_2.setFixedSize(514, 514)

        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hbox = QHBoxLayout()

        self.hbox.addWidget(self.view_1)
        self.hbox.addWidget(self.view_2)
        
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.lbl_pos)
        
        self.setLayout(self.vbox)


class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        
        #지현
        # self.window_level = 40
        # self.window_width = 400
        self.LRpoint = [0, 0]
        self.LRClicked = False #두 버튼 모두 눌림 여부 확인
        self.window_level = 0
        self.window_width = 0
        self.deltaWL = 0
        self.deltaWW = 0



        #종엄
        self.Nx = 0 #이미지 x차원
        self.Ny = 0 #이미지 y차원
        self.NofI = 0 #이미지 개수

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
        
        openAction = QAction(QIcon('exit.png'), 'Open', self)
        openAction.triggered.connect(self.openImage)
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openAction)

        btn1 = QPushButton('&previous', self)
        btn1.move(150, 565)
        btn1.setCheckable(True)
        btn1.toggle()

        btn2 = QPushButton('&next', self)
        btn2.move(800, 565)

        btn1.setShortcut('Ctrl+1')
        btn2.setShortcut('Ctrl+2')

        btn1.clicked.connect(self.btn1_clicked)
        btn2.clicked.connect(self.btn2_clicked)
        
        self.setWindowTitle('Test Image')

        self.setGeometry(300, 300, 1100, 600)
        self.show()

    #종엄
    def btn1_clicked(self):
        #QMessageBox.about(self, "메세지", "이전")
        self.cur_idx = self.cur_idx - 1
                
        if self.cur_idx < 0:
            self.cur_idx = 0
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1
            
        print("left", self.cur_idx)


        self.cur_image = self.EntireImage[self.cur_idx]

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_original_img)
        self.wg.view_1.show()
        self.wg.view_2.show()


    #종엄
    def btn2_clicked(self):
        #QMessageBox.about(self, "메세지", "다음")

        self.cur_idx = self.cur_idx + 1

        if self.cur_idx < 0:
            self.cur_idx = 0
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1

        print("right", self.cur_idx)


        self.cur_image = self.EntireImage[self.cur_idx]

        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_original_img)
        self.wg.view_1.show()
        self.wg.view_2.show()



    def AdjustPixelRange(self, image, level, width): #지현
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
    
        range_ratio = (Upper - Lower) / 256.0

        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)

        return image


    # #지현 예시
    # def mouseEvent():
    #     #self.EntireImage 이미지전체를 조절해줘야함.
    #     self.adjustedImage = self.AdjustPixelRange(self.EntireImage, self.window_level, self.window_width)


    
    def openImage(self):
        imagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', './')

        print("open", imagePath)

        folder_path = "C:\Project\label" #"C:\\Users\\yjm45\\python\\LD2HD\\L067"


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
        self.EntireImage = np.asarray(ImgArray, dtype=np.float32)
        self.EntireImage = np.squeeze(self.EntireImage)
        # 넘파이 이미지 (224, 512, 512)로 전체 데이터 받음.

        print(self.EntireImage.shape)

        self.NofI = self.EntireImage.shape[0]  #이미지 갯수
        self.Nx = self.EntireImage.shape[1] #x차원
        self.Ny = self.EntireImage.shape[2] #y차원

        self.cur_image = self.EntireImage[self.cur_idx] #현재 이미지 셋팅




        #image = self.AdjustPixelRange(image, self.window_level, self.window_width) #지현
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

        if self.LRClicked:
           # print("after click: ", event.globalX(), event.globalY())

            mX = float(event.globalX())
            mY = float(event.globalY())
            
            

            #조건
            rX = np.array(self.LRpoint[0]) #기준점
            rY = np.array(self.LRpoint[1])

           # print(type(mX), mY, type(rX), rY)

            #오른쪽부분
            # self.window_level
            # self.window_width

            square = (rX - mX)*(rX - mX) + (rY - mY)*(rY - mY)
            dist = math.sqrt(square)

            temp_wl = 0
            temp_ww = 0

            if rX < mX: #오른쪽
                
                #temp_wl = self.window_level + dist
                self.deltaWL  = dist
                
            else: #왼쪽부분
                #temp_wl = self.window_level - dist
                self.deltaWL  = -dist


            if rY < mY: #아래부분
                #temp_ww = self.window_width - dist
                self.deltaWW = -dist

            else: #윗부분
                #temp_ww = self.window_width + dist
                self.deltaWW = dist

            #self.deltaWL, self.deltaWW 가지고 요 내부에서 반영
            temp_wl = self.window_level + self.deltaWL
            temp_ww = self.window_width + self.deltaWW

            if temp_wl < 0:
                temp_wl = 0
            
            if temp_ww < 0:
                temp_ww = 0
            
            
            #self.EntireImage 이미지전체를 조절해줘야함.

            print("move: ", temp_wl, temp_ww)

    def mousePressEvent(self, event):
        if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
            if self.LRClicked == False:
                self.LRClicked = True
        
            else:
                self.LRClicked = False
                self.window_level = self.window_level + self.deltaWL
                self.window_width = self.window_width + self.deltaWW

                if self.window_level < 0:
                    self.window_level = 0
                if self.window_width < 0:
                    self.window_width = 0
            
                print("최종반영 ", self.window_level, self.window_width)
                self.adjustedImage = self.AdjustPixelRange(self.EntireImage, self.window_level, self.window_width)

            print("mousePressEvent")
            print("Mouse 클릭한 좌표: x={0},y={1}".format(event.x(), event.y()))
            x = event.globalX()
            y = event.globalY()
            self.LRpoint = [x, y] #기준점 셋업
            
            print('x = ', x)
            print('y = ', y)

    def mouseReleaseEvent(self, event): 

        # e ; QMouseEvent 
        # if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
        #     print('BUTTON RELEASE') 
            # self.mousePressEvent(e.buttons())
        print('BUTTON RELEASE')
        # self.mouseButtonKind(e.buttons())
        print("Click the left and right mouse button")
        print("Mouse 뗀 좌표: x={0},y={1}".format(event.x(), event.y()))
        x1 = event.x()
        y1 = event.y()
        print('x1 = ', x1)
        print('y1 = ', y1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
