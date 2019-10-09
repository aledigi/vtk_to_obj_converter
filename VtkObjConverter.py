from __main__ import vtk, qt, ctk, slicer
import os
import random


class VtkObjConverter:
    def __init__(self, parent):
        parent.title = "VTK to OBJ converter"
        parent.categories = ["MyModule"]
        parent.dependencies = []
        parent.contributors = ["Alessandro Di Girolamo (as.digirolamo@gmail.com)."]
        parent.helpText = """VTK to OBJ format converter. Drag and drop the VTK file you want to convert, then press 
                             the Apply button. A random color is given to the OBJ model and saved in a separated MTL 
                             file. Both the OBJ and the MTL files are saved in the same directory of the input VTK file.
                          """
        # parent.acknowledgementText = """Many thanks to..."""

        # Set module icon
        iconPath = os.path.dirname(os.path.realpath(__file__)) + '/icon.jpeg'
        if os.path.isfile(iconPath):
            parent.icon = qt.QIcon(iconPath)

        self.parent = parent


class VtkObjConverterWidget:
    def __init__(self, parent=None):
        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if not parent:
            self.setup()
            self.parent.show()

    def setup(self):

        # Instantiate and connect widgets ...

        #
        # Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Input"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # Input model selector
        #
        self.inputModelSelector = slicer.qMRMLNodeComboBox()
        self.inputModelSelector.nodeTypes = ["vtkMRMLModelNode"]
        self.inputModelSelector.addEnabled = False
        self.inputModelSelector.removeEnabled = True
        self.inputModelSelector.renameEnabled = True
        self.inputModelSelector.noneEnabled = False
        self.inputModelSelector.showHidden = False
        self.inputModelSelector.showChildNodeTypes = False
        self.inputModelSelector.setMRMLScene(slicer.mrmlScene)
        self.inputModelSelector.setToolTip("Drag and drop the VTK file you want to convert")
        parametersFormLayout.addRow("Model: ", self.inputModelSelector)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Start the conversion"
        self.applyButton.enabled = False
        parametersFormLayout.addRow(self.applyButton)

        # Connections
        self.inputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.applyButton.connect('clicked(bool)', self.onApplyButton)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Refresh Apply button state
        self.onSelect()

    def onSelect(self):
        self.applyButton.enabled = self.inputModelSelector.currentNode()

    def onApplyButton(self):
        logic = VtkObjLogic()
        logic.vtk_to_obj_converter(self.inputModelSelector.currentNode())


class VtkObjLogic:

    def vtk_to_obj_converter(self, node, radius=0.1, number_of_sides=3):

        qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        polydata = node.GetPolyData()
        tuber = vtk.vtkTubeFilter()
        tuber.SetNumberOfSides(int(number_of_sides))
        tuber.SetRadius(radius)
        tuber.SetInputData(polydata)
        tuber.Update()

        tubes = tuber.GetOutputDataObject(0)
        # scalars = tubes.GetPointData().GetArray(0)
        # scalars.SetName("scalars")

        triangles = vtk.vtkTriangleFilter()
        triangles.SetInputData(tubes)
        triangles.Update()

        tripolydata = vtk.vtkPolyData()
        tripolydata.ShallowCopy(triangles.GetOutput())

        # Decrease the number of triangle of 30% to reduce Blender loading costs
        decimate = vtk.vtkDecimatePro()
        decimate.SetInputData(tripolydata)
        decimate.SetTargetReduction(.30)
        decimate.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(decimate.GetOutputPort())

        r = random.randrange(0, 256, 1)
        g = random.randrange(0, 256, 1)
        b = random.randrange(0, 256, 1)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # actor.GetProperty().SetColor(0, 0, 0)  # Ka: ambient color of the material (r, g, b)
        actor.GetProperty().SetDiffuseColor(r, g, b)  # Kd: diffuse color of the material (r, g, b)
        # actor.GetProperty().SetSpecularColor(0, 0, 0)  # Ks: specular color of the material (r, g, b)

        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)

        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)

        # Get output path
        storageNode = node.GetStorageNode()
        filepath = storageNode.GetFullNameFromFileName()
        filename = filepath.rsplit('.', 1)

        writer = vtk.vtkOBJExporter()
        writer.SetFilePrefix(filename[0])
        writer.SetInput(window)
        writer.Write()

        qt.QApplication.restoreOverrideCursor()

        if writer.Write() == 0:
            qt.QMessageBox.critical(None, "Conversion", "Conversion failed")
        else:
            qt.QMessageBox.information(None, "Conversion", "Conversion done")
