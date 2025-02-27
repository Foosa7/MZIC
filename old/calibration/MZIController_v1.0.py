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

#import various python libraries
import numpy as np
from scipy import optimize

import matplotlib.ticker as ticker
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import shutil
import random
import string
import time


class MyUpperFrame(customtkinter.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.app = master

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

        IMAGE_WIDTH = 25
        IMAGE_HEIGHT = 29

        #IMAGE_WIDTH = 30 
        #IMAGE_HEIGHT = 33

        IMAGE_PATH = './logo_mini.png'
        #IMAGE_PATH = './kthlogo_mini_white2.png'
        
        self.your_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(IMAGE_WIDTH , IMAGE_HEIGHT))
        logo = customtkinter.CTkLabel(self, image=self.your_image, text="")
        logo.grid(row=0, column=0, padx=(10,0), pady=(10,3), rowspan = 6, sticky="n")

        labela = customtkinter.CTkLabel(self, text = 'Status:')
        labela.grid(row=0, column=1, padx=10, pady=(3,0), sticky="e")
        labelb = customtkinter.CTkLabel(self, text = 'Active')
        labelb.grid(row=0, column=2, padx=10, pady=(3,0), sticky="w")

        for i in range(len(self.keys)):
            label1 = customtkinter.CTkLabel(self, text=self.keys[i])
            label1.grid(row=i+1, column=1, padx=10, pady=(3,0), sticky="e")
            label2 = customtkinter.CTkLabel(self, text=self.values[i])
            label2.grid(row=i+1, column=2, padx=10, pady=(3,0), sticky="w")

        label3a = customtkinter.CTkLabel(self, text = 'Software version:')
        label3a.grid(row=5, column=1, padx=10, pady=(3,0), sticky="e")
        label3b = customtkinter.CTkLabel(self, text = 'v1.0')
        label3b.grid(row=5, column=2, padx=10, pady=(3,0), sticky="w")

        label3a = customtkinter.CTkLabel(self, text = 'Designed by:')
        label3a.grid(row=6, column=1, padx=10, pady=(3,5), sticky="e")
        label3b = customtkinter.CTkLabel(self, text = 'Mikael Schelin')
        label3b.grid(row=6, column=2, padx=10, pady=(3,5), sticky="w")

    

class MyCLExportFrame(customtkinter.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)

        self.upperframe = master
        self.app = self.upperframe.app #this is where I have initiated the frames. 
        self.title = title

        title = customtkinter.CTkLabel(self, text=self.title, corner_radius=6)
        title.grid(row=0, column=0, padx=10, pady=(10,0), sticky="new")

        entry = customtkinter.CTkEntry(self, placeholder_text = 'Max ' + str(self.app.globalcurrrentlimit) + ' (mA)', width = 100)
        entry.grid(row = 1, column = 0, padx = 10, pady = (5,5), sticky = 'ew')
            
        button = customtkinter.CTkButton(self, text = "Customize", width=100, command = lambda entry=entry : self.app.setGlobalCurrentLimit(entry))
        button.grid(row = 2, column=0, padx=10, pady=(5,5), sticky="ew")

        exporttitle = customtkinter.CTkLabel(self, text='Export data', corner_radius=6)
        exporttitle.grid(row=3, column=0, padx=10, pady=(10,0), sticky="ew")

        exportbutton = customtkinter.CTkButton(self, text = "Export", width=80, command = self.app.exportfunc)
        exportbutton.grid(row = 4, column=0, padx=10, pady=(5,5), sticky="ew")


