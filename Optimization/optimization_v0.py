'''
최적화 중
줌 실행 시 좌표 고정 필요(그릴 때 원본 좌표에 그려짐ㅜ)
'''

import sys
import os ##
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
    QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox, QPushButton,\
         QInputDialog, qApp, QLineEdit)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QWheelEvent, QPainter, QPen, QBrush, QCursor
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5 import QtWidgets, QtCore
import pydicom 
import numpy as np
import SimpleITK as itk
import qimage2ndarray
import math
import copy

class MyWidget(QWidget): 
    def __init__(self): 
        super().__init__() 

        self.lbl_original_img = QGraphicsScene()
        self.lbl_blending_img = QGraphicsScene()
        self.view_1 = QGraphicsView(self.lbl_original_img) 
        self.view_2 = QGraphicsView(self.lbl_blending_img) 
        self.view_1.setFixedSize(514, 514)
        self.view_2.setFixedSize(514, 514)

        self.deleteCurMaskBtn = QPushButton('Delete Current Mask', self)
        self.addMaskBtn = QPushButton('&Add Mask', self)
        self.maskComboBox = QComboBox(self)
        self.maskCheckBox = QCheckBox('Masking', self)
        self.blendCheckBox = QCheckBox('Blended Mask on', self)
        self.penSizeEdit = QLineEdit(self)
        self.penSizeEdit.setFixedWidth(30)

        self.dialogBtn = QPushButton('&ImgNum', self)  
        self.previousBtn = QPushButton('&previous', self)
        self.nextBtn = QPushButton('&next', self)

        self.lbl_pen_size = QLabel('Pen & Eraser size', self)
        self.lbl_pen_size.setAlignment(Qt.AlignCenter)
        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hViewbox = QHBoxLayout()
        self.hViewbox.addWidget(self.view_1)
        self.hViewbox.addWidget(self.view_2)
        self.view_1.wheelEvent = self.wheelEvent
        self.view_2.wheelEvent = self.wheelEvent

        self.hOptionbox = QHBoxLayout()
        self.hOptionbox.addWidget(self.deleteCurMaskBtn)
        self.hOptionbox.addWidget(self.addMaskBtn)
        self.hOptionbox.addWidget(self.maskComboBox)
        self.hOptionbox.addWidget(self.lbl_pen_size)
        self.hOptionbox.addWidget(self.penSizeEdit)
        self.hOptionbox.addWidget(self.maskCheckBox)
        self.hOptionbox.addWidget(self.blendCheckBox)
        self.hOptionbox.addWidget(self.previousBtn)
        self.hOptionbox.addWidget(self.nextBtn)
        self.hOptionbox.addWidget(self.dialogBtn)
        
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hViewbox)
        self.vbox.addLayout(self.hOptionbox)
        self.vbox.addWidget(self.lbl_pos)
        
        self.setLayout(self.vbox)

