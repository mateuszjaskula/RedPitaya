# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Redpitaya.ui'
#
# Created: Thu Aug 28 13:06:11 2014
#      by: PyQt4 UI code generator 4.11.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui, Qt
from PyTango import *
from taurus.qt.qtgui.display import TaurusLCD
from PyQt4.Qwt5 import Qwt
from taurus.qt.qtgui.application import TaurusApplication
import sys, os, time

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_RedpitayaGUI(object):
    def setupUi(self, RedpitayaGUI):
        self.Redpitaya = DeviceProxy("RedpitayaServer/rp1")
        print self.redpitaya.read_attribute('magny')
        self.sample = []
        self.iter = 0
        self.magnXdata = []
        self.magnYdata = []
        self.magnZdata = []
        self.accelXdata = []
        self.accelYdata = []
        self.accelZdata = []
        self.gyroXdata = []
        self.gyroYdata = []
        self.gyroZdata = []
        RedpitayaGUI.setObjectName(_fromUtf8("RedpitayaGUI"))
        RedpitayaGUI.resize(1309, 625)
        self.centralwidget = QtGui.QWidget(RedpitayaGUI)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.tangoHost = QtGui.QLineEdit(self.centralwidget)
        self.tangoHost.setGeometry(QtCore.QRect(0, 30, 201, 31))
        self.tangoHost.setObjectName(_fromUtf8("tangoHost"))
        self.deviceName = QtGui.QLineEdit(self.centralwidget)
        self.deviceName.setGeometry(QtCore.QRect(230, 30, 201, 31))
        self.deviceName.setObjectName(_fromUtf8("deviceName"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(60, 10, 81, 17))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(290, 10, 91, 17))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.refreshButton = QtGui.QPushButton(self.centralwidget)
        self.refreshButton.setGeometry(QtCore.QRect(460, 0, 95, 61))
        self.refreshButton.setObjectName(_fromUtf8("refreshButton"))
        self.tsiPOS = QtGui.QSlider(self.centralwidget)
        self.tsiPOS.setGeometry(QtCore.QRect(610, 20, 691, 41))
        self.tsiPOS.setSliderPosition(50)
        self.tsiPOS.setOrientation(QtCore.Qt.Horizontal)
        self.tsiPOS.setObjectName(_fromUtf8("tsiPOS"))
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(270, 70, 121, 17))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(160, 330, 151, 17))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.label_5 = QtGui.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(910, 60, 131, 17))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.label_6 = QtGui.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(890, 0, 151, 17))
        self.label_6.setObjectName(_fromUtf8("label_6"))
        self.label_7 = QtGui.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(450, 370, 71, 17))
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.label_8 = QtGui.QLabel(self.centralwidget)
        self.label_8.setGeometry(QtCore.QRect(440, 460, 91, 17))
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.label_9 = QtGui.QLabel(self.centralwidget)
        self.label_9.setGeometry(QtCore.QRect(910, 320, 131, 20))
        self.label_9.setObjectName(_fromUtf8("label_9"))
        self.magnPlot = Qwt.QwtPlot(self.centralwidget)
        self.magnPlot.setGeometry(QtCore.QRect(0, 90, 581, 211))
        self.magnPlot.setObjectName(_fromUtf8("magnPlot"))
        self.gyroPlot = Qwt.QwtPlot(self.centralwidget)
        self.gyroPlot.setGeometry(QtCore.QRect(620, 80, 581, 211))
        self.gyroPlot.setObjectName(_fromUtf8("gyroPlot"))
        self.accelPlot = Qwt.QwtPlot(self.centralwidget)
        self.accelPlot.setGeometry(QtCore.QRect(0, 350, 411, 211))
        self.accelPlot.setObjectName(_fromUtf8("accelPlot"))
        self.rollPlot = Qwt.QwtPlot(self.centralwidget)
        self.rollPlot.setGeometry(QtCore.QRect(620, 340, 581, 211))
        self.rollPlot.setObjectName(_fromUtf8("rollPlot"))
        self.rollLCD = TaurusLCD(self.centralwidget)
        self.rollLCD.setGeometry(QtCore.QRect(430, 390, 111, 41))
        self.rollLCD.setObjectName(_fromUtf8("rollLCD"))
        self.taurusLCD_2 = TaurusLCD(self.centralwidget)
        self.taurusLCD_2.setGeometry(QtCore.QRect(430, 480, 111, 51))
        self.taurusLCD_2.setObjectName(_fromUtf8("taurusLCD_2"))
        RedpitayaGUI.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(RedpitayaGUI)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1309, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        RedpitayaGUI.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(RedpitayaGUI)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        RedpitayaGUI.setStatusBar(self.statusbar)

        self.retranslateUi(RedpitayaGUI)
        QtCore.QMetaObject.connectSlotsByName(RedpitayaGUI)

    def retranslateUi(self, RedpitayaGUI):
        RedpitayaGUI.setWindowTitle(_translate("RedpitayaGUI", "RedpitayaGUI", None))
        self.label.setText(_translate("RedpitayaGUI", "Tango Host:", None))
        self.label_2.setText(_translate("RedpitayaGUI", "Device Name:", None))
        self.refreshButton.setText(_translate("RedpitayaGUI", "Refresh", None))
        self.label_3.setText(_translate("RedpitayaGUI", "Magnitude Plot", None))
        self.label_4.setText(_translate("RedpitayaGUI", "Accelerometer Plot", None))
        self.label_5.setText(_translate("RedpitayaGUI", "Gyroscope Plot", None))
        self.label_6.setText(_translate("RedpitayaGUI", "Touch Slider Position", None))
        self.label_7.setText(_translate("RedpitayaGUI", "Accel Roll", None))
        self.label_8.setText(_translate("RedpitayaGUI", "Accel Pitch", None))
        self.label_9.setText(_translate("RedpitayaGUI", "Roll and Pitch plot", None))

    def logData(self):
        self.magnXdata.append(self.redpitaya.read_attribute('magnX').value)
        self.magnYdata.append(self.redpitaya.read_attribute('magnY').value)
        self.magnZdata.append(self.redpitaya.read_attribute('magnZ').value)
        self.accelXdata.append(self.redpitaya.read_attribute('accelX').value)
        self.accelYdata.append(self.redpitaya.read_attribute('accelY').value)
        self.accelZdata.append(self.redpitaya.read_attribute('accelZ').value)
        self.gyroXdata.append(self.redpitaya.read_attribute('gyroX').value)
        self.gyroYdata.append(self.redpitaya.read_attribute('gyroY').value)
        self.gyroZdata.append(self.redpitaya.read_attribute('gyroZ').value)

        self.sample.append(self.iter)
        self.iter += 1

        self.magnPlot.setAutoReplot(1)
        self.accelPlot.setAutoReplot(1)
        self.gyroPlot.setAutoReplot(1)

        self.magnXcurve = Qwt.QwtPlotCurve('magnX')
        self.magnYcurve = Qwt.QwtPlotCurve('magnY')
        self.magnZcurve = Qwt.QwtPlotCurve('magnZ')
        self.accelXcurve = Qwt.QwtPlotCurve('accelX')
        self.accelYcurve = Qwt.QwtPlotCurve('accelY')
        self.accelZcurve = Qwt.QwtPlotCurve('accelZ')
        self.gyroXcurve = Qwt.QwtPlotCurve('gyroX')
        self.gyroYcurve = Qwt.QwtPlotCurve('gyroY')
        self.gyroZcurve = Qwt.QwtPlotCurve('gyroZ')

        self.magnXcurve.setData(self.sample, self.magnXdata)
        self.magnYcurve.setData(self.sample, self.magnYdata)
        self.magnZcurve.setData(self.sample, self.magnZdata)
        self.accelXcurve.setData(self.sample, self.accelXdata)
        self.accelYcurve.setData(self.sample, self.accelYdata)
        self.accelZcurve.setData(self.sample, self.accelZdata)
        self.gyroXcurve.setData(self.sample, self.gyroXdata)
        self.gyroYcurve.setData(self.sample, self.gyroYdata)
        self.gyroZcurve.setData(self.sample, self.gyroZdata)

        self.magnPlot.setCanvasBackground(Qt.Qt.white)
        self.accelPlot.setCanvasBackground(Qt.Qt.white)
        self.gyroPlot.setCanvasBackground(Qt.Qt.white)

        self.magnXcurve.setPen(Qt.QPen(Qt.Qt.red))
        self.magnYcurve.setPen(Qt.QPen(Qt.Qt.blue))
        self.magnZcurve.setPen(Qt.QPen(Qt.Qt.green))
        self.accelXcurve.setPen(Qt.QPen(Qt.Qt.red))
        self.accelYcurve.setPen(Qt.QPen(Qt.Qt.blue))
        self.accelZcurve.setPen(Qt.QPen(Qt.Qt.green))
        self.gyroXcurve.setPen(Qt.QPen(Qt.Qt.red))
        self.gyroYcurve.setPen(Qt.QPen(Qt.Qt.blue))
        self.gyroZcurve.setPen(Qt.QPen(Qt.Qt.green))

        self.magnPlot.insertLegend(self.magnPlot.legend(), Qwt.QwtPlot.RightLegend, 0.0)
        self.accelPlot.insertLegend(self.accelPlot.legend(), Qwt.QwtPlot.RightLegend, 0.0)
        self.gyroPlot.insertLegend(self.gyroPlot.legend(), Qwt.QwtPlot.RightLegend, 0.0)

        self.magnXcurve.attach(self.magnPlot)
        self.magnYcurve.attach(self.magnPlot)
        self.magnZcurve.attach(self.magnPlot)
        self.accelXcurve.attach(self.accelPlot)
        self.accelYcurve.attach(self.accelPlot)
        self.accelZcurve.attach(self.accelPlot)
        self.gyroXcurve.attach(self.gyroPlot)
        self.gyroYcurve.attach(self.gyroPlot)
        self.gyroZcurve.attach(self.gyroPlot)

        self.magnPlot.autoRefresh()
        self.accelPlot.autoRefresh()
        self.gyroPlot.autoRefresh()


if __name__ == "__main__":
    app = TaurusApplication(sys.argv)
    RedpitayaGUI = QtGui.QMainWindow()
    ui = Ui_RedpitayaGUI()
    ui.setupUi(RedpitayaGUI)
    RedpitayaGUI.show()
    while(1):
        ui.logData()
        time.sleep(1)
    sys.exit(app.exec_())
