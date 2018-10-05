import maya.cmds as cmds
import maya.OpenMayaUI as omui


from PySide2 import QtWidgets
from PySide2 import QtGui, QtCore
from shiboken2 import wrapInstance

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
        self.ui.pickMesh.clicked.connect(self.pickMesh)
        self.ui.pickFDM.clicked.connect(self.pickFDM)
        self.ui.pickXYZ.clicked.connect(self.pickXYZ)
        self.ui.setup.clicked.connect(self.setup)
        self.mesh = ["none"]
        self.floatDisplacementPath = ["none"]
        self.xyzDisplacementPath = ["none"]

#---------------------------------------------

    def pickMesh(self):
        
        selection = cmds.ls (selection=True)
        mesh = cmds.filterExpand(selection, sm=12)

        if  mesh == None:
            om.MGlobal.displayError("your selection is not a Polygon Mesh") 
            return 

        self.mesh = mesh
        self.ui.pickMesh.setText(mesh[0])
        self.shape = cmds.listRelatives(mesh, shapes=True)

        for node in mesh:
	        history = cmds.listHistory(node) or []
	        deformHistory = cmds.ls(history, type="geometryFilter", long=True)    
        if not deformHistory == []:
            om.MGlobal.displayWarning("mesh has deformer in it's history that might affect the displacement, don't forget to check them if the displacement isn't working as expected")

#---------------------------------------------

    def pickFDM(self):
        
        Filters = "*.exr *.tif *.tiff *.tex"
        floatDisplacementFile = cmds.fileDialog2(dialogStyle=2, fileMode=1, fileFilter= Filters, cap ="Select a float displacement map generated from Zbrush or Mudbox",okc ="Pick")
        if floatDisplacementFile == None :
            return
        self.ui.pickFDM.setText(floatDisplacementFile[0])
        self.floatDisplacementPath = floatDisplacementFile

#---------------------------------------------

    def pickXYZ(self):
        
        Filters = "*.exr *.tif *.tiff *.tex"
        xyzDisplacementFile = cmds.fileDialog2(dialogStyle=2, fileMode=1, fileFilter= Filters, cap ="Select an XYZ displacement map",okc ="Pick")
        if xyzDisplacementFile == None :
            return
        self.ui.pickXYZ.setText(xyzDisplacementFile[0])
        self.xyzDisplacementPath = xyzDisplacementFile

#---------------------------------------------
        
    def setup(self):
       
        storedSelection = cmds.ls(sl=True,long=True) or []
        mesh = self.mesh[0]
        FloatDisplacementFile = self.floatDisplacementPath[0]
        XYZDisplacementFile = self.xyzDisplacementPath[0]
        RenderEngineValue = str(self.ui.RenderEngine.currentIndex())
        fdmUdimValue = str(self.ui.udimFDM.isChecked())
        xyzUdimValue = str(self.ui.udimXYZ.isChecked())
        keepShaderValue = str(self.ui.keepShader.isChecked())
        currentEngine = cmds.getAttr("defaultRenderGlobals.currentRenderer")

        if (FloatDisplacementFile == "none" and XYZDisplacementFile == "none") or (mesh == "none"):
            om.MGlobal.displayError("Please select at least one displacement file and a Polygon Mesh")
            return

        if RenderEngineValue == "0" and currentEngine =="arnold" :
            self.arnoldMeshSetup(mesh)
            self.avShaderSetup(mesh,keepShaderValue,fdmUdimValue,xyzUdimValue,FloatDisplacementFile,XYZDisplacementFile,RenderEngineValue)
            om.MGlobal.displayInfo("done")
            cmds.select(storedSelection)
            
        elif RenderEngineValue == "1" and currentEngine =="renderman":
            self.rendermanMeshSetup(mesh)
            self.rendermanShaderSetup(mesh,keepShaderValue,fdmUdimValue,xyzUdimValue,FloatDisplacementFile,XYZDisplacementFile,RenderEngineValue)
            om.MGlobal.displayInfo("done")
            cmds.select(storedSelection)

        elif RenderEngineValue == "1" and currentEngine =="renderManRIS":
            self.renderManRISMeshSetup(mesh)
            self.rendermanShaderSetup(mesh,keepShaderValue,fdmUdimValue,xyzUdimValue,FloatDisplacementFile,XYZDisplacementFile,RenderEngineValue)
            om.MGlobal.displayInfo("done")
            cmds.select(storedSelection)            

        elif RenderEngineValue == "2" and currentEngine =="vray":
            self.vrayMeshSetup(mesh)
            self.avShaderSetup(mesh,keepShaderValue,fdmUdimValue,xyzUdimValue,FloatDisplacementFile,XYZDisplacementFile,RenderEngineValue)
            om.MGlobal.displayInfo("done")
            cmds.select(storedSelection)

        else:
            if RenderEngineValue == "0":
                RenderEngineValue = "arnold"
            elif RenderEngineValue == "1":
                RenderEngineValue = "renderMan"
            elif RenderEngineValue == "2":
                RenderEngineValue = "Vray"
            if currentEngine =="renderManRIS":
                currentEngine = "RenderMan"  
            om.MGlobal.displayError(" the current engine is "+ currentEngine +" not "+RenderEngineValue)                

