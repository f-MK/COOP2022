# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 12:11:11 2022 using Python 2.7
@author: Fatemeh MK

Description: This delay stage acquisition function is written based on Acquisition.py.
            This function is called from Full_Control_Panel.py in order to execute a delay sweep and 
            acquire a FROG trace. The translation stage motor goes thru a series of positions and the 
            spectrum is captured at each position via the spectrometer. The resulting 2D spectrogram 
            is plotted at the end, and the data is saved in a text file.
Parameters:
    stage: an mmc100 class object 
    spec: a spectrometer object
    inttime: the integration time of the spectrometer
    start_pos/end_pos: starting/stopping position for the delay sweep
    step_size: step size taken by the motor during delay sweep. MMC100 highest resolution = 1 nm
    axis: the motor controller number. Since only one motor (one dimension) is used in my FROG experiments the axis # is always 1.

The data.txt file structure is as follows, where POS = position value, WAV = wavelegnth value, INT = intensity value

0.0 POS POS POS POS ...\n
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
from scipy.ndimage import gaussian_filter1d


def delay_stage(stage, spec, inttime, start_pos, end_pos, step_size, axis=1):
  print 'starting aquisition'
  #*******Initialization*******
  n = int(abs(start_pos-end_pos)/step_size + 1) #number of positions
  spec.integration_time_micros(inttime) #sets spectrometer's integration time
  w = spec.wavelengths() #array of spectrometer wavelegnths
  bg = spec.intensities() #array of background spectrum 
  p = np.linspace(start_pos, end_pos, n) #array of delay positions
  data = [[0]*len(p) for _ in range(len(w))] #initilizaes a matrix for spectrum data [len(w) x len(p)]
                                             #every row corresponds to a wavelength and every column to a position

  #*******Delay sweep*******
  stage.mva(axis, start_pos) #motor moves to starting position
  col = 0 #column index 
  while (col<n): 
    I = spec.intensities() #- bg #captures spectrum 
    for i in range(len(w)): #adds intensities to data matrix
      data[i][col] = I[i]
    col += 1
    print col #to keep track of how many positions are left in the sweep
    stage.mvr(axis, step_size) #moves to the next position
  
  mid = (start_pos+end_pos)/2 
  stage.mva(axis, mid) #returns motor to the midpoint which I'm assuming is the temporal overlap point for the FROG
  
  print 'Aquisition finished\n Data will now be saved\n\n'
  #*******Finalization*******
  with open('intensities.txt', 'w') as f:
    np.savetxt(f, data, fmt = '%.5f', delimiter = ',')
  
  intensities = np.array(data[:]) #makes a copy of the original data matrix which only contains the intensities
  p2 = p[:] #makes a copy of the original position array

  #Storing all of the data (wavelegnths are the first column, positions are the first row)
  data = np.c_[w, data] #adding wavelenths as column
  p = np.insert(p, 0, 0) #adding an extra zero at the beginning to fix dimension issues
  data = np.r_[[p], data] #adding positions as row
  with open('data.txt', 'w') as f:
    np.savetxt(f, data, fmt = '%.5f', delimiter = ',')
  
  delay = (p2*2)/(1000*3e8) #delay [s], multiply by 2 since twice is added to pathlength, convert to meter, then convert to seconds
  delay = delay*1e15 #delay [fs]
  num_col = np.size(p2) #number of columns in intensity matrix. Equal to number of delay positions.
  FWHM_intensities = [] #array for storing the intensities summed over all wavelengths for each delay value.
  for i in range(num_col):
    sum_col = np.sum(intensities[:,i]) #sums the i'th column which corresponds to one time delay. 
    FWHM_intensities.append(sum_col)  
  #Filtering the approximate pulse intensity 
  FWHM_intensities = FWHM_intensities - np.average(FWHM_intensities[0:10]) #subtracting an average (kinda filtering)
  FWHM_intensities[FWHM_intensities<0] = 0 #replaces negatives with zero
  FWHM_intensities = FWHM_intensities - np.min(FWHM_intensities) #vertically shift intensities down to zero
  sigma = 3 # standard deviation for Guassian filter
  FWHM_intensities_smooth = gaussian_filter1d(FWHM_intensities, sigma) #filtered intensities
  FWHM_intensities_smooth = FWHM_intensities_smooth/np.max(FWHM_intensities_smooth) #normalization
  FWHM_intensities = FWHM_intensities/np.max(FWHM_intensities) #normalization
  
  #plotting the 2D spectrogram
  plt.figure('Spectrogram')
  X, Y = np.meshgrid(p2,w) #creates mesh of delay and wavelength
  plt.pcolormesh(X, Y, intensities, cmap='hot', shading = 'nearest') #Y rows, X columns
  plt.title('Spectrogram', size = 20)
  plt.xlabel('Position [mm]', size = 18), plt.ylabel('Wavelength [nm]', size = 18)
  plt.colorbar().ax.set_title('Intensity', size = 17)
  
  #plotting the approximate temporal pulse
  plt.figure('FWHM approximation')
  ax = plt.subplot(111)
  ax.plot(delay, FWHM_intensities, label = 'Original data') 
  ax.plot(delay, FWHM_intensities_smooth, label = r'Gaussian filtered, $\sigma$ = '+str(sigma))
  ax.hlines(y = 0.5, xmin = delay[0], xmax = delay[num_col-1], linestyles = 'dashed', color = 'r') #FWHM line
  ax.set_xlabel('Time [fs]', size = 18), ax.set_ylabel('Normalized Intensity', size = 18)
  ax.set_title('Approximate Temporal Pulse intensity', size = 20)
  ax.set_xticks(np.arange(delay[0], delay[num_col-1], 20)) #major gridlines
  ax.set_xticks(np.arange(delay[0], delay[num_col-1], 5), minor = 'True') #minor gridlines
  ax.grid(which='major', alpha = 1)
  ax.grid(which = 'minor', alpha = 0.4)
  ax.legend()
  #Finding the POI with FWHM line and displaying the approximate pulse duration
  idx = np.argwhere(np.where(np.abs(FWHM_intensities_smooth - 0.5) < 0.025, FWHM_intensities_smooth, 0)) #finds the POI with FWHM line
  print('POI indices are: ' + str(delay[idx])) #indices of POI with FWHM line
  if idx.any(): #if idx is not empty
    plt.plot(delay[idx], FWHM_intensities_smooth[idx], 'ro')
    plt.text(x = -200, y = 0.55, s = 'FWHM = '+ str(delay[idx][np.size(idx)-1]-delay[idx][0]) + ' fs\nBased on Gaussian filter', size = 15)
  
  plt.show()
    
  
  
  
#  #plotting the 2D spectrum
#  X, Y = np.meshgrid(p2,w)
#  plt.pcolormesh(X, Y, intensities, cmap='hot', shading = 'nearest') #Y rows, X columns
#  plt.title('Spectrogram')
#  plt.xlabel('Position [mm]'), plt.ylabel('Wavelength [nm]')
#  plt.colorbar().ax.set_title('Intensity')
##  figname = 'Spectrogram_' + str(datetime.datetime.now()) + '.png'
##  plt.savefig(figname)
#  plt.show()


# stage.ser.close() 
# spec.close() 


