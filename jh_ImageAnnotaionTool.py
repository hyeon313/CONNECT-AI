# 마우스를 왼쪽 오른쪽 동시에 누르는 것을 toggle로 만듦
# 움직인 만큼 기본 level, width를 더하여 level, width가 움직이게 만드는 코드
import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt
# import Utility
import pydicom

import numpy as np
import SimpleITK as itk
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
        self.view_1.viewport().installEventFilter(self)
        self.view_2.viewport().installEventFilter(self)

    # def eventFilter(self, obj, event):
    #     if obj is self.view_1.viewport():
    #         if event.type() == QEvent.MouseButtonPress:
    #             print('mouse press event = ', event.pos())
    #         elif event.type() == QEvent.MouseButtonRelease:
    #             print('mouse release event = ', event.pos())
    #     elif obj is self.view_2.viewport():
    #         if event.type() == QEvent.MouseButtonPress:
    #             print('mouse press event = ', event.pos())
    #         elif event.type() == QEvent.MouseButtonRelease:
    #             print('mouse release event = ', event.pos())
    #     return QWidget.eventFilter(self, obj, event)


# x widrh, y level 예정
#    def eventFilter(self, obj, event):
#        if obj is self.view_1.viewport() or self.view_2.viewport():
#            if event.type() == QEvent.MouseButtonPress:
#                if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
#                    global x1
#                    global y1
                    
#                     print("eventFilter")
#                     print("Mouse 클릭한 좌표: x1={0},y1={1}".format(event.globalX(), event.globalY()))
#                     x1 = event.globalX()
#                     y1 = event.globalY()
#                     print('x1 = ', x1)
#                     print('y1 = ', y1)
#             elif event.type() == QEvent.MouseButtonRelease:
#                 print('BUTTON RELEASE')
#                 print("Mouse 뗀 좌표: x2={0},y2={1}".format(event.globalX(), event.globalY()))
#                 x2 = event.globalX()
#                 y2 = event.globalY()
#                 print('x2 = ', x2)
#                 print('y2 = ', y2)
#                 x = x2 - x1
#                 y = y2 - y1
#                 print("이동한 거리: x={0}, y={1}".format(x,y))

#         return QWidget.eventFilter(self, obj, event)
    

class MyApp(QMainWindow):
    
    def __init__(self):
        super().__init__()
     
        #지현
        self.LRpoint = [0, 0]
        self.LRClicked = False #두 버튼 모두 눌림 여부 확인
        self.window_level = 0
        self.window_width = 0
        self.deltaWL = 0
        self.deltaWW = 0
         
     
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
        
        self.setWindowTitle('Test Image')

        self.setGeometry(300, 300, 1100, 600)
#         self.move(300, 300)
        self.show()

    def AdjustPixelRange(self, image, level, width):
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
    
        range_ratio = (Upper - Lower) / 256.0

        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)

        return image

    # def read_dicom(self, files, path):
        # return Utility.load_dicomseries(files, path)
    
    def openImage(self):
        imagePath, _ = QFileDialog.getOpenFileName()


        # original_img = pydicom.dcmread(imagePath)
        # blending_img = pydicom.dcmread(imagePath)

        ImgData = itk.ReadImage(imagePath)
        ImgArray = itk.GetArrayFromImage(ImgData)   
        image= np.asarray(ImgArray, dtype=np.float32)
        image = np.squeeze(image)
        # print(image)

        image = self.AdjustPixelRange(image, self.window_level, self.window_width)
        # print('o')

        image = qimage2ndarray.array2qimage(image)
        image = QPixmap.fromImage(QImage(image))

        original_img = image
        blending_img = image
        
        self.wg.lbl_original_img.addPixmap(image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_1.show()
        self.wg.lbl_blending_img.addPixmap(image)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_2.show()

        self.wg.view_1.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_2.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_1.setMouseTracking(True)
        self.wg.view_2.setMouseTracking(True)
          
     # 지현
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
          
     # 지현  
     def mousePressEvent(self, event):
        
        if event.buttons () == QtCore.Qt.LeftButton:
            print("L down")
        if event.buttons () == QtCore.Qt.RightButton:
            print("R down")


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


            print("mousePressEvent")
            print("Mouse 클릭한 좌표: x={0},y={1}".format(event.x(), event.y()))
            x = event.globalX()
            y = event.globalY()
            self.LRpoint = [x, y] #기준점 셋업
            
            print('x = ', x)
            print('y = ', y)

     # 지현               
    def mouseReleaseEvent(self, event): 
        # 인식이 안됨 이유 찾기
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