class MyImageFrame(customtkinter.CTkFrame):
    def __init__(self, master, val):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        self.val = val

        print(self.val)

        IMAGE_WIDTH = self.IMAGE_WIDTH = 647
        IMAGE_HEIGHT = self.IMAGE_HEIGHT = 200

        self.IMAGE_PATH_6 = './chipimages/6x6mesh.png'
        self.IMAGE_PATH_8 = './chipimages/8x8mesh.png'
        self.IMAGE_PATH_empty = './chipimages/dummyimage.png'

        if self.val == '6x6':
            IMAGE_PATH = self.IMAGE_PATH_6 

        elif self.val == '8x8':
            IMAGE_PATH = self.IMAGE_PATH_8
        
        self.your_image = customtkinter.CTkImage(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(IMAGE_WIDTH , IMAGE_HEIGHT))
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
        self.variable = customtkinter.StringVar(value="6x6")

        title = customtkinter.CTkLabel(self, text=self.title, corner_radius=6)
        title.grid(row=0, column=0, padx=10, pady=(10,0), sticky="new")

        for i, value in enumerate(self.options):
            radiobutton = customtkinter.CTkRadioButton(self, text=value, value=value, variable=self.variable, command = self.radiofunction)
            radiobutton.grid(row=i+1, column=0, padx=10, pady=(10,10), sticky="w")
            self.radiobuttons.append(radiobutton)

    def getValue(self):
        return self.variable.get()

    def setValue(self, value):
        self.variable.set(value)

    def radiofunction(self):
        self.app.val=self.getValue() 
        print("mesh size choosen:", self.app.val)

        if self.app.val == '6x6':

            IMAGE_PATH = self.app.image_frame.IMAGE_PATH_6
            self.app.image_frame.your_image.configure(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(self.app.image_frame.IMAGE_WIDTH , self.app.image_frame.IMAGE_HEIGHT))

            self.config = 6*5
            if self.config <= self.params['Available channels:']:

                if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                    self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()

                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid6x6, config = self.config, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

                
                children = self.app.tab_view.tab("Calibrate").winfo_children()
                for child in children:
                    print(child)
                
                self.app.tab_view.calculate_frame.winfo_children()[-1].destroy()

                self.app.choosechannelframe = MyChannelFrame(self.app.tab_view.calculate_frame, config = self.config)
                self.app.choosechannelframe.grid(column=0, row=0, padx=10, pady=10, sticky="n")

            else:
                #self.open_toplevel()
                messagebox.showerror(message='Available channels are less than required channels for this mesh size. 6x6 mesh requires 30 channels. Only ' + str(self.params['Available channels:']) + ' are available. \n\n Please add more modules and restart the program or choose a custom mesh with a smaller number of channels.')
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.heaterid8x8, config = 0, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

        elif self.app.val == '8x8': 
            
            IMAGE_PATH = self.app.image_frame.IMAGE_PATH_8
            self.app.image_frame.your_image.configure(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(self.app.image_frame.IMAGE_WIDTH , self.app.image_frame.IMAGE_HEIGHT))

            self.config = 8*7

            if self.config <= self.params['Available channels:']:

                if len(self.app.tab_view.tab("Calibrate").winfo_children()) > 1:
                    # only header frame
                    self.app.tab_view.tab("Calibrate").winfo_children()[1].destroy()

                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid8x8, config = self.config, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

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
                messagebox.showerror(message='Available channels are less than required channels for this mesh size. 8x8 mesh requires 56 channels. Only ' + str(self.params['Available channels:']) + ' are available. \n\n Please add more modules and restart the program or choose a custom mesh with a smaller number of channels.')
                self.app.scrollable_frame = MyScrollableFrame(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.app.heaterid8x8, config = 0, app=self.app)
                self.app.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")

                #test
                self.app.header_frame = MyHeaderFrame(self.app.tab_view.tab("Calibrate"), val=self.app.val)
                self.app.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

        elif self.app.val == 'custom':

            print("custom picked")

            IMAGE_PATH = self.app.image_frame.IMAGE_PATH_empty

            self.app.image_frame.your_image.configure(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(self.app.image_frame.IMAGE_WIDTH , self.app.image_frame.IMAGE_HEIGHT))

            self.app.channelentry = customtkinter.CTkEntry(self, placeholder_text="# Channels", width=100)
            self.app.channelentry.grid(column=1, row=3, padx=10, pady=10, sticky="se")
            self.app.channelbutton = customtkinter.CTkButton(self, text="Apply", width=60, command=self.customfunct)
            self.app.channelbutton.grid(column=2, row=3, padx=10, pady=10, sticky="se")

            self.app.browse = customtkinter.CTkButton(self, text="Browse image", width=100, command = self.selectpic)
            self.app.browse.grid(column=0, row=4, padx=10, pady=10, sticky="se")
            self.app.pathentry = customtkinter.CTkEntry(self, placeholder_text ="image path...", width=100)
            self.app.pathentry.grid(column=1, row=4, padx=10, pady=10, sticky="sw")
            self.app.upload = customtkinter.CTkButton(self, text="Upload", width=60, command = self.savepic)
            self.app.upload.grid(column=2, row=4, padx=10, pady=10, sticky="se")

    def selectpic(self):
        global filename
        filename = filedialog.askopenfilename(initialdir = os.getcwd(), title = "Select Image", filetypes = (("pgn images", "*.png"), ("jpg images", "*.jpg"), ("jpeg images", "*.jpeg")))
        self.app.pathentry.insert(0,filename)


    def savepic(self):
        filenameSplitted = filename.split('.')
        randomtext = ''.join((random.choice(string.ascii_lowercase) for x in range(12)))
        shutil.copy(filename, f"./chipimages/{randomtext}.{filenameSplitted[1]}")
        IMAGE_PATH = f"./chipimages/{randomtext}.{filenameSplitted[1]}"
        self.app.image_frame.your_image.configure(light_image=Image.open(os.path.join(IMAGE_PATH)), size=(self.app.image_frame.IMAGE_WIDTH , self.app.image_frame.IMAGE_HEIGHT))
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

                    self.app.scrollable_frame2 = MyScrollableFrame2(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, config = self.config, app=self.app) #app is argument so that data structures can be saved in app and be accessible globally
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
                    self.app.scrollable_frame2 = MyScrollableFrame2(self.app.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, config = 0, app=self.app) #app is argument so that data structures can be saved in app and be accessible globally
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
        self.config = config

        self.channels = []

        mylabel = customtkinter.CTkLabel(self, text = "Channel")
        mylabel.grid(column=0, row=0, padx=10, pady=10, sticky="w")

        for i in range(int(self.config)):
            self.channels.append(str(i))
         
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

        if self.app.caliparamlist[self.channel] != 'Null':

            fitxdata = np.linspace(self.app.xdatalist[self.channel][0], self.app.xdatalist[self.channel][-1], 300)

            plt.plot(self.app.xdatalist[self.channel], self.app.ydatalist[self.channel], "ok", label="optical power", color='white')
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
        self.app = self.mycalcsuperframe.tabview.app
        
        self.label = customtkinter.CTkLabel(self, text = 'Fitting:')
        self.label.grid(column=0, row=0, padx=10, pady=(10,0), sticky="e")

        self.labelb = customtkinter.CTkLabel(self, text = 'Y = -A * cos(b * P + c) + d')
        self.labelb.grid(column=1, row=0, padx=10, pady=(10,0), sticky="ew", columnspan=1)

        self.label2a = customtkinter.CTkLabel(self, text="Amplitude (A):")
        self.label2a.grid(column=0, row=1, padx=10, pady=0, sticky="e")
        self.label2b = customtkinter.CTkLabel(self, text="Null")
        self.label2b.grid(column=1, row=1, padx=10, pady=0, sticky="w")

        self.label3a = customtkinter.CTkLabel(self, text="Angular frequency (b):")
        self.label3a.grid(column=0, row=2, padx=10, pady=0, sticky="e")
        self.label3b = customtkinter.CTkLabel(self, text="Null")
        self.label3b.grid(column=1, row=2, padx=10, pady=0, sticky="w")

        self.label4a = customtkinter.CTkLabel(self, text="Phase (c):")
        self.label4a.grid(column=0, row=3, padx=10, pady=0, sticky="e")
        self.label4b = customtkinter.CTkLabel(self, text="Null")
        self.label4b.grid(column=1, row=3, padx=10, pady=0, sticky="w")

        self.label5a = customtkinter.CTkLabel(self, text="Offset (d):")
        self.label5a.grid(column=0, row=4, padx=10, pady=0, sticky="e")
        self.label5b = customtkinter.CTkLabel(self, text="Null")
        self.label5b.grid(column=1, row=4, padx=10, pady=0, sticky="w")

        self.label6a = customtkinter.CTkLabel(self, text="Frequency (f):")
        self.label6a.grid(column=0, row=5, padx=10, pady=0, sticky="e")
        self.label6b = customtkinter.CTkLabel(self, text="Null")
        self.label6b.grid(column=1, row=5, padx=10, pady=0, sticky="w")

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
        self.currentmode.grid(column=0, row=4, padx=10, pady=(10,10), sticky="e")
        self.currententry = customtkinter.CTkEntry(self, placeholder_text = "input current", width=100)
        self.currententry.grid(column=1, row=4, padx=10, pady=(10,10), sticky="ew")
        self.currbutton = customtkinter.CTkButton(self, text="Apply", width=100, command = self.applycurrentmode)
        self.currbutton.grid(column=2, row=4, padx=10, pady=(10,10), sticky="w")

        self.setcurr = customtkinter.CTkLabel(self, text = "Set current (mA):")
        self.setcurr.grid(column=0, row=6, padx=10, pady=(10,5), sticky="e")
        self.setcurr2 = customtkinter.CTkLabel(self, text = "Null")
        self.setcurr2.grid(column=1, row=6, padx=10, pady=(10,5), sticky="ew")

        self.release = customtkinter.CTkButton(self, text="Release", width=100, command = self.releasecurrent)
        self.release.grid(column=2, row=6, padx=10, pady=(10,5), sticky="w")

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
                self.current2apply = float(round(1000 * np.sqrt(P/(R*1000)), 5)) #Derive the current in A, converted to mA to apply for this phase.

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


