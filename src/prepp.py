# built-in Python 2 in Abaqus
# -*- coding: utf-8 -*-
# 
# Pre-processing script for finite element modeling of self-drilling screw connections between thin steel sheets
# Ver 1.0, by Kangyi Cai June, 2021 @ WHU

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Initialization
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Import modules
from math import *
import numpy as np
import os

from abaqus import *
from abaqusConstants import *
import __main__

import mesh
import regionToolset

from odbAccess import *
from visualization import *

backwardCompatibility.setValues(includeDeprecated = True, reportDeprecated = False)

def mkdir(path):
    
    "Set the working path."
    
    folder = os.path.exists(path)
    
    if not folder:
        os.makedirs(path)

def copyFiles(sourceDir, targetDir):

    "copy files."

    for f in os.listdir(sourceDir):

        sourceF = os.path.join(sourceDir, f)
        targetF = os.path.join(targetDir, f)

        if os.path.isfile(sourceF):
            
            #Create a work directory
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)

            #Copy any file that doesn't exist AND Overwrite any file that isn't the latest version
            if not os.path.exists(targetF) or (os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):
                open(targetF, "wb").write(open(sourceF, "rb").read()) #binary file

        if os.path.isdir(sourceF):
            copyFiles(sourceF, targetF)

#Path & File
currentPath = os.path.abspath("prepp.py")
path = os.path.abspath(os.path.dirname(currentPath) + os.path.sep + ".")
# print "%s" % path

pathSplit = path.split('\\')
caeName = pathSplit[-1]+".cae"

#Set the working path
mkdir(path)
mdb.saveAs(pathName=path+"\\"+caeName)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Parameter database
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Sheet
sheetC = {}

##Sheet characteristic
sheetC['length'] = [250.0] # sheet length
sheetC['width' ] = [50.0] # sheet width

###For verification of shear tests #----------------------------
sheetC['type'    ] = [         0,          1,          2,          3,          4,          5] # sheet type
sheetC['t'       ] = [       0.4,        0.5,        0.6,        0.8,        1.0,        2.5] # sheet thickness
sheetC['material'] = ['T04_Q350', 'T05_Q350', 'T06_Q350', 'T08_Q550', 'T10_Q550', 'T25_Q350'] # sheet material

# ###For parametric analysis, factor: sheet thickness #----------------------------
# sheetC['type'    ] = [         0,          1,          2,          3,          4,          5,          6,          7,          8,          9] # sheet type
# sheetC['t'       ] = [       0.4,        0.5,        0.6,        0.8,        1.0,        1.2,        1.5,        2.0,        2.5,        3.0] # sheet thickness
# sheetC['material'] = ['T04_Q350', 'T05_Q350', 'T06_Q350', 'T08_Q550', 'T10_Q550', 'T10_Q550', 'T10_Q550', 'T25_Q350', 'T25_Q350', 'T25_Q350'] # sheet material

# ###For parametric analysis, factor: screw spacing distance #----------------------------
# sheetC['type'    ] = [         0,          1,          2] # sheet type
# sheetC['t'       ] = [       0.5,        1.0,        2.5] # sheet thickness
# sheetC['material'] = ['T05_Q350', 'T10_Q550', 'T25_Q350'] # sheet material

#Screw
screwC = {}

##Screw characteristic
screwC['type'] = [    0,     1,     2,     3] # screw type, conform to GB/T 15856.5 and GB/T 5280, namely ISO 15480
screwC['dn'  ] = [  4.2,   4.8,   5.5,   6.3] # screw nominal diameter
screwC['tp'  ] = [ 1.40,  1.60,  1.80,  1.80] # thread pitch
screwC['td1' ] = [ 4.13,  4.71,  5.37,  6.14] # thread outer diameter
screwC['td2' ] = [ 3.03,  3.51,  4.08,  4.79] # thread inner diameter
screwC['tc'  ] = [ 0.10,  0.15,  0.15,  0.15] # thread tip width
screwC['a'   ] = [ 1.40,  1.60,  1.80,  1.80] # distance between head and closest thread
screwC['dc'  ] = [ 8.45, 10.15, 10.50, 12.85] # washer inner diameter
screwC['c'   ] = [ 0.80,  0.90,  1.00,  1.00] # washer thickness
screwC['s'   ] = [ 6.89,  7.89,  7.89,  9.89] # head inner diameter
screwC['k'   ] = [ 3.85,  4.05,  5.10,  5.60] # head and washer total hight
screwC['lg'  ] = [10.30,  8.70,  8.00,  7.00] # thread minimum length
screwC['material'] = ['D42_CarbonSteel', 'D48_CarbonSteel', 'D55_CarbonSteel', 'D63_CarbonSteel'] # screw material

##Screw arrangement
screwA = {} # [3, 2, 3, 2] means: there are 4 rows, and the screw number in each row from one end to another is 3, 2, 3, and 2, respectively

screwA['type'] = ['O', 'I', 'II', 'III', 'IV', 'V', 'VI'] # 7 types of screw arragement in total
screwA['O'   ] = [[1]]                                                          # 0-[0]
screwA['I'   ] = [[1, 1], [1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1, 1]]             # 1-[0, 1, 2, 3]
screwA['II'  ] = [[2], [2, 2], [2, 2, 2], [2, 2, 2, 2], [2, 2, 2, 2, 2]]        # 2-[0, 1, 2, 3, 4]
screwA['III' ] = [[3], [3, 3], [3, 3, 3]]                                       # 3-[0, 1, 2]
screwA['IV'  ] = [[2, 1, 2, 1, 2, 1], [2, 1, 1, 2, 1, 1], [2, 2, 1, 2, 2, 1]]   # 4-[0, 1, 2]
screwA['V'   ] = [[3, 2, 3, 2], [2, 3, 2, 3], [3, 2, 2, 3], [2, 3, 3, 2]]       # 5-[0, 1, 2, 3]
screwA['VI'  ] = [[1, 1, 1], [1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]] # 6-[0, 1, 2, 3]

screwA['spacingDistanceL'] = [3, 4, 5, 6, 8, 10] # screw longitudinal spacing distance, multiply by screw nominal diameter
screwA['spacingDistanceT'] = [3, 4, 5] # screw transversal spacing distance, multiply by screw nominal diameter
screwA['endDistance'] = [30.0] # screw end distance

#Basic control
bCF1 = 0.001 # boundary control factor, used in adds or subtracts

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Part-Functions
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Define part-creation functions.

