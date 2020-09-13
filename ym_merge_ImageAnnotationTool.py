'''
영민
이전, 다음, 다이얼로그 버튼 (버튼 변수명 변경, 생성 및 초기화 위치 변경)
폴더 경로 불러오기 추가
'''

import sys
from PyQt5.QtWidgets import (QApplication, QLabel, QMainWindow, QWidget, QHBoxLayout,\
    QVBoxLayout, QAction, QFileDialog, QGraphicsView, QGraphicsScene, QCheckBox, QComboBox, QPushButton,\
         QInputDialog)
from PyQt5.QtGui import QPixmap, QIcon, QImage, QWheelEvent, QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPoint

import pydicom # DICOM파일(국제 표준에 따라 생성된 메디컬 이미지 파일)을 
               # 가져오기 위해 python packages 중 하나인 pydicom을 import
import numpy as np
import SimpleITK as itk # SimpleITK로부터 itk(이미지 분할 및 이미지 등록 플랫폼)을 import
import qimage2ndarray # Qimages와 numpy.ndarrays를 빠르게 변환하기위해 qimage2ndarray를 import
import math

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

        self.addMaskBtn = QPushButton('&Add Mask', self)
        self.maskComboBox = QComboBox(self)
        self.drawCheckBox = QCheckBox('Draw', self)
        self.maskCheckBox = QCheckBox('Masking', self)
        self.blendCheckBox = QCheckBox('Blended Mask on', self)
        # 영민 
        # 버튼 변수명, 생성위치 변경
        self.dialogBtn = QPushButton('&ImgNum', self)  
        self.previousBtn = QPushButton('&previous', self)
        self.nextBtn = QPushButton('&next', self)
        # 단축키
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
        self.hOptionbox.addWidget(self.drawCheckBox)
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
        
        #지현
        self.LRpoint = [0, 0] # window_level, window_width설정을 위한 기준점을 0으로 설정
        self.LRClicked = False # 두 버튼 모두 눌림 여부 확인 / 마우스 동시 클릭을 토글로 설정하기 위한 전 처리
        self.window_level = 40 # 기준으로 값을 넣음
        self.window_width = 400 # 기준으로 값을 넣음
        self.deltaWL = 0
        self.deltaWW = 0

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
        self.isOpened = False
        self.drawing = False
        self.lastPoint = QPoint()
        self.mask_arrList = []
        self.mask_imgList = []
        self.drawn_imgList = []

        self.wg = MyWidget() 
        # wg = MyWidget2() # placeholder -- QWidget 상속하여 만든것으로 추후 교체하면 됨. 
        self.setCentralWidget(self.wg) # 반드시 필요함.
        self.initUI()

        self.openImage()
        
    def initUI(self):
        # file open Action===> 툴바로부터 파일을 여는 액션을 생성
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
        # self.wg.keyPressEvent = self.keyPressEvent
        self.wg.view_1.setMouseTracking(True)
        self.wg.view_2.setMouseTracking(True)
        
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

        # 출력 refresh함수로 대체
        self.refresh()

        '''
        ###########질문########
        # if self.cur_idx == -1: #self.cur_idx가 -1,즉 num이 0을 받아온 상황에서의 조건 생성 중....
        #     QMessageBox.about(self, "메세지", "no")

        cur_image = self.EntireImage[self.cur_idx] #cur_idx값을 EntireImage를 통해 cur_image에 넣기
        
        self.cur_img_arr = self.AdjustPixelRange(cur_image, self.window_level, self.window_width) #지현
        # cur_image와 window_level, window_width를 AdgustPixelRange함수에 통과시켜 image에 넣기
        self.cur_image = qimage2ndarray.array2qimage(self.cur_img_arr) # 통과시킨 imaeg를 Qimage로 전환
        cur_image = QPixmap.fromImage(QImage(self.cur_image)) #Qimage 형태인 image를 받아 fromImage매소드를 써서 QPixmap(이미지를 보여줄때 쓰는 객체, 포맷들을 지원)
                                #QImage=Qpaint를 사용하거나 이미지 필셀조작
                                #QPixmap= 기존 이미지를 반복해서 그릴 때
        self.wg.lbl_original_img.addPixmap(cur_image) #original_img = 왼쪽 화면
        self.wg.lbl_blending_img.addPixmap(cur_image) #blending_img = 오른쪽 화면
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        self.wg.view_1.show()
        self.wg.view_2.show()
        '''

    def onChanged(self, text):
        self.lbl.setText(text)
        self.lbl.adjustSize()


    def refresh(self):
        self.wg.maskComboBox.clear()
        for i in range(len(self.mask_imgList[self.cur_idx])):
            self.wg.maskComboBox.addItem('Mask' + str(i + 1))

        # 왼쪽 원본
        cur_image = self.EntireImage[self.cur_idx]
        self.cur_img_arr = self.AdjustPixelRange(cur_image, self.window_level, self.window_width) #지현
        self.cur_image = qimage2ndarray.array2qimage(self.cur_img_arr)
        cur_image = QPixmap.fromImage(QImage(self.cur_image))

        #왼쪽 프레임 이미지 업데이트 필요
        self.wg.lbl_original_img.addPixmap(cur_image)
        self.wg.lbl_blending_img.addPixmap(cur_image)
        self.wg.view_1.setScene(self.wg.lbl_original_img)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)

        # 오른쪽 마스크
        self.cur_maskPixmap = QPixmap.fromImage(\
            QImage(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]))

        self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    #종엄
    #btn1이 버튼 클릭으로부터 호출 할 btn1_clicked함수 선언
    # 영민 - 가독성을 위한 함수명 변경
    def previousBtn_clicked(self):
        #QMessageBox.about(self, "메세지", "이전")
        self.cur_idx = self.cur_idx - 1 # 현재 인덱스에 1을 빼서 cur_idx에 넣기
                
        if self.cur_idx < 0: 
            self.cur_idx = 0 #0보다 작으면 0으로 남기
            
        print("left and image", self.cur_idx +1)

        # 출력 refresh함수로 대체
        self.refresh()

    #종엄
    #btn2이 버튼 클릭으로부터 호출 할 btn2_clicked함수 선언
    # 영민 - 가독성을 위한 함수명 변경
    def nextBtn_clicked(self):
        #QMessageBox.about(self, "메세지", "다음")

        self.cur_idx = self.cur_idx + 1 # 현재 인덱스에서 1을 더해서 cur_idx에 넣기

        if self.cur_idx > self.NofI-1:
            self.cur_idx = self.NofI-1 #223보다 크면 223으로 남기

        print("right and image=", self.cur_idx +1)

        # 출력 refresh함수로 대체
        self.refresh()

    def AdjustPixelRange(self, image, level, width): #지현
        Lower = level - (width/2.0)
        Upper = level + (width/2.0)
    
        range_ratio = (Upper - Lower) / 256.0

        img_adjusted = (image - Lower)/range_ratio
        image = img_adjusted.clip(0, 255)

        return image
    
    def openImage(self):
        folder_path = str(QFileDialog.getExistingDirectory(self, "Select Directory", './'))
        print("open", folder_path)
        # folder_path = "C:\Project\label"

        if folder_path == "":
            return

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

        self.mask_arrList = [[np.zeros((self.Nx, self.Ny))] for _ in range(self.NofI)]
        self.mask_imgList = [[qimage2ndarray.array2qimage(np.zeros((self.Nx, self.Ny, 4)))] for _ in range(self.NofI)]
        # self.mask_imgList = \
        #     [[qimage2ndarray.array2qimage(\
        #         self.AdjustPixelRange(self.EntireImage[idx], self.window_level, self.window_width))] \
        #             for idx in range(self.NofI)]

        # 출력 refresh함수로 대체
        self.refresh()

        self.isOpened = True

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

    def mouseMoveEvent(self, event):
        txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
        self.wg.lbl_pos.setText(txt)
        self.wg.lbl_pos.adjustSize()
        # 지현
        if self.LRClicked:
            # 기준점
            rX = np.array(self.LRpoint[0]) #기준점
            rY = np.array(self.LRpoint[1])
            
            # 현재
            mX = event.globalX()
            mY = event.globalY()

            square = (rX - mX)*(rX - mX) + (rY - mY)*(rY - mY)
            dist = math.sqrt(square)

            # window_level 설정
            if rX < mX: # X축 기준 오른쪽 
                self.deltaWL  = dist
                
            else: # X축 기준 왼쪽부분
                self.deltaWL  = -dist

            # window_width 설정
            if rY < mY: # Y축 기준 아래부분     
                self.deltaWW = -dist

            else: # Y축 기준 윗부분
                self.deltaWW = dist

            # 기존의 self.window_level, self.window_width에서 움직인 만큼의 self.deltaWL, self.deltaWW를 더해줌
            self.window_level = self.window_level + self.deltaWL
            self.window_width = self.window_width + self.deltaWW

            # 현재의 window_width의 값이 0보다 작아지면 0으로 설정
            if self.window_width <= 0:
                self.window_width = 0
            elif self.window_width > 900:
                self.window_width = 900

            if self.window_level < -250:
                self.window_level = -250
            elif self.window_level > 100:
                self.window_level = 100

            print ("window_level, width",self.window_level, self.window_width)
            print ("delta_level, width",self.deltaWL, self.deltaWW)
            self.refresh()
        
        # 영민
        if self.drawing and self.isOpened and self.wg.drawCheckBox.isChecked():
            painter = QPainter(self.cur_maskPixmap)
            painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
            painter.drawLine(self.lastPoint, event.pos())
            # painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
            # painter.drawEllipse(event.pos(), 1, 1)
            self.lastPoint = event.pos()
            self.update()
            self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
        
        self.lastPoint = event.pos()

    def mousePressEvent(self, event):
        if self.isOpened:
            # 지현
            if event.buttons () == Qt.LeftButton | Qt.RightButton:
                # 마우스 동시 클릭을 토글로 설정함. (mouseReleaseEvent 인식을 안함)
                if self.LRClicked == False: # 
                    self.LRClicked = True
                    x = event.globalX()
                    y = event.globalY()

                    self.LRpoint = [x, y]
            
                else:
                    self.LRClicked = False
                
                print("mousePressEvent")
                print("Mouse 클릭한 글로벌 좌표: x={0},y={1}".format(event.globalX(), event.globalY()))

            # 영민
            if event.button() == Qt.LeftButton:
                self.drawing = True

    # 영민
    def mouseReleaseEvent(self, event):
        if self.isOpened:
            if event.button() == Qt.LeftButton:
                if self.drawing:
                    self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()] = \
                        self.cur_maskPixmap.toImage()
                    self.drawn_imgList.append(qimage2ndarray.rgb_view(self.cur_maskPixmap.toImage()))
                self.drawing = False
        
    # 영민
    def onMasking(self, state):
        if self.isOpened:
            if Qt.Checked == state:
                origin_qimg = self.cur_image
                masked_qimg = self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                
                origin_arr = qimage2ndarray.rgb_view(origin_qimg)
                masked_arr = qimage2ndarray.alpha_view(masked_qimg)

                height = origin_arr.shape[0]
                width = origin_arr.shape[1]
                channel = origin_arr.shape[2]

                temp = np.zeros((height, width, channel))
                for i in range(height):
                    for j in range(width):
                        if masked_arr[i, j] != 0:
                        # check = origin_arr[i, j] != masked_arr[i, j]
                        # if True in check:
                            temp[i, j] = origin_arr[i, j]
                            self.mask_arrList[self.cur_idx][self.wg.maskComboBox.currentIndex()][i, j] = \
                                self.wg.maskComboBox.currentIndex() + 1
                
                # gray = self.rgb2gray(temp)
                # mask = mask.astype(np.int32)
                # np.savetxt('mask{}.csv'.format(self.wg.maskComboBox.currentIndex() + 1), mask, fmt='%d', delimiter=',')
                self.masked_arr = temp
                self.masked_qimg = qimage2ndarray.array2qimage(self.masked_arr)
                self.masked_pixmap = QPixmap.fromImage(QImage(self.masked_qimg))

                self.wg.lbl_blending_img.addPixmap(self.masked_pixmap)
            else:
                self.refresh()
                # self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    # 영민
    # 추후 수정 필요
    def showBlendedMask(self, state):
        if self.isOpened:
            if Qt.Checked == state:
                origin_qimg = self.cur_image
                masked_qimg = self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]
                
                origin_arr = qimage2ndarray.byte_view(origin_qimg)
                masked_arr = qimage2ndarray.byte_view(masked_qimg)

                blended_arr = origin_arr + masked_arr * 0.5
                blended_mask = qimage2ndarray.array2qimage(blended_arr)
                blended_mask = QPixmap.fromImage(QImage(blended_mask))
                self.wg.lbl_blending_img.addPixmap(blended_mask)
            else:
                self.refresh()
                # self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)

    # 영민
    def addMask(self):
        if self.isOpened:
            self.mask_arrList[self.cur_idx].append(np.zeros((self.Nx, self.Ny)))
            self.mask_imgList[self.cur_idx].append(qimage2ndarray.array2qimage(self.cur_img_arr.copy()))
            self.wg.maskComboBox.addItem('Mask' + str(len(self.mask_imgList[self.cur_idx])))
            self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][self.wg.maskComboBox.currentIndex()]))

    # 영민
    def maskComboBoxActivated(self, index):
        self.cur_maskPixmap = QPixmap.fromImage(QImage(self.mask_imgList[self.cur_idx][index]))
        self.wg.lbl_blending_img.addPixmap(self.cur_maskPixmap)
        self.wg.view_2.setScene(self.wg.lbl_blending_img)
        if self.wg.maskCheckBox.isChecked(): self.wg.maskCheckBox.toggle()
        if self.wg.blendCheckBox.isChecked(): self.wg.blendCheckBox.toggle()

    # 영민
    def rgb2gray(self, rgb):
        return np.dot(rgb[...,:3], [0.2989, 0.5870, 0.1140])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