#---------------------------------------------

    def arnoldMeshSetup(self,mesh):
        shape = cmds.listRelatives(mesh, shapes=True)

        for shapes in shape:
            cmds.setAttr(shapes+".aiSubdivType" ,1)
            cmds.setAttr(shapes+".aiSubdivIterations" ,4)
            cmds.setAttr(shapes+".aiSubdivUvSmoothing" ,2)
            cmds.setAttr(shapes+".aiDispPadding" ,1)

#---------------------------------------------

    def rendermanMeshSetup(self,mesh):

        shape = cmds.listRelatives(mesh, shapes=True)

        for shapes in shape:
            cmds.setAttr(shapes+'.rman_displacementBound', 2.0002)

#---------------------------------------------

    def renderManRISMeshSetup(self,mesh):

        shape = cmds.listRelatives(mesh, shapes=True)

        for shapes in shape:
            cmds.rman("addAttr",shapes,"rman__torattr___subdivScheme")
            cmds.rman("addAttr",shapes,"rman__torattr___subdivFacevaryingInterp")
            cmds.setAttr(shapes+'.rman__torattr___subdivFacevaryingInterp', 3)
#---------------------------------------------

    def vrayMeshSetup(self,mesh):

        shape = cmds.listRelatives(mesh, shapes=True) 

        for shapes in shape:
            cmds.vray("addAttributesFromGroup", shapes, "vray_subdivision", 1)
            cmds.vray("addAttributesFromGroup", shapes, "vray_subquality", 1)
            cmds.vray("addAttributesFromGroup", shapes, "vray_displacement", 1)
            cmds.setAttr(shapes+".vraySubdivEnable" ,1)
            cmds.setAttr(shapes+".vraySubdivUVs" ,0)
            cmds.setAttr(shapes+".vrayEdgeLength" ,4)
            cmds.setAttr(shapes+".vrayDisplacementType" ,1)
            cmds.setAttr(shapes+".vrayDisplacementKeepContinuity" ,1)
            cmds.setAttr(shapes+".vray2dDisplacementFilterTexture" ,0)
            cmds.setAttr(shapes+".vrayDisplacementUseBounds" ,0)            