def sheet(modelName='SCS', partName='sheetPart',    sheetProfile=3, sheetPosition=0, sheetLength=250.0, sheetWidth=50.0,    screwProfile=1, arrangementType1=4, arrangementType2=0, spacingDistanceLongitudinal=4, spacingTransversalDistance=3, endDistance=30.0):
    
    "Create a steel sheet."

    #Screw characteristic parameters
    dn = screwC['dn'][screwProfile]
    tp = screwC['tp'][screwProfile]
    td1 = screwC['td1'][screwProfile]
    td2 = screwC['td2'][screwProfile]
    tc = screwC['tc'][screwProfile]
    a = screwC['a'][screwProfile]
    dc = screwC['dc'][screwProfile]
    c = screwC['c'][screwProfile]
    s = screwC['s'][screwProfile]
    k = screwC['k'][screwProfile]
    lg = screwC['lg'][screwProfile]

    #Sheet characteristic parameters
    st = sheetC['t'][sheetProfile]

    #Screw arrangement parameters
    arr = screwA[screwA['type'][arrangementType1]][arrangementType2]
    lgd = spacingDistanceLongitudinal*dn # screw longitudinal spacing distance
    tgd = spacingTransversalDistance*dn # screw transiversal spacing distance
    ed = endDistance # screw end distance

    #Create a sketch
    sk = mdb.models[modelName].ConstrainedSketch(name=partName, sheetSize=200.0)

    sk.rectangle(point1=(-sheetWidth/2.0, (len(arr)-1)*lgd+ed), point2=(sheetWidth/2.0, -ed))
    
    for i in range(len(arr)):
        if arrangementType1 < 6:
            for j in range(arr[i]):
                x = -sheetWidth/2.0+(sheetWidth-(arr[i]-1)*tgd)/2.0+j*tgd
                y = i*lgd
                sk.CircleByCenterPerimeter(center=(x, y), point1=(x+td1/2.0, y))
        else:
            for j in range(1):
                x = -sheetWidth/2.0+(sheetWidth-tgd)/2.0+i%2*tgd
                y = i*lgd
                sk.CircleByCenterPerimeter(center=(x, y), point1=(x+td1/2.0, y))
    
    #Create a part
    pa = mdb.models[modelName].Part(name=partName, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    pa.BaseSolidExtrude(sketch=sk, depth=st)
    
    #Partition cells
    ##Trasversal partition
    y = -lgd/2.0
    pa.PartitionCellByPlaneThreePoints(point1=(0.0, y, 0.0), point2=(1.0, y, 0.0), point3=(0.0, y, 1.0), cells=pa.cells)

    for i in range(len(arr)):
        y = i*lgd
        pa.PartitionCellByPlaneThreePoints(point1=(0.0, y, 0.0), point2=(1.0, y, 0.0), point3=(0.0, y, 1.0), cells=pa.cells)
        y = (i+0.5)*lgd
        pa.PartitionCellByPlaneThreePoints(point1=(0.0, y, 0.0), point2=(1.0, y, 0.0), point3=(0.0, y, 1.0), cells=pa.cells)

    ##Longitudinal partition
    maxNumber = 0
    for i in range(len(arr)):
        if arr[i] > maxNumber:
            maxNumber = arr[i]
        else:
            maxNumber = maxNumber

    if arrangementType1 < 6:
        
        if (sheetWidth-(maxNumber-1)*tgd)/2.0 >= tgd/2.0:
            x = -sheetWidth/2.0+((sheetWidth-(maxNumber-1)*tgd)/2.0-tgd/2.0)
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)
            x = -x
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)

        for i in range(maxNumber):
            x = -sheetWidth/2.0+(sheetWidth-(maxNumber-1)*tgd)/2.0+i*tgd
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)
        for i in range(maxNumber-1):
            x = -sheetWidth/2.0+(sheetWidth-(maxNumber-1)*tgd)/2.0+(i+0.5)*tgd
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)
    else:

        if (sheetWidth-tgd)/2.0 >= tgd/2.0:
            x = -sheetWidth/2.0+((sheetWidth-tgd)/2.0-tgd/2.0)
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)
            x = -x
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)

        for i in range(2):
            x = -sheetWidth/2.0+(sheetWidth-tgd)/2.0+i*tgd
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)
        for i in range(1):
            x = -sheetWidth/2.0+(sheetWidth-tgd)/2.0+(i+0.5)*tgd
            pa.PartitionCellByPlaneThreePoints(point1=(x, 0.0, 0.0), point2=(x, 1.0, 0.0), point3=(x, 0.0, 1.0), cells=pa.cells)

    #Seed parts
    ##Sheet seed size
    sheetS = {}
    sheetS['sheetEnd'], sheetS['holeAround'], sheetS['holeCircumference'], sheetS['sheetThickness'], sheetS['sheetTotal'] = [], [], [], [], []

    sheetS['sheetEnd'].append(2.0)
    sheetS['holeAround'].append(1.0)
    sheetS['holeCircumference'].append(0.5)

    if sheetC['t'][sheetProfile] >= 0.4 and sheetC['t'][sheetProfile] <= 0.6:
        sheetS['sheetThickness'].append(0.2)
    elif sheetC['t'][sheetProfile] > 0.6 and sheetC['t'][sheetProfile] <= 1.2:
        sheetS['sheetThickness'].append(0.4)
    elif sheetC['t'][sheetProfile] > 1.2 and sheetC['t'][sheetProfile] <= 1.8:
        sheetS['sheetThickness'].append(0.6)
    elif sheetC['t'][sheetProfile] > 1.8 and sheetC['t'][sheetProfile] <= 3.0:
        sheetS['sheetThickness'].append(1.0)

    sheetS['sheetTotal'].append(4.0)

    seed1 = sheetS['sheetEnd'][0]
    seed2 = sheetS['holeAround'][0]
    seed3 = sheetS['holeCircumference'][0]
    seed4 = sheetS['sheetThickness'][0]
    seed5 = sheetS['sheetTotal'][0]

    ##Seed in the area at the sheet end
    edge1 = pa.edges.getByBoundingBox(xMin=-sheetWidth/2.0-bCF1, yMin=-ed-bCF1, zMin=0.0-bCF1, xMax=sheetWidth/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=st+bCF1)
    pa.seedEdgeBySize(edges=edge1, size=seed1, deviationFactor=0.1, constraint=FINER)

    ##Seed in the area around the sheet hole
    for i in range(len(arr)):
        if arrangementType1 < 6:
            for j in range(arr[i]):
                x = -sheetWidth/2.0+(sheetWidth-(arr[i]-1)*tgd)/2.0+j*tgd
                y = i*lgd
                edge2_1 = pa.edges.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=0.0-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=0.0+bCF1)
                pa.seedEdgeBySize(edges=edge2_1, size=seed2, deviationFactor=0.1, constraint=FINER)
                edge2_2 = pa.edges.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=st-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=st+bCF1)
                pa.seedEdgeBySize(edges=edge2_2, size=seed2, deviationFactor=0.1, constraint=FINER)
        else:
            for j in range(1):
                x = -sheetWidth/2.0+(sheetWidth-tgd)/2.0+i%2*tgd
                y = i*lgd
                edge2_1 = pa.edges.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=0.0-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=0.0+bCF1)
                pa.seedEdgeBySize(edges=edge2_1, size=seed2, deviationFactor=0.1, constraint=FINER)
                edge2_2 = pa.edges.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=st-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=st+bCF1)
                pa.seedEdgeBySize(edges=edge2_2, size=seed2, deviationFactor=0.1, constraint=FINER)
    
    ##Seed on the circumference of the sheet hole
    for i in range(len(arr)):
        if arrangementType1 < 6:
            for j in range(arr[i]):
                x = -sheetWidth/2.0+(sheetWidth-(arr[i]-1)*tgd)/2.0+j*tgd
                y = i*lgd
                edge3_1 = pa.edges.getByBoundingCylinder(center1=(x, y, 0.0-bCF1), center2=(x, y, 0.0+bCF1), radius=td1/2.0+bCF1)
                pa.seedEdgeBySize(edges=edge3_1, size=seed3, deviationFactor=0.1, constraint=FINER)
                edge3_2 = pa.edges.getByBoundingCylinder(center1=(x, y, st-bCF1), center2=(x, y, st+bCF1), radius=td1/2.0+bCF1)
                pa.seedEdgeBySize(edges=edge3_2, size=seed3, deviationFactor=0.1, constraint=FINER)
        else:
            for j in range(1):
                x = -sheetWidth/2.0+(sheetWidth-tgd)/2.0+i%2*tgd
                y = i*lgd
                edge3_1 = pa.edges.getByBoundingCylinder(center1=(x, y, 0.0-bCF1), center2=(x, y, 0.0+bCF1), radius=td1/2.0+bCF1)
                pa.seedEdgeBySize(edges=edge3_1, size=seed3, deviationFactor=0.1, constraint=FINER)
                edge3_2 = pa.edges.getByBoundingCylinder(center1=(x, y, st-bCF1), center2=(x, y, st+bCF1), radius=td1/2.0+bCF1)
                pa.seedEdgeBySize(edges=edge3_2, size=seed3, deviationFactor=0.1, constraint=FINER)

    ##Seed along the sheet thickness
    edge4 = pa.edges.findAt(((sheetWidth/2.0, -ed, st/2.0), ),) #! Pay attention to the findAt function.
    pa.seedEdgeBySize(edges=edge4, size=seed4, deviationFactor=0.1, constraint=FINER)

    ##Seed on the total sheet
    pa.seedPart(size=seed5, deviationFactor=0.1, minSizeFactor=0.1)
    
    #Mesh part
    pa.setMeshControls(regions=pa.cells, elemShape=HEX, technique=STRUCTURED)
    pa.generateMesh()
    
    return pa