class MyHeaderFrame(customtkinter.CTkFrame):
    def __init__(self, master, val):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=0)
        #self.headings = headings
        self.val = val

        #for i in range(len(self.headings)):
        #    label1 = customtkinter.CTkLabel(self, text=self.headings[i])
        #    label1.grid(row=0, column=i, padx=10, pady=(10,0), sticky="ew")

        if self.val == '6x6' or self.val == '8x8':
            head0 = customtkinter.CTkLabel(self, text='CH')
            head0.grid(column=0, row=0, padx=(20,0), pady=10, sticky="e")
            head1 = customtkinter.CTkLabel(self, text='ID')
            head1.grid(column=1, row=0, padx=(25,0), pady=10, sticky="e")
            head2 = customtkinter.CTkLabel(self, text='Resistance')
            head2.grid(column=2, row=0, padx=(40,0), pady=10, sticky="e")
            head3 = customtkinter.CTkLabel(self, text='(mΩ)')
            head3.grid(column=3, row=0, padx=(60,0), pady=10, sticky="e")
            head4 = customtkinter.CTkLabel(self, text='Current Limit')
            head4.grid(column=4, row=0, padx=(20,0), pady=10, sticky="e")
            head5 = customtkinter.CTkLabel(self, text='                   ')
            head5.grid(column=5, row=0, padx=(80,0), pady=10, sticky="e")
            head6 = customtkinter.CTkLabel(self, text='(mA)')
            head6.grid(column=6, row=0, padx=10, pady=10, sticky="e")
            head7 = customtkinter.CTkLabel(self, text='Measure')
            head7.grid(column=7, row=0, padx=(15,0), pady=10, sticky="e")
            head8 = customtkinter.CTkLabel(self, text='            ')
            head8.grid(column=8, row=0, padx=(80,0), pady=10, sticky="e")
            head9 = customtkinter.CTkLabel(self, text='(mA)')
            head9.grid(column=9, row=0, padx=10, pady=10, sticky="e")
            head10 = customtkinter.CTkLabel(self, text='Phase Calibration')
            head10.grid(column=10, row=0, padx=(20,0), pady=10, sticky="e")
            head11 = customtkinter.CTkLabel(self, text='           ')
            head11.grid(column=11, row=0, padx=(40,0), pady=10, sticky="e")
            head12 = customtkinter.CTkLabel(self, text= '           ')
            head12.grid(column=12, row=0, padx=(40,0), pady=10, sticky="e")
            head13 = customtkinter.CTkLabel(self, text='           ')
            head13.grid(column=13, row=0, padx=(40,0), pady=10, sticky="e")
            head14 = customtkinter.CTkLabel(self, text='           ')
            head14.grid(column=14, row=0, padx=(40,0), pady=10, sticky="e")
            head15 = customtkinter.CTkLabel(self, text='Current (mA)')
            head15.grid(column=15, row=0, padx=10, pady=10, sticky="e")
        elif self.val == 'custom':
            head0 = customtkinter.CTkLabel(self, text='CH')
            head0.grid(column=0, row=0, padx=(20,0), pady=10, sticky="e")
            head1 = customtkinter.CTkLabel(self, text='Custom ID')
            head1.grid(column=1, row=0, padx=(15,0), pady=10, sticky="e")
            head2 = customtkinter.CTkLabel(self, text='Resistance')
            head2.grid(column=2, row=0, padx=(40,0), pady=10, sticky="e")
            head3 = customtkinter.CTkLabel(self, text='(mΩ)')
            head3.grid(column=3, row=0, padx=(60,0), pady=10, sticky="e")
            head4 = customtkinter.CTkLabel(self, text='Current Limit')
            head4.grid(column=4, row=0, padx=(30,0), pady=10, sticky="e")
            head5 = customtkinter.CTkLabel(self, text='                ')
            head5.grid(column=5, row=0, padx=(60,0), pady=10, sticky="e")
            head6 = customtkinter.CTkLabel(self, text='(mA)')
            head6.grid(column=6, row=0, padx=20, pady=10, sticky="e")
            head7 = customtkinter.CTkLabel(self, text='Measure')
            head7.grid(column=7, row=0, padx=(15,0), pady=10, sticky="e")
            head8 = customtkinter.CTkLabel(self, text='            ')
            head8.grid(column=8, row=0, padx=(80,0), pady=10, sticky="e")
            head9 = customtkinter.CTkLabel(self, text='(mA)')
            head9.grid(column=9, row=0, padx=10, pady=10, sticky="e")
            head10 = customtkinter.CTkLabel(self, text='Phase Calibration')
            head10.grid(column=10, row=0, padx=(20,0), pady=10, sticky="e")
            head11 = customtkinter.CTkLabel(self, text='           ')
            head11.grid(column=11, row=0, padx=(40,0), pady=10, sticky="e")
            head12 = customtkinter.CTkLabel(self, text= '           ')
            head12.grid(column=12, row=0, padx=(40,0), pady=10, sticky="e")
            head13 = customtkinter.CTkLabel(self, text='           ')
            head13.grid(column=13, row=0, padx=(40,0), pady=10, sticky="e")
            head14 = customtkinter.CTkLabel(self, text='           ')
            head14.grid(column=14, row=0, padx=(40,0), pady=10, sticky="e")
            head15 = customtkinter.CTkLabel(self, text='Current (mA)')
            head15.grid(column=15, row=0, padx=10, pady=10, sticky="e")


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

        self.app.caliparamlist = ["Null" for i in range(self.config)] #here save the calibration parameters for each channel (a dictionary of parameters per channel)

        self.app.xdatalist = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.ydatalist = [[] for i in range(self.config)] #list of lists for saved ydata for each channel

        self.app.derivedcurrentlist = ['Null' for i in range(self.config)] #here save the actual value
        self.app.setcurrentlist = ['Null' for i in range(self.config)] #here save the actual value
        self.app.phiphase2list  = ['Null' for i in range(self.config)] #here save the phase value

        self.app.currententrylist  = ['Null' for i in range(self.config)] #here save entry value for current mode

        #create data structures to be able to access and export data
        self.app.channellist = []
        self.app.idlist = []
        self.app.customtkinterresistancelist = []
        self.app.currentlimitlist = [] #initialize these globally for all channels at startup or set custom globally with an entry and button
        self.app.appliedcurrlist = []
        self.app.measuredcurrentlist = []
        self.app.rampstartlist = []
        self.app.rampendlist = []
        self.app.stepslist = []
        self.app.stabtimelist = []
        self.app.setcurrlabellist = []

        for i in range(self.config):
            channel = customtkinter.CTkLabel(self, text=str(i))
            channel.grid(column=0, row=i+1, padx=10, pady=10, sticky="e")
            heateridd = customtkinter.CTkLabel(self, text=self.heatid[i])
            heateridd.grid(column=1, row=i+1, padx=10, pady=10, sticky="e")
            
            acqresist = customtkinter.CTkLabel(self, text="Null")
            acqresist.grid(column=3, row=i+1, padx=10, pady=10, sticky="e")
            resist = customtkinter.CTkButton(self, text = "Charactarize",width=120, command = lambda i=i, acqresist=acqresist: self.app.char_resist_func(i,acqresist)) #fg_color="#858c22"
            resist.grid(column=2, row=i+1, padx=10, pady=10, sticky="e")

            currententry = customtkinter.CTkEntry(self, placeholder_text="Customize (mA)", width=120)
            currententry.grid(column=4, row=i+1, padx=10, pady=10, sticky="e")
            acqcurrentlimit = customtkinter.CTkLabel(self, text=str(self.app.globalcurrrentlimit))
            acqcurrentlimit.grid(column=6, row=i+1, padx=10, pady=10, sticky="e")
            
            submitcurrent = customtkinter.CTkButton(self, text = "Submit", width=80, command = lambda i=i, currententry=currententry, acqcurrentlimit=acqcurrentlimit, : self.app.submit_currentlimit(i, currententry,acqcurrentlimit))
            submitcurrent.grid(column=5, row=i+1, padx=10, pady=10, sticky="e")
            currentry = customtkinter.CTkEntry(self, placeholder_text="Apply (mA)", width=80)
            currentry.grid(column=8, row=i+1, padx=10, pady=10, sticky="e")
        
            measured_curr = customtkinter.CTkLabel(self, text="Null")
            measured_curr.grid(column=12, row=i+1, padx=10, pady=10, sticky="w")
            applycurr = customtkinter.CTkButton(self, text = "Measure", width=80, command = lambda i=i, currentry = currentry, measured_curr = measured_curr: self.app.measure(i, currentry, measured_curr))
            applycurr.grid(column=9, row=i+1, padx=10, pady=10, sticky="e")

            rampstart = customtkinter.CTkEntry(self, placeholder_text="Start (mA)", width=80)
            rampstart.grid(column=13, row=i+1, padx=10, pady=10, sticky="e")
            
            rampend = customtkinter.CTkEntry(self, placeholder_text="End (mA)", width=80)
            rampend.grid(column=14, row=i+1, padx=10, pady=10, sticky="e")
            
            steps = customtkinter.CTkEntry(self, placeholder_text="Steps", width=60)
            steps.grid(column=15, row=i+1, padx=10, pady=10, sticky="e")

            stabtime = customtkinter.CTkEntry(self, placeholder_text="Paus (s)", width=70) #stabilization time for the chip between measurements
            stabtime.grid(column=16, row=i+1, padx=10, pady=10, sticky="e")

            calibrate = customtkinter.CTkButton(self, text = "Calibrate", width=80, command = lambda i=i, rampstart = rampstart, rampend = rampend, steps = steps, stabtime = stabtime, acqresist=acqresist : self.app.calibration_func(i, rampstart, rampend, steps, stabtime, acqresist))
            calibrate.grid(column=17, row=i+1, padx=10, pady=10, sticky="e")

            setcurr = customtkinter.CTkLabel(self, text="Null")
            setcurr.grid(column=18, row=i+1, padx=10, pady=10, sticky="e")


            #save custom tkinter objects to lists to access and export data
            self.app.channellist.append(channel)
            self.app.idlist.append(heateridd)
            self.app.customtkinterresistancelist.append(acqresist)
            self.app.currentlimitlist.append(acqcurrentlimit)
            self.app.appliedcurrlist.append(currentry)
            self.app.measuredcurrentlist.append(measured_curr)
            self.app.rampstartlist.append(rampstart)
            self.app.rampendlist.append(rampend)
            self.app.stepslist.append(steps)
            self.app.stabtimelist.append(stabtime)
            self.app.setcurrlabellist.append(setcurr)

