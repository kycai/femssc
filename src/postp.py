# built-in Python 2 in Abaqus
# -*- coding: utf-8 -*-
# 
# Post-processing script for finite element modeling of self-drilling screw connections between thin steel sheets
# Ver 1.0, by Kangyi Cai June, 2021 @ WHU

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Initialization
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Import modules
from abaqusConstants import *
from abaqus import *

from odbAccess import *
from visualization import *

from multiprocessing import cpu_count
from math import *
import os

###################################################################################################
###################################################################################################
#Change processing mode
switchMode = 3 # 1 - Submit job | 2 - Export result | 3 - Submit job & Export result

#Copy files
copyOrNot  = 0 # 1 - copy resulting files | 0 - not copy resulting files
targetDirM = "E:\\sync\\" # target directory for copying files

###################################################################################################
###################################################################################################

def mkdir(dir):
    
    "Set the working directory."
    
    folder = os.path.exists(dir)
    
    if not folder:
        os.makedirs(dir)

def copyFiles(sourceDir, targetDir):

    "Copy resulting files."

    for f in os.listdir(sourceDir):

        fSplit = f.split('.')

        if len(fSplit) == 2:

            #Access inp files' name
            if fSplit[1] == 'png' or fSplit[1] == 'rpt':

                sourceF = os.path.join(sourceDir, f)
                targetF = os.path.join(targetDir, f)

                if os.path.isfile(sourceF):

                    #Create the working directory
                    if not os.path.exists(targetDir):
                        os.makedirs(targetDir)

                    #Copy any file that doesn't exist AND overwrite any file that isn't the latest version.
                    if not os.path.exists(targetF) or (os.path.exists(targetF) and (os.path.getsize(targetF) != os.path.getsize(sourceF))):
                        open(targetF, "wb").write(open(sourceF, "rb").read()) #binary file

                if os.path.isdir(sourceF):
                    copyFiles(sourceF, targetF)

currentPath = os.path.abspath("postp.py")
sourceDirM = os.path.abspath(os.path.dirname(currentPath) + os.path.sep + ".")
pathSplit = sourceDirM.split('\\')
caeNameM = pathSplit[-1]+".cae"

#Set the working directory
mkdir(sourceDirM)
mdb.saveAs(pathName=sourceDirM+"\\"+caeNameM) 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Functions
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def jobSubmit(jobName, numberOfUsedCores):

    "Submit job."

    #Import inp file
    mdb.ModelFromInputFile(name=jobName, inputFileName=jobName+'.inp')

    #Recreate job
    mdb.Job(name=jobName, model=jobName, description='', type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='', multiprocessingMode=DEFAULT, numCpus=numberOfUsedCores, numDomains=numberOfUsedCores, numGPUs=0) 
        
    #Submit job
    mdb.jobs[jobName].submit()
    mdb.jobs[jobName].waitForCompletion()

