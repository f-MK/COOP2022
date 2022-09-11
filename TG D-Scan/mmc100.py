'''
@author: Aleksey with modifications and documentation made by Fatemeh
Last Edited: July 5, 2022
Description: MMC100 class with methods for interacting with the MMC100 motor.\n
To make use of these functions/methods, first import this script and create a motor instance:\n
    import mmc100\n
    motorInstance = mmc100.mmc100(port)
'''
import serial
import io
import time
import threading
import math

class mmc100:
    def __init__(self, port):
        '''Initializes an mmc100 instance.\n port: The communication port name for the motor.'''
        self.lock = threading.Lock()
        self.ser = serial.Serial(port, timeout=0.5, baudrate=38400) #initializes communication port object
        self.ser.reset_input_buffer()
        self.probe_axes()
        self.set_cl(1)
        self.set_cl(2)
        self.set_cl(3)
        self.set_cl(4)    

    def __del__(self):
        self.ser.close()             
    
    def _exec_cmd(self, axis, cmd, num = None, query=False):
        '''Sends a command to the motor controller's serial port.\n 
            axis: controller number
            cmd: a command from the list found in the MMC100 manual. e.g. 'MVA'
            num: the numerical value associated with a command (if applicable).
            query: when TRUE a '?' is added at the end of the command, which means we are asking the controller for some value.
        '''
        cmd_full = str(axis)+cmd
        if num != None:
            cmd_full += '{0:.3f}'.format(num) 
            '''NOTE: I changed the decimal points to 3 instead of 6 because the vel/acc/dec 
             have a max precision of 3 decimal points. Before, the set velocity and accelertion
             commands would give error messgages that said [Error 28: Invalid Parameter Type]
             This was debugged after seeing how the moto speed wasn't changing.'''
            
        if query: #if we're asking the motor for a value (read request)
            cmd_full += '?'
            
        cmd_full += '\n\r'
        #if(cmd != 'POS'):
        #    print(cmd_full)
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        #print(cmd_full)
        self.ser.write(bytearray(cmd_full, 'ascii'))
        self.ser.flush()
        if query:
            return self.ser.readline()
        
    def probe_axes(self):
        self.axes = []
        for ind in range(1, 9, 1):
            if len(self._exec_cmd(ind, 'VER', query=True)) > 0:
                self.axes.append(ind)
   
    def get_pos(self, axis):
        '''Get the motor's position in [mm]. Returns the theoretical position.'''
        self.lock.acquire()
        pos = str(self._exec_cmd(axis=axis, cmd='POS', query=True))
        self.lock.release()
        #print(pos)
        try:
            #changed it so that the obtained position is the theoretical pos and not the encoder pos. The theoretical pos is returned first (index 0)
            return float(pos.split('#')[1].split(',')[0].split('\\n')[0])
        except:
            return 0.0
    
    def __update_pos(self):
        while True:
            for ind, ax_ in enumerate(self.axes):
                self.displays[ind].value = self.get_pos(ax_)
                #time.sleep(.100)
            time.sleep(200.00)
      
    def ismoving(self, axis):
        '''Check if motor is in motion. Returns TRUE if it is.'''
        res = self._exec_cmd(axis=axis, cmd='STA',  query=True)
        try:
            if((int( str(res).split('#')[1].split('\\n')[0] )//8)%2 == 0):
                return True
            else:
                return False
        except Exception:
            return True
    
    def mva(self, axis, pos, wait_stop = True):
        '''Move the motor to an absolute position.'''
        self._exec_cmd(axis=axis, cmd='MVA', num=pos, query=False)
        if(wait_stop):
            while(self.ismoving(axis)):
                time.sleep(.05)

    def mvr(self, axis, pos, wait_stop = True):
        '''Move the motor to a relative position.'''
        self._exec_cmd(axis=axis, cmd='MVR', num=pos, query=False)
        if(wait_stop):
            while(self.ismoving(axis)):
                time.sleep(.05)
    
    def stp(self, axis):
        '''Stop the motor motion.'''
        self._exec_cmd(axis=axis, cmd='STP', num=None, query=False)

    def set_vel(self, axis, vel):
        '''Set the motor speed [mm/s].'''
        self._exec_cmd(axis=axis, cmd='VEL', num=vel, query=False)
    
    def set_acc(self, axis, accel):
        '''Set the motor acceleration [mm/s^2].'''
        self._exec_cmd(axis=axis, cmd='ACC', num=accel, query=False)
    
    def set_dec(self, axis, decel):
        '''Set the motor deceleration [mm/s^2].'''
        self._exec_cmd(axis=axis, cmd='DEC', num=decel, query=False)

    def set_zero(self, axis):
        '''Make current position the new zero position.'''
        self._exec_cmd(axis=axis, cmd='ZRO', num=None, query=False)

    def mvr_ang(self, axis1, axis2, pos, angledeg): #This method can be used when there is also rotational motion
        self._exec_cmd(axis=axis1, cmd='MSR', num=pos*math.sin(angledeg*math.pi/180), query=False)
        self._exec_cmd(axis=axis2, cmd='MSR', num=pos*math.cos(angledeg*math.pi/180), query=False)
        self._exec_cmd(axis=0, cmd='RUN', query=False)
        while(self.ismoving(axis1) or self.ismoving(axis2)):
            time.sleep(.05)
            
    def read_err(self, axis):
      '''Read Error message and print it'''
      self.lock.acquire()
      error = self._exec_cmd(axis = axis, cmd = 'ERR', query = True)
      self.lock.release()
      print(error)

    def set_cl(self, axis): 
        '''Set motor to closed loop mode.'''
        self._exec_cmd(axis= axis, cmd='FBK3', query=False)
