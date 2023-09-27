import cv2
import mediapipe as mp
from pynput.keyboard import Key, Controller
import numpy as np
from mediapipe.python.solutions.drawing_utils import DrawingSpec
from PyQt5.QtMultimedia import QCameraInfo

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

import webbrowser
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal 
import  numpy
from PyQt5.QtGui import QIcon
# import device
import cv2, queue, threading, time
import time
from pynput.keyboard import Key, Controller
import math
#import dlib
import ctypes, sys

print("Starting....")
exename = sys.argv[0]

def hideConsole():
    """
    Hides the console window in GUI mode. Necessary for frozen application, because
    this application support both, command line processing AND GUI mode and theirfor
    cannot be run via pythonw.exe.
    """

    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)
        # if you wanted to close the handles...
        #ctypes.windll.kernel32.CloseHandle(whnd)

def showConsole():
    """Unhides console window"""
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 1)
if(not "_console.exe" in exename):
    hideConsole()

class ComboBox(QtWidgets.QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()

class VideoCapture:
    def __init__(self, name):
        self.running = True
        self.cap = cv2.VideoCapture(name)
        codec = 0x47504A4D  # MJPG
        self.cap.set(cv2.CAP_PROP_FPS, 30.0)
        #self.cap.set(cv2.CAP_PROP_FOURCC, codec)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)    
            
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()
        self.ret=True
        
    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while (self.running):
            ret, frame = self.cap.read()
            self.ret = ret
            if ret == False: break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass

            self.q.put(frame)
            #self.q.put(cv2.rotate(frame, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE) )

        self.ret=False

    def read(self):
        if(self.ret==False ):
            return self.ret, ""
        return self.ret, self.q.get()

    def close(self):
        print("close 1")
        self.cap.release()
        print("close 2")
        self.running =False
    def changeCap(self,indx):
        self.cap.release()
        name=indx
        self.cap=cv2.VideoCapture(name)


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(numpy.ndarray)
    
    def changeCap(self,cap,mw):
        self.cap=cap
        self.running = True
        self.ui = mw
        self.pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) 

    def done(self):
        self.running=False
        self.cap.running =False
        self.cap.close()
        self.finished.emit()

    def run(self):
        """Long-running task."""
        while self.running:
            #time.sleep(1)
            try:
                ret, image = self.cap.read()
                if(not ret):
                    self.running = False
                if(ret):
                    if( self.ui.checkBox_flipImage.isChecked()):
                        image = cv2.flip(image, 1)
                    rot = self.ui.rotateIndx
                    for i in range(rot):
                        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    height, width, channel = image.shape
                    quality = float (self.ui.spinbox_quality.value())/10.0
                    image=cv2.resize(image, ( int(width*quality), int(height*quality) ), interpolation = cv2.INTER_AREA)

                    if( self.ui.checkBox_startTracker.isChecked() ): 
                        image.flags.writeable = False
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        results = self.pose.process(image)
                        # Draw the pose annotation on the image.
                        image.flags.writeable = True	
                        self.ui.results=results
                        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                    self.progress.emit(image)
            except:
                pass

        self.done()
        # self.finished.emit()
        