def resultExport(odbName):

    "Export result."

    #Open odb file
    o3 = session.openOdb(name=odbName, path=odbName+'.odb', readOnly=True)

    #Export ALLKE/ALLIE versus step curve
    ##Export variables
    session.viewports['Viewport: 1'].setValues(displayedObject=o3)
    session.XYDataFromHistory(name='ALLIE', odb=session.odbs[odbName+'.odb'], outputVariableName='Internal energy: ALLIE for Whole Model', steps=('Step-1', ), )
    session.XYDataFromHistory(name='ALLKE', odb=session.odbs[odbName+'.odb'], outputVariableName='Kinetic energy: ALLKE for Whole Model', steps=('Step-1', ), )

    ##Generate curve
    xy0 = session.xyDataObjects['ALLKE']/session.xyDataObjects['ALLIE']
    xy0.setValues(sourceDescription='"ALLKE" / "ALLIE"')
    session.xyDataObjects.changeKey(xy0.name, odbName+'_ALLKE-ALLIE')
    
    ##Export curve
    x0 = session.xyDataObjects[odbName+'_ALLKE-ALLIE']
    session.xyReportOptions.setValues(numberFormat=SCIENTIFIC, minMax=ON, layout=SEPARATE_TABLES)
    session.writeXYReport(fileName=odbName+'_ALLKE-ALLIE.rpt', xyData=(x0, ))

    ##Clear data
    del session.xyDataObjects['XYData-1']
    del session.xyDataObjects['XYData-2']
    del session.xyDataObjects[odbName+'_ALLKE-ALLIE']
    
    #Export RF2 versus U2 curves
    ##Export variables
    session.viewports['Viewport: 1'].setValues(displayedObject=o3)
    session.xyDataListFromField(odb=session.odbs[odbName+'.odb'], outputPosition=NODAL, variable=(('RF', NODAL, ((COMPONENT, 'RF2'), )), ('U', NODAL, ((COMPONENT, 'U2'), )), ), nodeSets=('SHEETADJ_RP', ))

    ##Generate curve
    xy0 = combine(session.xyDataObjects['U:U2 PI: SHEETADJPART N: 1'], session.xyDataObjects['RF:RF2 PI: SHEETADJPART N: 1'])
    xy0.setValues(sourceDescription='combine ( "U:U2 PI: SHEETADJPART N: 1", "RF:RF2 PI: SHEETADJPART N: 1" )')
    session.xyDataObjects.changeKey(xy0.name, odbName+'_U2-RF2')

    ##Export curve
    x0 = session.xyDataObjects[odbName+'_U2-RF2']
    session.xyReportOptions.setValues(numberFormat=SCIENTIFIC, minMax=ON, layout=SEPARATE_TABLES)
    session.writeXYReport(fileName=odbName+'_U2-RF2.rpt', xyData=(x0, ))

    ##Clear data
    del session.xyDataObjects['U:U2 PI: SHEETADJPART N: 1']
    del session.xyDataObjects['RF:RF2 PI: SHEETADJPART N: 1']
    del session.xyDataObjects[odbName+'_U2-RF2']

    #Set options
    session.View(name='User-1', nearPlane=950.0, farPlane=1050.0, width=70.0, height=30.0, projection=PERSPECTIVE, cameraPosition=(1000.0, 0.0, 0.0), cameraUpVector=(0.0, 0.0, 1.0), cameraTarget=(0.0, 0.0, 0.0), viewOffsetX=-1.0, viewOffsetY=-6.0, autoFit=OFF)
    session.viewports['Viewport: 1'].view.setValues(session.views['User-1'])
    session.viewports['Viewport: 1'].odbDisplay.setValues(viewCut=ON)    
    session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
    session.viewports['Viewport: 1'].odbDisplay.commonOptions.setValues(visibleEdges=FEATURE)
    session.viewports['Viewport: 1'].viewportAnnotationOptions.setValues(triadFont='-*-times new roman-medium-r-normal-*-*-180-*-*-p-*-*-*', legendFont='-*-times new roman-medium-r-normal-*-*-180-*-*-p-*-*-*', titleFont='-*-times new roman-medium-r-normal-*-*-180-*-*-p-*-*-*', stateFont='-*-times new roman-medium-r-normal-*-*-180-*-*-p-*-*-*')

    #Export contour
    session.printToFile(fileName=odbName+'_Mises', format=PNG, canvasObjects=(session.viewports['Viewport: 1'], ))

    #Close odb file
    o3.close()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Computation and Analysis
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

d_jobs = {}
d_jobs['inp'] = []
d_jobs['odb'] = []
filesName = os.listdir(sourceDirM)

for i in range(len(filesName)):
    
    filesNameSplit = filesName[i].split('.')

    if len(filesNameSplit) == 2:
        #Access inp files' name
        if filesNameSplit[1] == 'inp':
            d_jobs['inp'].append(filesNameSplit[0])
        if filesNameSplit[1] == 'odb':
            d_jobs['odb'].append(filesNameSplit[0])


if switchMode == 1:
    
    i = 0
    while len(d_jobs['inp']) >= i+1:

        #Submit jobs
        jobSubmit(jobName=d_jobs['inp'][i], numberOfUsedCores=cpu_count()-1)

        #Copy files
        if copyOrNot == 1:
            copyFiles(sourceDir=sourceDirM, targetDir=targetDirM+pathSplit[-1])

        i = i + 1

        filesName = os.listdir(sourceDirM)

        for j in range(len(filesName)):

            filesNameSplit = filesName[j].split('.')

            if len(filesNameSplit) == 2:
                #Access inp files' name
                if filesNameSplit[1] == 'inp':
                    
                    signal = 0
                    
                    for k in range(len(d_jobs['inp'])):
                        if d_jobs['inp'][k] == filesNameSplit[0]:
                            signal = signal+1

                    if signal == 0:
                        d_jobs['inp'].append(filesNameSplit[0])

if switchMode == 2:
    for i in range(len(d_jobs['odb'])):

        #Export results
        resultExport(odbName=d_jobs['odb'][i])

        #Copy files
        if copyOrNot == 1:
            copyFiles(sourceDir=sourceDirM, targetDir=targetDirM+pathSplit[-1])

if switchMode == 3:

    i = 0
    while len(d_jobs['inp']) >= i+1:

        #Submit jobs
        jobSubmit(jobName=d_jobs['inp'][i], numberOfUsedCores=cpu_count()-1) 

        #Export results
        resultExport(odbName=d_jobs['inp'][i])

        #Copy files
        if copyOrNot == 1:
            copyFiles(sourceDir=sourceDirM, targetDir=targetDirM+pathSplit[-1])

        i = i + 1

        filesName = os.listdir(sourceDirM)

        for j in range(len(filesName)):

            filesNameSplit = filesName[j].split('.')

            if len(filesNameSplit) == 2:
                #Access inp files' name
                if filesNameSplit[1] == 'inp':
                    
                    signal = 0
                    
                    for k in range(len(d_jobs['inp'])):
                        if d_jobs['inp'][k] == filesNameSplit[0]:
                            signal = signal+1

                    if signal == 0:
                        d_jobs['inp'].append(filesNameSplit[0])

mdb.save()