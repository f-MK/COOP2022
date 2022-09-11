# -*- coding: utf-8 -*-
"""
Created on Fri Aug 05 13:15:18 2022

@author: Fatemeh MK

Description: This dispersion scan acquisiton script is a modified version of the "acquisition_func.py" written for the TG FROG 
            setup. This script is for a continuous dispersion scan. This function is called from "Control_Panel_D-scan.py" in 
            order to execute a continuous dispersion scan and acquire a D-scan. The piezo motor is attached to a wedge forming 
            a wedge pair and goes thru a series of positions thereby introducing extra dispersion to the beam path. The spectrum 
            is captured at each position via the spectrometer. The resulting 2D spectrogram is plotted at the end, and the data 
            is saved in a text file.

Parameters:
    stage: an mmc100 class object 
    spec: a spectrometer object
    inttime: the integration time of the spectrometer
    start_pos/end_pos: starting/stopping position for the delay sweep
    step_size: step size taken by the motor during delay sweep. MMC100 highest resolution = 1 nm
    deg: The angle of the wedges used for introducing dispersion. This is used to calculate the relative thickness added to the beam path.
    axis: the motor controller number. Since only one motor (one dimension) is used in my FROG experiments the axis # is always 1.
    
The data.txt file structure is as follows, where THK = thickness value, WAV = wavelegnth value, INT = intensity value

0.0 THK THK THK THK ...\n
WAV INT INT INT INT ...\n
WAV INT INT INT INT ...\n
WAV INT INT INT INT ...\n
WAV INT INT INT INT ...\n
WAV INT INT INT INT ...\n
.    .   .   .   .  ...\n
.    .   .   .   .  ...\n
"""

import numpy as np
import matplotlib.pyplot as plt
import seabreeze # To read OceanOptics spectrometers
seabreeze.use('pyseabreeze')


def D_scan(stage, spec, inttime, start_pos, end_pos, step_size, deg, axis=1):
  print 'starting Dispersion-Scan'
  #*******Initialization*******
  n = int(abs(start_pos-end_pos)/step_size + 1) #number of positions
  if end_pos<start_pos:
    step_size = -step_size

  p = np.linspace(start_pos, end_pos, n) #array of motor positions [mm]
  thickness = abs(p)*np.tan(np.deg2rad(deg)) #each extra mm in distance adds tan(4deg) in wedge thickness 
  #The thicknesses are relative to the starting position, and the starting position of the motor for the wedges is assumed to be set to zero beforehand 
  
  spec.integration_time_micros(inttime) #sets spectrometer's integration time
  w = spec.wavelengths() #array of spectrometer wavelegnths
  bg = spec.intensities() #array of background spectrum 
  data = [[0]*len(p) for _ in range(len(w))] #initilizaes a matrix for spectrum data [len(w) x len(p)]
                                             #every row corresponds to a wavelength and every column to a position

  #*******Dipersion scan******* 
  stage.mva(axis, start_pos) #motor moves to starting position
  col = 0 #column index 
  while (col<n): 
    I = spec.intensities() #- bg #captures spectrum 
    for i in range(len(w)): #adds intensities to data matrix
      data[i][col] = I[i]
    col += 1
    print col #to keep track of how many positions are left in the sweep
    if col != n:
      stage.mvr(axis, step_size) #moves to the next position
    #time.sleep(0.1)
  
  stage.mva(axis, start_pos) #returns motor to the start position
  
  print 'Scan is finished\n Data will now be saved\n\n'
  
  #*******Finalization*******
  intensities = np.array(data[:]) #copy of the original data matrix which only contains the intensities
  thickness2 = thickness[:] #copy of the original thickness array

  #Storing all of the data (wavelegnths are the first column, thicknesses are the first row)
  data = np.c_[w, data] #adding wavelenths as column
  thickness = np.insert(thickness, 0, 0) #adding an extra zero at the beginning to fix dimension issues
  data = np.r_[[thickness], data] #adding thicknesses as row
  with open('data.txt', 'w') as f:
    np.savetxt(f, data, fmt = '%.5f', delimiter = ',')
  
  w2= w[543:654] #to look at smaller range of wavelengths
  #plotting the 2D spectrogram
  plt.figure('Spectrogram')
  X, Y = np.meshgrid(thickness2, w2) 
  plt.pcolormesh(X, Y, intensities[544:655][:], cmap='hot', shading = 'nearest') #Y rows, X columns
  plt.title('Spectrogram', size = 20)
  plt.xlabel('Added Fused Silica thickness [mm]', size = 18), plt.ylabel('Wavelength [nm]', size = 18)
  plt.colorbar().ax.set_title('Intensity', size = 17)

  plt.figure('Spectrogram2')
  X, Y = np.meshgrid(p, w2) 
  plt.pcolormesh(X, Y, intensities[544:655][:], cmap='hot', shading = 'nearest') #Y rows, X columns
  plt.title('Spectrogram', size = 20)
  plt.xlabel('Motor Position [mm]', size = 18), plt.ylabel('Wavelength [nm]', size = 18)
  plt.colorbar().ax.set_title('Intensity', size = 17)
  
  plt.show()
    
  
  



