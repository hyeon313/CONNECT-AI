import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
# import Utility
import pydicom

import numpy as np
import SimpleITK as itk #dicom 관련
import qimage2ndarray

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
        # openAction.triggered.connect(self.read_dicom)
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openAction)
        
        ###########
        Dbtn = QPushButton('&ImgNum', self)
        Dbtn.move(900, 565)
        Dbtn.setCheckable(True)
        Dbtn.toggle()
        Dbtn.clicked.connect(self.showDialog)

        btn1 = QPushButton('&previous', self)
        btn1.move(700, 565)
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
#         self.move(300, 300)
        self.show()

    def showDialog(self):
        num, ok = QInputDialog.getInt(self, 'Input ImageNumber', 'Enter Num')
        #self.label.setText("text: %s" % (text))
        self.cur_idx = num - 1
        # if ok:
        #     self.label.setText(str(num))
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1
        
        self.cur_image = self.EntireImage[self.cur_idx]
        image = self.AdjustPixelRange(self.cur_image, self.window_level, self.window_width) #지현
        
        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        self.wg.lbl_original_img.addPixmap(image)
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()

    def onChanged(self,text):
        self.lbl.setText(text)
        self.lbl.adjustSize()
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
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
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
        self.EntireImage = np.asarray(ImgArray, dtype=np.float32)
        self.EntireImage = np.squeeze(self.EntireImage)
        # 넘파이 이미지 (224, 512, 512)로 전체 데이터 받음.

        print(self.EntireImage.shape)

        self.NofI = self.EntireImage.shape[0]  #이미지 갯수
        self.Nx = self.EntireImage.shape[1] #x차원
        self.Ny = self.EntireImage.shape[2] #y차원

        self.cur_image = self.EntireImage[self.cur_idx] #현재 이미지 셋팅


        


        # ===========================================================
        # original_img = QPixmap(imagePath)
        # blending_img = QPixmap(imagePath)
        
        # self.wg.lbl_original_img.setPixmap(original_img)
        # self.wg.lbl_blending_img.setPixmap(blending_img)

        # self.wg.lbl_original_img.mouseMoveEvent = self.mouseMoveEvent
        # self.wg.lbl_blending_img.mouseMoveEvent = self.mouseMoveEvent
        # self.wg.lbl_original_img.setMouseTracking(True)
        # self.wg.lbl_blending_img.setMouseTracking(True)
        # ===========================================================


        # original_img = pydicom.dcmread(imagePath)
        # blending_img = pydicom.dcmread(imagePath)

        #한장씩 읽을때 쓰던 것
        # ImgData = itk.ReadImage(imagePath)
        # ImgArray = itk.GetArrayFromImage(ImgData)   
        # image= np.asarray(ImgArray, dtype=np.float32)
        # image = np.squeeze(image)
        # # print(image)




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
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
