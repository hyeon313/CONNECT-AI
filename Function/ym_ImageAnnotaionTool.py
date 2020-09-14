import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
     QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox, QPushButton)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPoint
# import Utility
import pydicom

import numpy as np
import SimpleITK as itk
import qimage2ndarray
# import pandas as pd

class MyWidget(QWidget): 
    def __init__(self): 
        super().__init__() 

        self.lbl_original_img = QGraphicsScene()
        self.lbl_blending_img = QGraphicsScene()
        self.view_1 = QGraphicsView(self.lbl_original_img) 
        self.view_2 = QGraphicsView(self.lbl_blending_img) 
        self.view_1.setFixedSize(514, 514)
        self.view_2.setFixedSize(514, 514)

        self.addMaskBtn = QPushButton('&Add Mask', self)
        self.maskComboBox = QComboBox(self)
        self.drawCheckBox = QCheckBox('Draw', self)
        self.maskCheckBox = QCheckBox('Mask on', self)
        self.blendCheckBox = QCheckBox('Blended Mask on', self)

        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hViewbox = QHBoxLayout()
        self.hViewbox.addWidget(self.view_1)
        self.hViewbox.addWidget(self.view_2)

        self.hOptionbox = QHBoxLayout()
        self.hOptionbox.addWidget(self.addMaskBtn)
        self.hOptionbox.addWidget(self.maskComboBox)
        self.hOptionbox.addWidget(self.drawCheckBox)
        self.hOptionbox.addWidget(self.maskCheckBox)
        self.hOptionbox.addWidget(self.blendCheckBox)
        
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hViewbox)
        self.vbox.addLayout(self.hOptionbox)
        self.vbox.addWidget(self.lbl_pos)
        
        self.setLayout(self.vbox)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # 지현
        self.window_level = 40
        self.window_width = 400
        
        # 종엄
        # 
        self.Nx = 512 #이미지 x차원
        self.Ny = 512 #이미지 y차원
        self.NofI = 0 #이미지 개수

        # 영민
        self.isOpened = False
        self.drawing = False
        self.lastPoint = QPoint()
        self.mask_arrList = []
        self.mask_imgList = []
        self.checkExistMask = False

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
        self.wg.addMaskBtn.clicked.connect(self.addMask)
        self.wg.maskCheckBox.stateChanged.connect(self.showMask)
        self.wg.blendCheckBox.stateChanged.connect(self.showBlendedMask)
        self.wg.maskComboBox.activated.connect(self.maskComboBoxActivated)

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

        self.current_img_arr = self.AdjustPixelRange(image, self.window_level, self.window_width)
        # print(self.origin_img_arr)

        self.current_image = qimage2ndarray.array2qimage(self.current_img_arr)
        current_image = QPixmap.fromImage(QImage(self.current_image))
        # self.original_img = QPixmap.fromImage(QImage(self.current_image))
        # self.blending_img = QPixmap.fromImage(QImage(self.current_image))
        
        self.wg.lbl_original_img.addPixmap(current_image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        # self.wg.lbl_blending_img.addPixmap(self.blending_img)
        # self.wg.view_2.setScene(self.wg.lbl_blending_img)

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
            if self.checkExistMask:
                if event.buttons() and Qt.LeftButton and self.drawing and self.wg.drawCheckBox.isChecked():
                    painter = QPainter(self.current_maskPixmap)
                    painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
                    painter.drawLine(self.lastPoint, event.pos())
                    # painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
                    # painter.drawEllipse(event.pos(), 1, 1)
                    self.lastPoint = event.pos()
                    self.update()
                    self.mask_imgList[self.wg.maskComboBox.currentIndex()] = self.current_maskPixmap.toImage()
                    self.wg.lbl_blending_img.addPixmap(self.current_maskPixmap)
            self.lastPoint = event.pos()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            # self.lastPoint = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            
    def showMask(self, state):
        if Qt.Checked == state:
            origin_qimg = self.current_image
            masked_qimg = self.mask_imgList[self.wg.maskComboBox.currentIndex()]
            
            origin_arr = qimage2ndarray.rgb_view(origin_qimg)
            masked_arr = qimage2ndarray.rgb_view(masked_qimg)

            height = origin_arr.shape[0]
            width = origin_arr.shape[1]
            channel = origin_arr.shape[2]

            temp = np.zeros((height, width, channel))
            mask = np.zeros((height, width))
            for i in range(height):
                for j in range(width):
                    check = origin_arr[i, j] != masked_arr[i, j]
                    if True in check:
                        temp[i, j] = origin_arr[i, j]
                        mask[i, j] = 1
            
            # gray = self.rgb2gray(temp)
            # mask = mask.astype(np.int32)
            np.savetxt('mask{}.csv'.format(self.wg.maskComboBox.currentIndex() + 1), mask, fmt='%d', delimiter=',')
            self.masked_arr = temp
            self.masked_qimg = qimage2ndarray.array2qimage(self.masked_arr)
            self.masked_pixmap = QPixmap.fromImage(QImage(self.masked_qimg))

            self.wg.lbl_blending_img.addPixmap(self.masked_pixmap)
        else:
            self.wg.lbl_blending_img.addPixmap(self.current_maskPixmap)

    def showBlendedMask(self, state):
        if Qt.Checked == state:
            origin_qimg = self.current_image
            masked_qimg = self.mask_imgList[self.wg.maskComboBox.currentIndex()]
            
            origin_arr = qimage2ndarray.rgb_view(origin_qimg)
            masked_arr = qimage2ndarray.rgb_view(masked_qimg)

            blended_arr = origin_arr * 0.5 + masked_arr * 0.5
            blended_mask = qimage2ndarray.array2qimage(blended_arr)
            blended_mask = QPixmap.fromImage(QImage(blended_mask))
            self.wg.lbl_blending_img.addPixmap(blended_mask)
        else:
            self.wg.lbl_blending_img.addPixmap(self.current_maskPixmap)

    # def saveMaskArray(self, ):

    def rgb2gray(self, rgb):
        return np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    def addMask(self):
        self.mask_arrList.append(np.zeros((self.Nx, self.Ny)))
        temp = qimage2ndarray.array2qimage(self.current_img_arr)
        self.mask_imgList.append(temp)
        self.wg.maskComboBox.addItem('Mask' + str(len(self.mask_arrList)))
        self.current_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.wg.maskComboBox.currentIndex()]))
        if not self.checkExistMask:
            self.checkExistMask = True
            self.wg.lbl_blending_img.addPixmap(self.current_maskPixmap)
            self.wg.view_2.setScene(self.wg.lbl_blending_img)

    def maskComboBoxActivated(self, index):
        if self.checkExistMask:
            self.current_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[index]))
            self.wg.lbl_blending_img.addPixmap(self.current_maskPixmap)
            self.wg.view_2.setScene(self.wg.lbl_blending_img)
            if self.wg.maskCheckBox.isChecked():
                self.wg.maskCheckBox.toggle()
            if self.wg.blendCheckBox.isChecked():
                self.wg.blendCheckBox.toggle()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