#---------------------------------------------

    def avShaderSetup(self, mesh,keepShaderValue, fdmUdimValue, xyzUdimValue, FloatDisplacementFile, XYZDisplacementFile,RenderEngineValue ):

        if RenderEngineValue == "arnold":
            shader = cmds.shadingNode("aiStandard", name = mesh + "_aiStandard", asShader=True)
        else:
            shader = cmds.shadingNode("VRayMtl", name = mesh +"_VRayMtl", asShader=True)

        if keepShaderValue == "False":
            if RenderEngineValue == "arnold":
                shader = cmds.shadingNode("aiStandard", name = mesh + "_aiStandard", asShader=True)
            else:
                shader = cmds.shadingNode("VRayMtl", name = mesh +"_VRayMtl", asShader=True)            
            shading_group= cmds.sets(name = mesh + "SG", renderable=True,noSurfaceShader=True,empty=True)
            cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %shading_group)

        else:
            shape = cmds.listRelatives(mesh, shapes=True)
            shading_group = cmds.listConnections(shape,type='shadingEngine')
                
        floatUv = cmds.shadingNode("place2dTexture", asUtility=True)
        floatFile_node = cmds.shadingNode("file",name = "float_displacement_File" , asTexture=True, isColorManaged = True)
        cmds.setAttr(floatFile_node+".filterType" ,3)

        if not FloatDisplacementFile == "none":
            cmds.setAttr(floatFile_node+".fileTextureName" ,FloatDisplacementFile, type = "string") 

        cmds.setAttr(floatFile_node+".colorSpace", "Raw", type="string")
        cmds.defaultNavigation(connectToExisting=True, source=floatUv , destination=floatFile_node)

        XYZuv = cmds.shadingNode("place2dTexture", asUtility=True)
        XYZFile_node = cmds.shadingNode("file",name = "XYZ_displacement_File" , asTexture=True, isColorManaged = True)
        cmds.setAttr(XYZFile_node+".filterType" ,3)
        cmds.setAttr(XYZFile_node+".fileTextureName" ,XYZDisplacementFile, type = "string")
        cmds.setAttr(XYZFile_node+".colorSpace", "Raw", type="string")
        XYZLayeredTexture = cmds.shadingNode("layeredTexture",name = "It_XYZ_displacement" , asTexture=True, isColorManaged = True)
        XYZLayerBlendR = cmds.shadingNode("blendColors",name = "XYZ_R_intensity" , asUtility=True)
        XYZLayerBlendG = cmds.shadingNode("blendColors",name = "XYZ_G_intensity" , asUtility=True)
        XYZLayerBlendB = cmds.shadingNode("blendColors",name = "XYZ_B_intensity" , asUtility=True)
        cmds.setAttr(XYZLayerBlendR+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendG+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendB+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendR+".blender" ,0)
        cmds.setAttr(XYZLayerBlendG+".blender" ,0)
        cmds.setAttr(XYZLayerBlendB+".blender" ,0)

        cmds.defaultNavigation(connectToExisting=True, source=XYZuv , destination=XYZFile_node)
        cmds.connectAttr('%s.outColor' %XYZFile_node, '%s.inputs[1].color' %XYZLayeredTexture)
        cmds.connectAttr('%s.outColor' %XYZFile_node, '%s.inputs[0].color' %XYZLayeredTexture)
        cmds.disconnectAttr('%s.outColor' %XYZFile_node, '%s.inputs[0].color' %XYZLayeredTexture)
        cmds.setAttr(XYZLayeredTexture+".inputs[0].color" ,0.5,0.5,0.5, type = "double3")
        cmds.setAttr(XYZLayeredTexture+".inputs[0].blendMode" ,5)
        cmds.setAttr(XYZLayeredTexture+".inputs[1].blendMode" ,4)

        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendR)
        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendR)
        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendR)

        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendG)
        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendG)
        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendG)

        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendB)
        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendB)
        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendB)

        MapsMerge = cmds.shadingNode("plusMinusAverage", name = "merger", asUtility=True) 

        cmds.connectAttr('%s.output' %XYZLayerBlendR, '%s.input3D[0]' %MapsMerge)
        cmds.connectAttr('%s.output' %XYZLayerBlendG, '%s.input3D[1]' %MapsMerge)
        cmds.connectAttr('%s.output' %XYZLayerBlendB, '%s.input3D[2]' %MapsMerge)

        cmds.connectAttr('%s.outColorR' %floatFile_node, '%s.input3D[3].input3Dx' %MapsMerge)
        cmds.connectAttr('%s.outColorR' %floatFile_node, '%s.input3D[3].input3Dy' %MapsMerge)
        cmds.connectAttr('%s.outColorR' %floatFile_node, '%s.input3D[3].input3Dz' %MapsMerge)

        luminance = cmds.shadingNode("luminance", name = "ConvertToLuminance", asUtility=True) 
        cmds.connectAttr('%s.output3D' %MapsMerge, '%s.value' %luminance)
        displacement_shader = cmds.shadingNode("displacementShader",name = mesh + "_displacementShader", asShader=True)
        cmds.connectAttr('%s.outValue' %luminance, '%s.displacement' %displacement_shader)

        if fdmUdimValue == "True":
            cmds.setAttr(floatFile_node+".uvTilingMode", 3)
            cmds.setAttr(floatFile_node+".uvTileProxyQuality", 4)
        
        if xyzUdimValue == "True":
            cmds.setAttr(XYZFile_node+".uvTilingMode", 3)
            cmds.setAttr(XYZFile_node+".uvTileProxyQuality", 4)

        if keepShaderValue == "False":
            cmds.connectAttr('%s.displacement' %displacement_shader ,'%s.displacementShader' %shading_group, force=True)
        else:
            cmds.connectAttr('%s.displacement' %displacement_shader ,'%s.displacementShader' %str(shading_group[0]), force=True)

        cmds.select(cmds.listRelatives(mesh, shapes=True))

        if keepShaderValue == "False":
            cmds.hyperShade(assign=shading_group)
        