def screw(modelName='SCS', partName='screwPart',    sheetProfile_Adj=3, sheetProfile_Nonadj=4,    screwProfile=1):
    
    "Create a self-drilling screw."

    #Screw characteristic parameters
    dn = screwC['dn'][screwProfile]
    tp = screwC['tp'][screwProfile]
    td1 = screwC['td1'][screwProfile]
    td2 = screwC['td2'][screwProfile]
    tc = screwC['tc'][screwProfile]
    a = screwC['a'][screwProfile]
    dc = screwC['dc'][screwProfile]
    c = screwC['c'][screwProfile]
    s = screwC['s'][screwProfile]
    k = screwC['k'][screwProfile]
    lg = screwC['lg'][screwProfile]
    
    #Sheet characteristic parameters
    st_Adj = sheetC['t'][sheetProfile_Adj]
    st_Nonadj = sheetC['t'][sheetProfile_Nonadj]

    #Create the screw shank
    ##Create a sketch
    sk = mdb.models[modelName].ConstrainedSketch(name='shankSketch', sheetSize=200.0)
    
    sk.ConstructionLine(point1=(-1.0, 0.0), point2=(1.0, 0.0))

    points1 = [(c, 0.0), (c, dc/2.0), (0.0, dc/2.0), (0.0, s/2.0), (c/2.0, s/2.0-c), (c/2.0, td2/2.0+(td1-td2)/2.0/3.0*2.0), (0.0, td2/2.0+(td1-td2)/2.0/3.0), (0.0, td2/2.0), (-(( st_Adj+st_Nonadj)//tp+4)*tp, td2/2.0), (-(( st_Adj+st_Nonadj)//tp+4)*tp, 0.0)]
    
    lines1 = []
    lines1.append(sk.Line(point1=points1[len(points1)-1], point2=points1[0]))
    for i in range(len(points1)-1):
        lines1.append(sk.Line(point1=points1[i], point2=points1[i+1]))
    
    ##Create a part
    pa = mdb.models[modelName].Part(name=partName, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    pa.BaseSolidRevolve(sketch=sk, angle=360.0)

    #Create the screw head
    ##Create a sketch
    face2 = pa.faces.findAt(coordinates=(c, 0.0, 0.0)) #! Pay attention to the findAt function.
    edge2 = pa.edges.findAt(coordinates=(0.0, (dc+s)/4.0, 0.0))
    transform2 = pa.MakeSketchTransform(sketchPlane=face2, sketchUpEdge=edge2, sketchPlaneSide=SIDE1, sketchOrientation=TOP, origin=(c, 0.0, 0.0))
    sk2 = mdb.models[modelName].ConstrainedSketch(name='headSketch', sheetSize=200.0, transform=transform2)
    pa.projectReferencesOntoSketch(sketch=sk2, filter=COPLANAR_EDGES)
    
    ###Cyclinder form
    sk2.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(s/2.0, 0.0))

    # ###Hexagon form
    # points2 = [(s/sqrt(3.0), 0.0), (s/2.0/sqrt(3.0), s/2.0), (-s/2.0/sqrt(3.0), s/2.0), (-s/sqrt(3.0), 0.0), (-s/2.0/sqrt(3.0), -s/2.0), (s/2.0/sqrt(3.0), -s/2.0)]
    # lines2 = []
    # lines2.append(sk2.Line(point1=points2[len(points2)-1], point2=points2[0]))
    # for i in range(len(points2)-1):
    #     lines2.append(sk2.Line(point1=points2[i], point2=points2[i+1]))

    ##Create a part
    pa.SolidExtrude(sketchPlane=face2, sketchUpEdge=edge2, sketchPlaneSide=SIDE1, sketchOrientation=TOP, sketch=sk2, depth=k-c, flipExtrudeDirection=OFF)

    #Partition cells
    edge1_1 = pa.edges.findAt(coordinates=(-(( st_Adj+st_Nonadj)//tp+4)*tp+bCF1, td2/2.0, 0.0))
    edge1_2 = pa.edges.findAt(coordinates=(-(( st_Adj+st_Nonadj)//tp+4)*tp, 0.0, td2/2.0))
    pa.PartitionCellByExtrudeEdge(line=edge1_1, cells=pa.cells, edges=edge1_2, sense=FORWARD)
    
    edge2_1 = pa.edges.findAt(coordinates=(-(( st_Adj+st_Nonadj)//tp+4)*tp+bCF1, td2/2.0, 0.0)) 
    edge2_2 = pa.edges.findAt(coordinates=(c/2.0, 0.0, td2/2.0+(td1-td2)/2.0/3.0*2.0))
    pa.PartitionCellByExtrudeEdge(line=edge2_1, cells=pa.cells, edges=edge2_2, sense=FORWARD)

    edge3_1 = pa.edges.findAt(coordinates=(-(( st_Adj+st_Nonadj)//tp+4)*tp+bCF1, td2/2.0, 0.0))
    edge3_2 = pa.edges.findAt(coordinates=(c/2.0, 0.0, s/2.0-c))
    pa.PartitionCellByExtrudeEdge(line=edge3_1, cells=pa.cells, edges=edge3_2, sense=FORWARD)
    
    edge4_1 = pa.edges.findAt(coordinates=(-(( st_Adj+st_Nonadj)//tp+4)*tp+bCF1, td2/2.0, 0.0))
    edge4_2 = pa.edges.findAt(coordinates=(0.0, 0.0, s/2.0))
    pa.PartitionCellByExtrudeEdge(line=edge4_1, cells=pa.cells, edges=edge4_2, sense=FORWARD)
    
    face5 = pa.faces.findAt(coordinates=(c, 0.0, dc/2.0-bCF1))
    pa.PartitionCellByExtendFace(extendFace=face5, cells=pa.cells)

    face6 = pa.faces.findAt(coordinates=(c/2.0, 0.0, td1/2.0+bCF1))
    cells6 = pa.cells.getByBoundingCylinder(center1=(-(( st_Adj+st_Nonadj)//tp+4)*tp, 0.0, 0.0), center2=(k, 0.0, 0.0), radius=td1/2.0+bCF1)
    pa.PartitionCellByExtendFace(extendFace=face6, cells=cells6)
    
    face7 = pa.faces.findAt(coordinates=(0.0, 0.0, td2/2.0+(td1-td2)/2.0/3.0-bCF1))
    cells7 = pa.cells.getByBoundingCylinder(center1=(-(( st_Adj+st_Nonadj)//tp+4)*tp, 0.0, 0.0), center2=(k, 0.0, 0.0), radius=td1/2.0+bCF1)
    pa.PartitionCellByExtendFace(extendFace=face7, cells=cells7)

    pa.PartitionCellByPlaneThreePoints(point1=(0.0, 0.0, 0.0), point2=(1.0, 0.0, 0.0), point3=(0.0, 0.0, 1.0), cells=pa.cells)

    pa.PartitionCellByPlaneThreePoints(point1=(0.0, 0.0, 0.0), point2=(1.0, 0.0, 0.0), point3=(0.0, 1.0, 0.0), cells=pa.cells)

    #Seed parts
    ##Seed on the screw thread
    edge1 = pa.edges.getByBoundingCylinder(center1=(-(( st_Adj+st_Nonadj)//tp+4)*tp, 0.0, 0.0), center2=(0.0, 0.0, 0.0), radius=td1/2.0+bCF1)
    pa.seedEdgeBySize(edges=edge1, size=0.5, deviationFactor=0.1, constraint=FINER)

    ##Seed on the whole screw
    pa.seedPart(size=1.0, deviationFactor=0.1, minSizeFactor=0.1)

    #Mesh part
    pa.setMeshControls(regions=pa.cells, elemShape=HEX, technique=SWEEP, algorithm=MEDIAL_AXIS)
    pa.generateMesh()
    
    return pa

def thread(modelName='SCS', partName='threadPart',    sheetProfile_Adj=3, sheetProfile_Nonadj=4,    screwProfile=1):
    
    "Create the thread of a self-drilling screw."

    #Screw characteristic parameters
    dn = screwC['dn'][screwProfile]
    tp = screwC['tp'][screwProfile]
    td1 = screwC['td1'][screwProfile]
    td2 = screwC['td2'][screwProfile]
    tc = screwC['tc'][screwProfile]
    a = screwC['a'][screwProfile]
    dc = screwC['dc'][screwProfile]
    c = screwC['c'][screwProfile]
    s = screwC['s'][screwProfile]
    k = screwC['k'][screwProfile]
    lg = screwC['lg'][screwProfile]

    #Sheet characteristic parameters
    st_Adj = sheetC['t'][sheetProfile_Adj]
    st_Nonadj = sheetC['t'][sheetProfile_Nonadj]

    #Create a sketch
    sk = mdb.models[modelName].ConstrainedSketch(name=partName, sheetSize=200.0)
    
    sk.ConstructionLine(point1=(-1.0, 0.0), point2=(1.0, 0.0))

    points1 = [(0.0, td2/2.0), (-(td1-td2)/2.0/sqrt(3.0), td1/2.0), (-(td1-td2)/2.0/sqrt(3.0)-tc, td1/2.0), (-(td1-td2)/sqrt(3.0)-tc, td2/2.0)]
    
    lines1 = []
    lines1.append(sk.Line(point1=points1[len(points1)-1], point2=points1[0]))
    for i in range(len(points1)-1):
        lines1.append(sk.Line(point1=points1[i], point2=points1[i+1]))
    
    #Create a part
    pa = mdb.models[modelName].Part(name=partName, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    pa.BaseSolidRevolve(sketch=sk, angle=((st_Adj+st_Nonadj)//tp+3)*360.0, flipRevolveDirection=ON, pitch=tp, flipPitchDirection=ON, moveSketchNormalToPath=OFF)

    #Seed the part
    pa.seedPart(size=0.5, deviationFactor=0.1, minSizeFactor=0.1)

    #Mesh the part
    pa.setMeshControls(regions=pa.cells, elemShape=HEX, technique=SWEEP, algorithm=ADVANCING_FRONT)
    pa.generateMesh()
    
    return pa

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Model-Function
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Define the model-creation function.

def SCS(mdbNumber=1,    sheetP_Adj=3, sheetP_Nonadj=4, sheetL=250.0, sheetW=50.0,    screwP=1, screwA_T1=4, screwA_T2=0, screwGD_L=4, screwGD_T=3, screwED=30.0):

    "Create a finite element model of self-drilling screw connections."

    #Screw characteristic parameters
    dn = screwC['dn'][screwP]
    tp = screwC['tp'][screwP]
    td1 = screwC['td1'][screwP]
    td2 = screwC['td2'][screwP]
    tc = screwC['tc'][screwP]
    a = screwC['a'][screwP]
    dc = screwC['dc'][screwP]
    c = screwC['c'][screwP]
    s = screwC['s'][screwP]
    k = screwC['k'][screwP]
    lg = screwC['lg'][screwP]

    #Sheet characteristic parameters
    st_Adj = sheetC['t'][sheetP_Adj]
    st_Nonadj = sheetC['t'][sheetP_Nonadj]

    #Screw arrangement parameters
    arr = screwA[screwA['type'][screwA_T1]][screwA_T2]
    lgd = screwGD_L*dn # screw longitudinal spacing distance
    tgd = screwGD_T*dn # screw transiversal spacing distance
    ed = screwED # screw longitudinal end distance

    #----------------------------
    # Model
    #----------------------------
    if mdbNumber < 10:
        mdbNumberStr = str(0)+str(mdbNumber) # change the number 1 ~ 9 to 01 ~ 09, which can be used in model naming.
    else:
        mdbNumberStr = str(mdbNumber)

    if int(st_Adj*10.0) < 10:
        sheetP_AdjStr = str(0)+str(int(st_Adj*10.0))
    else:
        sheetP_AdjStr = str(int(st_Adj*10.0))

    if int(st_Nonadj*10.0) < 10:
        sheetP_NonadjStr = str(0)+str(int(st_Nonadj*10.0))
    else:
        sheetP_NonadjStr = str(int(st_Nonadj*10.0))

    modelName = 'M'+mdbNumberStr+'-'+sheetP_AdjStr+'-'+sheetP_NonadjStr+'-'+str(int(dn*10.0))+'-'+screwA['type'][screwA_T1]+str(screwA_T2)+'_'+str(screwGD_L)+'_'+str(screwGD_T)
    mdb.Model(name=modelName) #! the symbol '/' is not allowed in model names.

    #----------------------------
    # Part
    #----------------------------
    #Creat parts
    d_parts = {}

    d_parts['partName'] = ['sheetAdjPart', 'sheetNonadjPart', 'screwPart','threadPart']

    sheetAdjPart = sheet(modelName=modelName, partName=d_parts['partName'][0], sheetPosition=0, sheetProfile=sheetP_Adj, sheetLength=sheetL, sheetWidth=sheetW, screwProfile=screwP, arrangementType1=screwA_T1, arrangementType2=screwA_T2, spacingDistanceLongitudinal=screwGD_L, spacingTransversalDistance=screwGD_T, endDistance=ed)

    sheetNonadjPart = sheet(modelName=modelName, partName=d_parts['partName'][1], sheetPosition=1, sheetProfile=sheetP_Nonadj, sheetLength=sheetL, sheetWidth=sheetW, screwProfile=screwP, arrangementType1=screwA_T1, arrangementType2=screwA_T2, spacingDistanceLongitudinal=screwGD_L, spacingTransversalDistance=screwGD_T, endDistance=ed)

    screwPart = screw(modelName=modelName, partName=d_parts['partName'][2], sheetProfile_Adj=sheetP_Adj, sheetProfile_Nonadj=sheetP_Nonadj, screwProfile=screwP)
    
    threadPart = thread(modelName=modelName, partName=d_parts['partName'][3], sheetProfile_Adj=sheetP_Adj, sheetProfile_Nonadj=sheetP_Nonadj, screwProfile=screwP)

    d_parts['part'] = [sheetAdjPart, sheetNonadjPart, screwPart, threadPart]

    #----------------------------
    # Mesh
    #----------------------------
    #Assign element types of Abaqus/Explicit
    elemType1 = mesh.ElemType(elemCode=C3D8R, elemLibrary=EXPLICIT, kinematicSplit=AVERAGE_STRAIN, secondOrderAccuracy=OFF, hourglassControl=DEFAULT, distortionControl=DEFAULT)
    elemType2 = mesh.ElemType(elemCode=C3D6, elemLibrary=EXPLICIT)
    elemType3 = mesh.ElemType(elemCode=C3D4, elemLibrary=EXPLICIT)

    for i in range(len(d_parts['part'])):
        region1 =(mdb.models[modelName].parts[d_parts['partName'][i]].cells, )
        mdb.models[modelName].parts[d_parts['partName'][i]].setElementType(regions=region1, elemTypes=(elemType1, elemType2, elemType3))

    #----------------------------
    # Property
    #----------------------------
    #Create materials

    ##0.4mm Q350 steel sheet #----------------------------
    T04_Q350 = mdb.models[modelName].Material(name='T04_Q350')
    T04_Q350.Density(table=((7.85e-09, ), ))
    T04_Q350.Elastic(table=((230555.5, 0.2489), ))

    ###plastic response in the form of the modified Ludwik equation
    T04_Q350.Plastic(table=((303.01289, 0.0), (404.01719, 0.00199), (425.47204, 0.04297), (427.71463, 0.044), (431.89949, 0.046), (435.87689, 0.048), (439.66807, 0.05), (456.38209, 0.06), (470.33432, 0.07), (482.36099, 0.08), (492.96223, 0.09), (502.4623, 0.1), (511.08404, 0.11), (518.98758, 0.12), (526.29202, 0.13), (533.0885, 0.14), (539.44839, 0.15), (545.42868, 0.16), (551.07565, 0.17), (556.42739, 0.18), (561.51568, 0.19), (566.36732, 0.2), (587.77263, 0.25), (605.65767, 0.3), (621.08408, 0.35), (634.68829, 0.4), (646.88358, 0.45), (657.95433, 0.5), (668.10505, 0.55), (677.48799, 0.6), (686.21972, 0.65), (694.39157, 0.7), (702.0765, 0.75), (709.33377, 0.8), (716.21219, 0.85), (722.75249, 0.9), (728.989, 0.95), (734.95098, 1.0), (761.41495, 1.25), (783.69512, 1.5), (803.01195, 1.75), (820.11089, 2.0)))
    ###damage responses in the form of the modified Johnson-Cook model
    T04_Q350.DuctileDamageInitiation(table=((4.2695045663533, -0.33333, 0.0), (0.136043185333343, -0.32, 0.0), (0.131525785938247, -0.31, 0.0), (0.114961580394987, -0.27, 0.0), (0.100567266292083, -0.23, 0.0), (0.0880585904034665, -0.19, 0.0), (0.0771885363412948, -0.15, 0.0), (0.0677424465739464, -0.11, 0.0), (0.0524004455461111, -0.03, 0.0), (0.0408147333404271, 0.05, 0.0), (0.0254586333591192, 0.21, 0.0), (0.0117075453832422, 0.53, 0.0), (0.00511838110766909, 2.0, 0.0)))
    T04_Q350.ductileDamageInitiation.DamageEvolution(table=((0.0493891, ), ), type=DISPLACEMENT)

    ##0.5mm Q350 steel sheet #----------------------------
    T05_Q350 = mdb.models[modelName].Material(name='T05_Q350')
    T05_Q350.Density(table=((7.85e-09, ), ))
    T05_Q350.Elastic(table=((219303.5, 0.2831), ))

    ###plastic response in the form of the modified Ludwik equation
    T05_Q350.Plastic(table=((297.72264, 0.0), (396.96353, 0.00198), (422.37359, 0.06164), (422.88189, 0.062), (425.67696, 0.064), (428.38103, 0.066), (431.00037, 0.068), (433.5406, 0.07), (445.2165, 0.08), (455.50656, 0.09), (464.72748, 0.1), (473.09643, 0.11), (480.76917, 0.12), (487.86143, 0.13), (494.46167, 0.14), (500.63914, 0.15), (506.44907, 0.16), (511.9363, 0.17), (517.13774, 0.18), (522.08416, 0.19), (526.8015, 0.2), (547.62632, 0.25), (565.04251, 0.3), (580.07706, 0.35), (593.34564, 0.4), (605.24814, 0.45), (616.05978, 0.5), (625.97855, 0.55), (635.15189, 0.6), (643.69272, 0.65), (651.68952, 0.7), (659.21303, 0.75), (666.32069, 0.8), (673.05985, 0.85), (679.47002, 0.9), (685.58452, 0.95), (691.43173, 1.0), (717.40831, 1.25), (739.30572, 1.5), (758.31073, 1.75), (775.14898, 2.0)))
    ###damage responses in the form of the modified Johnson-Cook model
    T05_Q350.DuctileDamageInitiation(table=((5.18361188872818, -0.33333, 0.0), (0.198204279877645, -0.32, 0.0), (0.19162278063951, -0.31, 0.0), (0.167490022689966, -0.27, 0.0), (0.146518627642503, -0.23, 0.0), (0.128294460675914, -0.19, 0.0), (0.112457638143391, -0.15, 0.0), (0.0986954207324972, -0.11, 0.0), (0.0763433196130412, -0.03, 0.0), (0.0594638388795621, 0.05, 0.0), (0.0370911966825032, 0.21, 0.0), (0.017056932026825, 0.53, 0.0), (0.00745703264517974, 2.0, 0.0)))
    T05_Q350.ductileDamageInitiation.DamageEvolution(table=((0.05775, ), ), type=DISPLACEMENT)

    ##0.6mm Q350 steel sheet #----------------------------
    T06_Q350 = mdb.models[modelName].Material(name='T06_Q350')
    T06_Q350.Density(table=((7.85e-09, ), ))
    T06_Q350.Elastic(table=((210557.0, 0.2783), ))

    ###plastic response in the form of the modified Ludwik equation
    T06_Q350.Plastic(table=((267.60027, 0.0), (356.80036, 0.00318), (368.83634, 0.03938), (370.38537, 0.04), (375.21523, 0.042), (379.78182, 0.044), (384.11508, 0.046), (388.23996, 0.048), (392.17751, 0.05), (409.60321, 0.06), (424.23067, 0.07), (436.89711, 0.08), (448.1057, 0.09), (458.18393, 0.1), (467.3577, 0.11), (475.78978, 0.12), (483.6016, 0.13), (490.88628, 0.14), (497.71692, 0.15), (504.15202, 0.16), (510.23915, 0.17), (516.01757, 0.18), (521.52006, 0.19), (526.77432, 0.2), (550.04407, 0.25), (569.59481, 0.3), (586.53484, 0.35), (601.53173, 0.4), (615.02071, 0.45), (627.30232, 0.5), (638.59333, 0.55), (649.05556, 0.6), (658.81321, 0.65), (667.9638, 0.7), (676.58541, 0.75), (684.74155, 0.8), (692.48467, 0.85), (699.85856, 0.9), (706.90023, 0.95), (713.64122, 1.0), (743.67139, 1.25), (769.08828, 1.5), (791.22158, 1.75), (810.88722, 2.0)))
    ###damage responses in the form of the modified Johnson-Cook model
    T06_Q350.DuctileDamageInitiation(table=((6.29306164956642, -0.33333, 0.0), (0.751956201005406, -0.32, 0.0), (0.726986998956064, -0.31, 0.0), (0.635431004273488, -0.27, 0.0), (0.555868737189629, -0.23, 0.0), (0.486729033498244, -0.19, 0.0), (0.426646549655821, -0.15, 0.0), (0.374434800516884, -0.11, 0.0), (0.289634345653167, -0.03, 0.0), (0.225596175978977, 0.05, 0.0), (0.140717791406782, 0.21, 0.0), (0.0647108537778709, 0.53, 0.0), (0.0282903029822753, 2.0, 0.0)))
    T06_Q350.ductileDamageInitiation.DamageEvolution(table=((0.0681322, ), ), type=DISPLACEMENT)

    ##0.8mm Q550 steel sheet #----------------------------
    T08_Q550 = mdb.models[modelName].Material(name='T08_Q550')
    T08_Q550.Density(table=((7.85e-09, ), ))
    T08_Q550.Elastic(table=((245163.333333333, 0.234466666666667), ))

    ###plastic response in the form of the initiated Ludwik equation
    T08_Q550.Plastic(table=((783.0914841, 0.0), (811.0813275, 0.01), (824.1819422, 0.02), (834.5287566, 0.03), (843.4142849, 0.04), (851.3504892, 0.05), (858.6039141, 0.06), (865.3347358, 0.07), (871.648304, 0.08), (877.6183795, 0.09), (883.2990397, 0.1), (893.947422, 0.12), (903.8285972, 0.14), (913.0972239, 0.16), (921.8615866, 0.18), (930.2010734, 0.2), (938.1759831, 0.22), (945.833419, 0.24), (953.2110265, 0.26), (960.3394672, 0.28), (967.2441166, 0.3), (983.6586133, 0.35), (999.0555512, 0.4), (1013.614812, 0.45), (1027.468273, 0.5), (1040.716103, 0.55), (1053.436549, 0.6), (1065.692147, 0.65), (1077.533832, 0.7), (1089.003758, 0.75), (1100.13729, 0.8), (1121.510996, 0.9), (1141.848554, 1.0), (1161.297016, 1.1), (1179.971253, 1.2), (1197.96307, 1.3), (1215.347242, 1.4), (1232.185654, 1.5), (1248.530223, 1.6), (1264.425025, 1.7), (1279.907867, 1.8), (1295.011473, 1.9), (1309.764397, 2.0)))

    ##1.0mm Q550 steel sheet #----------------------------
    T10_Q550 = mdb.models[modelName].Material(name='T10_Q550')
    T10_Q550.Density(table=((7.85e-09, ), ))
    T10_Q550.Elastic(table=((226738.0, 0.2503), ))

    ###plastic response in the form of the initiated Ludwik equation
    T10_Q550.Plastic(table=((813.6921151, 0.0), (828.3909183, 0.01), (833.8909027, 0.02), (838.0183822, 0.03), (841.448866, 0.04), (844.4395331, 0.05), (847.1207619, 0.06), (849.5693187, 0.07), (851.8348608, 0.08), (853.9516696, 0.09), (855.944573, 0.1), (859.6290614, 0.12), (862.9938169, 0.14), (866.1070774, 0.16), (869.0159517, 0.18), (871.7545578, 0.2), (874.3485312, 0.22), (876.8177046, 0.24), (879.1777897, 0.26), (881.4414812, 0.28), (883.6192076, 0.3), (888.7411757, 0.35), (893.4803078, 0.4), (897.9083148, 0.45), (902.0771326, 0.5), (906.0257847, 0.55), (909.7844611, 0.6), (913.3770789, 0.65), (916.8229624, 0.7), (920.1379864, 0.75), (923.3353784, 0.8), (929.420253, 0.9), (935.1489551, 1.0), (940.5751101, 1.1), (945.7402044, 1.2), (950.6771046, 1.3), (955.4123655, 1.4), (959.967802, 1.5), (964.3615912, 1.6), (968.6090656, 1.7), (972.7232983, 1.8), (976.7155413, 1.9), (980.5955608, 2.0)))

    ##2.5mm thickness Q350 steel sheet #----------------------------
    T25_Q350 = mdb.models[modelName].Material(name='T25_Q350')
    T25_Q350.Density(table=((7.85e-09, ), ))
    T25_Q350.Elastic(table=((223477.666666667, 0.276833333333333), ))

    ###plastic response in the form of the modified Ludwik equation
    T25_Q350.Plastic(table=((289.06005, 0.0), (385.41341, 0.00204), (399.35796, 0.02155), (401.98821, 0.022), (412.61708, 0.024), (422.00103, 0.026), (430.42118, 0.028), (438.07126, 0.03), (445.09073, 0.032), (451.58353, 0.034), (457.6293, 0.036), (463.29048, 0.038), (468.617, 0.04), (473.64943, 0.042), (478.4212, 0.044), (482.96024, 0.046), (487.29008, 0.048), (491.43079, 0.05), (509.82753, 0.06), (525.33666, 0.07), (538.79783, 0.08), (550.72457, 0.09), (561.45521, 0.1), (571.22508, 0.11), (580.20488, 0.12), (588.52258, 0.13), (596.2767, 0.14), (603.54481, 0.15), (610.38913, 0.16), (616.86038, 0.17), (623.00048, 0.18), (628.84448, 0.19), (634.42203, 0.2), (659.08706, 0.25), (679.75926, 0.3), (697.63029, 0.35), (713.41844, 0.4), (727.59203, 0.45), (740.47435, 0.5), (752.29843, 0.55), (763.23814, 0.6), (773.42682, 0.65), (782.96911, 0.7), (791.9487, 0.75), (800.43365, 0.8), (808.48009, 0.85), (816.13487, 0.9), (823.43754, 0.95), (830.42181, 1.0), (861.45829, 1.25), (887.62964, 1.5), (910.34895, 1.75), (930.481, 2.0)))

    ##screw: carbon steel/C15 hard alloy steel #----------------------------
    carbonSteel = mdb.models[modelName].Material(name='carbonSteel')
    carbonSteel.Density(table=((7.85e-09, ), ))
    carbonSteel.Elastic(table=((206000.0, 0.3), ))
    carbonSteel.Plastic(table=((954.381068, 0.0), (1063.242233, 0.007403284), (1065.342233, 0.009334365)))

    ##ST4.2 self-drilling screw
    D42_CarbonSteel = mdb.models[modelName].Material(name='D42_CarbonSteel', objectToCopy=mdb.models[modelName].materials['carbonSteel'])

    ##ST4.8 self-drilling screw
    D48_CarbonSteel = mdb.models[modelName].Material(name='D48_CarbonSteel', objectToCopy=mdb.models[modelName].materials['carbonSteel'])

    ##ST5.5 self-drilling screw
    D55_CarbonSteel = mdb.models[modelName].Material(name='D55_CarbonSteel', objectToCopy=mdb.models[modelName].materials['carbonSteel'])

    ##ST6.3 self-drilling screw
    D63_CarbonSteel = mdb.models[modelName].Material(name='D63_CarbonSteel', objectToCopy=mdb.models[modelName].materials['carbonSteel'])

    #Create sections
    d_parts['sectionName'] = ['sheetAdjSection', 'sheetNonadjSection', 'screwSection', 'threadSection']
    d_parts['materialName'] = [sheetC['material'][sheetP_Adj], sheetC['material'][sheetP_Nonadj], screwC['material'][screwP], screwC['material'][screwP]]

    for i in range(len(d_parts['part'])):
        mdb.models[modelName].HomogeneousSolidSection(name=d_parts['sectionName'][i], material=d_parts['materialName'][i], thickness=None)
    
    #Assign sections
    for i in range(len(d_parts['part'])):
        region0 = regionToolset.Region(cells=d_parts['part'][i].cells)
        d_parts['part'][i].SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, region=region0, sectionName=d_parts['sectionName'][i], thicknessAssignment=FROM_SECTION)

    #----------------------------
    # Assembly
    #----------------------------
    #Create instances
    roAs = mdb.models[modelName].rootAssembly

    d_instances = {}
    d_instances['instanceName'] = []
    d_instances['instance'] = []

    ##Create sheet instances
    ###Sheet adjunct to screw head
    d_instances['instanceName'].append(d_parts['partName'][0])
    d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][0], part=d_parts['part'][0], dependent=ON))
    roAs.rotate(instanceList=(d_parts['partName'][0], ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=0.0)
    roAs.translate(instanceList=(d_parts['partName'][0], ), vector=(0.0, 0.0, -(st_Adj)))

    ###Sheet not adjunct to screw head
    d_instances['instanceName'].append(d_parts['partName'][1])
    d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][1], part=d_parts['part'][1], dependent=ON))
    #roAs.rotate(instanceList=(d_parts['partName'][1], ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=180.0)
    roAs.translate(instanceList=(d_parts['partName'][1], ), vector=(0.0, 0.0, -(st_Adj+st_Nonadj)))
    
    ##Create the screw and thread instances
    for i in range(len(arr)):
        if screwA_T1 < 6:
            for j in range(arr[i]):
                x = -sheetW/2.0+(sheetW-(arr[i]-1)*tgd)/2.0+j*tgd
                y = i*lgd

                ###Screw
                d_instances['instanceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j))
                d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j), part=d_parts['part'][2], dependent=ON))
                roAs.rotate(instanceList=(d_parts['partName'][2]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=270.0)
                roAs.translate(instanceList=(d_parts['partName'][2]+'-'+str(i)+'_'+str(j), ), vector=(x, y, 0.0))

                ###Thread
                rotateAngle = 270.0
                d_instances['instanceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j))
                d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j), part=d_parts['part'][3], dependent=ON))
                roAs.rotate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=270.0)
                roAs.rotate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=rotateAngle)
                roAs.translate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), vector=(x, y, 0.0))
                
        else:
            for j in range(1):
                x = -sheetW/2.0+(sheetW-tgd)/2.0+i%2*tgd
                y = i*lgd

                ###Screw
                d_instances['instanceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j))
                d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j), part=d_parts['part'][2], dependent=ON))
                roAs.rotate(instanceList=(d_parts['partName'][2]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=270.0)
                roAs.translate(instanceList=(d_parts['partName'][2]+'-'+str(i)+'_'+str(j), ), vector=(x, y, 0.0))

                ###Thread
                rotateAngle = 90.0
                d_instances['instanceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j))
                d_instances['instance'].append(roAs.Instance(name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j), part=d_parts['part'][3], dependent=ON))
                roAs.rotate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=270.0)
                roAs.rotate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=rotateAngle)
                roAs.translate(instanceList=(d_parts['partName'][3]+'-'+str(i)+'_'+str(j), ), vector=(x, y, 0.0))
    
    #Create reference points and corresponding sets
    referencePoint1 = roAs.ReferencePoint(point=(0.0, (len(arr)-1)*lgd+ed+bCF1, -st_Adj/2.0), instanceName=d_parts['partName'][0])
    roAs.Set(referencePoints=(roAs.referencePoints[referencePoint1.id], ), name='sheetAdj_RP') #! referencePoint.id

    referencePoint2 = roAs.ReferencePoint(point=(0.0, -ed-bCF1, -st_Adj-st_Nonadj/2.0), instanceName=d_parts['partName'][1])
    roAs.Set(referencePoints=(roAs.referencePoints[referencePoint2.id], ), name='sheetNonadj_RP')

    #Create Sets

    d_surfaces = {}
    d_surfaces['surfaceName'] = []
    d_surfaces['surface'] = []

    #Create surfaces
    ##Surface of sheetAdj elments
    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-surfErode')
    surfE = roAs.instances[d_parts['partName'][0]].elements.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=0.0+bCF1)
    d_surfaces['surface'].append(roAs.Surface(face1Elements=surfE, face2Elements=surfE, face3Elements=surfE, face4Elements=surfE, face5Elements=surfE, face6Elements=surfE, name=d_parts['partName'][0]+'-surfErode'))

    ##Surface of sheetNonadj elments
    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-surfErode')
    surfE = roAs.instances[d_parts['partName'][1]].elements.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-st_Nonadj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=-st_Adj+bCF1)
    d_surfaces['surface'].append(roAs.Surface(face1Elements=surfE, face2Elements=surfE, face3Elements=surfE, face4Elements=surfE, face5Elements=surfE, face6Elements=surfE, name=d_parts['partName'][1]+'-surfErode'))

    ##Surface of sheetAdj loading end
    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-E')
    surface0 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=(len(arr)-1)*lgd+ed-bCF1, zMin=-st_Adj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=0.0+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface0, name=d_parts['partName'][0]+'-E'))

    ##Surface of sheetNonadj fixed end
    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-E')
    surface0 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-st_Nonadj-bCF1, xMax=sheetW/2.0+bCF1, yMax=-ed+bCF1, zMax=-st_Adj+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface0, name=d_parts['partName'][1]+'-E'))

    ##Surface of sheetAdj total
    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-T')
    surface1 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=0.0+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface1, name=d_parts['partName'][0]+'-T'))

    ##Surface of sheetNonadj total
    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-T')
    surface1 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-st_Nonadj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=-st_Adj+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface1, name=d_parts['partName'][1]+'-T'))

    ##Surface of sheetAdj below
    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-B')
    surface2 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=-st_Adj+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface2, name=d_parts['partName'][0]+'-B'))

    ##Surface of sheetNonadj above
    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-A')
    surface2 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingBox(xMin=-sheetW/2.0-bCF1, yMin=-ed-bCF1, zMin=-st_Adj-bCF1, xMax=sheetW/2.0+bCF1, yMax=(len(arr)-1)*lgd+ed+bCF1, zMax=-st_Adj+bCF1)
    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface2, name=d_parts['partName'][1]+'-A'))

    for i in range(len(arr)):
            if screwA_T1 < 6:
                for j in range(arr[i]):
                    x = -sheetW/2.0+(sheetW-(arr[i]-1)*tgd)/2.0+j*tgd
                    y = i*lgd

                    ##Surface of sheetAdj above around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=0.0-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=0.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'))
                    
                    ##Surface of sheetAdj middle around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -st_Adj-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'))

                    ##Surface of sheetAdj below around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=-st_Adj-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=-st_Adj+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'))

                    ##Surface of sheetNonadj middle around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA')
                    surface3 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingCylinder(center1=(x, y, -st_Adj+bCF1), center2=(x, y, -st_Adj-st_Nonadj-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'))

                    ##Surface of sheetNonadj below around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA')
                    surface3 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=-st_Adj-st_Nonadj-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=-st_Adj-st_Nonadj+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'))

                    ##Surface of screw washer
                    d_surfaces['surfaceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c')
                    surface3 = roAs.instances[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, c/2.0+bCF1), center2=(x, y, 0.0-bCF1), radius=dc/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c'))

                    ##Surface of screw shank
                    d_surfaces['surfaceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b')
                    surface3 = roAs.instances[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'))

                    ##Surface of thread outer
                    d_surfaces['surfaceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O')
                    surface3 = roAs.instances[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'))
                    
                    ##Surface of thread inner
                    d_surfaces['surfaceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I')
                    surface3 = roAs.instances[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td2/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I'))

            else:
                for j in range(1):
                    x = -sheetW/2.0+(sheetW-tgd)/2.0+i%2*tgd
                    y = i*lgd

                    ##Surface of sheetAdj above around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=0.0-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=0.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'))
                    
                    ##Surface of sheetAdj middle around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -st_Adj-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'))

                    ##Surface of sheetAdj below around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA')
                    surface3 = roAs.instances[d_parts['partName'][0]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=-st_Adj-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=-st_Adj+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'))

                    ##Surface of sheetNonadj middle around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA')
                    surface3 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingCylinder(center1=(x, y, -st_Adj+bCF1), center2=(x, y, -st_Adj-st_Nonadj-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'))

                    ##Surface of sheetNonadj below around screw
                    d_surfaces['surfaceName'].append(d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA')
                    surface3 = roAs.instances[d_parts['partName'][1]].faces.getByBoundingBox(xMin=x-tgd/2.0-bCF1, yMin=y-lgd/2.0-bCF1, zMin=-st_Adj-st_Nonadj-bCF1, xMax=x+tgd/2.0+bCF1, yMax=y+lgd/2.0+bCF1, zMax=-st_Adj-st_Nonadj+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'))

                    ##Surface of screw washer
                    d_surfaces['surfaceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c')
                    surface3 = roAs.instances[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, c/2.0+bCF1), center2=(x, y, 0.0-bCF1), radius=dc/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c'))

                    ##Surface of screw shank
                    d_surfaces['surfaceName'].append(d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b')
                    surface3 = roAs.instances[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'))

                    ##Surface of thread outer
                    d_surfaces['surfaceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O')
                    surface3 = roAs.instances[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td1/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'))
                    
                    ##Surface of thread inner
                    d_surfaces['surfaceName'].append(d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I')
                    surface3 = roAs.instances[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)].faces.getByBoundingCylinder(center1=(x, y, 0.0+bCF1), center2=(x, y, -((st_Adj+st_Nonadj)//tp+4)*tp-bCF1), radius=td2/2.0+bCF1)
                    d_surfaces['surface'].append(roAs.Surface(side1Faces=surface3, name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I'))

    #----------------------------
    # Step
    #----------------------------
    #Quasi-Static analysis
    ##Create steps
    mdb.models[modelName].ExplicitDynamicsStep(name='Step-1', previous='Initial', timePeriod=0.06)
    
    ##Set output requests
    mdb.models[modelName].fieldOutputRequests['F-Output-1'].suppress()
    ##'S', 'PEEQ', 'LE', 'U', 'RF', 'STATUS'
    mdb.models[modelName].FieldOutputRequest(name='F-Output-loadStep', createStepName='Step-1', variables=('S', 'U', 'RF', 'STATUS'), numIntervals=250)
    
    mdb.models[modelName].historyOutputRequests['H-Output-1'].suppress()
    mdb.models[modelName].HistoryOutputRequest(name='H-Output-loadStep', createStepName='Step-1', variables=('ALLIE', 'ALLKE'), numIntervals=250)

    #----------------------------
    # Interaction
    #----------------------------
    #Create interaction properties
    #Default contact property
    mdb.models[modelName].ContactProperty('default')

    ##friction coefficient 0.00
    mdb.models[modelName].ContactProperty('friction-00')
    mdb.models[modelName].interactionProperties['friction-00'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=DEFAULT)
    mdb.models[modelName].interactionProperties['friction-00'].TangentialBehavior(formulation=FRICTIONLESS)

    ##friction coefficient 0.25
    mdb.models[modelName].ContactProperty('friction-25')
    mdb.models[modelName].interactionProperties['friction-25'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=DEFAULT)
    mdb.models[modelName].interactionProperties['friction-25'].TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, table=((0.25, ), ), shearStressLimit=None, maximumElasticSlip=FRACTION, fraction=0.005, elasticSlipStiffness=None)

    ##friction coefficient 4.00
    mdb.models[modelName].ContactProperty('friction-400')
    mdb.models[modelName].interactionProperties['friction-400'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=DEFAULT)
    mdb.models[modelName].interactionProperties['friction-400'].TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF, pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, table=((4.00, ), ), shearStressLimit=None, maximumElasticSlip=FRACTION, fraction=0.005, elasticSlipStiffness=None)

    #Create interactions
    mdb.models[modelName].ContactExp(name='generalContact', createStepName='Initial')
    
    ##All - self; All - sheetAdj elments; sheetAdj elments - self
    mdb.models[modelName].interactions['generalContact'].includedPairs.setValuesInStep(stepName='Initial', useAllstar=ON)
    
    if sheetP_Adj < 3:
        mdb.models[modelName].interactions['generalContact'].includedPairs.setValuesInStep(stepName='Initial', useAllstar=OFF, addPairs=((ALLSTAR, SELF), (ALLSTAR, roAs.surfaces[d_parts['partName'][0]+'-surfErode']), (roAs.surfaces[d_parts['partName'][0]+'-surfErode'], SELF)))
    
    if sheetP_Nonadj < 3:
        mdb.models[modelName].interactions['generalContact'].includedPairs.setValuesInStep(stepName='Initial', useAllstar=OFF, addPairs=((ALLSTAR, SELF), (ALLSTAR, roAs.surfaces[d_parts['partName'][1]+'-surfErode']), (roAs.surfaces[d_parts['partName'][1]+'-surfErode'], SELF)))

    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((GLOBAL, SELF, 'default'), ))

    ##sheetAdj elments - self
    if sheetP_Adj < 3:
        mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-surfErode'], SELF, 'friction-400'), ))
    
    ##sheetNonadj elments - self
    if sheetP_Nonadj < 3:
        mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][1]+'-surfErode'], SELF, 'friction-400'), ))

    # ##sheetAdj total - self
    # mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-T'], SELF, 'friction-35'), ))

    # ##sheetNonadj total - self
    # mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][1]+'-T'], SELF, 'friction-35'), ))

    ##sheetAdj below - sheetNonadj above
    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-B'], roAs.surfaces[d_parts['partName'][1]+'-A'], 'friction-25'), ))

    ##around screw
    for i in range(len(arr)):
            if screwA_T1 < 6:
                for j in range(arr[i]):
                    x = -sheetW/2.0+(sheetW-(arr[i]-1)*tgd)/2.0+j*tgd
                    y = i*lgd

                    ##sheetAdj above around screw - screw washer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c'], 'friction-25'), ))

                    ##sheetAdj above around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj above around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##sheetAdj middle around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj middle around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##sheetAdj below around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj below around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##screw shank - sheetNonadj middle around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'], 'friction-25'), ))

                    ##thread outer - sheetNonadj middle around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'], 'friction-25'), ))

                    ##screw shank - sheetNonadj below around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'], 'friction-25'), ))

                    ##thread outer - sheetNonadj below around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'], 'friction-25'), ))
            else:
                for j in range(1):
                    x = -sheetW/2.0+(sheetW-tgd)/2.0+i%2*tgd
                    y = i*lgd

                    ##sheetAdj above around screw - screw washer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-c'], 'friction-25'), ))

                    ##sheetAdj above around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj above around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-AA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##sheetAdj middle around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj middle around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-MA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##sheetAdj below around screw - screw shank
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'], roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], 'friction-25'), ))

                    ##sheetAdj below around screw - thread outer
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][0]+'-'+str(i)+'_'+str(j)+'-BA'], roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], 'friction-25'), ))

                    ##screw shank - sheetNonadj middle around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'], 'friction-25'), ))

                    ##thread outer - sheetNonadj middle around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-MA'], 'friction-25'), ))

                    ##screw shank - sheetNonadj below around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'], 'friction-25'), ))

                    ##thread outer - sheetNonadj below around screw
                    mdb.models[modelName].interactions['generalContact'].contactPropertyAssignments.appendInStep(stepName='Initial', assignments=((roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-O'], roAs.surfaces[d_parts['partName'][1]+'-'+str(i)+'_'+str(j)+'-BA'], 'friction-25'), ))
    
    #Create Tie constraints
    for i in range(len(arr)):
        if screwA_T1 < 6:
            for j in range(arr[i]):
                x = -sheetW/2.0+(sheetW-(arr[i]-1)*tgd)/2.0+j*tgd
                y = i*lgd
                ##thread inner - screw shank
                mdb.models[modelName].Tie(name=d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I--'+d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b', master=roAs.surfaces[d_parts['partName'][3]+'-'+str(i)+'_'+str(j)+'-I'], slave=roAs.surfaces[d_parts['partName'][2]+'-'+str(i)+'_'+str(j)+'-b'], positionToleranceMethod=COMPUTED, adjust=ON, tieRotations=ON, thickness=ON)
    
    #Create coupling constraints
    ##Loading point
    mdb.models[modelName].Coupling(name='loadPoint', controlPoint=roAs.sets['sheetAdj_RP'], surface=roAs.surfaces[d_parts['partName'][0]+'-E'], influenceRadius=WHOLE_SURFACE, couplingType=KINEMATIC, localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    ##Fixed point
    mdb.models[modelName].Coupling(name='fixPoint', controlPoint=roAs.sets['sheetNonadj_RP'], surface=roAs.surfaces[d_parts['partName'][1]+'-E'], influenceRadius=WHOLE_SURFACE, couplingType=KINEMATIC, localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    #----------------------------
    # Load
    #----------------------------
    #Create boundary conditions
    ##Encastre
    mdb.models[modelName].EncastreBC(name='sheetNonadj_encastre', createStepName='Initial', region=roAs.sets['sheetNonadj_RP'], localCsys=None)
    
    ##Displacement
    mdb.models[modelName].DisplacementBC(name='sheetAdj_displacement', createStepName='Initial', region=roAs.sets['sheetAdj_RP'], u1=0.0, u2=UNSET, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0, amplitude=UNSET, fixed=OFF, localCsys=None, distributionType=UNIFORM, fieldName='')
    
    ##Amplitude
    ###Smooth
    mdb.models[modelName].SmoothStepAmplitude(name='velocityAmp', timeSpan=STEP, data=((0.0, 0.0), (0.02, 200.0), (1.0, 200.0)))
    
    ##Velocity
    mdb.models[modelName].VelocityBC(name='sheetAdj_velocity', createStepName='Step-1', region=roAs.sets['sheetAdj_RP'], v1=UNSET, v2=1.0, v3=UNSET, vr1=UNSET, vr2=UNSET, vr3=UNSET, amplitude='velocityAmp', localCsys=None, distributionType=UNIFORM, fieldName='')

    #----------------------------
    # Job
    #----------------------------
    #Create a job
    d_jobs['name'].append('J'+modelName)
    mdb.Job(name='J'+modelName, model=modelName, description='', type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='', multiprocessingMode=DEFAULT, numCpus=4, numDomains=4, numGPUs=0)

    return

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Verification of shear tests
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Test specimens
shearT = {}
shearT['mdbNumber'    ] = [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
shearT['sheetP_Adj'   ] = [ 2,  1,  0,  0,  5,  4,  4,  5,  4,  3,  4,  3,  3,  4,  4,  4,  4,  4,  4]
shearT['sheetP_Nonadj'] = [ 4,  4,  4,  5,  5,  5,  4,  5,  5,  5,  4,  4,  3,  4,  4,  4,  4,  4,  4]
shearT['screwP'       ] = [ 1,  1,  1,  1,  2,  2,  2,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1]
shearT['screwA_T1'    ] = [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  2,  2,  2]
shearT['screwA_T2'    ] = [ 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0]
shearT['screwGD_L'    ] = [ 4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  5,  6,  4,  4,  4]
shearT['screwGD_T'    ] = [ 4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  4,  5,  6]

#Test groups
testGroup1 = [ 1,  2,  3,  4]
testGroup2 = [ 5,  6,  7,  8,  9, 10, 11, 12, 13]
testGroup3 = [ 14, 15, 16, 17, 18, 19]

d_jobs = {}
d_jobs['name'] = []

mdbIndex = 0
for i in testGroup1:

    mdbIndex = shearT['mdbNumber'][i-1]

    SCS(mdbNumber     =  mdbIndex, 
        sheetP_Adj    =  shearT['sheetP_Adj'][i-1], 
        sheetP_Nonadj =  shearT['sheetP_Nonadj'][i-1], 
        sheetL        =  250.0, 
        sheetW        =  50.0, 
        screwP        =  shearT['screwP'][i-1], 
        screwA_T1     =  shearT['screwA_T1'][i-1], 
        screwA_T2     =  shearT['screwA_T2'][i-1], 
        screwGD_L     =  shearT['screwGD_L'][i-1], 
        screwGD_T     =  shearT['screwGD_T'][i-1], 
        screwED       =  30.0)

mdb.save()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# parametric analysis
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# d_jobs = {}
# d_jobs['name'] = []

# mdbIndex = 0

# #Facotr: all
# for j1 in range(len(sheetC['type'])): # sheet adjunct to screw head
#     for j2 in range(j1, len(sheetC['type']), 1): # sheet not adjunct to screw head
        
#         for i1 in range(len(screwC['type'])): # screw profile
#             for i2 in range(len(screwA['type'])): # screw arrangement type1
#                 for i3 in range(len(screwA[screwA['type'][i2]])): # screw arrangement type2
#                     for i4 in range(len(screwA['spacingDistanceL'])): # screw longitudinal spacing distance
#                         for i5 in range(len(screwA['spacingDistanceT'])): # screw transversal spacing distance
                            

# #Factor: sheet thickness (single screw)
# for j1 in range(len(sheetC['type'])): # sheet adjunct to screw head
#     for j2 in range(j1, len(sheetC['type']), 1): # sheet not adjunct to screw head
        
#         for i1 in [1]: # screw profile
#             for i2 in [0]: # screw arrangement type1
#                 for i3 in [0]: # screw arrangement type2
#                     for i4 in [1]: # screw longitudinal spacing distance
#                         for i5 in [1]: # screw transversal spacing distance
                            

# #Factor: sheet thickness (double screws)
# for j1 in range(len(sheetC['type'])): # sheet adjunct to screw head
#     for j2 in range(j1, len(sheetC['type']), 1): # sheet not adjunct to screw head
        
#         for i1 in [1]: # screw profile
#             for i2 in [1]: # screw arrangement type1
#                 for i3 in [0]: # screw arrangement type2
#                     for i4 in [1]: # screw longitudinal spacing distance
#                         for i5 in [1]: # screw transversal spacing distance
                            

# #Factor: screw spacing distance
# for j1 in range(len(sheetC['type'])): # sheet adjunct to screw head
#     for j2 in range(j1, len(sheetC['type']), 1): # sheet not adjunct to screw head
        
#         for i1 in [1]: # screw profile
#             for i2 in [1]: # screw arrangement type1
#                 for i3 in [1]: # screw arrangement type2
#                     for i4 in [1, 3, 4, 5]: # screw longitudinal spacing distance
#                         for i5 in [1]: # screw transversal spacing distance
                            

# #Factor: screw arrangement
# for j1 in [4]: # sheet adjunct to screw head
#     for j2 in [4]: # sheet not adjunct to screw head
        
#         for i1 in [1]: # screw profile
#             for i2 in range(len(screwA['type'])): # screw arrangement type1
#                 for i3 in range(len(screwA[screwA['type'][i2]])): # screw arrangement type2
#                     for i4 in [2]: # screw longitudinal spacing distance
#                         for i5 in [0]: # screw transversal spacing distance


#                             mdbIndex += 1

#                             SCS(mdbNumber     =  mdbIndex, 
#                                 sheetP_Adj    =  sheetC['type'][j1], 
#                                 sheetP_Nonadj =  sheetC['type'][j2], 
#                                 sheetL        =  sheetC['length'][0], 
#                                 sheetW        =  sheetC['width'][0], 
#                                 screwP        =  screwC['type'][i1], 
#                                 screwA_T1     =  i2, 
#                                 screwA_T2     =  i3, 
#                                 screwGD_L     =  screwA['spacingDistanceL'][i4], 
#                                 screwGD_T     =  screwA['spacingDistanceT'][i5], 
#                                 screwED       =  screwA['endDistance'][0])

# mdb.save()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Computation
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

for i in range(len(d_jobs['name'])):

    #Write input file
    mdb.jobs[d_jobs['name'][i]].writeInput(consistencyChecking=OFF)
    
    # #Check job
    # mdb.jobs[d_jobs['name'][i]].submit(consistencyChecking=OFF, datacheckJob=True)
    # mdb.jobs[d_jobs['name'][i]].waitForCompletion()

    # #Submit job
    # mdb.jobs[d_jobs['name'][i]].submit()
    # mdb.jobs[d_jobs['name'][i]].waitForCompletion()

    # #Delete job.
    # del mdb.jobs[d_jobs['name'][i]]

# #Copy result files
# copyFiles(sourceDir=path,targetDir="G:\\SIMULIA\\"+pathSplit[-1])