import maya.cmds as cmds
import maya.OpenMayaUI as omui


from PySide2 import QtWidgets
from PySide2 import QtGui, QtCore
from shiboken2 import wrapInstance

from OpenEXR import OpenEXR 
from OpenEXR import Imath

from PIL import Image
import math

import maya.OpenMaya as om

import XYZToolUi
reload (XYZToolUi)



def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)



class ControlMainWindow(QtWidgets.QWidget):
 
    def __init__(self, parent=None):

        super(ControlMainWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.ui = XYZToolUi.Ui_XYZToolUi()
        self.ui.setupUi(self)
#        self.displacementPath = ["none"]
#        self.mesh = ["none"]
#        self.shape = ["none"]
#        self.MinLuma = ["none"]
#        self.MaxLuma = ["none"]
#        self.ui.pickMesh.clicked.connect(self.pickMesh)
#        self.ui.pickMap.clicked.connect(self.pickMap)
#        self.ui.setup.clicked.connect(self.displacementSetup)

#---------------------------------------------

def run():

    global win
    try:
        win.close()
        win.deleteLater()

    except: 
        pass

    win = ControlMainWindow(parent=maya_main_window())
    win.show()