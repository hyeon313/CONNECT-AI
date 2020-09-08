import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QAction, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt


class MyWidget(QWidget): 
    def __init__(self): 
        super().__init__() 
        self.lbl_original_img = QLabel()
        self.lbl_blending_img = QLabel()
        self.lbl_original_img.setStyleSheet("border-style: solid;""border-width: 2px;")
        self.lbl_pos = QLabel()
        self.lbl_pos.setAlignment(Qt.AlignCenter)
        
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.lbl_original_img)
        self.hbox.addWidget(self.lbl_blending_img)
        
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
        self.wg = MyWidget() 
        # wg = MyWidget2() # placeholder -- QWidget 상속하여 만든것으로 추후 교체하면 됨. 
        self.setCentralWidget(self.wg) # 반드시 필요함.
        self.initUI()
        
    def initUI(self):
        
        openAction = QAction(QIcon('exit.png'), 'Open', self)
        openAction.triggered.connect(self.openImage)
        self.toolbar = self.addToolBar('Open')
        self.toolbar.addAction(openAction)
        
        self.setWindowTitle('Test Image')

        self.setGeometry(300, 300, 300, 200)
#         self.move(300, 300)
        self.show()
    
    def openImage(self):
        imagePath, _ = QFileDialog.getOpenFileName()
        original_img = QPixmap(imagePath)
        blending_img = QPixmap(imagePath)
        
        self.wg.lbl_original_img.setPixmap(original_img)
        self.wg.lbl_blending_img.setPixmap(blending_img)
        
        self.wg.lbl_original_img.mouseMoveEvent = self.mouseMoveEvent
        self.wg.lbl_blending_img.mouseMoveEvent = self.mouseMoveEvent
        
        self.wg.lbl_original_img.setMouseTracking(True)
        self.wg.lbl_blending_img.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        txt = "Mouse 위치 ; x={0},y={1}".format(event.x(), event.y()) 
        self.wg.lbl_pos.setText(txt)
        self.wg.lbl_pos.adjustSize()
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())