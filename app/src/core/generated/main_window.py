# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QTabWidget, QVBoxLayout,
    QWidget)

from core.views.components import (EMGGraphGrid, SerialMonitor)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_3 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.frame_control = QFrame(self.centralwidget)
        self.frame_control.setObjectName(u"frame_control")
        self.frame_control.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_control.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout = QGridLayout(self.frame_control)
        self.gridLayout.setObjectName(u"gridLayout")
        self.duration_frame = QFrame(self.frame_control)
        self.duration_frame.setObjectName(u"duration_frame")
        self.duration_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.duration_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.duration_frame)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_duration = QLabel(self.duration_frame)
        self.label_duration.setObjectName(u"label_duration")

        self.horizontalLayout_5.addWidget(self.label_duration)

        self.doubleSpinBox_duration = QDoubleSpinBox(self.duration_frame)
        self.doubleSpinBox_duration.setObjectName(u"doubleSpinBox_duration")

        self.horizontalLayout_5.addWidget(self.doubleSpinBox_duration)


        self.gridLayout.addWidget(self.duration_frame, 0, 2, 1, 1)

        self.baudrate_frame = QFrame(self.frame_control)
        self.baudrate_frame.setObjectName(u"baudrate_frame")
        self.baudrate_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.baudrate_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.baudrate_frame)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_baudrate = QLabel(self.baudrate_frame)
        self.label_baudrate.setObjectName(u"label_baudrate")

        self.horizontalLayout_8.addWidget(self.label_baudrate)

        self.comboBox_baudrate = QComboBox(self.baudrate_frame)
        self.comboBox_baudrate.setObjectName(u"comboBox_baudrate")

        self.horizontalLayout_8.addWidget(self.comboBox_baudrate)


        self.gridLayout.addWidget(self.baudrate_frame, 0, 1, 1, 1)

        self.port_frame = QFrame(self.frame_control)
        self.port_frame.setObjectName(u"port_frame")
        self.port_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.port_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.port_frame)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.label_port = QLabel(self.port_frame)
        self.label_port.setObjectName(u"label_port")

        self.horizontalLayout_3.addWidget(self.label_port)

        self.comboBox_port = QComboBox(self.port_frame)
        self.comboBox_port.setObjectName(u"comboBox_port")

        self.horizontalLayout_3.addWidget(self.comboBox_port)


        self.gridLayout.addWidget(self.port_frame, 0, 0, 1, 1)

        self.samplingRate_frame = QFrame(self.frame_control)
        self.samplingRate_frame.setObjectName(u"samplingRate_frame")
        self.samplingRate_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.samplingRate_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.samplingRate_frame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.label_samplingRate = QLabel(self.samplingRate_frame)
        self.label_samplingRate.setObjectName(u"label_samplingRate")

        self.horizontalLayout_4.addWidget(self.label_samplingRate)

        self.doubleSpinBox_samplingRate = QDoubleSpinBox(self.samplingRate_frame)
        self.doubleSpinBox_samplingRate.setObjectName(u"doubleSpinBox_samplingRate")

        self.horizontalLayout_4.addWidget(self.doubleSpinBox_samplingRate)


        self.gridLayout.addWidget(self.samplingRate_frame, 1, 0, 1, 1)

        self.frame_actionButtons = QFrame(self.frame_control)
        self.frame_actionButtons.setObjectName(u"frame_actionButtons")
        self.frame_actionButtons.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_actionButtons.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_actionButtons)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_toggleRecording = QPushButton(self.frame_actionButtons)
        self.pushButton_toggleRecording.setObjectName(u"pushButton_toggleRecording")
        self.pushButton_toggleRecording.setAutoFillBackground(False)

        self.horizontalLayout.addWidget(self.pushButton_toggleRecording)

        self.pushButton_saveData = QPushButton(self.frame_actionButtons)
        self.pushButton_saveData.setObjectName(u"pushButton_saveData")

        self.horizontalLayout.addWidget(self.pushButton_saveData)


        self.gridLayout.addWidget(self.frame_actionButtons, 1, 2, 1, 1)

        self.frame_videoCheckbox = QFrame(self.frame_control)
        self.frame_videoCheckbox.setObjectName(u"frame_videoCheckbox")
        self.frame_videoCheckbox.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_videoCheckbox.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_videoCheckbox)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.checkBox_video = QCheckBox(self.frame_videoCheckbox)
        self.checkBox_video.setObjectName(u"checkBox_video")

        self.horizontalLayout_7.addWidget(self.checkBox_video)


        self.gridLayout.addWidget(self.frame_videoCheckbox, 1, 1, 1, 1)


        self.verticalLayout_3.addWidget(self.frame_control)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab_serial = QWidget()
        self.tab_serial.setObjectName(u"tab_serial")
        self.horizontalLayout_2 = QHBoxLayout(self.tab_serial)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.plainTextEdit_serial = SerialMonitor(self.tab_serial)
        self.plainTextEdit_serial.setObjectName(u"plainTextEdit_serial")
        self.plainTextEdit_serial.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.plainTextEdit_serial)

        self.tabWidget.addTab(self.tab_serial, "")
        self.tab_plots = QWidget()
        self.tab_plots.setObjectName(u"tab_plots")
        self.horizontalLayout_6 = QHBoxLayout(self.tab_plots)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.widget_plots = EMGGraphGrid(self.tab_plots)
        self.widget_plots.setObjectName(u"widget_plots")

        self.horizontalLayout_6.addWidget(self.widget_plots)

        self.tabWidget.addTab(self.tab_plots, "")

        self.verticalLayout_3.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        self.menuAbout = QMenu(self.menubar)
        self.menuAbout.setObjectName(u"menuAbout")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuAbout.menuAction())

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_duration.setText(QCoreApplication.translate("MainWindow", u"Duration", None))
        self.label_baudrate.setText(QCoreApplication.translate("MainWindow", u"Baudrate", None))
        self.label_port.setText(QCoreApplication.translate("MainWindow", u"Port", None))
        self.label_samplingRate.setText(QCoreApplication.translate("MainWindow", u"Sampling rate", None))
        self.pushButton_toggleRecording.setText(QCoreApplication.translate("MainWindow", u"Start", None))
        self.pushButton_saveData.setText(QCoreApplication.translate("MainWindow", u"Save recording", None))
        self.checkBox_video.setText(QCoreApplication.translate("MainWindow", u"Record video", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_serial), QCoreApplication.translate("MainWindow", u"Serial monitor", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_plots), QCoreApplication.translate("MainWindow", u"Signal plots", None))
        self.menuAbout.setTitle(QCoreApplication.translate("MainWindow", u"About", None))
    # retranslateUi

