# femssc

The pre- and post-processing scripts for finite element modelling of self-drilling screw connections between thin steel sheets (femssc) were adopted in the paper "[Testing, numerical and analytical modelling of self-drilling screw connections between thin steel sheets in shear]()"

![FE Model](images/FE_model.png)

As a type of widely utilised mechanical fastener responsible for transferring shear and/or tension forces, self-drilling screw connection plays a prominent role in the overall structural performance of cold-formed steel assembled members and structures. Although its bearing capacity has been widely investigated, far less attention has been paid to the deformation behaviour. A parameterised FE model of self-drilling screw connections is thus developed by using __femssc__ based on the built-in Python 2.X in ABAQUS software package, to further explore the shear deformation behaviour of screw connections and to propose a prediction model for quantitatively describe their load versus deformation relationships. Details of this FE model are presented in the related paper.

Kangyi Cai 2021 @ WHU

![CE1X0S-Exp](images/CE1X0S-Exp.gif) ![CE1X0S-FE](images/CE1X0S-FE.gif) ![CE1X0S-curve](images/CE1X0S-curve.gif)

## Citing

If you use these scripts in your study, please cite the related paper:
```
K. Cai, H. Yuan. Testing, numerical and analytical modelling of self-drilling screw connections between thin steel sheets in shear, Thin-Walled Struct. 182 (2023) 110292. 
```

Or in the format of BibTex:
```
@article{cai2023testing,
  title={Testing, numerical and analytical modelling of self-drilling screw connections between thin steel sheets in shear},
  author={Cai, Kangyi, and Yuan, Huanxin},
  journal={Thin-Walled Structures},
  volume={182},
  pages={110292},
  year={2021},
  publisher={Elsevier}
}
```

# Features

## prepp.py

Generate .inp files, namely establish FE models of self-drilling screw connections with different sheet thicknesses and materials, as well as diverse screw diameters and arrangements.

## postp.py

Based on generated .inp files, recreate jobs for computation, and obtain .rpt and .png files, corresponding to curves and contours, respectively.

# Usages

## prepp.py

- Create a folder containing this script

- Determine parameters of the database in this script

- Open Abaqus/CAE

- Set work directory to the folder

- Run this script

## postp.py

- Create a folder containing this script and all the .inp files for computation

- Determine the value of __switchMode__, __copyOrNot__ and __targetDirM__ in this script

- Open Abaqus/CAE

- Set work directory to the folder

- Run this script

# License

MIT