class MyScrollableFrame2(customtkinter.CTkScrollableFrame): #for custom channels with custom heater-id. 
    def __init__(self, master, title, params, config, app): #app is argument so that i can save data structures in app and access them globally
        super().__init__(master, label_text='')
        #self.geometry("1500x200")
        self.grid_columnconfigure(0, weight=0)
        #self.grid_rowconfigure((1), weight=0)
        self.params = params
        self.keys=list(self.params.keys())
        self.values=list(self.params.values())
        self.config = config
        
        self.app = app # so can access app

        #create list data structure to save all data
        self.app.resistancelist = ["Null" for i in range(self.config)] #list with saved resistances

        self.app.caliparamlist = ['Null' for i in range(self.config)] #here save the calibration parameters for each channel (a dictionary of parameters per channel)

        self.app.xdatalist = [[] for i in range(self.config)] #list of lists for saved xdata for each channel
        self.app.ydatalist = [[] for i in range(self.config)] #list of lists for saved ydata for each channel

        self.app.derivedcurrentlist = ['Null' for i in range(self.config)]
        self.app.setcurrentlist = ['Null' for i in range(self.config)]
        self.app.phiphase2list  = ['Null' for i in range(self.config)] #here save the phase value

        self.app.currententrylist  = ['Null' for i in range(self.config)] #here save entry value for current mode

        #create data structures to be able to access and export data
        self.app.channellist = []
        self.app.idlist = [] #list with customid initiated in app so globally accessible
        self.app.customtkinterresistancelist = []
        self.app.currentlimitlist = [] #initialize these globally for all channels at startup or set custom globally with an entry and button
        self.app.appliedcurrlist = []
        self.app.measuredcurrentlist = []
        self.app.rampstartlist = []
        self.app.rampendlist = []
        self.app.stepslist = []
        self.app.stabtimelist = []
        self.app.setcurrlabellist = []


        for i in range(self.config):
            channel = customtkinter.CTkLabel(self, text=str(i))
            channel.grid(column=0, row=i+1, padx=10, pady=10, sticky="e")
            heateridd = customtkinter.CTkEntry(self, placeholder_text="Heater ID", width=80) #custom heater id
            heateridd.grid(column=1, row=i+1, padx=10, pady=10, sticky="e")
            
            acqresist = customtkinter.CTkLabel(self, text="Null")
            acqresist.grid(column=3, row=i+1, padx=10, pady=10, sticky="e")
            resist = customtkinter.CTkButton(self, text = "Charactarize",width=120, command = lambda i=i, acqresist=acqresist: self.app.char_resist_func(i,acqresist)) #fg_color="#858c22"
            resist.grid(column=2, row=i+1, padx=10, pady=10, sticky="e")

            currententry = customtkinter.CTkEntry(self, placeholder_text="Customize (mA)", width=120)
            currententry.grid(column=4, row=i+1, padx=10, pady=10, sticky="e")
            acqcurrentlimit = customtkinter.CTkLabel(self, text=str(self.app.globalcurrrentlimit))
            acqcurrentlimit.grid(column=6, row=i+1, padx=10, pady=10, sticky="e")
            
            submitcurrent = customtkinter.CTkButton(self, text = "Submit", width=80, command = lambda i=i, currententry=currententry, acqcurrentlimit=acqcurrentlimit, : self.app.submit_currentlimit(i, currententry,acqcurrentlimit))
            submitcurrent.grid(column=5, row=i+1, padx=10, pady=10, sticky="e")
            currentry = customtkinter.CTkEntry(self, placeholder_text="Apply (mA)", width=80)
            currentry.grid(column=8, row=i+1, padx=10, pady=10, sticky="e")
            
            measured_curr = customtkinter.CTkLabel(self, text="Null")
            measured_curr.grid(column=12, row=i+1, padx=10, pady=10, sticky="w")
            applycurr = customtkinter.CTkButton(self, text = "Measure", width=80, command = lambda i=i, currentry = currentry, measured_curr = measured_curr: self.app.measure(i, currentry, measured_curr))
            applycurr.grid(column=9, row=i+1, padx=10, pady=10, sticky="e")

            rampstart = customtkinter.CTkEntry(self, placeholder_text="Start (mA)", width=80)
            rampstart.grid(column=13, row=i+1, padx=10, pady=10, sticky="e")
            
            rampend = customtkinter.CTkEntry(self, placeholder_text="End (mA)", width=80)
            rampend.grid(column=14, row=i+1, padx=10, pady=10, sticky="e")
            
            steps = customtkinter.CTkEntry(self, placeholder_text="Steps", width=60)
            steps.grid(column=15, row=i+1, padx=10, pady=10, sticky="e")

            stabtime = customtkinter.CTkEntry(self, placeholder_text="Paus (s)", width=70) #stabilization time for the chip between measurements
            stabtime.grid(column=16, row=i+1, padx=10, pady=10, sticky="e")

            calibrate = customtkinter.CTkButton(self, text = "Calibrate", width=80, command = lambda i=i, rampstart = rampstart, rampend = rampend, steps = steps, stabtime = stabtime, acqresist=acqresist : self.app.calibration_func(i, rampstart, rampend, steps, stabtime, acqresist))
            calibrate.grid(column=17, row=i+1, padx=10, pady=10, sticky="e")

            setcurr = customtkinter.CTkLabel(self, text="Null")
            setcurr.grid(column=18, row=i+1, padx=10, pady=10, sticky="e")


            #save custom tkinter objects to lists to access and export data
            self.app.channellist.append(channel)
            self.app.idlist.append(heateridd)
            self.app.customtkinterresistancelist.append(acqresist)
            self.app.currentlimitlist.append(acqcurrentlimit)
            self.app.appliedcurrlist.append(currentry)
            self.app.measuredcurrentlist.append(measured_curr)
            self.app.rampstartlist.append(rampstart)
            self.app.rampendlist.append(rampend)
            self.app.stepslist.append(steps)
            self.app.stabtimelist.append(stabtime)
            self.app.setcurrlabellist.append(setcurr)

