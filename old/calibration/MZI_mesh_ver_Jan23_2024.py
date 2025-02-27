"""
Author Mikael Schelin via Westbourne Gate (Marvelous Mechanics) AB (org nr 556725-1490)
mikaelrschelin@gmail.com
+46707582879
Copyright © 2023-09-29 all rights reserved
User agreement and license see separate file

"""

#import libraries for the Powermeter
from __future__ import print_function 
import pyvisa 
from ThorlabsPM100 import ThorlabsPM100

import zipfile

#for libraries for the qcontrol device
import qontrol 

#library libraries for the GUI (custom tkinter and tkinter)
import customtkinter 
from tkinter import *
import tkinter as tkinter
from tkinter import ttk, filedialog, Label
from tkinter import messagebox

#import OS related libraries
import sys
import os
from time import sleep 

import pickle

#import various python libraries
import numpy as np
from scipy import optimize

import matplotlib.ticker as ticker
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageTk
import shutil
import random
import string
import time
from io import BytesIO
import tkinter.font as tkFont
import sympy as sp

# The following classes define various frames in the app interface

class MyUpperleftframe(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=5)
        self.app = master

class MyUpperrightframe(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.app = master
        self.grid_columnconfigure(0, weight=1)

        
class MyLowerFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.app = master
        self.grid_columnconfigure(0, weight=1)

class MyInfoFrame(customtkinter.CTkFrame):
    def __init__(self, master, title, params):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.title = title
        self.params = params #dictionary with device info
        self.keys=list(self.params.keys())
        self.values=list(self.params.values())

        #IMAGE_WIDTH = 25
        #IMAGE_HEIGHT = 29

        IMAGE_WIDTH = 30 
        IMAGE_HEIGHT = 33

        IMAGE_PATH = './logo_mini.png'
        image=Image.open(IMAGE_PATH)
        #IMAGE_PATH = './kthlogo_mini_white2.png'
        
        #self.your_image = customtkinter.CTkImage(light_image=ImageTk.PhotoImage(Image.open(IMAGE_PATH)), size=(IMAGE_WIDTH , IMAGE_HEIGHT))
        self.your_image = customtkinter.CTkImage(light_image=image, size=(IMAGE_WIDTH, IMAGE_HEIGHT))
        logo = customtkinter.CTkLabel(self, image=self.your_image, text="")
        logo.grid(row=0, column=0, padx=(10,0), pady=(10,3), rowspan = 6, sticky="n")
      

        labela = customtkinter.CTkLabel(self, text = 'Status:')
        labela.grid(row=0, column=1, padx=10, pady=(3,0), sticky="e")
        labelb = customtkinter.CTkLabel(self, text = 'Active')
        labelb.grid(row=0, column=2, padx=10, pady=(3,0), sticky="w")

        for i in range(len(self.keys)):
            label1 = customtkinter.CTkLabel(self, text=self.keys[i])
            label1.grid(row=i+1, column=1, padx=10, pady=(0,0), sticky="e")
            label2 = customtkinter.CTkLabel(self, text=self.values[i])
            label2.grid(row=i+1, column=2, padx=10, pady=(0,0), sticky="w")

        label3a = customtkinter.CTkLabel(self, text = 'Software version:')
        label3a.grid(row=5, column=1, padx=10, pady=(0,0), sticky="e")
        label3b = customtkinter.CTkLabel(self, text = 'v1.1')
        label3b.grid(row=5, column=2, padx=10, pady=(0,0), sticky="w")

        label3a = customtkinter.CTkLabel(self, text = 'Designed by:')
        label3a.grid(row=6, column=1, padx=10, pady=(0,3), sticky="e")
        label3b = customtkinter.CTkLabel(self, text = 'Mikael Schelin')
        label3b.grid(row=6, column=2, padx=10, pady=(0,3), sticky="w")
        
        self.grid_rowconfigure((0,1,2,3,4,5), weight=1)



class MyCLExportFrame(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)

        self.upperframe = master
        self.app = self.upperframe.app #this is where I have initiated the frames. 
        self.title = title

        title = customtkinter.CTkLabel(self, text=self.title, corner_radius=6)
        title.grid(row=0, column=0, padx=10, pady=(10,10), sticky="new")

        entry = customtkinter.CTkEntry(self, placeholder_text = 'Max ' + str(self.app.globalcurrrentlimit) + ' (mA)', width = 100)
        entry.grid(row = 1, column = 0, padx = 10, pady = (0,5), sticky = 'ew')
            
        button = customtkinter.CTkButton(self, text = "Customize", width=100, command = lambda entry=entry : self.app.setGlobalCurrentLimit(entry))
        button.grid(row = 2, column=0, padx=10, pady=(0,5), sticky="ew")

        # exporttitle = customtkinter.CTkLabel(self, text='Export data', corner_radius=6)
        # exporttitle.grid(row=3, column=0, padx=10, pady=(5,5), sticky="ew")
        
        exportbutton = customtkinter.CTkButton(self, text = "Export data", width=80, command = self.app.exportfunc)
        exportbutton.grid(row = 3, column=0, padx=10, pady=(5,10), sticky="ew")

        importbutton = customtkinter.CTkButton(self, text = "Import data", width=80, command = self.app.importfunc)
        importbutton.grid(row = 4, column=0, padx=10, pady=(0,20), sticky="ew")


class MyImageFrame(customtkinter.CTkFrame):
    def __init__(self, master, val, IMAGE, height, width):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.val = val
        
        self.upperrightframe = master
        self.app = self.upperrightframe.app 

        self.IMAGE_HEIGHT = height
        self.IMAGE_WIDTH = width

        image = Image.open(IMAGE)
        
        self.your_image = customtkinter.CTkImage(light_image=image, size=(self.IMAGE_WIDTH , self.IMAGE_HEIGHT))
        label = customtkinter.CTkLabel(self, image=self.your_image, text="")
        label.grid(column=0, row=0)


class MyRadioButtonFrame(customtkinter.CTkFrame):
    def __init__(self, master, title, options, params):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self.upperframe = master
        self.app = self.upperframe.app #this is where I have initiated the frames. 
        self.params = params

        self.title = title
        self.options = options
        self.radiobuttons = []
        #self.variable = customtkinter.StringVar(value="6x6")
        #self.app.config=6*5
        self.app.config=8*7
        self.val=customtkinter.StringVar(value=self.app.val)

        title = customtkinter.CTkLabel(self, text=self.title, corner_radius=6)
        title.grid(row=0, column=0, padx=10, pady=(10,10), sticky="new")

        for i, value in enumerate(self.options):
            #radiobutton = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.variable, command = self.radiofunction)
            radiobutton = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.val, command = self.radiofunction)
            radiobutton.grid(row=i+1, column=0, padx=10, pady=(5,5), sticky="w")
            self.radiobuttons.append(radiobutton)

    def getValue(self):
        #return self.variable.get()
        return self.val.get()

    def setValue(self, value):
        #self.variable.set(value)
        self.val.set(value)

    def radiofunction(self):
        self.app.val=self.getValue() 
        print("mesh size choosen:", self.app.val)

        if self.app.val == '6x6':
 
            self.config = 6*5
            self.app.config=self.config
            
            if self.config <= self.params['Available channels:']:

                if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                    self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()
                
                self.app.currentheaterid = self.app.heaterid6x6

                
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid6x6, config = self.config, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                
                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val, app=self.app)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

                
                self.app.channel_selection_frame = MyChannel_selection_frame(self.upperrightframe, 100, 50, self.config, heaterid=self.app.currentheaterid) #val='6x6'
                self.app.channel_selection_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky = "ewns") #sticky="n", rowspan=1

                
                children = self.app.tab_view.tab("Calibrate").winfo_children()
                for child in children:
                    print(child)
                
                self.app.tab_view.calculate_frame.winfo_children()[-1].destroy()

                self.app.choosechannelframe = MyChannelFrame(self.app.tab_view.calculate_frame, config = self.config)
                self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")

            else:
                #self.open_toplevel()
                messagebox.showerror(message='Available channels are less than required channels for this mesh size. 6x6 mesh requires 30 channels. Only ' + str(self.params['Available channels:']) + ' are available. \n\n Please add more modules and restart the program or choose a custom mesh with a smaller number of channels.')
                
                self.app.currentheaterid = self.app.heaterid6x6
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.heaterid6x6, config = 0, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                
                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val, app=self.app)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

                
                self.app.channel_selection_frame = MyChannel_selection_frame(self.app.upperrightframe, 100, 50, self.config, heaterid=self.app.currentheaterid) #val='6x6'
                self.app.channel_selection_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky = "ewns") #sticky="n", rowspan=1)

        elif self.app.val == '8x8': 
            
            self.config = 8*7
            self.app.config=self.config
            
            if self.config <= self.params['Available channels:']:

                if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                    # only header frame
                    self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()
                    
                self.app.currentheaterid = self.app.heaterid8x8  

                
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid8x8, config = self.config, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val, app=self.app)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')
                
                self.app.channel_selection_frame = MyChannel_selection_frame(self.app.upperrightframe, 100, 50, self.config, heaterid=self.app.currentheaterid) #val='6x6'
                self.app.channel_selection_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky = "ewns") #sticky="n", rowspan=1


                children = self.app.tab_view.tab("Calibrate").winfo_children()
                for child in children:
                    print(child)
                
                self.app.tab_view.calculate_frame.winfo_children()[-1].destroy()

                self.app.choosechannelframe = MyChannelFrame(self.app.tab_view.calculate_frame, config = self.config)
                self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")

            else: 
                #self.app.open_toplevel()
                messagebox.showerror(message='Available channels are less than required channels for this mesh size. 8x8 mesh requires 56 channels. Only ' + str(self.params['Available channels:']) + ' are available. \n\n Please add more modules and restart the program or choose a custom mesh with a smaller number of channels.')
                
                self.app.currentheaterid = self.app.heaterid8x8
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid8x8, config = 0, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                #test
                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val, app=self.app)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')
                
                self.app.channel_selection_frame = MyChannel_selection_frame(self.app.upperrightframe, 100, 50, self.config, heaterid=self.self.app.currentheaterid) #val='6x6'
                self.app.channel_selection_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky = "ewns") #sticky="n", rowspan=1

        elif self.app.val == 'custom':

            print("custom picked")

            self.app.channelentry = customtkinter.CTkEntry(self, placeholder_text="# Channels", width=100)
            self.app.channelentry.grid(column=1, row=3, padx=10, pady=10, sticky="se")
            self.app.channelbutton = customtkinter.CTkButton(self, text="Apply", width=60, command=self.customfunct)
            self.app.channelbutton.grid(column=2, row=3, padx=10, pady=10, sticky="se")

            #self.app.browse = customtkinter.CTkButton(self, text="Browse image", width=100, command = self.selectpic)
            #self.app.browse.grid(column=0, row=4, padx=10, pady=10, sticky="se")
            #self.app.pathentry = customtkinter.CTkEntry(self, placeholder_text ="image path...", width=100)
            #self.app.pathentry.grid(column=1, row=4, padx=10, pady=10, sticky="sw")
            #self.app.upload = customtkinter.CTkButton(self, text="Upload", width=60, command = self.savepic)
            #self.app.upload.grid(column=2, row=4, padx=10, pady=10, sticky="se")

    def selectpic(self):
        global filename
        filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = "Select Image", filetypes = (("pgn images", "*.png"), ("jpg images", "*.jpg"), ("jpeg images", "*.jpeg")))
        self.app.pathentry.insert(0,filename)


    def savepic(self):
        filenameSplitted = filename.split('.')
        randomtext = ''.join((random.choice(string.ascii_lowercase) for x in range(12)))
        shutil.copy(filename, f"./chipimages/{randomtext}.{filenameSplitted[1]}")
        IMAGE_PATH = f"./chipimages/{randomtext}.{filenameSplitted[1]}"
        self.app.image_frame1.your_image.configure(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(self.app.image_frame1.IMAGE_WIDTH , self.app.image_frame1.IMAGE_HEIGHT))
        messagebox.showinfo("Success", "Upload Successfully")

        
    def customfunct(self):
        #self.config = int(self.app.channelentry.get())
        self.config = self.app.channelentry.get() #a string

        #first check so that entry is not empty

        if self.config == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in desired number of channels and then press submit again')

        else:
            illegalchar = False
            point = 0

            #check for invalid entry characters
            for i in range(len(self.config)):
                if self.config[i] in self.app.allowedinputvalues:
                    print(self.config[i])
                    if self.config[i] == '.':
                        point +=1
                        if point > 0:
                            print('input is not an integer!')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + self.config[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >0: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer. Please type in a value for the number of channels')
                self.app.channelentry.delete(0, 'end') #clear the entry field
            else: #now we know the entry field has an integer
                self.config = int(self.config) #now it is safe to convert it to an integer
                
                if self.config <= self.params['Available channels:']:

                    if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                        # only header frame
                        self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()

                    self.app.scrollable_frame2 = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, config = self.config, app=self.app) #app is argument so that data structures can be saved in app and be accessible globally
                    self.app.scrollable_frame2.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                    self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val)
                    self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')


                    children = self.app.tab_view.tab("Calibrate").winfo_children()
                    for child in children:
                        print(child)
                    
                    self.app.tab_view.calculate_frame.winfo_children()[-1].destroy()

                    self.app.choosechannelframe = MyChannelFrame(self.app.tab_view.calculate_frame, config = self.config)
                    self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")

                else: 
                    #self.app.open_toplevel()
                    messagebox.showerror(message='Available channels (' + str(self.params['Available channels:']) + ') are less than your desired number of channels (' + str(self.config) + '). \n\n Please add more modules and restart the program or choose a smaller number of channels.')
                    self.app.channelentry.delete(0, 'end') #clear the entry field

                    if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                        # only header frame
                        self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()

                    #clear the scrollable frame from channels
                    self.app.scrollable_frame2 = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, config = 0, app=self.app) #app is argument so that data structures can be saved in app and be accessible globally
                    self.app.scrollable_frame2.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                    self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val)
                    self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

                    children = self.app.tab_view.tab("Calibrate").winfo_children()
                    for child in children:
                        print(child)
                    
                    self.app.tab_view.calculate_frame.winfo_children()[-1].destroy()

                    self.app.choosechannelframe = MyChannelFrame(self.app.tab_view.calculate_frame, config = 0)
                    self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")


class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, headings):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.lowerframe = master
        self.app = self.lowerframe.app

        self.headings = headings

        # create tabs
        self.add("Calibrate")
        self.add("Calculate")

        self.calculate_frame = MyCalcSuperFrame(master = self.tab("Calculate"), tabview=self)
        self.calculate_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky="nsew")
        
class MyTab(customtkinter.CTkTabview):
    def __init__(self, master, width, height, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)

        self.master = master
        self.app = self.master.app
        
class MyFrame(customtkinter.CTkFrame):
    def __init__(self, master, width, height, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)

        self.master = master
        self.app = self.master.app
        