#---------------------------------------------

    def rendermanShaderSetup(self, mesh,keepShaderValue, fdmUdimValue, xyzUdimValue, FloatDisplacementFile, XYZDisplacementFile,RenderEngineValue ):

        if keepShaderValue == "False":
            shader = cmds.shadingNode("PxrSurface", name = mesh +"_PxrSurface", asShader=True)        
            shading_group= cmds.sets(name = mesh + "SG", renderable=True,noSurfaceShader=True,empty=True)
            cmds.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %shading_group)

        else:
            shape = cmds.listRelatives(mesh, shapes=True)
            shading_group = cmds.listConnections(shape,type='shadingEngine')

        displacement_shader = cmds.shadingNode("PxrDisplace",name = mesh + "_PxrDisplace", asShader=True)
        displacement_transform = cmds.shadingNode("PxrDispTransform",name = mesh + "_PxrDispTransform", asUtility=True)
        floatFile_node = cmds.shadingNode("PxrTexture",name = mesh +"_float_Displacement_PxrTexture_File" , asTexture=True,)
        XYZFile_node = cmds.shadingNode("PxrTexture",name = mesh +"_XYZ_Displacement_PxrTexture_File" , asTexture=True,)

        cmds.setAttr(floatFile_node+".filter" , 0)
        cmds.setAttr(XYZFile_node+".filter" , 0)
        cmds.setAttr(displacement_transform+".dispType", 1)
        cmds.setAttr(displacement_transform+".dispHeight", 1.2)
        cmds.setAttr(displacement_transform+".dispDepth", 1.2)
        
        XYZLayeredTexture = cmds.shadingNode("layeredTexture",name = "It_XYZ_displacement" , asTexture=True, isColorManaged = True)
        XYZLayerBlendR = cmds.shadingNode("blendColors",name = "XYZ_R_intensity" , asUtility=True)
        XYZLayerBlendG = cmds.shadingNode("blendColors",name = "XYZ_G_intensity" , asUtility=True)
        XYZLayerBlendB = cmds.shadingNode("blendColors",name = "XYZ_B_intensity" , asUtility=True)
        cmds.setAttr(XYZLayerBlendR+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendG+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendB+".color2" ,0.0,0.0,0.0, type = "double3")
        cmds.setAttr(XYZLayerBlendR+".blender" ,0)
        cmds.setAttr(XYZLayerBlendG+".blender" ,0)
        cmds.setAttr(XYZLayerBlendB+".blender" ,0)

        
        
        cmds.connectAttr('%s.resultRGB' %XYZFile_node, '%s.inputs[1].color' %XYZLayeredTexture)
        cmds.connectAttr('%s.resultRGB' %XYZFile_node, '%s.inputs[0].color' %XYZLayeredTexture)
        cmds.disconnectAttr('%s.resultRGB' %XYZFile_node, '%s.inputs[0].color' %XYZLayeredTexture)
        cmds.setAttr(XYZLayeredTexture+".inputs[0].color" ,0.5,0.5,0.5, type = "double3")
        cmds.setAttr(XYZLayeredTexture+".inputs[0].blendMode" ,5)
        cmds.setAttr(XYZLayeredTexture+".inputs[1].blendMode" ,4)

        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendR)
        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendR)
        cmds.connectAttr('%s.outColorR' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendR)

        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendG)
        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendG)
        cmds.connectAttr('%s.outColorG' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendG)

        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1R' %XYZLayerBlendB)
        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1G' %XYZLayerBlendB)
        cmds.connectAttr('%s.outColorB' %XYZLayeredTexture, '%s.color1B' %XYZLayerBlendB)

        MapsMerge = cmds.shadingNode("plusMinusAverage", name = "merger", asUtility=True) 

        cmds.connectAttr('%s.output' %XYZLayerBlendR, '%s.input3D[0]' %MapsMerge)
        cmds.connectAttr('%s.output' %XYZLayerBlendG, '%s.input3D[1]' %MapsMerge)
        cmds.connectAttr('%s.output' %XYZLayerBlendB, '%s.input3D[2]' %MapsMerge)

        cmds.connectAttr('%s.resultRGB' %floatFile_node, '%s.input3D[3]' %MapsMerge)


        luminance = cmds.shadingNode("luminance", name = "ConvertToLuminance", asUtility=True) 
        cmds.connectAttr('%s.output3D' %MapsMerge, '%s.value' %luminance)
        cmds.connectAttr('%s.outValue' %luminance, '%s.dispScalar' %displacement_transform)


        
        if fdmUdimValue == "True":

            udimcoords = range(1001,1999)

            for coords in udimcoords:
               FloatDisplacementFile = FloatDisplacementFile.replace(str(coords), '_MAPID_')
            cmds.setAttr(floatFile_node+".filename" ,FloatDisplacementFile, type = "string")
            cmds.setAttr(floatFile_node+".atlasStyle", 1)                        
        
        cmds.setAttr(floatFile_node+".filename" ,FloatDisplacementFile, type = "string")

        if xyzUdimValue == "True":

            udimcoords = range(1001,1999)

            for coords in udimcoords:
               XYZDisplacementFile = XYZDisplacementFile.replace(str(coords), '_MAPID_')
            cmds.setAttr(XYZFile_node+".filename" ,XYZDisplacementFile, type = "string")
            cmds.setAttr(XYZFile_node+".atlasStyle", 1)                        
        cmds.setAttr(XYZFile_node+".filename" ,XYZDisplacementFile, type = "string")
        
        if keepShaderValue == "False":
            cmds.connectAttr('%s.outColor' %displacement_shader ,'%s.displacementShader' %shading_group, force=True)
        else:
            cmds.connectAttr('%s.outColor' %displacement_shader ,'%s.displacementShader' %str(shading_group[0]), force=True)                
        
        cmds.connectAttr('%s.resultF' %displacement_transform, '%s.dispScalar' %displacement_shader)
        cmds.select(cmds.listRelatives(mesh, shapes=True))

        if keepShaderValue == "False":
            cmds.hyperShade(assign=shading_group)        

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