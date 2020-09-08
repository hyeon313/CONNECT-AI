import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene, QCheckBox)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint
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

        self.drawCB = QCheckBox('Draw', self)
        # self.cb.toggle()
        # self.cb.stateChanged.connect(self.changeTitle)
        # self.drawCB.setAlignment(Qt.AlignCenter)

        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.view_1)
        self.hbox.addWidget(self.view_2)
        
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.drawCB)
        self.vbox.addWidget(self.lbl_pos)
        
        self.setLayout(self.vbox)

class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.isOpened = False
        self.drawing = True
        self.lastPoint = QPoint()
        self.image = None
        self.window_level = 40
        self.window_width = 400
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
        print(self.wg.view_2.pos())
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
        imagePath, _ = QFileDialog.getOpenFileName(self, 'Open file', './')

        # original_img = pydicom.dcmread(imagePath)
        # blending_img = pydicom.dcmread(imagePath)

        ImgData = itk.ReadImage(imagePath)
        ImgArray = itk.GetArrayFromImage(ImgData)   
        image = np.asarray(ImgArray, dtype=np.float32)
        image = np.squeeze(image)
        # print(image)

        image = self.AdjustPixelRange(image, self.window_level, self.window_width)
        # print(image.shape)

        image = qimage2ndarray.array2qimage(image)
        self.original_img = QPixmap.fromImage(QImage(image))
        self.blending_img = QPixmap.fromImage(QImage(image))
        
        self.wg.lbl_original_img.addPixmap(self.original_img)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        # self.wg.view_1.show()
        self.wg.lbl_blending_img.addPixmap(self.blending_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        # self.wg.view_2.show()

        self.isOpened = True

        self.wg.view_1.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_2.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_1.setMouseTracking(True)
        self.wg.view_2.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        if self.isOpened:
            txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
            self.wg.lbl_pos.setText(txt)
            self.wg.lbl_pos.adjustSize()
            if event.buttons() and Qt.LeftButton and self.drawing and self.wg.drawCB.isChecked():
                painter = QPainter(self.blending_img)
                painter.setPen(QPen(Qt.red, 3, Qt.SolidLine))
                painter.drawLine(self.lastPoint, event.pos())
                self.lastPoint = event.pos()
                self.update()
                self.wg.lbl_blending_img.addPixmap(self.blending_img)
                # self.wg.view_2.setScene(self.wg.lbl_blending_img)
            self.lastPoint = event.pos()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            # self.lastPoint = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False
    
    # def paintEvent(self, event):
    #     if self.isOpened:
    #         painter = QPainter(self)
    #         painter.drawPixmap(self.rect(), self.image)
    #         self.wg.lbl_blending_img.addPixmap(self.blending_img)
    #         self.wg.view_2.setScene(self.wg.lbl_blending_img)
    #         self.wg.view_2.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())