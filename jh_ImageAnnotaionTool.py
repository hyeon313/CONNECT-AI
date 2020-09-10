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
    def eventFilter(self, obj, event):
        if obj is self.view_1.viewport() or self.view_2.viewport():
            if event.type() == QEvent.MouseButtonPress:
                if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
                    global x1
                    global y1
                    
                    print("eventFilter")
                    print("Mouse 클릭한 좌표: x1={0},y1={1}".format(event.globalX(), event.globalY()))
                    x1 = event.globalX()
                    y1 = event.globalY()
                    print('x1 = ', x1)
                    print('y1 = ', y1)
            elif event.type() == QEvent.MouseButtonRelease:
                print('BUTTON RELEASE')
                print("Mouse 뗀 좌표: x2={0},y2={1}".format(event.globalX(), event.globalY()))
                x2 = event.globalX()
                y2 = event.globalY()
                print('x2 = ', x2)
                print('y2 = ', y2)
                x = x2 - x1
                y = y2 - y1
                print("이동한 거리: x={0}, y={1}".format(x,y))

        return QWidget.eventFilter(self, obj, event)
    

class MyApp(QMainWindow):
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
     
    def __init__(self):
        super().__init__()
        self.window_level = 0
        self.window_width = 0
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

    def mouseMoveEvent(self, event):
        txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
        self.wg.lbl_pos.setText(txt)
        self.wg.lbl_pos.adjustSize()
  
    # def mousePressEvent(self, e):
    #     self.c.closeApp.emit()
# https://wikidocs.net/21942         
# https://www.programmersought.com/article/36971069089/
'''
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_A:
            self.window_level = self.window_level - 10
            return self.window_level
        elif e.key() == Qt.Key_D:
            self.window_level = self.window_level + 10
            return self.window_level
        elif e.key() == Qt.Key_W:
            self.window_width = self.window_width + 10
            return self.window_width
        elif e.key() == Qt.Key_S:
            self.window_width = self.window_width - 10
            return self.window_width
          
     def mousePressEvent(self, event):
        # # 왼쪽 오른쪽 동시에 누를 때  
        if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
            print("Click the left and right mouse button")
            print("Mouse 클릭한 좌표: x={0},y={1}".format(event.x(), event.y()))
            x1 = event.x()
            y1 = event.y()
            print('x1 = ', x1)
            print('y1 = ', y1)

    def mouseReleaseEvent(self, event):
     # ***마우스를 뗄 때 작동하지 않음!***
        if event.buttons () == QtCore.Qt.LeftButton | QtCore.Qt.RightButton:
            print("mouse release")
            print("Mouse 뗄 때 좌표: x={0},y={1}".format(event.x(), event.y()))
    # def mouseReleaseEvent(self, event):
    #     if event.buttons() == QtCore.Qt.LeftButton:
    #         print("RELEASE left mouse button")     
'''     

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