class MyApp(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.LRpoint = [0, 0]
        self.LRClicked = False
        self.window_level = 40
        self.window_width = 400
        self.deltaWL = 0
        self.deltaWW = 0

        self.Nx = 0 
        self.Ny = 0 
        self.NofI = 0 

        self.cur_idx = 0 
        self.cur_image = [] 
        self.EntireImage = [] 
        self.adjustedImage = []
        
        self.drawing = False
        self.lastPoint = QPoint()
        self.mask_arrList = []
        self.mask_imgList = []
        self.drawn_imgList = []
        self.onCtrl = False
        self.onShift = False
        self.pen_size = 10
        self.file_names = []

        self.wg = MyWidget() 
        self.setCentralWidget(self.wg)
        self.initUI()
        
    def initUI(self): ##
        openAction = QAction(QIcon('exit.png'), 'Open', self)
        openAction.triggered.connect(self.openImage)
        exitAction = QAction('Quit', self)
        exitAction.triggered.connect(qApp.quit)
        saveAction = QAction('Save Current Masks', self)
        saveAction.triggered.connect(self.saveCurrentMasks)
        saveallAction = QAction('Save all', self)
        saveallAction.triggered.connect(self.saveAllMasks)
        adjustAction = QAction('Adjust', self)
        adjustAction.triggered.connect(self.adjustImage)

        self.statusBar()

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openAction)
        filemenu.addAction(saveAction)
        filemenu.addAction(saveallAction)
        filemenu.addAction(exitAction)
        filemenu = menubar.addMenu('&Image')
        filemenu.addAction(adjustAction)
        
        self.wg.deleteCurMaskBtn.clicked.connect(self.deleteMask)
        self.wg.addMaskBtn.clicked.connect(self.addMask)
        self.wg.maskCheckBox.stateChanged.connect(self.onMasking)
        self.wg.blendCheckBox.stateChanged.connect(self.showBlendedMask)
        self.wg.maskComboBox.activated.connect(self.maskComboBoxActivated)
        self.wg.penSizeEdit.textChanged[str].connect(self.setPenSize)
        self.wg.penSizeEdit.setText(str(self.pen_size))

        self.wg.dialogBtn.clicked.connect(self.showDialog)
        self.wg.previousBtn.clicked.connect(self.previousBtn_clicked)
        self.wg.nextBtn.clicked.connect(self.nextBtn_clicked)

        self.wg.view_1.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_1.mousePressEvent = self.mousePressEvent
        self.wg.view_1.mouseReleaseEvent = self.mouseReleaseEvent
        self.wg.view_2.mouseMoveEvent = self.mouseMoveEvent
        self.wg.view_2.mousePressEvent = self.mousePressEvent
        self.wg.view_2.mouseReleaseEvent = self.mouseReleaseEvent
        self.wg.view_1.setMouseTracking(True)
        self.wg.view_2.setMouseTracking(True)

        self.wg.view_2.keyPressEvent = self.keyPressEvent
        self.wg.view_2.keyReleaseEvent = self.keyReleaseEvent
        
        self.setWindowTitle('Test Image')
        self.setGeometry(300, 300, 1100, 600)
        self.show()
    
    def openImage(self): ##
        try:
            self.folder_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
            reader = itk.ImageSeriesReader() 
            dicom_names = reader.GetGDCMSeriesFileNames(self.folder_path)
            for i in range(len(dicom_names)):
                self.file_names.append(dicom_names[i].replace(self.folder_path + '/', '').replace('.IMA', ''))
            reader.SetFileNames(dicom_names)
            images = reader.Execute()
            ImgArray = itk.GetArrayFromImage(images)   
            self.EntireImage = np.asarray(ImgArray, dtype=np.float32) 
            self.EntireImage = np.squeeze(self.EntireImage)
            self.NofI = self.EntireImage.shape[0]  
            self.Nx = self.EntireImage.shape[1] 
            self.Ny = self.EntireImage.shape[2] 
            self.mask_arrList = [[np.zeros((self.Nx, self.Ny))] for _ in range(self.NofI)]
            self.mask_imgList = [[qimage2ndarray.array2qimage(np.zeros((self.Nx, self.Ny, 4)))] for _ in range(self.NofI)]
            self.refresh()
            self.isOpened = True
        except:
            return

    def adjustImage(self):
        level, ok = QInputDialog.getInt(self, 'Level', 'Level Set')
        width, ok = QInputDialog.getInt(self, 'Width', 'Width Set')
        self.window_level = level
        self.window_width = width
        self.refresh()

    def showDialog(self):
        num, ok = QInputDialog.getInt(self, 'Input ImageNumber', 'Enter Num')
        self.cur_idx = num - 1
        print("show image",self.cur_idx + 1)
        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1
        elif self.cur_idx < 0:
            self.cur_idx = self.NofI-224
        self.refresh()

    def refresh(self): ##
        try:
            self.wg.maskComboBox.clear()
            for i in range(len(self.mask_imgList[self.cur_idx])):
                self.wg.maskComboBox.addItem('Mask' + str(i + 1))

            self.cur_orginal_image = self.EntireImage[self.cur_idx]
            self.cur_img_arr = self.AdjustPixelRange(self.cur_orginal_image, self.window_level, self.window_width)
            self.cur_image = qimage2ndarray.array2qimage(self.cur_img_arr)
            cur_image = QPixmap.fromImage(QImage(self.cur_image))

            self.wg.lbl_original_img.clear()
            self.wg.lbl_blending_img.clear()
            self.wg.lbl_original_img.addPixmap(cur_image)
            self.wg.lbl_blending_img.addPixmap(cur_image)
            self.wg.view_1.setScene(self.wg.lbl_original_img)
            self.wg.view_2.setScene(self.wg.lbl_blending_img)

            self.cur_maskPixmap = QPixmap.fromImage(\
                QImage(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]))
            self.drawn_arrList = \
                [qimage2ndarray.byte_view(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()])]

            self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
        except:
            return
        
    def previousBtn_clicked(self):
        try:
            self.cur_idx = self.cur_idx - 1
            if self.cur_idx < 0: 
                self.cur_idx = 0
            self.refresh()
        except:
            return

    def nextBtn_clicked(self):
        try:
            self.cur_idx = self.cur_idx + 1
            if self.cur_idx > self.NofI-1:
                self.cur_idx = self.NofI-1
            self.refresh()
        except:
            return

    def AdjustPixelRange(self, image, level, width):
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
        range_ratio = (Upper - Lower) / 256.0
        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)
        return image

    def wheelEvent(self, event):
        try:
            n_scroll = int(event.angleDelta().y() / 120)
            
            self.cur_idx = self.cur_idx + n_scroll
            if self.cur_idx < 0:
                self.cur_idx = 0
            if self.cur_idx > self.NofI-1:
                self.cur_idx = self.NofI-1
            self.refresh() 
        except:
            return

    def mouseMoveEvent(self, event): ##
        try:
            if self.LRClicked:
                rX = np.array(self.LRpoint[0])
                rY = np.array(self.LRpoint[1])
                
                mX = event.globalX()
                mY = event.globalY()

                square = (rX - mX)*(rX - mX) + (rY - mY)*(rY - mY)
                dist = math.sqrt(square) / 20

                if rX < mX:
                    self.deltaWL  = dist                
                else:
                    self.deltaWL  = -dist
                if rY < mY:
                    self.deltaWW = -dist
                else:
                    self.deltaWW = dist
                self.window_level = self.window_level + self.deltaWL
                self.window_width = self.window_width + self.deltaWW

                if self.window_width <= 0:
                    self.window_width = 0
                elif self.window_width > 900:
                    self.window_width = 900

                if self.window_level < -250:
                    self.window_level = -250
                elif self.window_level > 100:
                    self.window_level = 100
                self.refresh()
            
            if self.drawing:
                painter = QPainter(self.cur_maskPixmap)
                painter.setPen(QPen(Qt.red, self.pen_size, Qt.SolidLine))
                if self.onCtrl:
                    painter.drawLine(self.lastPoint, event.pos())
                elif self.onShift:
                    r = QRect(self.lastPoint, self.pen_size * QSize())
                    r.moveCenter(event.pos())
                    painter.setCompositionMode(QPainter.CompositionMode_Clear)
                    painter.eraseRect(r)
                # self.update()
                self.wg.lbl_blending_img.removeItem(self.wg.lbl_blending_img.items()[0])
                self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
            
            self.lastPoint = event.pos()
            txt = "x={0}, y={1}, z={2}, image value={3}".format(event.x(), event.y(), self.cur_idx+1, self.cur_orginal_image[event.x(),event.y()]) 
            self.wg.lbl_pos.setText(txt)
            self.wg.lbl_pos.adjustSize()
        except:
            return

    def mousePressEvent(self, event):
        try:
            if event.buttons () == Qt.LeftButton | Qt.RightButton:
                if self.LRClicked == False: 
                    self.LRClicked = True
                    x = event.globalX()
                    y = event.globalY()
                    self.LRpoint = [x, y]
                else:
                    self.LRClicked = False
            if event.button() == Qt.LeftButton:
                self.drawing = True
        except:
            return

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.LeftButton:
                if self.drawing:
                    self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()] = \
                        self.cur_maskPixmap.toImage()
                    self.drawn_imgList.append(qimage2ndarray.byte_view(self.cur_maskPixmap.toImage())) ##
                    self.refreshMaskView()
                self.drawing = False
        except:
            return

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.onCtrl = True
        if event.key() == Qt.Key_Shift:
            self.onShift = True
        if self.onCtrl and event.key() == Qt.Key_Z:
            self.erasePreviousLine()
        if self.onCtrl and event.key() == Qt.Key_Plus:
            self.wg.view_2.scale(1.25, 1.25)
        if self.onCtrl and event.key() == Qt.Key_Minus:
            self.wg.view_2.scale(0.8, 0.8)
        if self.onCtrl and event.key() == Qt.Key_Asterisk:
            self.refresh()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.onCtrl = False
        if event.key() == Qt.Key_Shift:
            self.onShift = False
        
    def erasePreviousLine(self):
        if len(self.drawn_arrList) > 1:
            del self.drawn_arrList[len(self.drawn_arrList)-1]
            temp = self.bgra2rgba(self.drawn_arrList[len(self.drawn_arrList)-1])
            self.cur_maskPixmap = QPixmap.fromImage(QImage(qimage2ndarray.array2qimage(temp)))
            self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()] = \
                self.cur_maskPixmap.toImage()
            self.refreshMaskView()

    def onMasking(self, state): ##
        try:
            if Qt.Checked == state:
                origin_qimg = self.cur_image
                masked_qimg = self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                
                origin_arr = qimage2ndarray.rgb_view(origin_qimg)
                masked_alpha_arr = qimage2ndarray.alpha_view(masked_qimg)

                channel = origin_arr.shape[2]
                temp = np.zeros((self.Nx, self.Ny, channel))

                for i in range(self.Nx):
                    for j in range(self.Ny):
                        if masked_alpha_arr[i, j] != 0:
                            temp[i, j] = origin_arr[i, j]
                            self.mask_arrList[self.cur_idx][self.wg.maskComboBox.currentIndex()][i, j] = \
                                self.wg.maskComboBox.currentIndex() + 1
                
                self.masked_arr = temp
                self.masked_qimg = qimage2ndarray.array2qimage(self.masked_arr)
                self.masked_pixmap = QPixmap.fromImage(QImage(self.masked_qimg))

                self.wg.lbl_blending_img.addPixmap(self.masked_pixmap)
            else:
                self.wg.lbl_blending_img.removeItem(self.wg.lbl_blending_img.items()[0])
        except:
            return
                
    def showBlendedMask(self, state):
        try:
            if Qt.Checked == state:
                masked_qimg = self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                masked_arr = self.bgra2rgba(qimage2ndarray.byte_view(masked_qimg))
                masked_alpha_arr = masked_arr[:, :, 3].copy()
                masked_arr[:, :, 3] = masked_alpha_arr * 0.5

                blended_mask = qimage2ndarray.array2qimage(masked_arr)
                blended_mask = QPixmap.fromImage(QImage(blended_mask))
                self.wg.lbl_blending_img.removeItem(self.wg.lbl_blending_img.items()[0])
                self.wg.lbl_blending_img.addPixmap(blended_mask)
            else:
                self.wg.lbl_blending_img.removeItem(self.wg.lbl_blending_img.items()[0])
                self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
        except:
            return

    def addMask(self):
        try:
            self.mask_arrList[self.cur_idx].append(np.zeros((self.Nx, self.Ny)))
            self.mask_imgList[self.cur_idx].append(qimage2ndarray.array2qimage(np.zeros((self.Nx, self.Ny, 4))))
            self.wg.maskComboBox.addItem('Mask' + str(len(self.mask_imgList[self.cur_idx])))
            self.maskComboBoxActivated(len(self.mask_imgList[self.cur_idx])-1)
            self.wg.maskComboBox.setCurrentIndex(len(self.mask_imgList[self.cur_idx])-1)
        except:
            return

    def deleteMask(self): ##
        try:
            if len(self.mask_arrList[self.cur_idx]) > 1:
                del self.mask_arrList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                del self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                self.wg.maskComboBox.removeItem(self.wg.maskComboBox.currentIndex())
                cur_mask_index = self.wg.maskComboBox.currentIndex()
                self.wg.maskComboBox.clear()
                for i in range(len(self.mask_imgList[self.cur_idx])):
                    self.wg.maskComboBox.addItem('Mask' + str(i + 1))
                self.maskComboBoxActivated(cur_mask_index)
                self.wg.maskComboBox.setCurrentIndex(cur_mask_index)
        except:
            return

    def maskComboBoxActivated(self, index): ##
        self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][index]))
        self.drawn_arrList = [qimage2ndarray.byte_view(self.mask_imgList[self.cur_idx][index])]
        self.refreshMaskView()
        if self.wg.maskCheckBox.isChecked(): self.wg.maskCheckBox.toggle()
        if self.wg.blendCheckBox.isChecked(): self.wg.blendCheckBox.toggle()

    def rgb2gray(self, rgb):
        return np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    def bgra2rgba(self, bgra):
        rgba = bgra.copy()
        rgba[:, :, 0], rgba[:, :, 2] = bgra[:, :, 2], bgra[:, :, 0]
        
        return rgba

    def refreshMaskView(self):
        self.wg.lbl_blending_img.clear()
        self.wg.lbl_blending_img.addPixmap(QPixmap.fromImage(QImage(self.cur_image)))
        self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    def setPenSize(self, text):
        self.pen_size = int(text)

    def saveCurrentMasks(self):
        try:
            save_dir = QFileDialog.getExistingDirectory(self, "Save Current Masks")
            save_new_dir = save_dir + '/' + self.file_names[self.cur_idx]
            os.mkdir(save_new_dir)
            for i in range(len(self.mask_arrList[self.cur_idx])):
                np.save(save_new_dir + '/' + self.file_names[self.cur_idx] + '_mask_{}.npy'.format(i + 1), \
                    self.mask_arrList[self.cur_idx][i])
        except:
            return

    def saveAllMasks(self):
        try:
            save_new_dir = self.folder_path + '/Masks'
            os.mkdir(save_new_dir)
            for i in range(len(self.mask_arrList)):
                for j in range(len(self.mask_arrList[i])):
                    np.save(save_new_dir + '/' + self.file_names[i] + '_mask_{}.npy'.format(j + 1), \
                        self.mask_arrList[i][j])
        except:
            return 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
    
