# MRLCinema
The purpose of MRLCinema is to be a research tool in radiotherapy focusing around motion management for MR-Linacs.

Currently it can: 
- Parse the Elekta cine files (*.bin files in MSNRBF format) into SimpleITK images
- Perform group registration of a list of cines to determine the motion between the cines (i.e. create a motion trace)
- Replay the motion (cines and motion trace) in a web application.
- Perform dose accumulation using a motion trace and a Linac Logfile (i.e. move around, and accumulate, the dose whole distribution using the motion trace and beam on information)

## Authors
David Tilly, PhD, Medical Physics, Uppsala University Hospital

## COPYRIGHT
Copyright (C) 2025 David Tilly

This code is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.



