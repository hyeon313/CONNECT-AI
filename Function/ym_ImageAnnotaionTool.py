import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
    QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox, QPushButton,\
         QInputDialog)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QWheelEvent, QPainter, QPen, QBrush, QCursor
from PyQt5.QtCore import Qt, QPoint, QRect, QSize

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

        self.addMaskBtn = QPushButton('&Add Mask', self)
        self.maskComboBox = QComboBox(self)
        self.maskCheckBox = QCheckBox('Masking', self)
        self.blendCheckBox = QCheckBox('Blended Mask on', self)

        self.dialogBtn = QPushButton('&ImgNum', self)  
        self.previousBtn = QPushButton('&previous', self)
        self.nextBtn = QPushButton('&next', self)

        self.previousBtn.setShortcut('Ctrl+1')
        self.nextBtn.setShortcut('Ctrl+2')

        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hViewbox = QHBoxLayout()
        self.hViewbox.addWidget(self.view_1)
        self.hViewbox.addWidget(self.view_2)

        self.hOptionbox = QHBoxLayout()
        self.hOptionbox.addWidget(self.addMaskBtn)
        self.hOptionbox.addWidget(self.maskComboBox)
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
        self.wg = MyWidget() 
        self.setCentralWidget(self.wg)
        self.initUI()
        
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

        self.isOpened = False
        self.drawing = False
        self.lastPoint = QPoint()
        self.mask_arrList = []
        self.mask_imgList = []
        self.drawn_arrList = []
        self.onCtrl = False
        self.onShift = False
        
    def initUI(self):
        openAction = QAction(QIcon('exit.png'), 'Open', self)
        openAction.triggered.connect(self.openImage)

        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openAction)
        
        self.wg.addMaskBtn.clicked.connect(self.addMask)
        self.wg.maskCheckBox.stateChanged.connect(self.onMasking)
        self.wg.blendCheckBox.stateChanged.connect(self.showBlendedMask)
        self.wg.maskComboBox.activated.connect(self.maskComboBoxActivated)

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

        # self.wg.view_1.keyPressEvent = self.mousePressEvent
        # self.wg.view_1.keyReleaseEvent = self.mouseReleaseEvent
        self.wg.view_2.keyPressEvent = self.keyPressEvent
        self.wg.view_2.keyReleaseEvent = self.keyReleaseEvent

        # self.wg.wheelEvent = self.wheelEvent
        
        self.setWindowTitle('Test Image')
        self.setGeometry(300, 300, 1100, 600)
        self.show()
    
    def openImage(self):
        try:
            folder_path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
            reader = itk.ImageSeriesReader() 
            dicom_names = reader.GetGDCMSeriesFileNames(folder_path)
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

    def showDialog(self):
        if self.isOpened:
            num, ok = QInputDialog.getInt(self, 'Input ImageNumber', 'Enter Num')
            self.cur_idx = num - 1
            print("show image",self.cur_idx + 1)
            if self.cur_idx > self.NofI-1:
                self.cur_idx = self.NofI-1
            elif self.cur_idx < 0:
                self.cur_idx = self.NofI-224
            self.refresh()

    def refresh(self):
        self.drawn_arrList = [np.zeros((self.Nx, self.Ny, 4))]

        self.wg.maskComboBox.clear()
        for i in range(len(self.mask_imgList[self.cur_idx])):
            self.wg.maskComboBox.addItem('Mask' + str(i + 1))

        cur_image = self.EntireImage[self.cur_idx]
        self.cur_img_arr = self.AdjustPixelRange(cur_image, self.window_level, self.window_width) #지현
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

        self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    def previousBtn_clicked(self):
        if self.isOpened:
            self.cur_idx = self.cur_idx - 1
            if self.cur_idx < 0: self.cur_idx = 0
            self.refresh()

    def nextBtn_clicked(self):
        if self.isOpened:
            self.cur_idx = self.cur_idx + 1
            if self.cur_idx > self.NofI-1: self.cur_idx = self.NofI-1
            self.refresh()

    def AdjustPixelRange(self, image, level, width):
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
        range_ratio = (Upper - Lower) / 256.0
        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)
        return image
    
    def wheelEvent(self, event):
        if self.isOpened:
            n_scroll = int(event.angleDelta().y() / 120)
            
            self.cur_idx = self.cur_idx + n_scroll
            if self.cur_idx < 0:
                self.cur_idx = 0
            if self.cur_idx > self.NofI-1:
                self.cur_idx = self.NofI-1
            self.refresh() 

    def mouseMoveEvent(self, event):
        txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
        self.wg.lbl_pos.setText(txt)
        self.wg.lbl_pos.adjustSize()
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
        
        if self.drawing and self.isOpened:
            painter = QPainter(self.cur_maskPixmap)
            painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
            if self.onCtrl:
                painter.drawLine(self.lastPoint, event.pos())
            if self.onShift:
                r = QRect(self.lastPoint, 10 * QSize())
                r.moveCenter(event.pos())
                # QCursor.setShape(r)
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.eraseRect(r)
            self.update()
            self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
        
        self.lastPoint = event.pos()


    def mousePressEvent(self, event):
        if self.isOpened:
            if event.buttons () == Qt.LeftButton | Qt.RightButton:
                if self.LRClicked == False: 
                    self.LRClicked = True
                    x = event.globalX()
                    y = event.globalY()

                    self.LRpoint = [x, y]
            
                else:
                    self.LRClicked = False
                
                print("Mouse 클릭한 글로벌 좌표: x={0},y={1}".format(event.globalX(), event.globalY()))

            if event.button() == Qt.LeftButton:
                self.drawing = True

    def mouseReleaseEvent(self, event):
        if self.isOpened:
            if event.button() == Qt.LeftButton:
                self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()] = \
                    self.cur_maskPixmap.toImage()
                self.drawn_arrList.append(qimage2ndarray.byte_view(self.cur_maskPixmap.toImage()))
                self.wg.lbl_blending_img.clear()
                self.wg.lbl_blending_img.addPixmap(QPixmap.fromImage(QImage(self.cur_image)))
                self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
                self.drawing = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.onCtrl = True
        if event.key() == Qt.Key_Shift:
            self.onShift = True
        if self.onCtrl and event.key() == Qt.Key_Z:
            self.erasePreviousLine()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.onCtrl = False
        if event.key() == Qt.Key_Shift:
            self.onShift = False
        
    def erasePreviousLine(self):
        if len(self.drawn_arrList) > 1:
            del self.drawn_arrList[len(self.drawn_arrList)-1]
            temp = self.bgra2rgba(self.drawn_arrList[len(self.drawn_arrList)-1])
            print(len(self.drawn_arrList))
            self.cur_maskPixmap = QPixmap.fromImage(QImage(qimage2ndarray.array2qimage(temp)))
            self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()] = \
                self.cur_maskPixmap.toImage()
            self.wg.lbl_blending_img.clear()
            self.wg.lbl_blending_img.addPixmap(QPixmap.fromImage(QImage(self.cur_image)))
            self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    def onMasking(self, state):
        if self.isOpened:
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
                
    def showBlendedMask(self, state):
        if self.isOpened:
            if Qt.Checked == state:
                origin_qimg = self.cur_image
                masked_qimg = self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                
                origin_arr = qimage2ndarray.rgb_view(origin_qimg)
                masked_arr = qimage2ndarray.rgb_view(masked_qimg)
                masked_alpha_arr = qimage2ndarray.alpha_view(masked_qimg)

                channel = origin_arr.shape[2]
                temp = np.zeros((self.Nx, self.Ny, channel))

                for i in range(self.Nx):
                    for j in range(self.Ny):
                        if masked_alpha_arr[i, j] != 0:
                            temp[i, j] = origin_arr[i, j] * 0.5 + masked_arr[i, j] * 0.5
                        else:
                            temp[i, j] = origin_arr[i, j]

                blended_arr = temp
                blended_mask = qimage2ndarray.array2qimage(blended_arr)
                blended_mask = QPixmap.fromImage(QImage(blended_mask))
                self.wg.lbl_blending_img.addPixmap(blended_mask)
            else:
                self.wg.lbl_blending_img.removeItem(self.wg.lbl_blending_img.items()[0])

    def addMask(self):
        if self.isOpened:
            self.mask_arrList[self.cur_idx].append(np.zeros((self.Nx, self.Ny)))
            self.mask_imgList[self.cur_idx].append(qimage2ndarray.array2qimage(np.zeros((self.Nx, self.Ny, 4))))
            self.wg.maskComboBox.addItem('Mask' + str(len(self.mask_imgList[self.cur_idx])))
            # self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]))
            # self.maskComboBoxActivated(len(self.mask_imgList[self.cur_idx])-1)
            self.wg.maskComboBox.setCurrentIndex(len(self.mask_imgList[self.cur_idx])-1)

    # def deleteMask(self):
    #     if self.isOpened:
    #         self.mask_arrList[self.cur_idx].append(np.zeros((self.Nx, self.Ny)))
    #         self.mask_imgList[self.cur_idx].append(qimage2ndarray.array2qimage(self.cur_img_arr.copy()))
    #         self.wg.maskComboBox.addItem('Mask' + str(len(self.mask_imgList[self.cur_idx])))
    #         self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]))

    def maskComboBoxActivated(self, index):
        self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][index]))
        self.refresh()
        if self.wg.maskCheckBox.isChecked(): self.wg.maskCheckBox.toggle()
        if self.wg.blendCheckBox.isChecked(): self.wg.blendCheckBox.toggle()

    def rgb2gray(self, rgb):
        return np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

    def bgra2rgba(self, bgra):
        rgba = bgra.copy()
        rgba[:, :, 0], rgba[:, :, 2] = bgra[:, :, 2], bgra[:, :, 0]
        
        return rgba

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
