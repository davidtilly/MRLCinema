# MRLCinema
The purpose of MRLCinema is to be a research tool in radiotherapy focusing around motion management for MR-Linacs.

Currently it can: 
- Parse the Elekta cine files (*.bin files in MSNRBF format) into SimpleITK images
- Perform group registration of a list of cines to determine the motion between the cines (i.e. create a motion trace)
- Replay the motion (cines and motion trace) in a web application (based on the panel framework).
- Perform dose accumulation using a motion trace and a Linac Logfile (i.e. move around, and accumulate, the dose whole distribution using the motion trace and beam on information)

## Authors
David Tilly, PhD, Medical Physics, Uppsala University Hospital

## Disclaimer
The source code is available as is for the purpose of research and education in radiotherapy. The authors take no responsibility for potential bugs or limitations of the code.