# class ToplevelWindow(customtkinter.CTkToplevel):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.geometry("400x300")
#         self.title("Warning!")
#         self.configure(fg_color = 'gray80')

#         self.label = customtkinter.CTkLabel(self, text="\n\n\nAvailable channels are less than required \n channels for this mesh size. \n\n Please add more modules and restart \n the program or choose a smaller \n mesh size. \n\n 6x6 mesh requires 30 channels \n 8x8 mesh requires 56 channels", text_color='#246BCE')
#         self.label.pack(padx=20, pady=20)

class App(customtkinter.CTk):
    def __init__(self, params, headings, heaterid6x6, heaterid8x8, options, globalcurrrentlimit):
        super().__init__()

        self.title("MZI Controller")
        self.geometry("1500x900")
        self.grid_columnconfigure((0,1), weight=0)#1
        self.grid_rowconfigure((0), weight=0)
        self.params = params
        self.headings = headings
        self.heaterid6x6 = heaterid6x6
        self.heaterid8x8 = heaterid8x8
        self.val = '6x6' 
        self.options = options
        self.globalcurrrentlimit = globalcurrrentlimit #this is the globally initalized current limit that can never be exceeded
        self.newCL = self.globalcurrrentlimit

        self.allowedinputvalues = ['0','1','2','3','4','5','6','7','8','9','.']

        self.upperframe = MyUpperFrame(self)
        self.upperframe.grid(row=0, column=0, padx=10, pady=(20,20), sticky="ewns")

        self.lowerframe = MyLowerFrame(self)
        self.lowerframe.grid(row=1, column=0, padx=10, pady=(20,20), sticky="ewns")

        self.info_frame = MyInfoFrame(self.upperframe, title = 'Device settings', params=self.params)
        self.info_frame.grid(row=0, column=0, padx=10, pady=(20,20), sticky="ewns") 

        self.radiobuttons_frame = MyRadioButtonFrame(self.upperframe, title = "Mesh size", options=self.options, params = self.params)
        self.radiobuttons_frame.grid(row=0, column=1, padx=10, pady=(20,20), sticky="ewns") 

        self.CLexportframe = MyCLExportFrame(self.upperframe, title = "Global Current Limit")
        self.CLexportframe.grid(row=0, column=2, padx=10, pady=(20,20), sticky="ewns")

        self.image_frame = MyImageFrame(self.upperframe, self.val) #val='6x6'
        self.image_frame.grid(row=0, column=3, padx=10, pady=(20,20), sticky = "ewns") #sticky="n", rowspan=1

        self.tab_view = MyTabView(self.lowerframe, headings=self.headings)
        self.tab_view.grid(row=0, column=0, padx=10, pady=(20,0), sticky="nsew")

        self.header_frame = MyHeaderFrame(self.tab_view.tab("Calibrate"), val =self.val)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(20,0), sticky='ew')

        self.scrollable_frame = MyScrollableFrame(self.tab_view.tab("Calibrate"), title = "Channel configuration", params=self.params, heaterid=self.heaterid6x6, config = 6*5, app = self)
        self.scrollable_frame.grid(row=1, column=0, padx=10, pady=(5,30), sticky = "nsew")
        
        #self.toplevel_window = None

    # def open_toplevel(self):
    #     if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
    #         self.toplevel_window = ToplevelWindow(self)  # create window if its None or destroyed
    #     else:
    #         self.toplevel_window.focus()  # if window exists focus it

    
    def char_resist_func(self, channel, label):
        self.channel=channel
        self.label=label

        print("Perform resistance charactarization for channel " + str(self.channel))
        startcurr = 0.0 #unit mA
        endcurr = q.imax[self.channel] #unit mA
        currentramp = np.linspace(startcurr, endcurr, num=10) #divide ramp into 10 equidistant steps

        currentramplist = [float(elem) for elem in currentramp] #convert elements to float which is needed for device

        measured_voltlist = [] #unit V

        for i in range(len(currentramplist)):
           q.i[self.channel] = currentramplist[i]
           measured_voltlist.append(q.v[self.channel])
           sleep(1.0)
           print ("Channel {:} applied current of {:} mA and measured voltage of {:} V".format(self.channel, currentramplist[i], measured_voltlist[i]))
        
        #Reset channel's current and voltage to zero after the measurement
        q.i[self.channel] = 0
        print("Reset channel " + str(self.channel) + " to 0 mA after measurement")

        ###################Charactarize the resistance with a linear fit####################

        currlist_amphere = [elem / 1000 for elem in currentramplist] #convert measured current in measured_currlist to ampere from mA

        x=np.array(currlist_amphere) #unit Amphere
        y=np.array(measured_voltlist) #unit V

        a, b = np.polyfit(x, y, 1)

        self.resistancelist[self.channel] = a #add resistance, this is a float
        print('Acquired resistance is ' + str(self.resistancelist[self.channel]) + ' Ω')

        self.label.configure(text=str(round(a, 1))) #reconfigure label with value for resistance

        for child in self.tab_view.calculate_frame.graphframe.winfo_children():
            print("printar child")
            print(child)
            child.destroy()  # remove existing figures

        #set white font colors
        COLOR = 'white'
        matplotlib.rcParams['text.color'] = COLOR
        matplotlib.rcParams['axes.labelcolor'] = COLOR
        matplotlib.rcParams['xtick.color'] = COLOR
        matplotlib.rcParams['ytick.color'] = COLOR

        fig, ax = plt.subplots(1, figsize=(6,4))

        plt.scatter(x,y,label='applied current', color='white')
        plt.plot(x, a*x+b, label = "fit", color = "red")
        plt.text(endcurr/1000 - 5/1000, 0.7, 'y = ' + '{:.2f}'.format(b) + ' + {:.2f}'.format(a) + 'x', size=9)
        plt.text(endcurr/1000 - 5/1000, 0.4, 'Resistance: ' + '{:.2f}'.format(a) + 'Ω', size=9)
        
        plt.xlabel("applied current (A)")
        plt.ylabel("measured voltage (V)")
        plt.title("Charactarized Resistance for Channel "+str(self.channel))
        plt.legend(loc="best", facecolor="#323334", framealpha=1)

        ax.set_facecolor("#323334")
        plt.setp(ax.spines.values(), color=COLOR)
        fig.patch.set_facecolor("#323334")

        #plt.savefig("Measured resistance for channel "+str(self.channel)+".png", format='png', dpi=300)
        
        #reset to default colors
        COLOR = 'black'
        matplotlib.rcParams['text.color'] = COLOR
        matplotlib.rcParams['axes.labelcolor'] = COLOR
        matplotlib.rcParams['xtick.color'] = COLOR
        matplotlib.rcParams['ytick.color'] = COLOR

        plt.show()
        plt.close()


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
            ff = np.fft.fftfreq(len(self.xdata), (self.xdata[1]-self.xdata[0]))  #assume uniform spacing
            Fyy = abs(np.fft.fft(self.ydata))
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


    def calibrationplotX(self, channel, xdata, ydata): #calibration plot on the calibration tab

        self.channel = channel
        self.xdata = xdata #in mW
        self.ydata = ydata #in mW

        fitxdata = np.linspace(self.xdata[0], self.xdata[-1], 300)
        
        print("CalibrationplotX initiated")

        res = self.fit_cos(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
        
        print( "Amplitude=%(amp)s, Angular freq.=%(omega)s, phase=%(phase)s, offset=%(offset)s, Max. Cov.=%(maxcov)s" % res)
    
        self.caliparamlist[self.channel] = res #save the dictionary of calibration parameters for each channel in a list

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
        plt.title("Phase calibration curve for channel " + str(channel))

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

        plt.show()
        plt.close()

        #return fig

    def calibration_func(self, channel, rampstart, rampend, steps, stabtime, acqresist):

        self.channel = channel
        self.currstart = rampstart.get() #these are strings
        self.currend = rampend.get()
        self.numsteps = steps.get()
        self.numpaus = stabtime.get()

        maxsteps = 300 
        maxpaus = 30 #seconds

        self.numresist = self.resistancelist[self.channel] #this is a float

        print("Perform phase calibration measurements and fitting for channel: " + str(self.channel)) 

        currentlimit = q.imax[self.channel] #get the current limit for this channel

        #check1. Check so that self.resistancelist[self.channel] is not NULL. Then do resistance first. 
        print('Check so that channel has a resistance')

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

                                                                #Check7. Check if calibration has been done and is to be updated. 
                                                                #Then make sure to reset current to zero and reset the derivedcurrentlist and setcurrentlist
                                                                if self.caliparamlist[self.channel] != 'Null':
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

                                                                        xdata, ydata = self.getReadData(self.channel, self.currstart, self.currend, self.numsteps, self.numpaus, self.numresist) # in mW both

                                                                        self.xdatalist[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                        self.ydatalist[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW

                                                                        self.calibrationplotX(self.channel, xdata, ydata)

                                                                else: #calibration has not been done before

                                                                    #xdata, ydata = self.getExampleData() #get exsampel data

                                                                    self.currstart = float(self.currstart) #now convert inputs to floats
                                                                    self.currend = float(self.currend)
                                                                    self.numsteps = int(self.numsteps)
                                                                    self.numpaus = float(self.numpaus)

                                                                    xdata, ydata = self.getReadData(self.channel, self.currstart, self.currend, self.numsteps, self.numpaus, self.numresist) # in mW both

                                                                    self.xdatalist[self.channel] = xdata #save the xdata to its place in the xdatalist heating power in mW 
                                                                    self.ydatalist[self.channel] = ydata #save the ydata to its place in the ydatalist optical power in mW

                                                                    self.calibrationplotX(self.channel, xdata, ydata)
        

    def getReadData(self, channel, currstart, currend, numsteps, numpaus, numresist): #return x-data and y-data (x being heating power, y being optical power)

        self.channel = channel
        self.currstart = currstart #mA
        self.currend = currend #mA
        self.numsteps = numsteps
        self.numpaus = numpaus
        self.numresist = numresist #Ohm

        #currentlist = list(np.linspace(self.currstart, self.currend, self.numsteps)) #mA
        currentlist_squared = list(np.linspace(self.currstart**2, self.currend**2, self.numsteps)) #mA**2
        currentlist = np.sqrt(currentlist_squared) #mA
        currentramp = [float(elem) for elem in currentlist] #mA

        opticalpowerlist = [] #this is ydata in mW

        heatingpowerlist = [] #this is xdata in mW

        for i in range(len(currentramp)):
            heatingpowerlist.append((self.numresist * (currentramp[i]/1000)**2)*1000) #in mW

        print("Measure optical power for channel " + str(self.channel) + ' over the current ramp')

        print("Measurement type :" , power_meter.getconfigure)
        print("Wavelength       :", power_meter.sense.correction.wavelength)

        for i in range(len(currentramp)):
            q.i[self.channel] = currentramp[i] #apply current from the ramp to channel in mA
            opticalpowerlist.append(power_meter.read*1000) # read optical power on power meter in W and add to opticalpowerlist for channel in mW
            sleep(self.numpaus)
            print ("Channel {:} set to {:} mA and measured optical power  to {:} mW".format(self.channel, currentramp[i], opticalpowerlist[i]))

        #Set channel current to zero after phase calibration data acquired
        q.i[self.channel] = 0
        print('Reset current on channel ' + str(self.channel) + ' to zero mA after measurement')

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

    
    def exportfunc(self):
        print("Export function button is pressed")
        if self.val == '6x6':
            self.channels = 6*5
        elif self.val == '8x8':
            self.channels = 8*7
        elif self.val == 'custom':
            self.channels = int(self.channelentry.get())

        #create an export file with the current date and time
        timestr = time.strftime("%Y%m%d-%H%M%S")

        #1. Create folder structure for the export
        superfolderpath = './' + timestr #here place overall data file
        subfolderpath1 = superfolderpath + '/' + 'timeseriesdata' #here place timeseriesdata for all channels
        subfolderpath2 = superfolderpath + '/' + 'fittingparameterdata' #here place fitting parameters for all channels
        self.makeDir(superfolderpath)
        self.makeDir(subfolderpath1)
        self.makeDir(subfolderpath2)

        #2. Create overall export file
        path1 = superfolderpath + '/overall_calibrationdata_all_channels_' + timestr + '.txt'
        print('Export calibration date to file with name ' + path1)
        
        text_file1=open(path1, 'a')

        text_file1.write('CHANNEL' + ' ' + 'HEADERID' + ' ' + 'CHARACTARIZED_RESISTANCE' + ' ' + 'CURRENT_LIMIT' + ' ' + 'APPLIED_CURRENT' +  ' ' + 'MEASURED_CURRENT' + ' ' + 'RAMP_START_V' + ' ' + 'RAMP_END_V' + ' ' + 'STEPS' + ' ' + 'STABILIZATION_TIME' +'\n')

        #write data on file. Each channel per row. Each data-label per column, separated by space
        for i in range(self.channels):
            if self.val == '6x6' or self.val == '8x8':
                text_file1.write(str(self.channellist[i].cget('text')) +' '+ str(self.idlist[i].cget('text')) + ' ' + str(self.resistancelist[i]) + ' ' + str(self.currentlimitlist[i].cget('text')) +  ' ' + str(self.appliedcurrlist[i].get()) + ' ' + str(self.measuredcurrentlist[i].cget('text')) + ' ' + str(self.rampstartlist[i].get()) + ' ' + str(self.rampendlist[i].get()) + ' ' + str(self.stepslist[i].get()) + ' ' + str(self.stabtimelist[i].get()) +'\n')
            else:
                text_file1.write(str(self.channellist[i].cget('text')) +' '+ str(self.idlist[i].get()) + ' ' + str(self.resistancelist[i]) + ' ' + str(self.currentlimitlist[i].cget('text')) +  ' ' + str(self.appliedcurrlist[i].get()) + '  ' + str(self.measuredcurrentlist[i].cget('text')) + ' ' + str(self.rampstartlist[i].get()) + ' ' + str(self.rampendlist[i].get()) + ' ' + str(self.stepslist[i].get()) + ' ' + str(self.stabtimelist[i].get()) +'\n')

        text_file1.close()

        #3. save xdata and ydata if data exist for each channel
        for i in range(self.channels):
            if len(self.xdatalist[i]) != 0:
                path2 = subfolderpath1 + '/phase_calibration_data_for_channel_' + str(i) + '_' + timestr + '.txt'
                text_file = open(path2, 'a')
                print('Export xdata and ydata for channel_' + str(i) + ' to file named ' + path2)
                text_file.write('Heating_Power_mW' + ' ' + 'Optical_Power_mW' + '\n')
                for j in range(len(self.xdatalist[i])):
                    text_file.write(str(self.xdatalist[i][j]) + ' ' + str(self.ydatalist[i][j]) + '\n')
                text_file.close()

        #4. save phase fitting parameters to file for each channel if not empty
        for i in range(self.channels):
            if self.caliparamlist[i] != 'Null':
                path3 = subfolderpath2 + '/phase_calibration_fitting_parameters_for_channel_' + str(i) + '_' + timestr + '.txt'
                text_file = open(path3, 'a')
                print('Export fitting parameters for channel_' + str(i) + ' to file named ' + path3)
                text_file.write('Amplitude_mW' + ' ' + 'Angular_freq' + ' ' + 'Phase' + ' ' + 'Offset' + ' ' + 'Max_Cov' + '\n')
                text_file.write(str(self.caliparamlist[i].get('amp')) + ' ' + str(self.caliparamlist[i].get('omega')) + ' ' + str(self.caliparamlist[i].get('phase')) + ' ' + str(self.caliparamlist[i].get('offset')) + ' ' + str(self.caliparamlist[i].get('maxcov')) + '\n')
                text_file.close()

        messagebox.showinfo(message='EXPORT COMPLETED! \n Export data saved in folder ' + superfolderpath)
        

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
        params = {'Device id:': q.device_id, 'Firmware:': q.firmware, 'Available channels:': q.n_chs, 'Available modules:': int(q.n_chs / 8)}

        #Connecting to powermeter device
        print('')
        print("Connecting to Thorlabs P100D Powermeter Device...")
        rm = pyvisa.ResourceManager()
        print("Available resources are ", rm.list_resources()) #tuple
        #serial_port_name_powermeter = 'COM4'nput
        #print("Serial port name for the powermeter is: ", serial_port_name_powermeter)
        
        #inst = rm.open_resource('USB0::4883::32888::P0043301::0::INSTR') #ASRL4::INSTR
        inst = rm.open_resource('USB0::4883::32888::PM001464::0::INSTR')
        power_meter = ThorlabsPM100(inst = inst)

        headings = ['  CH', '   ID', '    Resistance (mΩ)', '', '           Current Limit (mA)', '         ', '               mA', '','Measure', '                       ', ' mA','', 'Phase Calibration                                                                                    ', '    Set Current          '] #this heading is replaced with the headings in the heading frame
        #heaterid6x6 = ['U_A1', 'U_A2', 'U_A3','L_A1', 'L_A2', 'L_A3', 'U_B1', 'U_B2', 'L_B1', 'L_B2', 'U_C1', 'U_C2', 'U_C3','L_C1', 'L_C2', 'L_C3', 'U_D1', 'U_D2', 'L_D1', 'L_D2', 'U_E1', 'U_E2', 'U_E3','L_E1', 'L_E2', 'L_E3', 'U_F1', 'U_F2', 'L_F1', 'L_F2']
        #heaterid6x6 = ['U_A1', 'U_A2', 'U_A3', 'U_B1', 'U_B2', 'U_C1', 'U_C2', 'U_C3', 'U_D1', 'U_D2', 'U_E1', 'U_E2', 'U_E3', 'U_F1', 'U_F2', 'L_A3', 'L_A2', 'L_A1', 'L_B2', 'L_B1', 'L_C3', 'L_C2', 'L_C1', 'L_D2', 'L_D1', 'L_E3', 'L_E2', 'L_E1', 'L_F2', 'L_F1']
        heaterid6x6 = ['L_A3', 'L_A2', 'L_A1', 'L_B2', 'L_B1', 'L_C3', 'L_C2', 'L_C1', 'L_D2', 'L_D1', 'L_E3', 'L_E2', 'L_E1', 'L_F2', 'L_F1', 'U_A1', 'U_A2', 'U_A3', 'U_B1', 'U_B2', 'U_C1', 'U_C2', 'U_C3', 'U_D1', 'U_D2', 'U_E1', 'U_E2', 'U_E3', 'U_F1', 'U_F2']
        #heaterid8x8 = ['U_A1', 'U_A2', 'U_A3', 'U_A4', 'L_A1', 'L_A2', 'L_A3', 'L_A4', 'U_B1', 'U_B2', 'U_B3', 'L_B1', 'L_B2', 'L_B3', 'U_C1', 'U_C2', 'U_C3', 'U_C4', 'L_C1', 'L_C2', 'L_C3', 'L_C4', 'U_D1', 'U_D2', 'U_D3', 'L_D1', 'L_D2', 'L_D3', 'U_E1', 'U_E2', 'U_E3', 'U_E4', 'L_E1', 'L_E2', 'L_E3', 'L_E4', 'U_F1', 'U_F2', 'U_F3', 'L_F1', 'L_F2', 'L_F3', 'U_G1', 'U_G2', 'U_G3', 'U_G4', 'L_G1', 'L_G2', 'L_G3', 'L_G4', 'U_H1', 'U_H2', 'U_H3', 'L_H1', 'L_H2', 'L_H3']
        heaterid8x8 = ['L_A4', 'L_A3', 'L_A2', 'L_A1', 'L_B3', 'L_B2', 'L_B1', 'L_C4', 'L_C3', 'L_C2', 'L_C1', 'L_D3', 'L_D2', 'L_D1', 'L_E4', 'L_E3', 'L_E2', 'L_E1', 'L_F3', 'L_F2', 'L_F1', 'L_G4', 'L_G3', 'L_G2', 'L_G1', 'L_H3', 'L_H2', 'L_H1', 'U_A1', 'U_A2', 'U_A3', 'U_A4', 'U_B1', 'U_B2', 'U_B3', 'U_C1', 'U_C2', 'U_C3', 'U_C4', 'U_D1', 'U_D2', 'U_D3', 'U_E1', 'U_E2', 'U_E3', 'U_E4', 'U_F1', 'U_F2', 'U_F3', 'U_G1', 'U_G2', 'U_G3', 'U_G4', 'U_H1', 'U_H2', 'U_H3']

        options =['6x6', '8x8', 'custom']

        globalcurrrentlimit = 5.0 #mA 

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