class MyChannel_selection_frame(customtkinter.CTkFrame):
    def __init__(self, master, width, height, config, heaterid, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)

        self.master = master
        self.app = self.master.app
        self.channels=[]
        self.config=config
        
        self.heaterid=heaterid

        for i in range(int(self.config)):
            self.channels.append("Ch_"+str(i)+" ("+self.heaterid[i]+")")
        self.channelselect = customtkinter.CTkComboBox(self, width=140, values=self.channels, command=lambda choice: self.channel_change(choice))
        self.channelselect.grid(column = 0, row = 0, padx=10, pady=10, sticky="sw")
        self.channelselect.set("Select channel")
        
        self.fitselect = customtkinter.CTkComboBox(self, width=150, values=self.app.fit_func, command=lambda choice: self.fitselect_change(choice))
        self.fitselect.grid(column=1, row=0, padx=10, pady=10, sticky="sw")
        self.fitselect.set(self.app.fit_func[0])
        
        self.IOconfigselect = customtkinter.CTkComboBox(self, width=100, values=self.app.IOconfig_options, command=lambda choice: self.IOconfig_change(choice))
        self.IOconfigselect.grid(column=2, row=0, padx=10, pady=10, sticky="sw")
        self.IOconfigselect.set("Cross")
        
        self.barstate_button = customtkinter.CTkButton(self, text = "Set bar state", width=60)
        self.barstate_button.grid(column=3, row=0, padx=10, pady=10, sticky="nsew")
        
        self.crossstate_button = customtkinter.CTkButton(self, text = "Set cross state", width=60)
        self.crossstate_button.grid(column=4, row=0, padx=10, pady=10, sticky="nsew")
        
        self.halfstate_button = customtkinter.CTkButton(self, text = "Set 50:50 state", width=60)
        self.halfstate_button.grid(column=5, row=0, padx=(10,20), pady=10, sticky="nsew")
        
    def channel_change(self, choice):
        self.channelselect.set(choice)
        self.app.channel = self.channels.index(choice)
        self.app.fit = self.fitselect.get()
        self.app.IOconfig = self.IOconfigselect.get()

        self.heaterid=self.app.currentheaterid
        self.fit_index = self.app.fit_func.index(self.app.fit)
        self.IOconfig_index = self.app.IOconfig_options.index(self.app.IOconfig)
        
        self.app.image_frame1.your_image.configure(light_image=Image.open(self.app.IVimagechoices[self.fit_index][self.app.channel]), size=((250)*(395/278), 250))
        self.app.image_frame2.your_image.configure(light_image=Image.open(self.app.opmodimagechoices[self.fit_index][self.IOconfig_index][self.app.channel]), size=((250)*(395/278),250) ) 
        
        if self.app.calframe is not None:
            self.app.calframe.destroy()
        
        self.app.calframe = MyCalcFrame_main(self.app.settings_frame, Channel=self.app.channel, Fit=self.app.fit, IOconfig=self.app.IOconfig)
        self.app.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
        
        for i in range(self.app.config):
            if self.app.rmin_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_minpack[self.app.channel].configure(text=str(np.round(self.app.rmin_list[self.app.channel]/1000, 2))) 
            if self.app.rmax_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_maxpack[self.app.channel].configure(text=str(np.round(self.app.rmax_list[self.app.channel]/1000, 2)))
            if self.app.alpha_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.alphapack[self.app.channel].configure(text=str(np.round(self.app.alpha_list[self.app.channel]/1000, 2)))
            if self.app.linear_resistance_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_linpack[self.app.channel].configure(text=str(np.round(self.app.linear_resistance_list[self.app.channel]/1000, 2)))
        
    def fitselect_change(self, choice):
        self.fitselect.set(choice)
        self.app.fit = choice

        self.app.channel = self.channels.index(self.channelselect.get())
        self.app.IOconfig = self.IOconfigselect.get()

        self.heaterid=self.app.currentheaterid
        self.fit_index = self.app.fit_func.index(self.app.fit)
        self.IOconfig_index = self.app.IOconfig_options.index(self.app.IOconfig)
        
        self.app.image_frame1.your_image.configure(light_image=Image.open(self.app.IVimagechoices[self.fit_index][self.app.channel]), size=((250)*(395/278), 250))
        self.app.image_frame2.your_image.configure(light_image=Image.open(self.app.opmodimagechoices[self.fit_index][self.IOconfig_index][self.app.channel]), size=((250)*(395/278),250) ) 
        
        if self.app.calframe is not None:
            self.app.calframe.destroy()
        
        self.app.calframe = MyCalcFrame_main(self.app.settings_frame, Channel=self.app.channel, Fit=self.app.fit, IOconfig=self.app.IOconfig)
        self.app.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
        
        for i in range(self.app.config):
            if self.app.rmin_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_minpack[self.app.channel].configure(text=str(np.round(self.app.rmin_list[self.app.channel]/1000, 2))) 
            if self.app.rmax_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_maxpack[self.app.channel].configure(text=str(np.round(self.app.rmax_list[self.app.channel]/1000, 2)))
            if self.app.alpha_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.alphapack[self.app.channel].configure(text=str(np.round(self.app.alpha_list[self.app.channel]/1000, 2)))
            if self.app.linear_resistance_list[self.app.channel] != "Null" :
                self.app.scrollable_frame.acqresist_linpack[self.app.channel].configure(text=str(np.round(self.app.linear_resistance_list[self.app.channel]/1000, 2)))
        
    def IOconfig_change(self, choice):
        self.IOconfigselect.set(choice)
        self.app.IOconfig = choice

        self.app.fit = self.fitselect.get()
        self.app.channel = self.channels.index(self.channelselect.get())
        
        self.heaterid=self.app.currentheaterid
        self.fit_index = self.app.fit_func.index(self.app.fit)
        self.IOconfig_index = self.app.IOconfig_options.index(self.app.IOconfig)
        
        self.app.image_frame1.your_image.configure(light_image=Image.open(self.app.IVimagechoices[self.fit_index][self.app.channel]), size=((250)*(395/278), 250))
        self.app.image_frame2.your_image.configure(light_image=Image.open(self.app.opmodimagechoices[self.fit_index][self.IOconfig_index][self.app.channel]), size=((250)*(395/278),250) ) 
        
        if self.app.calframe is not None:
            self.app.calframe.destroy()
        
        self.app.calframe = MyCalcFrame_main(self.app.settings_frame, Channel=self.app.channel, Fit=self.app.fit, IOconfig=self.app.IOconfig)
        self.app.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
        
        for i in range(self.app.config):
            self.app.scrollable_frame.acqresist_minpack[self.channel].configure(text=str(np.round(self.app.rmin_list[self.channel]/1000, 2)))
            self.app.scrollable_frame.acqresist_maxpack[self.channel].configure(text=str(np.round(self.app.rmax_list[self.channel]/1000, 2)))
            self.app.scrollable_frame.alphapack[self.channel].configure(text=str(np.round(self.app.alpha_list[self.channel]/1000, 2)))
            self.app.scrollable_frame.acqresist_linpack[self.channel].configure(text=str(np.round(self.app.linear_resistance_list[self.channel]/1000, 2)))

class MyCalcSuperFrame(customtkinter.CTkFrame):
    def __init__(self, master, tabview):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.tabview = tabview
        self.app = self.tabview.app 

        self.infoframe = MyCalcInfoFrame(master=self)
        self.infoframe.grid(column=0, row=1, padx=10, pady=10, sticky="nsew")

        self.graphframe = MyCalibrationPlot(master=self)
        self.graphframe.grid(column=2, row=0, rowspan = 2, padx=10, pady=10, sticky="nsew")

        self.equationframe = MyEquationFrame(master=self)
        self.equationframe.grid(column=4, row=0, padx=10, pady=10, sticky="nsew")

        self.calframe = MyCalcFrame(master=self)
        self.calframe.grid(column=4, row=1, padx=10, pady=10, sticky="nsew")

        self.app.choosechannelframe = MyChannelFrame(master=self, config=6*5) #this is needed to initialize the frame. But it is replaced when using the radiobutton and config is choosen
        self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")

        self.channel = customtkinter.CTkLabel(self.infoframe, text = "Channel:")
        self.channel.grid(column=0, row=0, padx=10, pady=10, sticky="e")
        self.HeaterID = customtkinter.CTkLabel(self.infoframe, text = "Heater ID:")
        self.HeaterID.grid(column=0, row=1, padx=10, pady=10, sticky="e")
        self.Resistance = customtkinter.CTkLabel(self.infoframe, text = "Resistance:")
        self.Resistance.grid(column=0, row=2, padx=10, pady=10, sticky="e")

        self.channel2 = customtkinter.CTkLabel(self.infoframe, text = "Null")
        self.channel2.grid(column=1, row=0, padx=10, pady=10, sticky="e")
        self.HeaterID2 = customtkinter.CTkLabel(self.infoframe, text = "Null")
        self.HeaterID2.grid(column=1, row=1, padx=10, pady=10, sticky="e")
        self.Resistance2 = customtkinter.CTkLabel(self.infoframe, text = "Null")
        self.Resistance2.grid(column=1, row=2, padx=10, pady=10, sticky="e")

class MyPackFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
    
