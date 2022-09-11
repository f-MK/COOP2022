# -*- coding: utf-8 -*-
"""
originally written in python 3, modified to work in python 2.7 
@author: Fatemeh MK

Description: This control panel is an upgraded version of Control_Panel.py. It's an interactive GUI which 
             lets the user control the MMC100 motor while observing the position and spectrometer readings 
             simultaneously. It also includes the option for executing a delay sweep in order to acquire 
             a FROG trace. 
"""
import mmc100  # To interact with the motor
import time
import numpy as np
import tkinter as tk 
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg #added 'Agg' at the end of NavigationToolbar2Tk for python 2
from matplotlib.figure import Figure
import matplotlib.animation as animation
import seabreeze # To read OceanOptics spectrometers
seabreeze.use('pyseabreeze')
import seabreeze.spectrometers as sb
from acquisition_func import delay_stage # To run the delay sweep

#*******Initialization*******
axis = 1 #controller number
stage = mmc100.mmc100(port='COM3') #creates an MMC100 object and connects to the motor on COM3
stage.set_vel(axis, 1) #set motor velocity mm/s, Minimum = 0.001 mm/s
stage.set_acc(axis, 200) #set acceleration mm/s^2
stage.set_dec(axis, 200) #set deceleration mm/s^2
start_time = time.time()   #time.perf_counter() doesnt work in python 2

inttime = 50000*8   # Integration time (microsec)
devices = sb.list_devices() #list of  available OceanOptics devices
time.sleep(1) #this is placed to prevent errors with the spectrometer
spec = sb.Spectrometer(devices[0])  #makes a specrtometer instance
time.sleep(0.5) #this is placed to prevent errors with the spectrometer
spec.integration_time_micros(inttime)

fig = Figure(figsize = (9,5),tight_layout = True)
ax1 = fig.add_subplot(121) #for the position-time plot
ax2 = fig.add_subplot(122) #for the spectrum plot
times = [] #for storing the time stamps of the position readings
positions = []
bg = spec.intensities() #background spectrum array
w = spec.wavelengths() #wavelength array

#**********Start of GUI window************8
root = tk.Tk() #creates a tkinter GUI window
root.title('FROG Control Panel')
root.geometry('1200x900') # (width pixels X height pixels)
   
def animate(i): #plots two graphs
    t = time.time() - start_time
    times.append(t)     #add current time stamp
    positions.append(stage.get_pos(axis))  #add current motor position
    ax1.clear(), ax2.clear()
    ax1.plot(times[-100:], positions[-100:]) #plot the last 100 points
    ax1.set_xlabel('Time [s]'), ax1.set_ylabel('Position [mm]')
    ax1.set_title("P-T graph")
    
    y = spec.intensities() #get current spectrometer reading
    ax2.plot(w, y)
    ax2.set_xlabel('Wavelength [nm]'), ax2.set_ylabel('Intensity')
    ax2.set_title("Spectrum")
    ax2.set_xlim([200,1200]), ax2.set_ylim([-1000, 60000])

def read_pos(): #reads realtime position 
    pos_reading.set(str(stage.get_pos(axis))) #gets the current position from controller and writes it to a GUI window widget
    root.after(50, read_pos) #calls itself every 50 ms

def move_to(pos):
    stage.mva(axis, pos, wait_stop=False) 
    # wait_stop=false so that the program does not wait for the motor to complete its motion before sending a stop command.

def moveFwd():
    stage.mvr(axis, float(inc.get()), wait_stop=False) 

def moveBack():
    stage.mvr(axis, -float(inc.get()), wait_stop=False) 

def stop():
   stage.stp(axis)

def zero():
   stage.set_zero(axis)

def set_inttime():
  spec.integration_time_micros(float(inttime.get()))  
  
def set_vel():
  stage.set_vel(axis, float(vel.get()))  
  stage.read_err(axis) #read error message if it exists

def set_accel():
  stage.set_acc(axis, float(accel.get()))
  stage.read_err(axis)

def set_decel():
  stage.set_dec(axis, float(decel.get())) 
  stage.read_err(axis)
  

#Widgets (labels and textboxes for user input)   
pos1_label = tk.Label(root, text = 'Position 1 (mm)')
pos1_default = tk.StringVar(root, value=str(0)) #default value for 'Position 1'
pos1 = tk.Entry(root, textvariable = pos1_default) #textbox entry where users can input a value

pos2_label = tk.Label(root, text = 'Position 2 (mm)') 
pos2_default = tk.StringVar(root, value=str(-2)) 
pos2 = tk.Entry(root, textvariable = pos2_default) 

inc_label = tk.Label(root, text = 'Increment (mm)')
inc_default = tk.StringVar(root, value=str(0.01))
inc = tk.Entry(root, textvariable = inc_default)

pos_reading_label = tk.Label(root, text = 'Position (mm)')
pos_reading = tk.StringVar(root, value=str(stage.get_pos(axis)))
curr_pos = tk.Label(root, textvariable= pos_reading)

vel_label = tk.Label(root, text = 'Velocity [mm/s]') 
vel_default = tk.StringVar(root, value=str(1))
vel = tk.Entry(root, textvariable = vel_default)