class Ui_MainWindow(QtWidgets.QMainWindow):
    def setupUi(self):
        self.results =""
        self.state=["front","upright","center"]
        self.rotateIndx = 0
        self.keyboard = Controller()
        self.image=[[["","",""]]]
        self.cap =VideoCapture(0)
        self.width=320
        self.height = 350
        self.device_list = self.get_devices()
        self.camIndex =0
        self.space=False
        self.right=False
        self.left=False

        self.style = mp_drawing_styles.get_default_pose_landmarks_style()
        empty = DrawingSpec(color=(0, 0, 0), thickness=-1,circle_radius=0)
        faceList=[mp_pose.PoseLandmark.NOSE,mp_pose.PoseLandmark.RIGHT_EYE_INNER,mp_pose.PoseLandmark.RIGHT_EYE, mp_pose.PoseLandmark.RIGHT_EYE_OUTER,mp_pose.PoseLandmark.RIGHT_EAR,mp_pose.PoseLandmark.MOUTH_RIGHT,mp_pose.PoseLandmark.LEFT_EYE_INNER,mp_pose.PoseLandmark.LEFT_EYE, mp_pose.PoseLandmark.LEFT_EYE_OUTER,mp_pose.PoseLandmark.LEFT_EAR,mp_pose.PoseLandmark.MOUTH_LEFT]		
        for ele in faceList:
            self.style[ele]=empty


        self.setObjectName("MainWindow")
        self.setWindowIcon(QIcon('logo.png'))
        self.resize(self.width, self.height)
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, self.width, self.height))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_usedCam = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_usedCam.setObjectName("label_usedCam")
        self.label_usedCam.setMaximumHeight(15)
        self.label_usedCam.setMinimumHeight(15)
        self.label_usedCam.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label_usedCam)
        self.dropDown_camera = ComboBox(self.verticalLayoutWidget)
        self.dropDown_camera.setObjectName("dropDown_camera")
        self.verticalLayout.addWidget(self.dropDown_camera)
        self.dropDown_camera.addItems(self.device_list)  
        self.dropDown_camera.popupAboutToBeShown.connect(self.updateCamList)
        self.dropDown_camera.currentIndexChanged.connect(self.camChanged)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


        ##line 1
        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout_1)
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")
        #flipbox
        self.checkBox_flipImage = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_flipImage.setObjectName("checkBox_flipImage")
        self.horizontalLayout_1.addWidget(self.checkBox_flipImage)
        #rotate
        self.pushButton_rotate = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.pushButton_rotate.setObjectName("pushButton_rotate")
        self.pushButton_rotate.setText("Rotate")
        self.pushButton_rotate.clicked.connect(self.rotate)
        self.horizontalLayout_1.addWidget(self.pushButton_rotate)
        #showlines
        self.checkBox_showLines = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_showLines.setObjectName("checkBox_showLines")
        self.horizontalLayout_1.addWidget(self.checkBox_showLines)
        #quality spinbox
        self.spinbox_quality = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_quality.setRange(1,10)
        self.spinbox_quality.setValue(10)
        self.horizontalLayout_1.addWidget(self.spinbox_quality)
        self.label_quality = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_quality.setObjectName("label_quality")
        self.label_quality.setText("Quality")
        self.label_quality.setMinimumHeight(15)
        self.horizontalLayout_1.addWidget(self.label_quality)
        #start tracker
        self.checkBox_startTracker = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_startTracker.setObjectName("checkBox_startTracker")
        self.horizontalLayout_1.addWidget(self.checkBox_startTracker)


        ##line 2
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        #checkbox position
        self.checkBox_usePos = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_usePos.setObjectName("checkBox_usePos")
        self.horizontalLayout_2.addWidget(self.checkBox_usePos)
        #left spinbox
        self.spinbox_left = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_left.setRange(0,100)
        self.spinbox_left.setValue(35)
        self.horizontalLayout_2.addWidget(self.spinbox_left)
        self.label_left = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_left.setObjectName("label_left")
        self.label_left.setText("Left Line")
        self.label_left.setMinimumHeight(15)
        self.label_left.setMaximumHeight(15)
        self.horizontalLayout_2.addWidget(self.label_left)
        #right spinbox
        self.spinbox_right = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_right.setRange(0,100)
        self.spinbox_right.setValue(65)
        self.horizontalLayout_2.addWidget(self.spinbox_right)
        self.label_right = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_right.setObjectName("label_right")
        self.label_right.setText("Right Line")
        self.label_right.setMinimumHeight(15)
        self.label_right.setMaximumHeight(15)
        self.horizontalLayout_2.addWidget(self.label_right)		
        #bot spinbox
        self.spinbox_bot = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_bot.setRange(0,100)
        self.spinbox_bot.setValue(30)
        self.horizontalLayout_2.addWidget(self.spinbox_bot)
        self.label_bot = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_bot.setObjectName("label_bot")
        self.label_bot.setText("Bottom Line")
        self.label_bot.setMinimumHeight(15)
        self.label_bot.setMaximumHeight(15)		
        self.horizontalLayout_2.addWidget(self.label_bot)

        ##line 3
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")		
        #checkbox arms
        self.checkBox_useArm = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox_useArm.setObjectName("checkBox_useArm")
        self.horizontalLayout_3.addWidget(self.checkBox_useArm)
        #arm spinbox
        self.spinbox_arm = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_arm.setRange(0,180)
        self.spinbox_arm.setValue(30)
        self.horizontalLayout_3.addWidget(self.spinbox_arm)
        self.label_arm = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_arm.setObjectName("label_right")
        self.label_arm.setText("Angle Treshold in Deg")
        self.label_arm.setMinimumHeight(15)
        self.label_arm.setMaximumHeight(15)				
        self.horizontalLayout_3.addWidget(self.label_arm)			
        #body spinbox
        self.spinbox_body = QtWidgets.QSpinBox(self.verticalLayoutWidget)
        self.spinbox_body.setRange(0,90)
        self.spinbox_body.setValue(13)
        self.horizontalLayout_3.addWidget(self.spinbox_body)
        self.label_body = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_body.setObjectName("label_right")
        self.label_body.setText("Body Rotation Treshold in Deg")
        self.label_body.setMinimumHeight(15)
        self.label_body.setMaximumHeight(15)				
        self.horizontalLayout_3.addWidget(self.label_body)	


        self.shameless = QtWidgets.QHBoxLayout()
        self.shameless.addItem(spacerItem)
        self.shamelessLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.shamelessLabel.setText(" Made By ZiedYT")
        self.shamelessYT = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.shamelessYT.setText(" Youtube")
        self.shamelessYT.setIcon(QtGui.QIcon('youtube.png'))
        self.shamelessYT.clicked.connect(lambda: { webbrowser.open('http://youtube.com/ziedyt')  } )
        self.shamelessTwitt = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.shamelessTwitt.setText(" Twitter")
        self.shamelessTwitt.clicked.connect(lambda: { webbrowser.open('https://twitter.com/ZiedYT')  } )
        self.shameless.addWidget(self.shamelessLabel)
        self.shameless.addWidget(self.shamelessYT)
        self.shameless.addWidget(self.shamelessTwitt)
        self.shameless.addItem(spacerItem)
        self.verticalLayout.addLayout(self.shameless)



        self.display = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.display.setObjectName("display")
        self.verticalLayout.addWidget(self.display)
        self.display.setAlignment(QtCore.Qt.AlignCenter)
        self.display.setScaledContents(False)
        self.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 326, 21))
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        
        # if(self.dropDown_camera.count()>1):
        #     self.ipframe.setHidden(True)
        thread = QThread()    
        self.worker = Worker()
        self.worker.changeCap(self.cap,self)
        self.worker.moveToThread(thread)
        thread.started.connect(self.worker.run)
        self.worker.finished.connect(thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        # Step 6: Start the thread
        thread.start()
        self.threads=[]
        self.threads.append(thread)
    def updateCamList(self):
        devices = self.get_devices()
        if(devices == self.device_list ):
            return
        
        camName = self.dropDown_camera.currentText()
        self.device_list = devices.copy()
        self.dropDown_camera.clear()
        self.dropDown_camera.addItems(self.device_list)
        indx = 0
        if(camName in self.device_list):
            indx = self.device_list.index(camName)
        self.dropDown_camera.setCurrentIndex(indx)

    def get_devices(self):
        cameras = []
        camera_infos = QCameraInfo.availableCameras()
        for camera_info in camera_infos:
            cameras.append(camera_info.description())
        return cameras

        
    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Jump(Squat)King"))
        self.label_usedCam.setText(_translate("MainWindow", "Select camera to use:"))
        #self.label_ipcam.setText(_translate("MainWindow", "IP cam:"))
        self.checkBox_flipImage.setText(_translate("MainWindow", "Flip"))
        self.checkBox_usePos.setText(_translate("MainWindow", "Use Position"))
        self.checkBox_useArm.setText(_translate("MainWindow", "Use Arm Angle"))
        self.checkBox_showLines.setText(_translate("MainWindow", "Show Lines"))
        self.checkBox_startTracker.setText(_translate("MainWindow", "Start Tracker"))


    def resizeEvent(self, event):
        print("resize")
        self.width = event.size().width() 
        self.height=event.size().height() 
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, self.width, self.height))
        self.fitImage()
        
    def rotate(self):
        self.rotateIndx =  (self.rotateIndx+1)%4

    def camChanged(self):
        try:
            if(self.camIndex!=self.dropDown_camera.currentIndex()):
                print("1")
                #
                self.worker.running = False
                camIndex = self.dropDown_camera.currentIndex()

                print("2")
                try:
                    self.worker.done()
                    self.threads[-1].exit()
                    self.threads[-1].terminate()
                except:
                    pass
                print("2.5")
                self.cap.close()
                self.cap = VideoCapture(camIndex)

                thread = QThread()    
                self.worker = Worker()
                self.worker.changeCap(self.cap,self)
                self.worker.moveToThread(thread)
                thread.started.connect(self.worker.run)
                self.worker.finished.connect(thread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                thread.finished.connect(thread.deleteLater)
                self.worker.progress.connect(self.reportProgress)
                thread.start()
                self.threads.append(thread)
                print("3")
                # self.ipframe.setHidden(True)
                print("4")
                self.camIndex = camIndex


                    #self.cap =VideoCapture(self.camIndex)
        except:
            self.dropDown_camera.setCurrentIndex(self.camIndex)
            print()

    # def startIPCam(self):
    #     print(self.lineEdit_ipCam.text())
    #     self.cap =VideoCapture(self.lineEdit_ipCam.text())
    #     self.worker.changeCap(self.cap,self)

    def reportProgress(self,ele):
        #print()
        self.image=ele
        self.drawLines()
        self.exCommand()
        self.fitImage()

    def fitImage(self):
        try:
            height, width, channel = self.image.shape
            
            fitwidth = self.display.height()*width/height
            #print("display.width()",self.display.width(),"fitwidth",fitwidth)
            if( self.display.width()<fitwidth ):
                fitwidth = self.display.width()
            
            bytesPerLine = 3 * width
            qImg = QtGui.QImage(self.image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()

            pix = QtGui.QPixmap(qImg)
            pix = pix.scaled(fitwidth,fitwidth*height/width,QtCore.Qt.KeepAspectRatio)

            self.display.setPixmap(pix)
            self.display.show()
        except:
            pass

    def drawLines(self):
        height, width, channel = self.image.shape
        if(self.spinbox_right.value()< self.spinbox_left.value() ):
            self.spinbox_left.setValue( self.spinbox_right.value()) 

        self.leftLineX = (int) ( width*self.spinbox_left.value()/100)
        self.rightLineX = (int) ( width*self.spinbox_right.value()/100)
        self.botLineY = (int) ( height*(100-self.spinbox_bot.value())/100)

        if( not self.checkBox_showLines.isChecked()):
            return

        bottomLineStart =  ( 0,self.botLineY )
        bottomLineEnd =  ( width,self.botLineY )
        self.image = cv2.line(self.image, bottomLineStart, bottomLineEnd, (255,255,0), 2) #bot if self.boxY+self.boxA<Y  


        if(self.checkBox_usePos.isChecked()):
            leftLineStart =  ( self.leftLineX,0 )
            leftLineEnd =  ( self.leftLineX,self.botLineY )
            self.image = cv2.line(self.image, leftLineStart, leftLineEnd, (255,255,0), 2) 

            rightLineStart =  ( self.rightLineX,0 )
            rightLineEnd =  ( self.rightLineX,self.botLineY )
            self.image = cv2.line(self.image, rightLineStart, rightLineEnd, (255,255,0), 2) 


        if(self.checkBox_startTracker and self.results!=""):
            if( self.results.pose_landmarks!= None):
                image_height, image_width, _ = self.image.shape
                x= image_width*(self.results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x + self.results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x)/2
                y=image_height*(self.results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y + self.results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y)/2		
                self.image= cv2.circle(self.image, (int(x),int(y)), 6, (0, 0, 255), 6) 		
                indx=0
                temp=[]
                for res in mp_pose.POSE_CONNECTIONS:
                    if(not indx in [1,7,9,14,21,23,24,30,31]): 
                        temp.append(res)
                    indx+=1		

                mp_drawing.draw_landmarks(
                    self.image,
                    self.results.pose_landmarks,
                    frozenset(temp),
                    landmark_drawing_spec=self.style)


    def getFacing(self,landmarks, poses):
        facing="front"
        tresh = float(self.spinbox_body.value())/90.0
        # print(landmarks[poses.RIGHT_SHOULDER].z - landmarks[poses.LEFT_SHOULDER].z )
        if( landmarks[poses.RIGHT_SHOULDER].z - landmarks[poses.LEFT_SHOULDER].z <= -tresh):
            facing="right"

        elif( landmarks[poses.RIGHT_SHOULDER].z - landmarks[poses.LEFT_SHOULDER].z >= tresh): 
            facing="left"

        #print(facing)
        if(facing!=self.state[0]):
            self.state[0]=facing
            print("facing",self.state[0])

    def getVertical(self,landmarks, poses):
        stance ="upright"
        x= (landmarks[poses.RIGHT_SHOULDER].x + landmarks[poses.LEFT_SHOULDER].x)/2
        y=(landmarks[poses.RIGHT_SHOULDER].y + landmarks[poses.LEFT_SHOULDER].y)/2
        if(y> (100.0-self.spinbox_bot.value())/100.0 ):
            stance ="squat"
        if(stance!=self.state[1]):
            self.state[1]=stance
            print(self.state[1])

    def getHorizontal(self,landmarks, poses):
        move = "center"
        x= (landmarks[poses.RIGHT_SHOULDER].x + landmarks[poses.LEFT_SHOULDER].x)/2
        RIGHT_ANG,LEFT_ANG = self.getAngles(landmarks, poses)
        #print(x)
        if(self.checkBox_usePos.isChecked() and  x<  self.spinbox_left.value()/100.0 ):
            move = "left"
        elif(self.checkBox_usePos.isChecked() and x>  self.spinbox_right.value()/100.0  ):
            move = "right"
        elif(self.state[0]=="front" and self.checkBox_useArm.isChecked() and LEFT_ANG>120 and RIGHT_ANG<120):
            move = "right"
        elif(self.state[0]=="front" and self.checkBox_useArm.isChecked() and LEFT_ANG<120 and RIGHT_ANG>120):
            move = "left"

        if(move!=self.state[2]):
            self.state[2]=move
            print(self.state[2])

    def getAngles(self,landmarks, poses):
        def calculate_angle(a,b,c):
            a = np.array(a) # First
            b = np.array(b) # Mid
            c = np.array(c) # End
            
            radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            angle = np.abs(radians*180.0/np.pi)
            
            if angle >180.0:
                angle = 360-angle
                
            return angle 
        LEFT_shoulder = [landmarks[poses.LEFT_SHOULDER].x,landmarks[poses.LEFT_SHOULDER].y]
        LEFT_elbow = [landmarks[poses.LEFT_ELBOW].x,landmarks[poses.LEFT_ELBOW].y]
        RIGHT_elbow = [landmarks[poses.RIGHT_ELBOW].x,landmarks[poses.RIGHT_ELBOW].y]
        RIGHT_shoulder = [landmarks[poses.RIGHT_SHOULDER].x,landmarks[poses.RIGHT_SHOULDER].y]

        LEFT_ANG=calculate_angle(RIGHT_shoulder,LEFT_shoulder,LEFT_elbow)
        RIGHT_ANG=calculate_angle(LEFT_shoulder,RIGHT_shoulder,RIGHT_elbow)	
        return RIGHT_ANG,LEFT_ANG


    def commands(self,oldstate):
        if(self.isActiveWindow()):
            return
        #jump
        # print(self.state)
        # if(self.state[1]!=oldstate[1]):
        #     if( self.state[1]=="squat"):
        #         self.keyboard.press(Key.space)
        #         if(self.state[0]=="right"):
        #             self.keyboard.press(Key.right)
        #         elif(self.state[0]=="left"):
        #             self.keyboard.press(Key.left)
        #     else:
        #         self.keyboard.release(Key.space)
        #         if(self.state[0]=="right"):
        #             self.keyboard.release(Key.right)
        #         elif(self.state[0]=="left"):
        #             self.keyboard.release(Key.left)	

        # if(self.state[2]!=oldstate[2] and self.state[1]=="upright"):
        #     if( self.state[2]=="right"):
        #         self.keyboard.press(Key.right)
        #     elif( self.state[2]=="left"):
        #         self.keyboard.press(Key.left)
        #     else:
        #         self.keyboard.release(Key.left)	
        #         self.keyboard.release(Key.right)
        

        if(self.state[1]!=oldstate[1]):
            if( self.state[1]=="squat"):
                self.keyboard.press(Key.space)
                if(self.state[0]=="right"):
                    self.keyboard.release(Key.left)	
                    self.keyboard.press(Key.right)
                elif(self.state[0]=="left"):
                    self.keyboard.release(Key.right)
                    self.keyboard.press(Key.left)
            else:
                self.keyboard.release(Key.space)
                self.keyboard.release(Key.right)
                self.keyboard.release(Key.left)	

        if( self.state[1]=="upright"):
            if( self.state[2]=="right"):
                self.keyboard.release(Key.left)
                self.keyboard.press(Key.right)
            elif( self.state[2]=="left"):
                self.keyboard.release(Key.right)
                self.keyboard.press(Key.left)
            else:
                self.keyboard.release(Key.left)	
                self.keyboard.release(Key.right)

        if(self.state[1]=="upright" ):
            self.keyboard.release(Key.space)
      
        if(  self.state[1]=="upright" and self.state[0]=="front" and self.state[2]=="center" ):
            self.keyboard.release(Key.right)
            self.keyboard.release(Key.left)

        # if(self.state[1]=="squat" ):
        #     if(not self.space):
        #         self.keyboard.press(Key.space)
        #         self.space=True

        # if(self.state[1]=="upright" ):
        #     if(self.space):
        #         self.keyboard.release(Key.space)
        #         self.space=False

        # if ( self.state[0] ==  self.state[2]):
        #     if(self.state[0]=="right"):
        #         if(not self.right):
        #             self.keyboard.press(Key.right)
        #             self.right=True

        #         if(self.left):
        #             self.keyboard.release(Key.left)
        #             self.left=False

        #     elif(self.state[0]=="left" ):
        #         if(not self.left):
        #             self.keyboard.press(Key.left)
        #             self.left=True
        #         if(self.right):
        #             self.keyboard.release(Key.right)
        #             self.right=False

        
        # if(self.state[0]=="center" and self.state[2]=="center" ):
        #     if(self.right):
        #         self.keyboard.release(Key.right)
        #         self.right=False
        #     if(self.left):
        #         self.keyboard.release(Key.left)
        #         self.left=False

    def exCommand(self):
        global mp_pose
        if(self.checkBox_startTracker.isChecked()):
            oldstate = self.state[:]
            if( self.results.pose_landmarks!= None):
                self.getFacing(self.results.pose_landmarks.landmark,mp_pose.PoseLandmark)
                self.getVertical(self.results.pose_landmarks.landmark,mp_pose.PoseLandmark)
                self.getHorizontal(self.results.pose_landmarks.landmark,mp_pose.PoseLandmark)
                self.commands(oldstate)
            
    def closeEvent(self, event):
        print("Quit")
        self.keyboard.release(Key.space)	
        self.keyboard.release(Key.left)	
        self.keyboard.release(Key.right)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    #MainWindow = QtWidgets.QMainWindow()
    MW = Ui_MainWindow()
    MW.setupUi()
    MW.show()
    sys.exit(app.exec_())