class MyChannelFrame(customtkinter.CTkFrame):
    def __init__(self, master, config=6*5):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)

        self.mycalcsuperframe = master
        self.app = self.mycalcsuperframe.tabview.app

        self.channels = []
        heaterid = self.app.currentheaterid
        self.config=config

        mylabel = customtkinter.CTkLabel(self, text = "Channel")
        mylabel.grid(column=0, row=0, padx=10, pady=10, sticky="w")

        for i in range(int(self.config)):
            self.channels.append("Ch_"+str(i)+" ("+heaterid[i]+")")
        
         
        self.combobox = customtkinter.CTkComboBox(self, values=self.channels, command=self.combobox_callback)
        self.combobox.grid(column = 0, row = 1, padx=10, pady=10, sticky="e")
        self.combobox.set("Select")

    def combobox_callback(self, choice):
        print("combobox dropdown clicked:", choice)
        self.choice = int(choice)
        print('channel choosen is ' + str(self.choice))

        rest = self.mycalcsuperframe.tabview.app.resistancelist[self.choice]

        if rest != 'Null':
            rest = str(round(float(rest), 3))

        #Update infoframe with channel, heaterid name, acquired resistance
        self.mycalcsuperframe.channel2.configure(text=str(self.choice))

        self.mycalcsuperframe.Resistance2.configure(text=rest)
        
        for child in self.mycalcsuperframe.graphframe.winfo_children():
            child.destroy()  # remove existing figures

        print('printa self.choice')
        print(self.choice)
        print(type(self.choice))

        figur = self.calibrationplot2(str(self.choice))

        if figur != 'No data':
            figureframe = self.packplot(self.mycalcsuperframe.graphframe, figur)
            figureframe.grid(column=0, row=0)

            amp = str(round(self.app.caliparamlist[self.choice]["amp"],3))
            omega = str(round(self.app.caliparamlist[self.choice]["omega"],3))
            phase = str(round(self.app.caliparamlist[self.choice]["phase"],3))
            offset = str(round(self.app.caliparamlist[self.choice]["offset"],3))
            freq = str(round(self.app.caliparamlist[self.choice]["freq"],3))
            period = str(round(self.app.caliparamlist[self.choice]["period"],3))

        else: 
            amp = 'Null'
            omega = 'Null'
            phase = 'Null'
            offset = 'Null'
            freq = 'Null'
            period = 'Null'

        self.mycalcsuperframe.equationframe.label2b.configure(text=amp) 
        self.mycalcsuperframe.equationframe.label3b.configure(text=omega) 
        self.mycalcsuperframe.equationframe.label4b.configure(text=phase)
        self.mycalcsuperframe.equationframe.label5b.configure(text=offset) 
        self.mycalcsuperframe.equationframe.label6b.configure(text=freq)

        if self.mycalcsuperframe.tabview.app.val == "custom":
            self.mycalcsuperframe.HeaterID2.configure(text=self.mycalcsuperframe.tabview.app.idlist[self.choice].get())
        else: 
            self.mycalcsuperframe.HeaterID2.configure(text=self.mycalcsuperframe.tabview.app.idlist[self.choice].cget('text'))

        #reset calcframe with Null values if no calibration done, and if calibration done and applied currents then restore with those values
        self.mycalcsuperframe.calframe.curr2.configure(text=str(self.app.derivedcurrentlist[self.choice]))
        self.mycalcsuperframe.calframe.setcurr2.configure(text=str(self.app.setcurrentlist[self.choice]))

        print('graphframe children')
        for child in self.mycalcsuperframe.graphframe.winfo_children():
            print(child)  # check figures

        print('mychannelframe children')
        for child in self.winfo_children():
            print(child)  # check


    def packplot(self, master, fig): #figur to pack
        plt_frame = MyPackFrame(master)
        canvas = FigureCanvasTkAgg(fig, master=plt_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()
        plt.close('all')

        return plt_frame


    def calibrationplot2(self, channel):

        self.channel = int(channel)
        print('calibrationplot2')
        print(self.channel)
        print(type(self.channel))


        #set white font colors
        COLOR = 'white'
        matplotlib.rcParams['text.color'] = COLOR
        matplotlib.rcParams['axes.labelcolor'] = COLOR
        matplotlib.rcParams['xtick.color'] = COLOR
        matplotlib.rcParams['ytick.color'] = COLOR

        fig, ax = plt.subplots(1, figsize=(8,4))
        
        if self.app.IOconfig == self.IOconfig_options[0]:
            self.xdata = self.app.xdatalist_IOcross[self.channel]
            self.ydata = self.app.ydatalist_IOcross[self.channel]
        elif self.app.IOconfig == self.IOconfig_options[1]:
            self.xdata = self.app.xdatalist_IObar[self.channel]
            self.ydata = self.app.ydatalist_IObar[self.channel]

        if self.app.caliparamlist[self.channel] != 'Null':

            fitxdata = np.linspace(self.xdata[0], self.xdata[-1], 300)

            plt.plot(self.xdata,  self.ydata, "ok", label="optical power", color='white')
            plt.plot(fitxdata, self.app.caliparamlist[self.channel]["fitfunc"](fitxdata), "r-", label="fit curve", linewidth=2)
            plt.legend(loc="best", facecolor="#323334", framealpha=1)

            #plt.show()

            ax.set_facecolor("#323334")
            plt.setp(ax.spines.values(), color=COLOR)
            plt.xlabel("Heating power (P) mW")
            plt.ylabel("Optical power (Y) mW")
            fig.patch.set_facecolor("#323334")
            
            #reset to default colors
            COLOR = 'black'
            matplotlib.rcParams['text.color'] = COLOR
            matplotlib.rcParams['axes.labelcolor'] = COLOR
            matplotlib.rcParams['xtick.color'] = COLOR
            matplotlib.rcParams['ytick.color'] = COLOR

            return fig
        else: 
            return 'No data'
        
class MyCalcInfoFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.mycalcsuperframe = master

class MyCalibrationPlot(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)

class MyEquationFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.mycalcsuperframe = master
        #self.app = self.mycalcsuperframe.tabview.app

        self.label3a = customtkinter.CTkLabel(self, text="Angular frequency (b):")
        self.label3a.grid(column=0, row=0, padx=10, pady=0, sticky="e")
        self.label3b = customtkinter.CTkLabel(self, text="Null")
        self.label3b.grid(column=1, row=0, padx=10, pady=0, sticky="w")

        self.label4a = customtkinter.CTkLabel(self, text="Phase (c):")
        self.label4a.grid(column=0, row=1, padx=10, pady=0, sticky="e")
        self.label4b = customtkinter.CTkLabel(self, text="Null")
        self.label4b.grid(column=1, row=1, padx=10, pady=0, sticky="w")

        self.label5a = customtkinter.CTkLabel(self, text="Offset (d):")
        self.label5a.grid(column=0, row=2, padx=10, pady=0, sticky="e")
        self.label5b = customtkinter.CTkLabel(self, text="Null")
        self.label5b.grid(column=1, row=2, padx=10, pady=0, sticky="w")

        self.label6a = customtkinter.CTkLabel(self, text="Frequency (f):")
        self.label6a.grid(column=0, row=3, padx=10, pady=0, sticky="e")
        self.label6b = customtkinter.CTkLabel(self, text="Null")
        self.label6b.grid(column=1, row=3, padx=10, pady=0, sticky="w")

        #self.label7a = customtkinter.CTkLabel(self, text="Period:")
        #self.label7a.grid(column=0, row=6, padx=10, pady=0, sticky="e")
        #self.label7b = customtkinter.CTkLabel(self, text="Null")
        #self.label7b.grid(column=1, row=6, padx=10, pady=5, sticky="w")

class MyCalcFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.mycalcsuperframe = master
        self.app = self.mycalcsuperframe.tabview.app

        self.current2apply = 0 

        #phase mode
        self.phiphase = customtkinter.CTkLabel(self, text = "Phase mode (φ):")
        self.phiphase.grid(column=0, row=0, padx=10, pady=(10,5), sticky="e")
        self.phiphase2 = customtkinter.CTkEntry(self, placeholder_text = "input phase", width=100)
        self.phiphase2.grid(column=1, row=0, padx=10, pady=(10,5), sticky="ew")
        self.button = customtkinter.CTkButton(self, text="Apply", width=100, command = self.applyphase)
        self.button.grid(column=2, row=0, padx=10, pady=(10,5), sticky="w")
            #derived current given the phase
        self.curr = customtkinter.CTkLabel(self, text = "Derived current (mA):")
        self.curr.grid(column=0, row=1, padx=10, pady=(5,10), sticky="e")
        self.curr2 = customtkinter.CTkLabel(self, text = "Null")
        self.curr2.grid(column=1, row=1, padx=10, pady=(5,10), sticky="ew")
        self.button = customtkinter.CTkButton(self, text="Apply", width=100, command = self.applycurrent)
        self.button.grid(column=2, row=1, padx=10, pady=(5,10), sticky="w")

        #current mode
        self.currentmode = customtkinter.CTkLabel(self, text = "Current mode (mA):")
        self.currentmode.grid(column=0, row=4, padx=10, pady=(5,10), sticky="e")
        self.currententry = customtkinter.CTkEntry(self, placeholder_text = "input current", width=100)
        self.currententry.grid(column=1, row=4, padx=10, pady=(5,10), sticky="ew")
        self.currbutton = customtkinter.CTkButton(self, text="Apply", width=100, command = self.applycurrentmode)
        self.currbutton.grid(column=2, row=4, padx=10, pady=(5,10), sticky="w")

        self.setcurr = customtkinter.CTkLabel(self, text = "Set current (mA):")
        self.setcurr.grid(column=0, row=6, padx=10, pady=(5,5), sticky="e")
        self.setcurr2 = customtkinter.CTkLabel(self, text = "Null")
        self.setcurr2.grid(column=1, row=6, padx=10, pady=(5,5), sticky="ew")

        self.release = customtkinter.CTkButton(self, text="Release", width=100, command = self.releasecurrent)
        self.release.grid(column=2, row=6, padx=10, pady=(5,5), sticky="w")


    def applyphase(self):
        self.channel = int(self.app.choosechannelframe.combobox.get())
        print('apply phase button pressed')
        print('choosen channel is' + str(self.channel))

        phi = self.phiphase2.get() #get the entry as string

        #check if the entry cell is empty 
        if phi == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a integer or float phase value and then press submit again')

        else:
            illegalchar = False
            point = 0

            #check for invalid entry characters
            for i in range(len(phi)):
                if phi[i] in self.app.allowedinputvalues:
                    print(phi[i])
                    if phi[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + phi[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new phase value')
                self.phiphase2.delete(0, 'end') #clear the entry field
            else:
                phi = float(phi) #make the entry value a float
                self.app.phiphase2list[self.channel] = phi #save the entry value for the phase
            
                c = self.app.caliparamlist[self.channel]["phase"] #get the phase from the parameter list for the right channel
                b = self.app.caliparamlist[self.channel]["omega"] #get the angular frequency for the paramter list for the right channel
                R = self.app.resistancelist[self.channel] #get the resistance for the right channel

                P = abs((phi / 2 - c) / b) #Derive the eletrical power (heating power for this phase) in mW since the fitting is made with data in mW both x and y data. 
                self.current2apply = float(round(1000 * np.sqrt(P/(R*1000)), 3)) #Derive the current in A, converted to mA to apply for this phase.

                self.phiphase2.delete(0, 'end') #clear the entry field

                self.curr2.configure(text = str(self.current2apply)) #reconfigure the label with this value in the GUI
                self.app.derivedcurrentlist[self.channel] = self.current2apply #save the value of the current for this channel
                print('derivedcurrentlist')
                print(self.app.derivedcurrentlist)

    def applycurrent(self):
        print('Apply current button is pressed')
        self.channel = int(self.app.choosechannelframe.combobox.get())
        print('the choosen channel is ' + str(self.channel))

        #check if the entry cell is empty 
        if self.app.derivedcurrentlist[self.channel] == 'Null':
            messagebox.showerror(message='PROCESS FAILURE! \n Please first fill in a desired phase value in the cell above and submit, then apply the derived current value')

        else: #check so not exceeding current limit
            if self.app.derivedcurrentlist[self.channel] > q.imax[self.channel] or self.app.derivedcurrentlist[self.channel] < 0: 
                messagebox.showwarning(message='WARNING! \n\n Desired current to apply is exceeding the current limit or is negative. Please recalculate the desired current by applying a new phase')
            else: 
                print('Set the current on channel ' + str(self.channel) + ' to ' + str(self.app.derivedcurrentlist[self.channel]) + ' mA')
                q.i[self.channel] = self.app.derivedcurrentlist[self.channel] #set the current to the derived current for the phase on the channel
                self.setcurr2.configure(text = str(self.app.derivedcurrentlist[self.channel])) # print it out on the GUI
                self.app.setcurrentlist[self.channel] = self.app.derivedcurrentlist[self.channel] #save the actual value of the current that is set on the channel
                self.app.setcurrlabellist[self.channel].configure(text = str(round(self.app.setcurrentlist[self.channel], 3)))
                

    def applycurrentmode(self):
        print('apply current mode button is pressed')
        self.channel = int(self.app.choosechannelframe.combobox.get())
        print('choosen channel is ' + str(self.channel))

        self.currmodeapply = self.currententry.get()

        #check if the entry cell is empty 
        if self.currmodeapply == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a integer or float value of desired current in mA and submit')

        else: 
            illegalchar = False
            point = 0

            #check for invalid entry characters
            for i in range(len(self.currmodeapply)):
                if self.currmodeapply[i] in self.app.allowedinputvalues:
                    print(self.currmodeapply[i])
                    if self.currmodeapply[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + self.currmodeapply[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new current value in mA')
                self.currententry.delete(0, 'end') #clear the entry field
            else:
                self.currmodeapply = float(self.currmodeapply)
                self.app.currententrylist[self.channel] = self.currmodeapply #save the entry value for the desired current
                if self.currmodeapply > q.imax[self.channel] or self.currmodeapply < 0: 
                    messagebox.showerror(message='Desired current to apply is exceeding the current limit. Please input a lower desired current value in mA')
                    self.currententry.delete(0, 'end') #clear the entry field
                else: 
                    print('Set the current on channel ' + str(self.channel) + ' to ' + str(self.currmodeapply) + ' mA')
                    q.i[self.channel] = self.currmodeapply
                    self.currententry.delete(0, 'end') #clear the entry field
                    self.setcurr2.configure(text = str(self.currmodeapply))
                    self.app.setcurrentlist[self.channel] = self.currmodeapply #save this current value that the channel is set to
                    self.app.setcurrlabellist[self.channel].configure(text = str(round(self.app.setcurrentlist[self.channel], 3)))

    def releasecurrent(self):
        self.channel = int(self.app.choosechannelframe.combobox.get())
        print('release button is pressed')
        print('Release the current on channel ' + str(self.channel) + ' and set it to 0 mA')
        q.i[self.channel] = 0
        self.setcurr2.configure(text = str(0))
        self.app.setcurrentlist[self.channel] = 'Null' #save the current value to Null in the list for the right channel
        self.app.setcurrlabellist[self.channel].configure(text = str(self.app.setcurrentlist[self.channel]))
        messagebox.showinfo(message='Release of current on channel ' + str(self.channel) + ' and set to 0 mA')

class MyCalcFrame_main(customtkinter.CTkFrame):
    def __init__(self, master, Channel, Fit, IOconfig):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.settingsframe = master
        self.app = self.settingsframe.app
        self.currentchannel = Channel
        self.currentIOconfig = IOconfig
        self.currentfit = Fit
        self.fitnames = np.array(["Linear", "Linear+cubic"])
        self.currentfit_name = self.fitnames[self.app.fit_func.index(self.currentfit)]
        self.fit_index = self.app.fit_func.index(self.currentfit)
        self.IOconfig_index = self.app.IOconfig_options.index(self.currentIOconfig)
        
        self.calpararrays = [[self.app.caliparamlist_lin_cross, self.app.caliparamlist_lin_bar], [self.app.caliparamlist_lincub_cross, self.app.caliparamlist_lincub_bar]]
        self.currentarray = self.calpararrays[self.fit_index][self.IOconfig_index]
        
        self.currentsettings = self.currentarray[self.currentchannel]
        
        #{"amp": A, "omega": b, "phase": c, "offset": d, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}
        #A * np.cos(b*P + c) + d
        
        if self.currentsettings != "Null":
        
            self.A = self.currentsettings["amp"]
            self.d = self.currentsettings["offset"]
            self.c = self.currentsettings["phase"] 
            self.b = self.currentsettings["omega"]
    
            self.visibility = self.A/self.d
            
            if self.currentfit == self.app.fit_func[0]:
                self.R = self.app.linear_resistance_list[self.currentchannel] #get the resistance for the right channel    
                self.P_pi = abs((np.pi - self.c) / self.b) #Heating power of phi phase shift
 
                self.mod_period = 2*(np.pi)/self.b
                self.pi_PS_current = 1000*np.sqrt(self.P_pi/(self.R*1000))
                    
            elif self.currentfit == self.app.fit_func[1]:
                    
                # Define symbols
                I = sp.symbols('I')
                self.R0 = self.app.resistance_parameter_list[self.currentchannel][1]
                self.alpha = self.app.resistance_parameter_list[self.currentchannel][0]/self.app.resistance_parameter_list[self.currentchannel][1]
                
                # Define equation
                self.P_pi = abs((np.pi - self.c) / self.b)
                self.P_pi=self.P_pi/1000   #unit in W
                
                self.mod_period = 2*(np.pi)/self.b
                eq = sp.Eq(self.P_pi/self.R0, I**2 + self.alpha*I**4)
                
                # Solve the equation
                solutions = sp.solve(eq, I)
                
                # Filter and choose the real, positive solution
                self.pi_PS_current_pos_sol = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
                self.pi_PS_current = 1000*self.pi_PS_current_pos_sol[0]
        
        self.title1 = customtkinter.CTkLabel(self, text="Settings Ch " + str(self.currentchannel) + " (" + str(self.app.currentheaterid[self.currentchannel]) + ")", font=customtkinter.CTkFont(family="Arial", size=14, weight="bold", underline=True), corner_radius=6)
        self.title1.grid(row=0, column=0, columnspan=3, padx=10, pady=(10,0), sticky="new")
        
        self.title2 = customtkinter.CTkLabel(self, text="IO config - " + str(self.currentIOconfig) + ", I-V fit - " + str(self.currentfit_name), font=customtkinter.CTkFont(family="Arial", size=12, weight="bold"), corner_radius=6)
        self.title2.grid(row=1, column=0, columnspan=3, padx=10, pady=0, sticky="new")

        self.label3a = customtkinter.CTkLabel(self, text="Offset phase (c):")
        self.label3a.grid(column=0, row=2, padx=10, pady=0, sticky="e")
        self.label3b = customtkinter.CTkLabel(self, text="Null" if self.currentsettings == "Null" else str(float(round(self.currentsettings["phase"]/np.pi, 2)))+" π")
        self.label3b.grid(column=1, row=2, padx=10, pady=0, sticky="w")

        self.label4a = customtkinter.CTkLabel(self, text="Visibility:")
        self.label4a.grid(column=0, row=3, padx=10, pady=0, sticky="e")
        self.label4b = customtkinter.CTkLabel(self, text="Null" if self.currentsettings == "Null" else float(round(self.visibility, 2)))
        self.label4b.grid(column=1, row=3, padx=10, pady=0, sticky="w")

        self.label5a = customtkinter.CTkLabel(self, text="Modulation period (mW):")
        self.label5a.grid(column=0, row=4, padx=10, pady=0, sticky="e")
        self.label5b = customtkinter.CTkLabel(self, text="Null" if self.currentsettings == "Null" else str(float(round(self.mod_period, 2))) + " mW")
        self.label5b.grid(column=1, row=4, padx=10, pady=0, sticky="w")

        self.label6a = customtkinter.CTkLabel(self, text="Current for π PS (mA):")
        self.label6a.grid(column=0, row=5, padx=10, pady=0, sticky="e")
        self.label6b = customtkinter.CTkLabel(self, text="Null" if self.currentsettings == "Null" else f"{round(self.pi_PS_current, 2):.2f} mA")
        self.label6b.grid(column=1, row=5, padx=10, pady=0, sticky="w")

        #self.label7a = customtkinter.CTkLabel(self, text="Period:")
        #self.label7a.grid(column=0, row=6, padx=10, pady=0, sticky="e")
        #self.label7b = customtkinter.CTkLabel(self, text="Null")
        #self.label7b.grid(column=1, row=6, padx=10, pady=5, sticky="w")

        self.current2apply = 0 
        
        self.button_width = 50
        self.box_width = 60
        
        #phase mode
        self.phiphase = customtkinter.CTkLabel(self, text = "Phase mode (φ):")
        self.phiphase.grid(column=0, row=6, padx=10, pady=(5,0), sticky="e")
        self.phiphase2 = customtkinter.CTkEntry(self, placeholder_text = "π units", width=self.box_width) #Enter in units of pi
        self.phiphase2.grid(column=1, row=6, padx=10, pady=(5,0), sticky="ew")
        self.button = customtkinter.CTkButton(self, text="Apply", width=self.button_width, command = self.applyphase)
        self.button.grid(column=2, row=6, padx=10, pady=(5,0), sticky="nsew")
            #derived current given the phase
        self.curr = customtkinter.CTkLabel(self, text = "Derived current (mA):")
        self.curr.grid(column=0, row=7, padx=10, pady=(5,0), sticky="e")
        self.curr2 = customtkinter.CTkLabel(self, text = "Null")
        self.curr2.grid(column=1, row=7, padx=10, pady=(5,0), sticky="ew")
        self.button = customtkinter.CTkButton(self, text="Apply", width=self.button_width, command = self.applycurrent)
        self.button.grid(column=2, row=7, padx=10, pady=(5,0), sticky="nsew")

        #current mode
        self.currentmode = customtkinter.CTkLabel(self, text = "Current mode (mA):")
        self.currentmode.grid(column=0, row=8, padx=10, pady=(5,0), sticky="e")
        self.currententry = customtkinter.CTkEntry(self, placeholder_text = "(mA)", width=self.box_width)
        self.currententry.grid(column=1, row=8, padx=10, pady=(5,0), sticky="nsew")
        self.currbutton = customtkinter.CTkButton(self, text="Apply", width=self.button_width, command = self.applycurrentmode)
        self.currbutton.grid(column=2, row=8, padx=10, pady=(5,0), sticky="nsew")

        self.setcurr = customtkinter.CTkLabel(self, text = "Set current (mA):")
        self.setcurr.grid(column=0, row=9, padx=10, pady=(5,5), sticky="e")
        self.setcurr2 = customtkinter.CTkLabel(self, text = "Null")
        self.setcurr2.grid(column=1, row=9, padx=10, pady=(5,5), sticky="ew")

        self.release = customtkinter.CTkButton(self, text="Release", width=self.button_width, command = self.releasecurrent)
        self.release.grid(column=2, row=9, padx=10, pady=(5,5), sticky="nsew")
        
    def applyphase(self):
        
        self.channel = self.currentchannel
        print('apply phase button pressed')
        print('choosen channel is' + str(self.currentchannel))

        phi = self.phiphase2.get() #get the entry as string
        self.recieved_phase_input = float(phi)
        
        if self.currentsettings == "Null":
            messagebox.showerror(message='Phase shifter characterization data missing. Characterize the phase shiter before attempting to set the phase or current')
            
        elif self.recieved_phase_input<self.c/np.pi:
            
            messagebox.showerror(message='Entered phase less than  the offset phase of this phase shifter. Enter a greater value')
        #check if the entry cell is empty 
        elif phi == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a integer or float phase value and then press submit again')

        else:
            illegalchar = False
            point = 0

            #check for invalid entry characters
            for i in range(len(phi)):
                if phi[i] in self.app.allowedinputvalues:
                    print(phi[i])
                    if phi[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + phi[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new phase value')
                self.phiphase2.delete(0, 'end') #clear the entry field
            else:
                phi = float(phi) #make the entry value a float (Unit of pi)
                self.app.phiphase2list[self.currentchannel] = phi #save the entry value for the phase
                
                if self.currentfit == self.app.fit_func[0]:

                    P = abs((phi*np.pi - self.c) / self.b) #Heating power of phi phase shift
                    self.current2apply = float(round(1000 * np.sqrt(P/(self.R*1000)), 2)) #Derive the current in A, converted to mA to apply for this phase.
                        
                elif self.currentfit == self.app.fit_func[1]:
                        
                    # Define symbols
                    I = sp.symbols('I')
                    
                    P = abs((phi*np.pi - self.c) / self.b)
                    # Define equation
                    P=P/1000  #Unit in W
                    
                    eq = sp.Eq(P/self.R0, I**2 + self.alpha*I**4)
                    
                    # Solve the equation
                    solutions = sp.solve(eq, I)
                    
                    # Filter and choose the real, positive solution
                    positive_solution_list = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
                    positive_solution = 1000*positive_solution_list[0]

                    self.current2apply = float(round(positive_solution, 5)) #Derive the current in A, converted to mA to apply for this phase.
                
                            

                self.phiphase2.delete(0, 'end') #clear the entry field

                self.curr2.configure(text = f"{self.current2apply:.2f} mA") #reconfigure the label with this value in the GUI
                self.app.derivedcurrentlist[self.currentchannel] = self.current2apply #save the value of the current for this channel
                print('derivedcurrentlist')
                print(self.app.derivedcurrentlist)

    def applycurrent(self):
        print('Apply current button is pressed')
        self.channel = self.currentchannel
        print('the choosen channel is ' + str(self.channel))

        #check if the entry cell is empty 
        if self.app.derivedcurrentlist[self.channel] == 'Null':
            messagebox.showerror(message='PROCESS FAILURE! \n Please first fill in a desired phase value in the cell above and submit, then apply the derived current value')

        else: #check so not exceeding current limit
            if self.app.derivedcurrentlist[self.channel] > q.imax[self.channel] or self.app.derivedcurrentlist[self.channel] < 0: 
                messagebox.showwarning(message='WARNING! \n\n Desired current to apply is exceeding the current limit or is negative. Please recalculate the desired current by applying a new phase')
            else: 
                print('Set the current on channel ' + str(self.channel) + ' to ' + str(self.app.derivedcurrentlist[self.channel]) + ' mA')
                q.i[self.channel] = self.app.derivedcurrentlist[self.channel] #set the current to the derived current for the phase on the channel
                #self.setcurr2.configure(text = str(self.app.derivedcurrentlist[self.channel])) # print it out on the GUI
                self.setcurr2.configure(text = f"{self.app.derivedcurrentlist[self.channel]:.2f} mA") # print it out on the GUI
                self.app.setcurrentlist[self.channel] = self.app.derivedcurrentlist[self.channel] #save the actual value of the current that is set on the channel
                self.app.setcurrlabellist[self.channel].configure(text = str(round(self.app.setcurrentlist[self.channel], 3)))
                self.app.setphaselabellist[self.channel].configure(text = str(round(self.recieved_phase_input, 3))+"π")

    def applycurrentmode(self):
        print('apply current mode button is pressed')
        self.channel = self.currentchannel
        print('choosen channel is ' + str(self.channel))

        self.currmodeapply = self.currententry.get()
        
        if self.currentsettings == "Null":
            messagebox.showerror(message='Phase shifter characterization data missing. Characterize the phase shiter before attempting to set the phase or current')

        #check if the entry cell is empty 
        elif self.currmodeapply == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a integer or float value of desired current in mA and submit')

        else: 
            illegalchar = False
            point = 0

            #check for invalid entry characters
            for i in range(len(self.currmodeapply)):
                if self.currmodeapply[i] in self.app.allowedinputvalues:
                    print(self.currmodeapply[i])
                    if self.currmodeapply[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + self.currmodeapply[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new current value in mA')
                self.currententry.delete(0, 'end') #clear the entry field
            else:
                self.currmodeapply = float(self.currmodeapply)
                self.app.currententrylist[self.channel] = self.currmodeapply #save the entry value for the desired current
                if self.currmodeapply > q.imax[self.channel] or self.currmodeapply < 0: 
                    messagebox.showerror(message='Desired current to apply is exceeding the current limit. Please input a lower desired current value in mA')
                    self.currententry.delete(0, 'end') #clear the entry field
                else: 
                    print('Set the current on channel ' + str(self.channel) + ' to ' + str(self.currmodeapply) + ' mA')
                    q.i[self.channel] = self.currmodeapply
                    self.currententry.delete(0, 'end') #clear the entry field
                    #self.setcurr2.configure(text = str(self.currmodeapply))
                    self.setcurr2.configure(text = f"{self.currmodeapply:.2f} mA")

                    self.app.setcurrentlist[self.channel] = self.currmodeapply #save this current value that the channel is set to
                    self.app.setcurrlabellist[self.channel].configure(text = str(round(self.app.setcurrentlist[self.channel], 3)))
                    
                    set_current = self.app.setcurrentlist[self.channel]  #Unit mA
                    
                    if self.currentfit == self.app.fit_func[0]:
                        self.set_phase = (self.b*self.R*(set_current**2))/1000+self.c
                            
                    elif self.currentfit == self.app.fit_func[1]:
                            
                        self.set_phase = (self.b*(set_current**2)*(self.R0*(1+self.alpha*((set_current/1000)**2))))/1000+self.c
                        
                    self.app.setphaselabellist[self.channel].configure(text = str(round(self.set_phase/np.pi, 3))+"π")

    def releasecurrent(self):
        self.channel = self.currentchannel
        print('release button is pressed')
        print('Release the current on channel ' + str(self.channel) + ' and set it to 0 mA')
        q.i[self.channel] = 0
        self.setcurr2.configure(text = str(0))
        self.app.setcurrentlist[self.channel] = 'Null' #save the current value to Null in the list for the right channel
        self.app.setcurrlabellist[self.channel].configure(text = str(self.app.setcurrentlist[self.channel]))
        self.app.setphaselabellist[self.channel].configure(text = str(round(self.c/np.pi, 3))+"π")
        messagebox.showinfo(message='Release of current on channel ' + str(self.channel) + ' and set to 0 mA')

class MyHeaderFrame(customtkinter.CTkFrame):
    def __init__(self, master, val, app):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        #self.headings = headings
        self.val = val
        self.app=app

        #for i in range(len(self.headings)):
        #    label1 = customtkinter.CTkLabel(self, text=self.headings[i])
        #    label1.grid(row=0, column=i, padx=10, pady=(10,0), sticky="ew")

        if self.val == '6x6' or self.val == '8x8' or self.val == 'custom':
            head0 = customtkinter.CTkLabel(self, text='CH')
            head0.grid(column=0, row=0, padx=(20,0), pady=(10,0), sticky="e")
            head1 = customtkinter.CTkLabel(self, text='ID')
            head1.grid(column=1, row=0, padx=(25,0), pady=(10,0), sticky="e")
            head2 = customtkinter.CTkLabel(self, text='Fitting Function')
            head2.grid(column=2, row=0, padx=(28,0), pady=(10,0), sticky="e")
            self.fitselect_all = customtkinter.CTkComboBox(self,width=90, values=self.app.fit_func, command=lambda choice, idx=i: self.update_all_comboboxes(self.app.scrollable_frame.fitselectpack, choice, self.app.fit_func_allchannels))
            self.fitselect_all.grid(column=2, row=2, padx=(28,0), pady=(0,10), sticky="nsew")
            self.fitselect_all.set(self.app.fit_func[0])
            
            head3 = customtkinter.CTkLabel(self, text='Resistance (R)')
            head3.grid(column=3, row=0, padx=(25,0), pady=(10,0), sticky="e")
            head4 = customtkinter.CTkLabel(self, text='L+C fit values (kΩ)')
            head4.grid(column=4, columnspan=3, row=0, padx=(22,0), pady=(10,0), sticky="e")
            head5_21 = customtkinter.CTkLabel(self, text='R min')
            head5_21.grid(column=4, row=1, padx=(15,0), pady=(0,10), sticky="w")
            head6_22 = customtkinter.CTkLabel(self, text='R max')
            head6_22.grid(column=5, row=1, padx=(10,0), pady=(0,10), sticky="w")
            head7_23 = customtkinter.CTkLabel(self, text='α')
            head7_23.grid(column=6, row=1, padx=(10,0), pady=(0,10), sticky="w")
            head8 = customtkinter.CTkLabel(self, text='Linear fit')
            head8.grid(column=7, row=0, padx=(20,0), pady=(10,0), sticky="e")
            head8_2 = customtkinter.CTkLabel(self, text='R (kΩ)')
            head8_2.grid(column=7, row=1, padx=(25,0), pady=(0,10), sticky="nsew")
            head9 = customtkinter.CTkLabel(self, text='Set I Limit')
            head9.grid(column=8, row=0, padx=(20,0), pady=(10,0), sticky="e")
            head9_2 = customtkinter.CTkLabel(self, text='(mA)')
            head9_2.grid(column=8, row=1, padx=(25,0), pady=(0,10), sticky="nsew")
            self.currententry_all = customtkinter.CTkEntry(self, placeholder_text="(mA)", width=50)
            self.currententry_all.grid(column=8, row=2, padx=(25,0), pady=(0,10), sticky="nsew")
            self.currententry_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.setIlimitpack, master=self.currententry_all, event=event))
            
            head10 = customtkinter.CTkLabel(self, text='Measure')
            head10.grid(column=9, row=0, padx=(50,0), pady=(10,0), sticky="e")
            head10_2 = customtkinter.CTkLabel(self, text='(mA)')
            head10_2.grid(column=9, row=1, padx=(50,0), pady=(0,10), sticky="nsew")
            head11 = customtkinter.CTkLabel(self, text='Set I')
            head11.grid(column=10, row=0, padx=50, pady=(10,0), sticky="nsew")
            head11_2 = customtkinter.CTkLabel(self, text='(mA)')
            head11_2.grid(column=10, row=1, padx=50, pady=(0,10), sticky="nsew")
            self.currentry_all = customtkinter.CTkEntry(self, placeholder_text="(mA)", width=50)
            self.currentry_all.grid(column=10, row=2, padx=(0,0), pady=(0,10), sticky="n")
            self.currentry_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.setIpack, master=self.currentry_all, event=event))
            
            head12 = customtkinter.CTkLabel(self, text='Measure')
            head12.grid(column=11, row=0, padx=(15,0), pady=(10,0), sticky="e")
            head12_2 = customtkinter.CTkLabel(self, text='(mA)')
            head12_2.grid(column=11, row=1, padx=(15,0), pady=(0,10), sticky="nsew")
            head13 = customtkinter.CTkLabel(self, text='Start I')
            head13.grid(column=12, row=0, padx=(45,0), pady=(10,0), sticky="nsew")
            head13_2 = customtkinter.CTkLabel(self, text='(mA)')
            head13_2.grid(column=12, row=1, padx=(45,0), pady=(0,10), sticky="nsew")
            self.rampstart_all = customtkinter.CTkEntry(self, placeholder_text="Start", width=50)
            self.rampstart_all.grid(column=12, row=2, padx=(50,0), pady=(0,10), sticky="n")
            self.rampstart_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.startpack, master=self.rampstart_all, event=event))
            
            head14 = customtkinter.CTkLabel(self, text='End I')
            head14.grid(column=13, row=0, padx=(12,0), pady=(10,0), sticky="nsew")
            head14_2 = customtkinter.CTkLabel(self, text='(mA)')
            head14_2.grid(column=13, row=1, padx=(12,0), pady=(0,10), sticky="nsew")
            self.rampend_all = customtkinter.CTkEntry(self, placeholder_text="End", width=50)
            self.rampend_all.grid(column=13, row=2, padx=(10,0), pady=(0,10), sticky="n")
            self.rampend_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.endpack, master=self.rampend_all, event=event))
            
            
            head15 = customtkinter.CTkLabel(self, text='Steps')
            head15.grid(column=14, row=0, padx=(20,15), pady=(10,0), sticky="nsew")
            self.steps_all = customtkinter.CTkEntry(self, placeholder_text="Steps", width=50)
            self.steps_all.grid(column=14, row=2, padx=(0,0), pady=(0,10), sticky="n")
            self.steps_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.stepspack, master=self.steps_all, event=event))
            
            head16 = customtkinter.CTkLabel(self, text='Pause')
            head16.grid(column=15, row=0, padx=(12,12), pady=(10,0), sticky="nsew")
            head16_2 = customtkinter.CTkLabel(self, text='(sec)')
            head16_2.grid(column=15, row=1, padx=(12,12), pady=(0,10), sticky="nsew")
            self.pause_all = customtkinter.CTkEntry(self, placeholder_text="Pause", width=50)
            self.pause_all.grid(column=15, row=2, padx=(0,0), pady=(0,10), sticky="n")
            self.pause_all.bind("<Return>", lambda event: self.update_all_entries(entriespack=self.app.scrollable_frame.pausepack, master=self.pause_all, event=event))
            
            head17 = customtkinter.CTkLabel(self, text='IO config')
            head17.grid(column=16, row=0, padx=(20,15), pady=(10,0), sticky="nsew")
            self.IOconfigselect_all = customtkinter.CTkComboBox(self,width=80, values=self.app.IOconfig_options, command=lambda choice, idx=i: self.update_all_comboboxes(self.app.scrollable_frame.IOconfigselectpack, choice, self.app.IOconfig_allchannels))
            self.IOconfigselect_all.grid(column=16, row=2, padx=(15, 10), pady=(0,10), sticky="e")
            self.IOconfigselect_all.set(self.app.IOconfig_options[0])

            head18 = customtkinter.CTkLabel(self, text='Calibrate')
            head18.grid(column=17, row=0, padx=(15,0), pady=(10,0), sticky="nsew") 
            head19 = customtkinter.CTkLabel(self, text='Current')
            head19.grid(column=18, row=0, padx=(25,10), pady=(10,0), sticky="nsew")
            head19_2 = customtkinter.CTkLabel(self, text='(mA)')
            head19_2.grid(column=18, row=1, padx=(20,0), pady=(0,10), sticky="nsew")
            head20 = customtkinter.CTkLabel(self, text='Phase')
            head20.grid(column=19, row=0, padx=(5,20), pady=(10,0), sticky="nsew")
            head20_2 = customtkinter.CTkLabel(self, text='(φ)')
            head20_2.grid(column=19, row=1, padx=(5,20), pady=(0,10), sticky="nsew")
            
    def update_all_comboboxes(self, comboboxpack, choice, packarray):
        for x in comboboxpack:
            x.set(choice)
            for i in range (self.app.config):
                packarray[i] = choice
                
    def update_all_entries(self, entriespack, master, event=None):
        value=master.get() 
        for x in entriespack:
            x.delete(0, customtkinter.END)  # Clear existing text
            x.insert(0, value)

class MyScrollableFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, title, params, heaterid, config, app):
        super().__init__(master, label_text='')
        #self.geometry("1500x200")
        self.grid_columnconfigure(0, weight=0)
        #self.grid_rowconfigure((1), weight=0)
        self.params = params
        self.keys=list(self.params.keys())
        self.values=list(self.params.values())
        self.heatid = heaterid
        self.config = config
        self.app = app
 

        self.app.resistancelist = ["Null" for i in range(self.config)] #list with saved resistances
        self.app.resistance_parameter_list = ["Null" for i in range(self.config)] #list with saved resistances
        self.app.rmin_list = ["Null" for i in range(self.config)]
        self.app.rmax_list = ["Null" for i in range(self.config)]
        self.app.alpha_list = ["Null" for i in range(self.config)]
        self.app.linear_resistance_list = ["Null" for i in range(self.config)]
        
        self.app.caliparamlist_lin_cross = ["Null" for i in range(self.config)] #here save the calibration parameters for each channel (a dictionary of parameters per channel)
        self.app.caliparamlist_lin_bar = ["Null" for i in range(self.config)]
        self.app.caliparamlist_lincub_cross = ["Null" for i in range(self.config)]
        self.app.caliparamlist_lincub_bar = ["Null" for i in range(self.config)]
        
        self.app.xdatalist_IObar = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.ydatalist_IObar = [[] for i in range(self.config)] #list of lists for saved ydata for each channel
        self.app.xdatalist_IOcross = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.ydatalist_IOcross = [[] for i in range(self.config)] #list of lists for saved ydata for each channel
        
        self.app.linchar_current = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.linchar_voltage = [[] for i in range(self.config)] #list of lists for saved ydata for each channel
        self.app.lincubchar_current = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.lincubchar_voltage = [[] for i in range(self.config)] #list of lists for saved ydata for each channel

        self.app.derivedcurrentlist = ['Null' for i in range(self.config)] #here save the actual value
        self.app.setcurrentlist = ['Null' for i in range(self.config)] #here save the actual value
        self.app.phiphase2list  = ['Null' for i in range(self.config)] #here save the phase value

        self.app.currententrylist  = ['Null' for i in range(self.config)] #here save entry value for current mode
        self.app.res_lin_char_images = [BytesIO() for _ in range(self.config)]
        self.app.res_lincub_char_images = [BytesIO() for _ in range(self.config)]
        self.app.opmod_lin_char_cross_state_images = [BytesIO() for _ in range(self.config)]
        self.app.opmod_lin_char_bar_state_images = [BytesIO() for _ in range(self.config)]
        self.app.opmod_lincub_char_cross_state_images = [BytesIO() for _ in range(self.config)]
        self.app.opmod_lincub_char_bar_state_images = [BytesIO() for _ in range(self.config)]
        for i in range(self.config):
            image = Image.new("RGB", (100, 100), color=(255, 255, 255))  # Create a white image
            image.save(self.app.res_lin_char_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.res_lin_char_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.res_lincub_char_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.res_lincub_char_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lin_char_cross_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lin_char_cross_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lin_char_bar_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lin_char_bar_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lincub_char_cross_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lincub_char_cross_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lincub_char_bar_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lincub_char_bar_state_images[i].seek(0)  # Reset buffer position to the start
            
        self.app.IVimagechoices = [self.app.res_lin_char_images, self.app.res_lincub_char_images]
        self.app.opmodimagechoices = [[self.app.opmod_lin_char_cross_state_images, self.app.opmod_lin_char_bar_state_images],[self.app.opmod_lincub_char_cross_state_images, self.app.opmod_lincub_char_bar_state_images]]
        
        #create data structures to be able to access and export data
        self.app.channellist = []
        self.app.idlist = []
        self.app.customtkinterresistancelist = []
        self.app.customtkinterrmin_list = []
        self.app.customtkinterrmax_list = []
        self.app.customtkinteralpha_list = []
        self.app.customtkinterlinear_resistance_list = []
        self.app.customtkinterresistance_parameter_list = []
        self.app.currentlimitlist = [] #initialize these globally for all channels at startup or set custom globally with an entry and button
        self.app.appliedcurrlist = []
        self.app.measuredcurrentlist = []
        self.app.rampstartlist = []
        self.app.rampendlist = []
        self.app.stepslist = []
        self.app.stabtimelist = []
        self.app.setcurrlabellist = []
        self.app.setphaselist = []
        self.app.setphaselabellist = []
        self.app.fit_func = [f"Linear fit (V = R\u2080 * I )", f"Cubic + linear fit (V = R\u2080 ( I + αI\u00B3)"]
        self.app.IOconfig_options = ["Cross", "Bar"]
        self.app.fit_func_allchannels = [self.app.fit_func[0] for i in range(self.config)] 
        self.app.IOconfig_allchannels = [self.app.IOconfig_options[0] for i in range(self.config)] 
        
        
        self.app.fit=self.app.fit_func[0]
        self.app.IOconfig=self.app.IOconfig_options[0]
        
        self.fitselectpack=[]
        self.IOconfigselectpack = []
        self.setIlimitpack = []
        self.setIpack = []
        self.startpack = []
        self.endpack = []
        self.stepspack = []
        self.pausepack = []
        self.acqresist_minpack = []
        self.acqresist_maxpack = []
        self.alphapack = []
        self.acqresist_linpack = []
        
        for i in range(self.config):
            channel = customtkinter.CTkLabel(self, text=str(i))
            channel.grid(column=0, row=i+1, padx=10, pady=10, sticky="e")
            heateridd = customtkinter.CTkLabel(self, text=self.heatid[i])
            heateridd.grid(column=1, row=i+1, padx=10, pady=10, sticky="nsew")
            
            acqresist_min = customtkinter.CTkLabel(self, text="Null")
            acqresist_min.grid(column=4, row=i+1, padx=10, pady=10, sticky="nsew")
            self.acqresist_minpack.append(acqresist_min)
            
            acqresist_max = customtkinter.CTkLabel(self, text="Null")
            acqresist_max.grid(column=5, row=i+1, padx=10, pady=10, sticky="nsew")
            self.acqresist_maxpack.append(acqresist_max)
            
            alpha = customtkinter.CTkLabel(self, text="Null")
            alpha.grid(column=6, row=i+1, padx=10, pady=10, sticky="nsew")
            self.alphapack.append(alpha)
            
            acqresist_lin = customtkinter.CTkLabel(self, text="Null")
            acqresist_lin.grid(column=7, row=i+1, padx=20, pady=10, sticky="nsew")
            self.acqresist_linpack.append(acqresist_lin)
            
            output_list = [acqresist_min, acqresist_max, alpha, acqresist_lin]

            self.fitselect = customtkinter.CTkComboBox(self,width=90, values=self.app.fit_func, command=lambda choice, idx=i: self.fitselect_change(idx, choice))
            self.fitselect.grid(column=2, row=i+1, padx=10, pady=10, sticky="nsew")
            self.fitselect.set(self.app.fit_func[0])
            fittingfunction = self.fitselect.get()
            self.fitselectpack.append(self.fitselect)
            
            resist = customtkinter.CTkButton(self, text = "Charactarize",width=60, command = lambda i=i, output_list=output_list: self.app.char_resist_func(i,output_list)) #fg_color="#858c22"
            resist.grid(column=3, row=i+1, padx=10, pady=10, sticky="nsew")

            currententry = customtkinter.CTkEntry(self, placeholder_text="(mA)", width=50)
            currententry.grid(column=8, row=i+1, padx=(20,10), pady=10, sticky="nsew")
            self.setIlimitpack.append(currententry)
            
            acqcurrentlimit = customtkinter.CTkLabel(self, text=str(self.app.globalcurrrentlimit))
            acqcurrentlimit.grid(column=10, row=i+1, padx=(10,15), pady=10, sticky="nsew")
            
            submitcurrent = customtkinter.CTkButton(self, text = "Submit", width=30, command = lambda i=i, currententry=currententry, acqcurrentlimit=acqcurrentlimit, : self.app.submit_currentlimit(i, currententry,acqcurrentlimit))
            submitcurrent.grid(column=9, row=i+1, padx=10, pady=10, sticky="nsew")
            currentry = customtkinter.CTkEntry(self, placeholder_text="(mA)", width=50)
            currentry.grid(column=11, row=i+1, padx=(10,10), pady=10, sticky="nsew")
            self.setIpack.append(currentry)
        
            measured_curr = customtkinter.CTkLabel(self, text="Null")
            measured_curr.grid(column=13, row=i+1, padx=(10,15), pady=10, sticky="w")
            applycurr = customtkinter.CTkButton(self, text = "Measure", width=60, command = lambda i=i, currentry = currentry, measured_curr = measured_curr: self.app.measure(i, currentry, measured_curr))
            applycurr.grid(column=12, row=i+1, padx=10, pady=10, sticky="nsew")

            rampstart = customtkinter.CTkEntry(self, placeholder_text="Start", width=50)
            rampstart.grid(column=14, row=i+1, padx=(10,5), pady=10, sticky="nsew")
            self.startpack.append(rampstart)
            
            rampend = customtkinter.CTkEntry(self, placeholder_text="End", width=50)
            rampend.grid(column=15, row=i+1, padx=5, pady=10, sticky="nsew")
            self.endpack.append(rampend)
            
            steps = customtkinter.CTkEntry(self, placeholder_text="Steps", width=50)
            steps.grid(column=16, row=i+1, padx=5, pady=10, sticky="nsew")
            self.stepspack.append(steps)

            stabtime = customtkinter.CTkEntry(self, placeholder_text="Pause", width=50) #stabilization time for the chip between measurements
            stabtime.grid(column=17, row=i+1, padx=(5,10), pady=10, sticky="nsew")
            self.pausepack.append(stabtime)
            
            self.IOconfigselect = customtkinter.CTkComboBox(self,width=80, values=self.app.IOconfig_options, command=lambda choice, idx=i: self.IOconfig_change(idx, choice))
            self.IOconfigselect.grid(column=18, row=i+1, padx=10, pady=10, sticky="nsew")
            self.IOconfigselect.set(self.app.IOconfig_options[0])
            IOconfig_selected = self.IOconfigselect.get()
            self.IOconfigselectpack.append(self.IOconfigselect)
            
            calibrate = customtkinter.CTkButton(self, text = "Calibrate", width=60, command = lambda i=i, rampstart = rampstart, rampend = rampend, steps = steps, stabtime = stabtime, acqresist=acqresist_lin : self.app.calibration_func(i, rampstart, rampend, steps, stabtime, self.app.linear_resistance_list[i], self.app.resistance_parameter_list[i]))
            calibrate.grid(column=19, row=i+1, padx=10, pady=10, sticky="nsew")
            
            setcurr = customtkinter.CTkLabel(self, text="Null")
            setcurr.grid(column=20, row=i+1, padx=15, pady=10, sticky="nsew")
            
            setphase = customtkinter.CTkLabel(self, text="Null")
            setphase.grid(column=21, row=i+1, padx=(0,20), pady=10, sticky="nsew")


            #save custom tkinter objects to lists to access and export data
            self.app.channellist.append(channel)
            self.app.idlist.append(heateridd)
            self.app.customtkinterresistancelist.append(acqresist_max)
            self.app.customtkinterrmin_list.append(acqresist_min)
            self.app.customtkinterrmax_list.append(acqresist_max)
            self.app.customtkinteralpha_list.append(alpha)
            self.app.customtkinterlinear_resistance_list.append(acqresist_lin)
            self.app.customtkinterresistance_parameter_list.append(acqresist_min)
            self.app.currentlimitlist.append(acqcurrentlimit)
            self.app.appliedcurrlist.append(currentry)
            self.app.measuredcurrentlist.append(measured_curr)
            self.app.rampstartlist.append(rampstart)
            self.app.rampendlist.append(rampend)
            self.app.stepslist.append(steps)
            self.app.stabtimelist.append(stabtime)
            self.app.setcurrlabellist.append(setcurr)
            self.app.setphaselabellist.append(setphase)
            
            self.app.res_lin_char_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.res_lincub_char_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.res_lincub_char_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lin_char_cross_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lin_char_cross_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lin_char_bar_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lin_char_bar_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lincub_char_cross_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lincub_char_cross_state_images[i].seek(0)  # Reset buffer position to the start
            
            image.save(self.app.opmod_lincub_char_bar_state_images[i], format="PNG")  # Save the image to the BytesIO object
            self.app.opmod_lincub_char_bar_state_images[i].seek(0)  # Reset buffer position to the start
        
            
    def fitselect_change(self, channel, choice):
        self.channel=channel
        self.heaterid=self.app.currentheaterid
        self.app.fit_func_allchannels[channel] = choice
        self.fit_index = self.app.fit_func.index(choice)
        self.IOconfig_index = self.app.IOconfig_options.index(self.app.IOconfig_allchannels[channel])
        self.app.channel_selection_frame.fitselect.set(choice)
        self.app.channel_selection_frame.IOconfigselect.set(self.app.IOconfig_allchannels[channel])
        self.app.channel_selection_frame.channelselect.set("Ch_"+str(channel)+" ("+self.heaterid[channel]+")")
        self.app.channel = self.channel
        self.app.fit = choice
        self.app.IOconfig = self.app.IOconfig_allchannels[channel]

        self.app.image_frame1.your_image.configure(light_image=Image.open(self.app.IVimagechoices[self.fit_index][self.channel]), size=((250)*(395/278), 250))
        self.app.image_frame2.your_image.configure(light_image=Image.open(self.app.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250))  
        
        if self.app.calframe is not None:
            self.app.calframe.destroy()
        
        self.app.calframe = MyCalcFrame_main(self.app.settings_frame, Channel=self.app.channel, Fit=self.app.fit, IOconfig=self.app.IOconfig)
        self.app.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew")                            
        
    def IOconfig_change(self, channel, choice):
        self.channel=channel
        self.heaterid=self.app.currentheaterid
        self.app.IOconfig_allchannels[channel] = choice
        self.fit_index = self.app.fit_func.index(self.app.fit_func_allchannels[channel])
        self.IOconfig_index = self.app.IOconfig_options.index(choice)
        self.app.channel_selection_frame.IOconfigselect.set(choice)
        self.app.channel_selection_frame.channelselect.set("Ch_"+str(channel)+" ("+self.heaterid[channel]+")")
        self.app.channel_selection_frame.fitselect.set(self.app.fit_func_allchannels[channel])
        self.app.channel = self.channel
        self.app.IOconfig = choice
        self.app.fit = self.app.fit_func_allchannels[channel]
        
        self.app.image_frame1.your_image.configure(light_image=Image.open(self.app.IVimagechoices[self.fit_index][self.channel]), size=((250)*(395/278), 250))
        self.app.image_frame2.your_image.configure(light_image=Image.open(self.app.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250) ) 
        
        if self.app.calframe is not None:
           self.app.calframe.destroy()
        
        self.app.calframe = MyCalcFrame_main(self.app.settings_frame, Channel=self.app.channel, Fit=self.app.fit, IOconfig=self.app.IOconfig)
        self.app.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew")  

class App(customtkinter.CTk):
    def __init__(self, params, headings, heaterid6x6, heaterid8x8, options, globalcurrrentlimit):
        super().__init__()

        self.title("MZI Controller")
        self.geometry("1920x980")
        #self.geometry("1800x918.75")
        #self.geometry("800x600")
        self.grid_columnconfigure((0), weight=1)#1
        self.grid_columnconfigure((1), weight=20)#1
        self.grid_rowconfigure((0), weight=1)
        self.grid_rowconfigure((1), weight=1)
        self.params = params
        self.headings = headings
        self.heaterid6x6 = heaterid6x6
        self.heaterid8x8 = heaterid8x8
        self.currentheaterid = self.heaterid8x8
        #self.val = '6x6' 
        self.val = '8x8' 
        self.options = options
        self.globalcurrrentlimit = globalcurrrentlimit #this is the globally initalized current limit that can never be exceeded
        self.newCL = self.globalcurrrentlimit
        self.channel=0
        print(self.val)
        

        self.allowedinputvalues = ['0','1','2','3','4','5','6','7','8','9','.']

        self.upperleftframe = MyUpperleftframe(self)
        self.upperleftframe.grid(row=0, column=0, padx=10, pady=(10,10), sticky="ewns")
        self.upperleftframe.grid_columnconfigure((0), weight=1)
        self.upperleftframe.grid_columnconfigure((1), weight=1)
        self.upperleftframe.grid_rowconfigure((0), weight=3)
        self.upperleftframe.grid_rowconfigure((1), weight=2)

        self.upperrightframe = MyUpperrightframe(self)
        self.upperrightframe.grid(row=0, column=1, padx=10, pady=(10,10), sticky="ewns")
        self.upperrightframe.grid_rowconfigure((0,1), weight=1)
        self.upperrightframe.grid_columnconfigure((2), weight=1)

        self.lowerframe = MyLowerFrame(self)
        self.lowerframe.grid(row=1, column=0,columnspan=2, padx=10, pady=(0,10), sticky="ewns")
        self.lowerframe.grid_rowconfigure((0,1), weight=1)
        
        self.info_frame = MyInfoFrame(self.upperleftframe, title = 'Device settings', params=self.params)
        self.info_frame.grid(row=0, column=0, columnspan=2, padx=(20,5), pady=(10,5), sticky="ewns") 

        self.radiobuttons_frame = MyRadioButtonFrame(self.upperleftframe, title = "Mesh size", options=self.options, params = self.params)
        self.radiobuttons_frame.grid(row=1, column=0, padx=(20,10), pady=(5,10), sticky="ewns") 

        self.CLexportframe = MyCLExportFrame(self.upperleftframe, title = "Global Current Limit")
        self.CLexportframe.grid(row=1, column=1, padx=(10,5), pady=(5,10), sticky="ewns")

        self.tab_view = MyTabView(self.lowerframe, headings=self.headings)
        self.tab_view.grid(row=0, column=0, padx=10, pady=(10,10), sticky="nsew")
        self.tab_view.grid_columnconfigure((0), weight=1)
        
        self.scrollable_frame = MyScrollableFrame(self.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.currentheaterid, config = self.config , app = self)
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")
        
        self.header_frame = MyHeaderFrame(self.tab_view.tab("Calibrate"), val =self.val, app = self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(0,0), sticky='nsew')
        
        self.channel_selection_frame = MyChannel_selection_frame(self.upperrightframe, 100, 50, self.config, heaterid=self.currentheaterid) #val='6x6'
        self.channel_selection_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,20), sticky = "ewns") #sticky="n", rowspan=1
        
        self.settings_frame = MyFrame(self.upperrightframe, 380, 380) #val='6x6'
        self.settings_frame.grid(row=0, column=2, rowspan=2, padx=(10,10), pady=(0,10), sticky = "es") #sticky="n", rowspan=1
        
        self.settings_frame.grid_columnconfigure((0), weight=1)
        self.settings_frame.grid_rowconfigure((0), weight=1)

        self.image_frame1 = MyImageFrame(self.upperrightframe, self.val, self.res_lin_char_images[self.channel], height=250, width= (250)*(395/278)) #val='6x6'
        self.image_frame1.grid(row=0, column=0, padx=(10,0), pady=(20,5), sticky = "ewns") #sticky="n", rowspan=1

        self.image_frame2 = MyImageFrame(self.upperrightframe, self.val, self.opmod_lin_char_cross_state_images[self.channel], height=250, width= (250)*(460/278)) #val='6x6'
        self.image_frame2.grid(row=0, column=1, padx=10, pady=(20,5), sticky = "ewns") #sticky="n", rowspan=1

        self.calframe = MyCalcFrame_main(self.settings_frame, Channel=self.channel, Fit=self.fit, IOconfig=self.IOconfig)
        self.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew")
        
        
        #self.toplevel_window = None

    # def open_toplevel(self):
    #     if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
    #         self.toplevel_window = ToplevelWindow(self)  # create window if its None or destroyed
    #     else:
    #         self.toplevel_window.focus()  # if window exists focus it
    
    def fit_cos(self, xdata, ydata): #Fit cos to the input time sequence, and return a dictionary with fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc
            self.xdata = np.array(xdata) #in mW
            self.ydata = np.array(ydata) # in mW
            #guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   #excluding the zero frequency "peak", which is related to offset
            guess_freq = 1/20
            guess_amp = np.std(self.ydata) * 2.**0.5
            guess_offset = np.mean(self.ydata)
            guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

            def cosfunc(P, A, b, c, d):  
                return A * np.cos(b*P + c) + d

            print('before optimize.curvefit')
            popt, pcov = optimize.curve_fit(cosfunc, self.xdata, self.ydata, p0=guess)
            A, b, c, d = popt
            
            f = b/(2.*np.pi)

            fitfunc = lambda P: -A * np.cos(b*P + c) + d
            
            return {"amp": A, "omega": b, "phase": c, "offset": d, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}
    
    def fit_cos_negative(self, xdata, ydata): #Fit cos to the input time sequence, and return a dictionary with fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc
            self.xdata = np.array(xdata) #in mW
            self.ydata = np.array(ydata) # in mW
            #guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   #excluding the zero frequency "peak", which is related to offset
            guess_freq = 1/20
            guess_amp = np.std(self.ydata) * 2.**0.5
            guess_offset = np.mean(self.ydata)
            guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

            def cosfunc(P, A, b, c, d):  
                return -A * np.cos(b*P + c) + d

            print('before optimize.curvefit')
            popt, pcov = optimize.curve_fit(cosfunc, self.xdata, self.ydata, p0=guess)
            A, b, c, d = popt
            
            f = b/(2.*np.pi)

            fitfunc = lambda P: -A * np.cos(b*P + c) + d
            
            return {"amp": A, "omega": b, "phase": c, "offset": d, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}
    
    def char_resist_linear_fit_func(self, xdata, ydata): 
            self.xdata = np.array(xdata) 
            self.ydata = np.array(ydata)
    
    def char_resist_func(self, channel, output_list):
        self.channel=channel
        self.resist_min=output_list[0]
        self.resist_max=output_list[1]
        self.alpha=output_list[2]
        self.resist_lin=output_list[3]
        currentdatapoints = []
        
        self.fit=self.fit_func_allchannels[self.channel]
        
        self.channel_selection_frame.fitselect.set(self.fit)
        self.channel_selection_frame.IOconfigselect.set(self.IOconfig_allchannels[self.channel])
        self.channel_selection_frame.channelselect.set("Ch_"+str(self.channel)+" ("+self.currentheaterid[channel]+")")
        self.channel_selection_frame.fitselect.set(self.fit)

        self.IOconfig = self.IOconfig_allchannels[self.channel]
        self.fit_index = self.fit_func.index(self.fit)
        self.IOconfig_index = self.IOconfig_options.index(self.IOconfig_allchannels[self.channel])
        
        print("Perform resistance charactarization for channel " + str(self.channel))
        startcurr = 0.0 #unit mA
        endcurr = q.imax[self.channel] #unit mA
        currentramp = np.linspace(startcurr, endcurr, num=10) #divide ramp into 10 equidistant steps

        currentramplist = [float(elem) for elem in currentramp] #convert elements to float which is needed for device

        measured_voltlist = [] #unit V

        for i in range(len(currentramplist)):
           q.i[self.channel] = currentramplist[i]
           currentdatapoints.append(q.i[self.channel])
           measured_voltlist.append(q.v[self.channel])
           sleep(1.0)
           print ("Channel {:} applied current of {:} mA and measured voltage of {:} V".format(self.channel, currentramplist[i], measured_voltlist[i]))
        
        #Reset channel's current and voltage to zero after the measurement
        q.i[self.channel] = 0
        print("Reset channel " + str(self.channel) + " to 0 mA after measurement")
        
        currlist_amphere = [elem / 1000 for elem in currentdatapoints] #convert measured current in measured_currlist to ampere from mA

        x=np.array(currlist_amphere) #unit Amphere
        y=np.array(measured_voltlist) #unit V
        
        
        ###################Charactarize the resistance with a linear fit####################
        
        if self.fit == self.fit_func[0]:
            #Design matrix for linear transformation
            X = np.vstack([x, np.ones_like(x)]).T
            
            self.linchar_voltage[self.channel] = y
            self.linchar_current[self.channel] = x
            
            #Solve for coefficients [c, d] using least squares
            coefficients, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            
            #Extract coefficients
            c, d = coefficients
            a=0
        
            self.linear_resistance_list[self.channel] = c
            
            print('Acquired resistance for channel'+str(self.channel) +" is "+ str(c) + ' Ω when fitted with a linear funtion')
            
            
            for child in self.tab_view.calculate_frame.graphframe.winfo_children():
                print("printar child")
                print(child)
                child.destroy()  # remove existing figures
            

            # Set white font colors
            COLOR = 'white'
            matplotlib.rcParams['text.color'] = COLOR
            matplotlib.rcParams['axes.labelcolor'] = COLOR
            matplotlib.rcParams['xtick.color'] = COLOR
            matplotlib.rcParams['ytick.color'] = COLOR
            
            # Create figure and axes explicitly
            fig, ax = plt.subplots(1, figsize=(6, 4))
            
            # Plot on the explicit axes
            ax.scatter(x, y, label='Measured data points', color='white')
            ax.plot(x, [c * xi + d for xi in x], label="Linear fit", color="red")

            # Apply custom formatter to x-axis
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value * 1000:.0f}"))
            
            # Add labels, title, and legend
            ax.set_xlabel("Applied current (mA)")
            ax.set_ylabel("Measured voltage (V)")
            ax.set_title("Characterized Resistance for Channel"+str(self.channel)+"("+str(self.currentheaterid[self.channel])+"): Linear fit")  # Adjust channel dynamically
            ax.legend(loc="best", facecolor="#323334", framealpha=1)
            
            # Customize appearance
            ax.set_facecolor("#323334")
            plt.setp(ax.spines.values(), color=COLOR)
            fig.patch.set_facecolor("#323334")
            
            # Show the plot
            #plt.show()
            
            # Save plot to a BytesIO buffer
            buf = BytesIO()
            print(buf)
            fig.savefig(buf, format="png")
            buf.seek(0)  # Reset buffer position to the start

            self.res_lin_char_images[self.channel] = buf  # Store the buffer in the array
            plt.close(fig)  # Close the figure to free memory
            
            self.image_frame1.your_image.configure(light_image=Image.open(self.res_lin_char_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            

            self.resist_lin.configure(text=str(np.round(self.linear_resistance_list[self.channel]/1000, 2)))
        ###################Charactarize the resistance with a linear + cubic function fit####################
        
        elif self.fit == self.fit_func[1]: 
            
            self.lincubchar_voltage[self.channel] = y
            self.lincubchar_current[self.channel] = x
            
            # Design matrix excluding the x^2 term
            X = np.vstack([x**3, x, np.ones_like(x)]).T
            
            # Solve for coefficients [a, c, d] using least squares
            coefficients, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            
            # Extract coefficients
            a, c, d = coefficients
            print(a, c, d)
            
            self.resistancelist[self.channel] = a*(x**2) + c
            self.rmin_list[self.channel] = np.min(self.resistancelist[self.channel])
            self.rmax_list[self.channel] = np.max(self.resistancelist[self.channel])
            self.alpha_list[self.channel] = a/c
            self.resistance_parameter_list[self.channel] = [a, c, d] #add resistance, this is a float
            
            print('Acquired resistance for channel ' +str(self.channel) +" is "+ str(self.resistancelist[self.channel]) + ' Ω '+ 'for the current values '+ str(x*1000)+'mA when when fitted using a linear + cubic function')
            
            # Set white font colors
            COLOR = 'white'
            matplotlib.rcParams['text.color'] = COLOR
            matplotlib.rcParams['axes.labelcolor'] = COLOR
            matplotlib.rcParams['xtick.color'] = COLOR
            matplotlib.rcParams['ytick.color'] = COLOR
            
            # Create figure and axes explicitly
            fig, ax = plt.subplots(1, figsize=(6, 4))
            
            plt.scatter(x,y,label='Measured data points', color='white')
            plt.plot(x, a*(x**3)+c*(x)+d, label = "Linear +cubic fit", color = "red")
            #plt.text(endcurr/1000 - 5/1000, 0.7, 'y = ' + '{:.2f}'.format(b) + ' + {:.2f}'.format(a) + 'x', size=9)
            #plt.text(endcurr/1000 - 5/1000, 0.4, 'Resistance near zero current: ' + '{:.2f}'.format(c) + 'Ω', size=9)
            
            # Apply custom formatter to x-axis
            ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value * 1000:.0f}"))
            
            # Add labels, title, and legend
            ax.set_xlabel("Applied current (mA)")
            ax.set_ylabel("Measured voltage (V)")
            ax.set_title("Characterized Resistance for Channel"+str(self.channel)+"("+str(self.currentheaterid[self.channel])+"): Linear+Cubic fit")  # Adjust channel dynamically
            ax.legend(loc="best", facecolor="#323334", framealpha=1)
            
            # Customize appearance
            ax.set_facecolor("#323334")
            plt.setp(ax.spines.values(), color=COLOR)
            fig.patch.set_facecolor("#323334")
            
            # Show the plot
            #plt.show()
            
            # Save plot to a BytesIO buffer
            buf = BytesIO()
            print(buf)
            fig.savefig(buf, format="png")
            buf.seek(0)  # Reset buffer position to the start

            self.res_lincub_char_images[self.channel] = buf  # Store the buffer in the array
            plt.close(fig)  # Close the figure to free memory
            
            self.image_frame1.your_image.configure(light_image=Image.open(self.res_lincub_char_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            
            self.resist_min.configure(text=str(np.round(self.rmin_list[self.channel]/1000, 2)))
            self.resist_max.configure(text=str(np.round(self.rmax_list[self.channel]/1000, 2)))
            #self.alpha.configure(text=str(np.round(self.alpha_list[self.channel], 2)))
        ##########################################################################
        self.image_frame2.your_image.configure(light_image=Image.open(self.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250))
       
        if self.calframe is not None:
            self.calframe.destroy()
        
        self.calframe = MyCalcFrame_main(self.settings_frame, Channel=self.channel, Fit=self.fit, IOconfig=self.IOconfig)
        self.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
        #self.label.configure(text=str(round(self.resistancelist[self.channel][0], 0))) #reconfigure label with value for resistance

        
    def submit_currentlimit(self, channel, currententry, acqcurrentlimit):
        self.channel = channel
        self.currententry = currententry #object
        self.acqcurrentlimit = acqcurrentlimit # object

        self.currententrynumber = self.currententry.get() #returns a string
        print(self.currententrynumber)


        #check if the entry cell is empty 
        if self.currententrynumber == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a positive integer or float current limit value in mA and then press submit again')

        else:

            illegalchar = False
            point = 0

            for i in range(len(self.currententrynumber)):
                if self.currententrynumber[i] in self.allowedinputvalues:
                    print(self.currententrynumber[i])
                    if self.currententrynumber[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character ' + self.currententrynumber[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new value and submit')
                self.currententry.delete(0, 'end') #clear the entry field
            else:
                self.currententrynumber = float(self.currententrynumber)
                if self.currententrynumber > self.newCL or self.currententrynumber < 0: #check so not input value is exceeding current limit
                    messagebox.showwarning(message='WARNING! \n Desired current limit is exceeding the globally set current limit. Please set a lower value.')
                    print('Customized current entry to channel ' + str(self.channel) + ' is exceeding the globally set current limit. Please set a lower value.')
                    self.currententry.delete(0, 'end') #clear the entry field
                else:
                    q.imax[self.channel] = self.currententrynumber #unit mA
                    self.acqcurrentlimit.configure(text=str(self.currententrynumber)) #unit mA
                    print("Current limit for channel: " + str(self.channel) + ' is now customized to ' + str(self.currententrynumber))   
            
    def measure(self, channel, currentry, measured_curr):
        self.channel = channel
        self.currentry = currentry
        self.measured_curr = measured_curr
                
        currentlimit = q.imax[self.channel] #get the current limit for this channel

        applycurrent = self.currentry.get() #as a string

        #check if the entry cell is empty 
        if applycurrent == '':
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a positive integer or float global current value in mA and then press submit again')

        else:
            illegalchar = False
            point = 0

            for i in range(len(applycurrent)):
                if applycurrent[i] in self.allowedinputvalues:
                    print(applycurrent[i])
                    if applycurrent[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character ' + applycurrent[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new value and submit')
                self.currentry.delete(0, 'end') #clear the entry field
            else:
                applycurrent = float(applycurrent)
                if applycurrent > round(currentlimit, 1) or applycurrent < 0:
                    print('Desired current is exceeding the set current limit. Please input a lower value in mA')
                    messagebox.showwarning(message = 'WARNING! \n Desired current is exceeding the set current limit. Please input a lower value in mA')
                    self.currentry.delete(0, 'end') #clear the entry field
                    #self.measured_curr.configure(text='Null')#print on GUI measued current in unit mA
                else: 
                    q.i[self.channel] = applycurrent
                    print('Applied current to channel ' + str(self.channel) + ' is ' + str(applycurrent) + ' mA')
                    mcurr = q.i[self.channel] #measure current unit mA
                    print('Measured current to channel ' + str(self.channel) + ' is ' + str(mcurr) + ' mA')
                    self.measured_curr.configure(text=str(round(mcurr,1)))#print on GUI measued current in unit mA
                    #Set channel current to zero after measurement
                    q.i[self.channel] = 0
                    print("Reset current to channel " + str(self.channel) + " to 0 mA after measurement")

    def fit_cos(self, xdata, ydata): #Fit cos to the input time sequence, and return a dictionary with fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc
            self.xdata = np.array(xdata) #in mW
            self.ydata = np.array(ydata) # in mW
            #guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   #excluding the zero frequency "peak", which is related to offset
            guess_freq = 1/20
            guess_amp = np.std(self.ydata) * 2.**0.5
            guess_offset = np.mean(self.ydata)
            guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

            def cosfunc(P, A, b, c, d):  
                return A * np.cos(b*P + c) + d

            print('before optimize.curvefit')
            
            # Define parameter bounds
            lower_bounds = [0, 0, -np.pi, -np.inf]  
            upper_bounds = [np.inf, np.inf, np.pi, np.inf]  
            
            popt, pcov = optimize.curve_fit(cosfunc, self.xdata, self.ydata, p0=guess, bounds=(lower_bounds, upper_bounds))
            A, b, c, d = popt
            
            f = b/(2.*np.pi)

            fitfunc = lambda P: A * np.cos(b*P + c) + d
            
            return {"amp": A, "omega": b, "phase": c, "offset": d, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}
    
    def fit_cos_negative(self, xdata, ydata): #Fit cos to the input time sequence, and return a dictionary with fitting parameters "amp", "omega", "phase", "offset", "freq", "period" and "fitfunc
            self.xdata = np.array(xdata) #in mW
            self.ydata = np.array(ydata) # in mW
            #guess_freq = abs(ff[np.argmax(Fyy[1:])+1])   #excluding the zero frequency "peak", which is related to offset
            guess_freq = 1/20
            guess_amp = np.std(self.ydata) * 2.**0.5
            guess_offset = np.mean(self.ydata)
            guess = np.array([guess_amp, 2.*np.pi*guess_freq, 0., guess_offset])

            def cosfunc(P, A, b, c, d):  
                return -A * np.cos(b*P + c) + d

            print('before optimize.curvefit')

            # Define parameter bounds
            lower_bounds = [0, 0, -np.pi, -np.inf]  
            upper_bounds = [np.inf, np.inf, np.pi, np.inf]  
            
            popt, pcov = optimize.curve_fit(cosfunc, self.xdata, self.ydata, p0=guess, bounds=(lower_bounds, upper_bounds))
            A, b, c, d = popt
            
            f = b/(2.*np.pi)

            fitfunc = lambda P: -A * np.cos(b*P + c) + d
            
            return {"amp": A, "omega": b, "phase": c, "offset": d, "freq": f, "period": 1./f, "fitfunc": fitfunc, "maxcov": np.max(pcov), "rawres": (guess,popt,pcov)}

    def calibrationplotX(self, channel, xdata, ydata): #calibration plot on the calibration tab

        self.channel = channel
        self.xdata = xdata #in mW
        self.ydata = ydata #in mW
        
        self.fit = self.fit_func_allchannels[self.channel]
        self.IOconfig = self.IOconfig_allchannels[self.channel]
        self.fitnames = np.array(["Linear", "Linear+cubic"])
        self.currentfit_name = self.fitnames[self.fit_func.index(self.fit)]

        fitxdata = np.linspace(self.xdata[0], self.xdata[-1], 300)
        print("CalibrationplotX initiated")

        if self.fit == self.fit_func[0]:
            if self.IOconfig == self.IOconfig_options[0]:
                res = self.fit_cos(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
                self.caliparamlist_lin_cross[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
                
            elif self.IOconfig == self.IOconfig_options[1]:
                res = self.fit_cos_negative(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
                self.caliparamlist_lin_bar[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
                
        elif self.fit == self.fit_func[1]:
            if self.IOconfig == self.IOconfig_options[0]:
                res = self.fit_cos(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
                self.caliparamlist_lincub_cross[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
                
            elif self.IOconfig == self.IOconfig_options[1]:
                res = self.fit_cos_negative(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
                self.caliparamlist_lincub_bar[self.channel] = res #save the dictionary of calibration parameters for each channel in a list

        
        print( "Amplitude=%(amp)s, Angular freq.=%(omega)s, phase=%(phase)s, offset=%(offset)s, Max. Cov.=%(maxcov)s" % res)

        #set white font colors
        COLOR = 'white'
        matplotlib.rcParams['text.color'] = COLOR
        matplotlib.rcParams['axes.labelcolor'] = COLOR
        matplotlib.rcParams['xtick.color'] = COLOR
        matplotlib.rcParams['ytick.color'] = COLOR

        fig, ax = plt.subplots(1, figsize=(8,4))

        plt.plot(self.xdata, self.ydata, "ok", label="optical power", color='white')
        plt.plot(fitxdata, res["fitfunc"](fitxdata), "r-", label="fit", linewidth=2)
        plt.legend(loc="best", facecolor="#323334", framealpha=1)
        plt.title("Phase calibration curve for channel "+ str(self.channel)+ " ("+ str(self.currentheaterid[self.channel])+ ")\n"+ str(self.currentfit_name)+ " I-V, "+ self.IOconfig+ " config")


        ax.set_facecolor("#323334")
        plt.setp(ax.spines.values(), color=COLOR)
        plt.xlabel("Heating power (P) mW")
        plt.ylabel("Optical power (Y) mW")
        fig.patch.set_facecolor("#323334")
        
        #reset to default colors
        COLOR = 'black'
        matplotlib.rcParams['text.color'] = COLOR
        matplotlib.rcParams['axes.labelcolor'] = COLOR
        matplotlib.rcParams['xtick.color'] = COLOR
        matplotlib.rcParams['ytick.color'] = COLOR

        #plt.show()
        
        # Save plot to a BytesIO buffer
        buf = BytesIO()
        print(buf)
        fig.savefig(buf, format="png")
        buf.seek(0)  # Reset buffer position to the start
        
        if self.fit == self.fit_func[0]:
            if self.IOconfig == self.IOconfig_options[0]:
                self.opmod_lin_char_cross_state_images[self.channel] = buf  # Store the buffer in the array
                plt.close(fig)  # Close the figure to free memory
                self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lin_char_cross_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
                
            elif self.IOconfig == self.IOconfig_options[1]:
                self.opmod_lin_char_bar_state_images[self.channel] = buf  # Store the buffer in the array
                plt.close(fig)  # Close the figure to free memory
                self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lin_char_bar_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
                
        if self.fit==self.fit_func[1]:
            if self.IOconfig == self.IOconfig_options[0]:
                self.opmod_lincub_char_cross_state_images[self.channel] = buf  # Store the buffer in the array
                plt.close(fig)  # Close the figure to free memory
                self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lincub_char_cross_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
                
            elif self.IOconfig == self.IOconfig_options[1]:
                self.opmod_lincub_char_bar_state_images[self.channel] = buf  # Store the buffer in the array
                plt.close(fig)  # Close the figure to free memory
                self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lincub_char_bar_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
        
        

    def calibration_func(self, channel, rampstart, rampend, steps, stabtime, acqlinresist, acqvariying_resist_param):

        self.channel = channel
        self.currstart = rampstart.get() #these are strings
        self.currend = rampend.get()
        self.numsteps = steps.get()
        self.numpaus = stabtime.get()
        self.fit = self.fit_func_allchannels[self.channel]
        self.IOconfig = self.IOconfig_allchannels[self.channel]
        self.linresistance = acqlinresist
        self.varying_resistance_parameters = acqvariying_resist_param
        self.calpararrays = [[self.caliparamlist_lin_cross, self.caliparamlist_lin_bar], [self.caliparamlist_lincub_cross, self.caliparamlist_lincub_bar]]
        self.currentarray = self.calpararrays[self.fit_func.index(self.fit)][self.IOconfig_options.index(self.IOconfig)]
        

        maxsteps = 300 
        maxpaus = 30 #seconds

        currentlimit = q.imax[self.channel] #get the current limit for this channel
        
        if self.fit == self.fit_func[0]:
            self.numresist = self.linear_resistance_list[self.channel] #this is a float
            print("Perform phase calibration measurements and linear fitting for channel: " + str(self.channel)) 

        if self.fit == self.fit_func[1]:
            self.numresist = self.resistancelist[self.channel] #this is an array of float values
            print("Perform phase calibration measurements and linear + cubic fitting for channel: " + str(self.channel)) 
        
        
        if self.numresist == 'Null':
            messagebox.showerror(message='PROCESS FAILURE! \n The resistance for this channel is missing. Please do the resistance charactarization step first')

        else: #Check2. Check for invalid characters in start entry
            print('Checks that all entries of the ramp have valid characters and fullfill the conditions for the ramp')
            if self.currstart == '': #if empty: 
                messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a positive integer or float starting value for the current ramp in mA')
            else:
                illegalchar = False
                point = 0

                for i in range(len(self.currstart)):
                    if self.currstart[i] in self.allowedinputvalues:
                        print(self.currstart[i])
                        if self.currstart[i] == '.':
                            point +=1
                            if point > 1:
                                print('input has more than one comma points')
                                break
                    else:
                        print('Error: Input has at least one illegal character: ' + self.currstart[i]) 
                        illegalchar = True
                        break

                if illegalchar == True or point >1: #check for invalid characters in input
                    messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new starting ramp value in mA')
                    rampstart.delete(0, 'end') #clear the entry field
                else:
                    self.currstart = float(self.currstart) #now set to float
                    if self.currstart > round(currentlimit, 1) or self.currstart < 0:
                        messagebox.showwarning(message = 'WARNING! \n Desired start value is exceeding the set current limit or is negative. Please input a new starting ramp value in mA')
                        rampstart.delete(0, 'end') #clear the entry field

                    else: #check3. Check for invalid characters in end-entry
                        if self.currend == '': #if empty: 
                            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a positive integer or float ending ramp value for the current ramp in mA')
                        else:
                            illegalchar = False
                            point = 0

                            for i in range(len(self.currend)):
                                if self.currend[i] in self.allowedinputvalues:
                                    print(self.currend[i])
                                    if self.currend[i] == '.':
                                        point +=1
                                        if point > 1:
                                            print('input has more than one comma points')
                                            break
                                else:
                                    print('Error: Input has at least one illegal character: ' + self.currend[i]) 
                                    illegalchar = True
                                    break

                            if illegalchar == True or point >1: #check for invalid characters in input
                                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new ending ramp value in mA')
                                rampend.delete(0, 'end') #clear the entry field
                            else:
                                self.currend = float(self.currend) #now set to float
                                if self.currend > round(currentlimit, 1) or self.currend < 0:
                                    messagebox.showwarning(message = 'WARNING! \n Desired end value of the current ramp is exceeding the set current limit or is negative. Please input a new end value in mA')
                                    rampend.delete(0, 'end') #clear the entry field

                                else: #Check 4. Check if end value for the ramp is smaller than the start value for the current ramp. 
                                    if self.currend <= self.currstart:
                                        messagebox.showwarning(message = 'WARNING! \n Desired end value is smaller than the desired start value for the current ramp. Please input new start and end values for the ramp in mA')
                                        rampstart.delete(0, 'end') #clear the entry field
                                        rampend.delete(0, 'end') #clear the entry field
                                    else:#Check5. Check for invalid characters in step-entry
                                        if self.numsteps == '': #if empty: 
                                            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in number of steps for the current ramp as an integer. Maximum ' + str(maxsteps) + ' steps.')
                                        else:
                                            illegalchar = False
                                            point = 0

                                            for i in range(len(self.numsteps)):
                                                if self.numsteps[i] in self.allowedinputvalues:
                                                    print(self.numsteps[i])
                                                    if self.numsteps[i] == '.':
                                                        point +=1
                                                        if point > 0:
                                                            print('input is not an integer')
                                                            break
                                                else:
                                                    print('Error: Input has at least one illegal character: ' + self.numsteps[i]) 
                                                    illegalchar = True
                                                    break

                                            if illegalchar == True or point >0: #check for invalid characters in input
                                                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer. Please type in a new step value. Maximum ' + str(maxsteps) + ' steps.')
                                                steps.delete(0, 'end') #clear the entry field
                                            else:
                                                self.numsteps = float(self.numsteps) #now set to float
                                                if self.numsteps > maxsteps or self.numsteps < 0:
                                                    messagebox.showwarning(message = 'WARNING! \n Desired number of steps is exceeding the maximum number of steps for the ramp. Maximum number of steps is ' + str(maxsteps) + '. Please input a new step value')
                                                    steps.delete(0, 'end') #clear the entry field

                                                else: #Check6. Check for invalid characters in paus-entry
                                                    if self.numpaus == '': #if empty: 
                                                        messagebox.showerror(message='ENTRY EMPTY! \n Please fill in stabilization time in seconds for the current ramp as an integer or a float.')
                                                    else:
                                                        illegalchar = False
                                                        point = 0

                                                        for i in range(len(self.numpaus)):
                                                            if self.numpaus[i] in self.allowedinputvalues:
                                                                print(self.numpaus[i])
                                                                if self.numpaus[i] == '.':
                                                                    point +=1
                                                                    if point > 1:
                                                                        print('input has more than one comma points')
                                                                        break
                                                            else:
                                                                print('Error: Input has at least one illegal character: ' + self.numpaus[i]) 
                                                                illegalchar = True
                                                                break

                                                        if illegalchar == True or point > 1: #check for invalid characters in input
                                                            messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new value for the stabilization time in seconds.')
                                                            stabtime.delete(0, 'end') #clear the entry field
                                                        else:
                                                            self.numpaus = float(self.numpaus) #now set to float
                                                            if self.numpaus > maxpaus or self.numpaus < 0:
                                                                messagebox.showwarning(message = 'WARNING! \n Desired stabilization time is exceeding the maximum value of ' +str(maxpaus) + ' seconds or is negative. Please input a lower but non-negative float number')
                                                                stabtime.delete(0, 'end') #clear the entry field
                                                            else:
                                                                for child in self.tab_view.calculate_frame.graphframe.winfo_children():
                                                                    print("printar child")
                                                                    print(child)
                                                                    child.destroy()  # remove existing figures

                                                                self.channel_selection_frame.fitselect.set(self.fit)
                                                                self.channel_selection_frame.IOconfigselect.set(self.IOconfig)
                                                                self.channel_selection_frame.channelselect.set("Ch_"+str(self.channel)+" ("+self.currentheaterid[self.channel]+")")
                                                                self.fit_index = self.fit_func.index(self.fit)
                                                                self.IOconfig_index = self.IOconfig_options.index(self.IOconfig)

                                                                self.image_frame1.your_image.configure(light_image=Image.open(self.IVimagechoices[self.fit_index][self.channel]), size=((250)*(395/278), 250))
                                                                self.image_frame2.your_image.configure(light_image=Image.open(self.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250)) 

                                                                #Check7. Check if calibration has been done and is to be updated. 
                                                                #Then make sure to reset current to zero and reset the derivedcurrentlist and setcurrentlist
                                                                if self.currentarray[self.channel] != 'Null':
                                                                    answer = messagebox.askokcancel(message = 'WARNING! \n Phase calibration curve and parameters have already been acquired. Are you sure you want to update it?')
                                                                    if answer == True:
                                                                        print('Update of the calibration in progress')
                                                                        print('Reset the derived current for the old phase and set current for channel ' + str(self.channel) + ' to zero mA before a new calibration is done')
                                                                        q.i[self.channel] = 0
                                                                        self.derivedcurrentlist[self.channel] = 'Null'
                                                                        self.setcurrentlist[self.channel] = 'Null'
                                                                        self.setcurrlabellist[self.channel].configure(text = str(self.setcurrentlist[self.channel]))

                                                                        #xdata, ydata = self.getExampleData() #get exsampel data

                                                                        self.currstart = float(self.currstart) #now convert inputs to floats
                                                                        self.currend = float(self.currend)
                                                                        self.numsteps = int(self.numsteps)
                                                                        self.numpaus = float(self.numpaus)

                                                                        xdata, ydata = self.getReadData(self.channel, self.currstart, self.currend, self.numsteps, self.numpaus, self.linresistance, self.varying_resistance_parameters) # in mW both
                                                                        
                                                                        if self.IOconfig == self.IOconfig_options[0]:

                                                                            self.xdatalist_IOcross[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                            self.ydatalist_IOcross[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW
                                                                            
                                                                        elif self.IOconfig == self.IOconfig_options[1]:

                                                                            self.xdatalist_IObar[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                            self.ydatalist_IObar[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW

                                                                        self.calibrationplotX(self.channel, xdata, ydata)

                                                                else: #calibration has not been done before

                                                                    #xdata, ydata = self.getExampleData() #get exsampel data

                                                                    self.currstart = float(self.currstart) #now convert inputs to floats
                                                                    self.currend = float(self.currend)
                                                                    self.numsteps = int(self.numsteps)
                                                                    self.numpaus = float(self.numpaus)

                                                                    xdata, ydata = self.getReadData(self.channel, self.currstart, self.currend, self.numsteps, self.numpaus, self.linresistance, self.varying_resistance_parameters) # in mW both

                                                                    if self.IOconfig == self.IOconfig_options[0]:

                                                                        self.xdatalist_IOcross[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                        self.ydatalist_IOcross[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW
                                                                        
                                                                    elif self.IOconfig == self.IOconfig_options[1]:

                                                                        self.xdatalist_IObar[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                        self.ydatalist_IObar[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW

                                                                    self.calibrationplotX(self.channel, xdata, ydata)
                                                                     
                                                                self.image_frame2.your_image.configure(light_image=Image.open(self.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250)) 
                                                                
                                                                if self.calframe is not None:
                                                                    self.calframe.destroy()
                                                                
                                                                self.calframe = MyCalcFrame_main(self.settings_frame, Channel=self.channel, Fit=self.fit, IOconfig=self.IOconfig)
                                                                self.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
    
    def Tempdependent_resistance(self, current, R0, alpha):
        self.R = R0 + alpha*(current**2)
        
        return self.R

    def getReadData(self, channel, currstart, currend, numsteps, numpaus, acqlinresist, acqvariying_resist_param): #return x-data and y-data (x being heating power, y being optical power)

        self.channel = channel
        self.currstart = currstart #mA
        self.currend = currend #mA
        self.numsteps = numsteps
        self.numpaus = numpaus
        self.linresistance = acqlinresist
        self.varying_resistance_parameters = acqvariying_resist_param
        self.alpha = self.varying_resistance_parameters[0]
        self.R0 = self.varying_resistance_parameters[1]
        self.fit = self.fit_func_allchannels[channel]
        
        
        currentlist_squared = list(np.linspace(self.currstart**2, self.currend**2, self.numsteps)) #mA**2
        currentlist = np.sqrt(currentlist_squared) #mA
        currentramp = [float(elem) for elem in currentlist] #mA

        opticalpowerlist = [] #this is ydata in mW
        heatingpowerlist = [] #this is xdata in mW
        currentdatapointslist2 = []
    
        print("Measure optical power for channel " + str(self.channel) + ' over the current ramp and fit using constant resistance model')

        print("Measurement type :" , power_meter.getconfigure)
        print("Wavelength       :", power_meter.sense.correction.wavelength)

        for i in range(len(currentramp)):
            q.i[self.channel] = currentramp[i] #apply current from the ramp to channel in mA
            currentdatapointslist2.append(q.i[self.channel])
            opticalpowerlist.append(power_meter.read*1000) # read optical power on power meter in W and add to opticalpowerlist for channel in mW
            sleep(self.numpaus)
            print ("Channel {:} set to {:} mA and measured optical power  to {:} mW".format(self.channel, currentramp[i], opticalpowerlist[i]))

        #Set channel current to zero after phase calibration data acquired
        q.i[self.channel] = 0
        print('Reset current on channel ' + str(self.channel) + ' to zero mA after measurement')
        
        if self.fit == self.fit_func[0]:
            for i in range(len(currentramp)):
                heatingpowerlist.append((self.linresistance * (currentdatapointslist2[i]/1000)**2)*1000) #in mW
                
        elif self.fit == self.fit_func[1]:
            for i in range(len(currentramp)):
                heatingpowerlist.append(((self.R0 + self.alpha*((currentdatapointslist2[i]/1000)**2)) * (currentdatapointslist2[i]/1000)**2)*1000) #in mW

        return np.array(heatingpowerlist), np.array(opticalpowerlist) # both in mW

    def getExampleData(self):

        print("Getexampeldata function initiated")

        #N, amp, omega, phase, offset, noise = 500, 1., 2., .5, 4., 3
        #N, amp, omega, phase, offset, noise = 50, 1., .4, .5, 4., .2
        N, amp, omega, phase, offset, noise = 30, 0.5, .8, 2., 0.5, .4
        #N, amp, omega, phase, offset, noise = 200, 1., 20, .5, 4., 1

        xdata = np.linspace(0, 7, N)
        yy = -amp*np.cos(omega*xdata + phase) + offset
        ydata = yy + noise*(np.random.random(len(xdata))-0.5)

        return xdata, ydata

    
    # def exportfunc(self):
    #     print("Export function button is pressed")
    #     if self.val == '6x6':
    #         self.channels = 6*5
    #     elif self.val == '8x8':
    #         self.channels = 8*7
    #     elif self.val == 'custom':
    #         self.channels = int(self.channelentry.get())

    #     #create an export file with the current date and time
    #     timestr = time.strftime("%Y%m%d-%H%M%S")

    #     #1. Create folder structure for the export
    #     superfolderpath = './' + timestr #here place overall data file
    #     subfolderpath1 = superfolderpath + '/' + 'timeseriesdata' #here place timeseriesdata for all channels
    #     subfolderpath2 = superfolderpath + '/' + 'fittingparameterdata' #here place fitting parameters for all channels
    #     self.makeDir(superfolderpath)
    #     self.makeDir(subfolderpath1)
    #     self.makeDir(subfolderpath2)

    #     #2. Create overall export file
    #     path1 = superfolderpath + '/overall_calibrationdata_all_channels_' + timestr + '.txt'
    #     print('Export calibration date to file with name ' + path1)
        
    #     text_file1=open(path1, 'a')

    #     text_file1.write('CHANNEL' + ' ' + 'HEADERID' + ' ' + 'CHARACTARIZED_RESISTANCE' + ' ' + 'CURRENT_LIMIT' + ' ' + 'APPLIED_CURRENT' +  ' ' + 'MEASURED_CURRENT' + ' ' + 'RAMP_START_V' + ' ' + 'RAMP_END_V' + ' ' + 'STEPS' + ' ' + 'STABILIZATION_TIME' +'\n')

    #     #write data on file. Each channel per row. Each data-label per column, separated by space
    #     for i in range(self.channels):
    #         if self.val == '6x6' or self.val == '8x8':
    #             text_file1.write(str(self.channellist[i].cget('text')) +' '+ str(self.idlist[i].cget('text')) + ' ' + str(self.resistancelist[i]) + ' ' + str(self.currentlimitlist[i].cget('text')) +  ' ' + str(self.appliedcurrlist[i].get()) + ' ' + str(self.measuredcurrentlist[i].cget('text')) + ' ' + str(self.rampstartlist[i].get()) + ' ' + str(self.rampendlist[i].get()) + ' ' + str(self.stepslist[i].get()) + ' ' + str(self.stabtimelist[i].get()) +'\n')
    #         else:
    #             text_file1.write(str(self.channellist[i].cget('text')) +' '+ str(self.idlist[i].get()) + ' ' + str(self.resistancelist[i]) + ' ' + str(self.currentlimitlist[i].cget('text')) +  ' ' + str(self.appliedcurrlist[i].get()) + '  ' + str(self.measuredcurrentlist[i].cget('text')) + ' ' + str(self.rampstartlist[i].get()) + ' ' + str(self.rampendlist[i].get()) + ' ' + str(self.stepslist[i].get()) + ' ' + str(self.stabtimelist[i].get()) +'\n')

    #     text_file1.close()

    #     #3. save xdata and ydata if data exist for each channel
    #     for i in range(self.channels):
    #         if len(self.xdatalist[i]) != 0:
    #             path2 = subfolderpath1 + '/phase_calibration_data_for_channel_' + str(i) + '_' + timestr + '.txt'
    #             text_file = open(path2, 'a')
    #             print('Export xdata and ydata for channel_' + str(i) + ' to file named ' + path2)
    #             text_file.write('Heating_Power_mW' + ' ' + 'Optical_Power_mW' + '\n')
    #             for j in range(len(self.xdatalist[i])):
    #                 text_file.write(str(self.xdatalist[i][j]) + ' ' + str(self.ydatalist[i][j]) + '\n')
    #             text_file.close()

    #     #4. save phase fitting parameters to file for each channel if not empty
    #     for i in range(self.channels):
    #         if self.caliparamlist[i] != 'Null':
    #             path3 = subfolderpath2 + '/phase_calibration_fitting_parameters_for_channel_' + str(i) + '_' + timestr + '.txt'
    #             text_file = open(path3, 'a')
    #             print('Export fitting parameters for channel_' + str(i) + ' to file named ' + path3)
    #             text_file.write('Amplitude_mW' + ' ' + 'Angular_freq' + ' ' + 'Phase' + ' ' + 'Offset' + ' ' + 'Max_Cov' + '\n')
    #             text_file.write(str(self.caliparamlist[i].get('amp')) + ' ' + str(self.caliparamlist[i].get('omega')) + ' ' + str(self.caliparamlist[i].get('phase')) + ' ' + str(self.caliparamlist[i].get('offset')) + ' ' + str(self.caliparamlist[i].get('maxcov')) + '\n')
    #             text_file.close()

    #     messagebox.showinfo(message='EXPORT COMPLETED! \n Export data saved in folder ' + superfolderpath)
    


    def exportfunc(self):
        # Ask for the export file name
        export_file = filedialog.asksaveasfilename(
            title="Save Export File",
            defaultextension=".pkl",
            filetypes=[("Pickle Files", "*.pkl")]
        )
        if not export_file:
            messagebox.showinfo("Export Canceled", "No file name provided for export.")
            return

    
        # Define matrices explicitly
        standard_matrices = {
            "xdatalist_IObar" : self.xdatalist_IObar,
            "ydatalist_IObar" : self.ydatalist_IObar,
            "xdatalist_IOcross" : self.xdatalist_IOcross,
            "ydatalist_IOcross" : self.ydatalist_IOcross,
            "linchar_current" : self.linchar_current,
            "linchar_voltage" : self.linchar_voltage,
            "lincubchar_current" : self.lincubchar_current,
            "lincubchar_voltage" : self.lincubchar_voltage,
            "resistancelist": self.resistancelist,
            "resistance_parameter_list": self.resistance_parameter_list,
            "rmin_list": self.rmin_list,
            "rmax_list": self.rmax_list,
            "alpha_list": self.alpha_list,
            "linear_resistance_list": self.linear_resistance_list,
            "caliparamlist_lin_cross": self.caliparamlist_lin_cross,
            "caliparamlist_lin_bar": self.caliparamlist_lin_bar,
            "caliparamlist_lincub_cross": self.caliparamlist_lincub_cross,
            "caliparamlist_lincub_bar": self.caliparamlist_lincub_bar,
            "derivedcurrentlist": self.derivedcurrentlist,
            "phiphase2list": self.phiphase2list
        }
    
        bytesio_matrices = {
            "res_lin_char_images": self.res_lin_char_images,
            "res_lincub_char_images": self.res_lincub_char_images,
            "opmod_lin_char_cross_state_images": self.opmod_lin_char_cross_state_images,
            "opmod_lin_char_bar_state_images": self.opmod_lin_char_bar_state_images,
            "opmod_lincub_char_cross_state_images": self.opmod_lincub_char_cross_state_images,
            "opmod_lincub_char_bar_state_images": self.opmod_lincub_char_bar_state_images
        }
    
        # Export standard matrices
        export_data = {"standard_matrices": standard_matrices}
    
        # Export BytesIO matrices as PNG images
        export_dir = os.path.dirname(export_file)
        image_map = {}
    
        for matrix_name, matrix in bytesio_matrices.items():
            if isinstance(matrix, list):  # Ensure the matrix is a list
                image_map[matrix_name] = []
                for i, value in enumerate(matrix):
                    if isinstance(value, BytesIO):
                        image_filename = f"{matrix_name}_{i}.png"
                        image_path = os.path.join(export_dir, image_filename)
                        with open(image_path, "wb") as img_file:
                            img_file.write(value.getvalue())
                        image_map[matrix_name].append(image_filename)
    
        export_data["image_map"] = image_map
        
        # Exclude any lambda functions or non-pickleable objects
        # Here, we replace the lambda function with a reference name
        for key in ['caliparamlist_lin_cross', 'caliparamlist_lin_bar', 'caliparamlist_lincub_cross',
                    'caliparamlist_lincub_bar']:
            if hasattr(self, key):
                matrix = getattr(self, key)
                for i, data in enumerate(matrix):
                    if isinstance(data, dict) and 'fitfunc' in data:
                        # Replace lambda with a string reference name
                        data['fitfunc'] = 'fit_cos_func'  # You could use a unique name here
                        matrix[i] = data  # Replace with the modified data
    
        # Save data to a pickle file
        with open(export_file, "wb") as file:
            pickle.dump(export_data, file)
    
        messagebox.showinfo("Export Complete", " Current chip data and acquired plots exported to {export_file}")


    
    def importfunc(self):
        # Ask for the import file
        import_file = filedialog.askopenfilename(
            title="Open Import File",
            filetypes=[("Pickle Files", "*.pkl")]
        )
        if not import_file:
            messagebox.showinfo("Import Canceled", "No file selected for import.")
            return
    
        with open(import_file, "rb") as file:
            imported = pickle.load(file)
            
        # Reassign the fitfunc back from the reference string
        for key in ['caliparamlist_lin_cross', 'caliparamlist_lin_bar', 'caliparamlist_lincub_cross',
                    'caliparamlist_lincub_bar']:
            if hasattr(self, key):
                matrix = getattr(self, key)
                for i, data in enumerate(matrix):
                    if isinstance(data, dict) and 'fitfunc' in data:
                        # Check for the reference name and assign the correct function
                        if data['fitfunc'] == 'fit_cos_func':
                            # Assign the actual function or lambda here
                            data['fitfunc'] = self.fit_cos  # Or use the function reference
                        matrix[i] = data  # Replace with the modified data
    
        # Import standard matrices
        standard_matrices = imported.get("standard_matrices", {})
        for attr_name, matrix in standard_matrices.items():
            if hasattr(self, attr_name):
                setattr(self, attr_name, matrix)
    
        # Import BytesIO matrices from images
        import_dir = os.path.dirname(import_file)
        image_map = imported.get("image_map", {})
        for matrix_name, image_filenames in image_map.items():
            if hasattr(self, matrix_name):
                matrix = getattr(self, matrix_name)
                if isinstance(matrix, list):
                    for i, filename in enumerate(image_filenames):
                        image_path = os.path.join(import_dir, filename)
                        if os.path.exists(image_path):
                            with open(image_path, "rb") as img_file:
                                buf = BytesIO(img_file.read())
                                buf.seek(0)  # Reset position
                                # Ensure the list is large enough to accommodate the index
                                if i >= len(matrix):
                                    matrix.extend([None] * (i + 1 - len(matrix)))
                                matrix[i] = buf
    
        messagebox.showinfo("Import Complete", " Chip data and plot set to the imported values from {import_file}")

    def makeDir(self, path):
        self.path = path

        print('Make folder-structure')
        if not os.path.isdir(self.path):
            os.makedirs(self.path)

    def setGlobalCurrentLimit(self, entry):

        self.newCL = entry.get()
        print('Global Current Limit Button is pressed')

        if self.val == '6x6':
            channels = 6*5
        elif self.val == '8x8':
            channels = 8*7
        elif self.val == 'custom':
            channels = self.channelentry.get() #string
            if channels == '': #if empty: 
                messagebox.showerror(message='ENTRY EMPTY! \n Please fill in the number of desired channels first')
                entry.delete(0, 'end') #clear the entry field

            else:
                channels = int(self.channelentry.get())

        #check if the entry cell is empty 
        if self.newCL == '': #if empty: 
            messagebox.showerror(message='ENTRY EMPTY! \n Please fill in a positive integer or float global current limit value in mA and then press submit again')
        else: #check for invalid characters

            illegalchar = False
            point = 0

            for i in range(len(self.newCL)):
                if self.newCL[i] in self.allowedinputvalues:
                    print(self.newCL[i])
                    if self.newCL[i] == '.':
                        point +=1
                        if point > 1:
                            print('input has more than one comma points')
                            break
                else:
                    print('Error: Input has at least one illegal character: ' + self.newCL[i]) 
                    illegalchar = True
                    break

            if illegalchar == True or point >1: #check for invalid characters in input
                messagebox.showerror(message='INVALID INPUT! \n Input value needs to be an integer or a float with a decimal point, not a comma. Please type in a new value')
                entry.delete(0, 'end') #clear the entry field
            else:
                self.newCL = float(self.newCL) #now set to float
                if self.newCL > self.globalcurrrentlimit or self.newCL < 0: 
                    messagebox.showwarning(message = 'WARNING! \n Entered global current limit exceeds maxium allowed current limit of ' + str(self.globalcurrrentlimit) + ' mA. Please enter a lower value')
                    entry.delete(0, 'end') #clear the entry field
                else:
                    for i in range(q.n_chs):
                        q.imax[i] = self.newCL
                    for i in range(channels):
                        self.currentlimitlist[i].configure(text=str(self.newCL))
                    messagebox.showinfo(message = 'COMPLETED, \n\n Current limit is now globally set on all available channels to: ' + str(self.newCL) + ' mA')


if __name__ == "__main__":
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

    q = None
    try:
        #connecting to QControl device
        print('')
        print("Connecting to QControl Device...")
        #serial_port_name_qcontrol = "/dev/tty.usbserial-FT672B5J" #this is static. for windows COM3 or COM5 etc.
        serial_port_name_qcontrol = "COM5" 
        print("Serial port name for the QControl device is: ", serial_port_name_qcontrol)
        q = qontrol.QXOutput(serial_port_name = serial_port_name_qcontrol, response_timeout = 0.1) #connect to the device. this is done automatically when software is started
        print ("Qontroller '{:}' initialised with firmware {:} and {:} channels".format(q.device_id, q.firmware, q.n_chs) )
        #create a dictionary with device info
        #params = {'Device id:': q.device_id, 'Firmware:': q.firmware, 'Available channels:': q.n_chs, 'Available modules:': int(q.n_chs / 8)}
        params = {'Device id:': q.device_id, 'Available channels:': q.n_chs}
        
        #Connecting to powermeter device
        print('')
        print("Connecting to Thorlabs P100D Powermeter Device...")
        rm = pyvisa.ResourceManager()
        print("Available resources are ", rm.list_resources()) #tuple
        #serial_port_name_powermeter = 'COM4'
        #print("Serial port name for the powermeter is: ", serial_port_name_powermeter)
        
        #inst = rm.open_resource('USB0::4883::32888::P0043301::0::INSTR') #ASRL4::INSTR
        
        devices = rm.list_resources()
        
        inst = rm.open_resource(devices[0])
        power_meter = ThorlabsPM100(inst = inst)

        headings = ['  CH', '   ID', '    Resistance (mΩ)', '', '           Current Limit (mA)', '         ', '               mA', '','Measure', '                       ', ' mA','', 'Phase Calibration                                                                                    ', '    Set Current          '] #this heading is replaced with the headings in the heading frame
        #heaterid6x6 = ['U_A1', 'U_A2', 'U_A3','L_A1', 'L_A2', 'L_A3', 'U_B1', 'U_B2', 'L_B1', 'L_B2', 'U_C1', 'U_C2', 'U_C3','L_C1', 'L_C2', 'L_C3', 'U_D1', 'U_D2', 'L_D1', 'L_D2', 'U_E1', 'U_E2', 'U_E3','L_E1', 'L_E2', 'L_E3', 'U_F1', 'U_F2', 'L_F1', 'L_F2']
        #heaterid6x6 = ['U_A1', 'U_A2', 'U_A3', 'U_B1', 'U_B2', 'U_C1', 'U_C2', 'U_C3', 'U_D1', 'U_D2', 'U_E1', 'U_E2', 'U_E3', 'U_F1', 'U_F2', 'L_A3', 'L_A2', 'L_A1', 'L_B2', 'L_B1', 'L_C3', 'L_C2', 'L_C1', 'L_D2', 'L_D1', 'L_E3', 'L_E2', 'L_E1', 'L_F2', 'L_F1']
        heaterid6x6 = ['L_A3', 'L_A2', 'L_A1', 'L_B2', 'L_B1', 'L_C3', 'L_C2', 'L_C1', 'L_D2', 'L_D1', 'L_E3', 'L_E2', 'L_E1', 'L_F2', 'L_F1', 'U_A1', 'U_A2', 'U_A3', 'U_B1', 'U_B2', 'U_C1', 'U_C2', 'U_C3', 'U_D1', 'U_D2', 'U_E1', 'U_E2', 'U_E3', 'U_F1', 'U_F2']
        heaterid8x8 = ['L_A4', 'L_A3', 'L_A2', 'L_A1', 'L_B3', 'L_B2', 'L_B1', 'L_C4', 'L_C3', 'L_C2', 'L_C1', 'L_D3', 'L_D2', 'L_D1', 'L_E4', 'L_E3', 'L_E2', 'L_E1', 'L_F3', 'L_F2', 'L_F1', 'L_G4', 'L_G3', 'L_G2', 'L_G1', 'L_H3', 'L_H2', 'L_H1', 'U_A1', 'U_A2', 'U_A3', 'U_A4', 'U_B1', 'U_B2', 'U_B3', 'U_C1', 'U_C2', 'U_C3', 'U_C4', 'U_D1', 'U_D2', 'U_D3', 'U_E1', 'U_E2', 'U_E3', 'U_E4', 'U_F1', 'U_F2', 'U_F3', 'U_G1', 'U_G2', 'U_G3', 'U_G4', 'U_H1', 'U_H2', 'U_H3']

        options =['6x6', '8x8', 'custom']

        globalcurrrentlimit = 6.0 #mA 

        print('')
        print('Initialize current limit globally on all available channels (' + str(q.n_chs) + ') to ' + str(globalcurrrentlimit) + ' mA')
        for i in range(q.n_chs):
            q.imax[i] = globalcurrrentlimit
        print('')

        app = App(params, headings, heaterid6x6, heaterid8x8, options, globalcurrrentlimit)
        app.mainloop()

    finally:
        if q is not None:

            #Reset all channels currents to zero and closing connection to serial port on closing the software
            for i in range(q.n_chs):
                q.i[i] = 0
                print("Resetting the current for channel " + str(i) + " to 0 mA")

            q.close()
            
            q = None
            print("Closing connection to serial port")