accel_label = tk.Label(root, text = 'Acceleration [mm/s^2]') 
accel_default = tk.StringVar(root, value=str(200))
accel = tk.Entry(root, textvariable = accel_default)

decel_label = tk.Label(root, text = 'Deceleration [mm/s^2]') 
decel_default = tk.StringVar(root, value=str(200))
decel = tk.Entry(root, textvariable = decel_default)

inttime_label = tk.Label(root, text = 'Integration time [us]')
inttime_default = tk.StringVar(root, value=str(400000))
inttime = tk.Entry(root, textvariable = inttime_default)

start_label = tk.Label(root, text = 'Start Position [mm]:')
start_default = tk.StringVar(root, value=str(-0.06))
start_pos = tk.Entry(root, textvariable = start_default)
end_label = tk.Label(root, text = 'End Position [mm]:')
end_default = tk.StringVar(root, value=str(0.06))
end_pos = tk.Entry(root, textvariable = end_default)
step_label = tk.Label(root, text = 'Step Size [mm]:')
step_default = tk.StringVar(root, value=str(0.004))
step_size = tk.Entry(root, textvariable = step_default)

#Button widgets
Pos1GoBut= tk.Button(root, text= "Go", bg='green', command = lambda: move_to(float(pos1.get())))
Pos2GoBut= tk.Button(root, text= "Go", bg='green', command = lambda: move_to(float(pos2.get())))
stopBut = tk.Button(root, text= "Stop", bg='red', command = stop)
ForwardBut= tk.Button(root, text= "-->", width = 7, height = 1, command= moveFwd)
BackBut= tk.Button(root, text= "<--", width = 7, height = 1, command= moveBack)
zeroBut = tk.Button(root, text= "Zero", bg = 'gray', command = zero)
inttimeBut = tk.Button(root, text = 'Set', command = set_inttime)
velBut   = tk.Button(root, text = 'Set', command = set_vel)
accelBut = tk.Button(root, text = 'Set', command = set_accel)
decelBut = tk.Button(root, text = 'Set', command = set_decel)
StartBut = tk.Button(root, text= 'Start Aquisition', bg='#1CAAEF', command = lambda: delay_stage(stage, spec,
    float(inttime.get()), float(start_pos.get()), float(end_pos.get()), float(step_size.get())))

#Widget Layout (without this code the widgets won't be visible in the GUI window)
pos1_label.grid(row = 0, column = 0)
pos1.grid(row = 0, column = 1)
Pos1GoBut.grid(row = 0, column = 2, sticky = 'W')
pos2_label.grid(row = 1, column = 0)
pos2.grid(row = 1, column = 1)
Pos2GoBut.grid(row = 1, column = 2, sticky = 'W')
stopBut.grid(row = 0, column = 3, sticky = 'W')
zeroBut.grid(row = 0, column = 4, sticky = 'W')
inc_label.grid(row = 2, column = 0)
inc.grid(row = 2, column = 1)
BackBut.grid(row = 2, column = 2, columnspan= 1, sticky='E') # E = East side of cell
ForwardBut.grid(row = 2, column = 3, columnspan= 1, sticky='W') # W = West side of cell
pos_reading_label.grid(row = 3, column = 0)
curr_pos.grid(row = 3, column = 1)

vel_label.grid(row = 0, column = 5)
vel.grid(row = 0, column = 6)
velBut.grid(row = 0, column = 7, sticky = 'W')
accel_label.grid(row = 1, column = 5)
accel.grid(row = 1, column = 6)
accelBut.grid(row = 1, column = 7, sticky = 'W')
decel_label.grid(row = 2, column = 5)
decel.grid(row = 2, column = 6)
decelBut.grid(row = 2, column = 7, sticky = 'W')

inttime_label.grid(row = 3, column = 5, pady= 10)
inttime.grid(row = 3, column = 6, pady= 10)
inttimeBut.grid(row = 3, column= 7, sticky = 'W', pady= 10)

start_label.grid(row = 6, column = 0)
start_pos.grid(row = 6, column = 1)
end_label.grid(row = 6, column = 2)
end_pos.grid(row = 6, column = 3)
step_label.grid(row = 6, column = 4)
step_size.grid(row = 6, column = 5)
StartBut.grid(row = 6, column = 6)

#Adding the matplotlib figure and toolbar to the GUI window
canvas = FigureCanvasTkAgg(fig, root)
canvas.get_tk_widget().grid(row = 4, columnspan= 15, padx= 30, pady= 10)
toolbarFrame = tk.Frame(master=root)
toolbarFrame.grid(row = 5, columnspan= 15, padx= 15, pady = 15)
toolbar = NavigationToolbar2TkAgg(canvas, toolbarFrame)
toolbar.update()

root.after(50, read_pos) #to constantly read the current position value
ani = animation.FuncAnimation(fig, animate, interval=500) #to constantly update the plots

root.mainloop()
#*************End of GUI window***************

stage.ser.close() #terminates communication with the motor
spec.close()  #terminates communication with the spectrometer

