**waterverse-flood-simulation-component**

This is the flood simulation component project for WATERVERSE.

it consists of two projects:

* flood\_simulation is a python package that wraps CAFlood functionality (https://cafloodpro.com/) and localises data to the Etteln case study.  
* wdme\_flood\_component is a python/fastapi application that exposes the flood\_simulation package to WATERVERSE'S WDME.

All code is python and designed to be used with Python3.12+. Each project contains a requirements.txt file detailing required packages.

The flood\_simulation package is closely tied to the Etteln case study, with land use, rain mask and DEM data hard coded to the region. In addition, the simulation package assumes a rainfall data format of bucketted historic and forecast data which is tied to the Etteln region.  
The flood\_simulation/[testbed.py](http://testbed.py) illustrates how the flood\_simulation package operates.

The wdme\_flood\_component contains an api in main.py, using fastapi and provides methods for passing rainfall data to the flood\_simulation package, retrieving textual and geojson data, and a webapp to visualise flood results and citizen support.

The overall concept and operation of the flood simulation component is explained in this paper: https://dx.doi.org/10.15131/SHEF.DATA.29921135.V1
