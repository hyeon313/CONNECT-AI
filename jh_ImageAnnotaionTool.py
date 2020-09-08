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
    #     self.initUI()

    # def initUI(self):
    #     lbl_original_img = QGraphicsScene()
    #     lbl_blending_img = QGraphicsScene()
    #     view_1 = QGraphicsView(lbl_original_img) 
    #     view_2 = QGraphicsView(lbl_blending_img) 

    #     view_1.setFixedSize(512, 512)
    #     view_2.setFixedSize(512, 512)
        
    #     lbl_pos = QLabel()
    #     lbl_pos.setAlignment(Qt.AlignCenter)
        
    #     hbox = QHBoxLayout()
    #     hbox.addWidget(view_1)
    #     hbox.addWidget(view_2)
        
    #     vbox = QVBoxLayout()
    #     vbox.addLayout(hbox)
    #     vbox.addWidget(lbl_pos)
        
    #     self.setLayout(vbox)

class MyApp(QMainWindow):

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
