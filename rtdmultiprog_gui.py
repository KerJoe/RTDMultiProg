#!/usr/bin/python3

import os, sys
import rtdmultiprog as isp
import traceback

try:
    import PySimpleGUI as sg
except ModuleNotFoundError:
    import time
    print("Please install PySimpleGUI: pip install PySimpleGUI")
    time.sleep(3)
    exit(1)

ifSel  = None
devSel = None
devInvDict = None

# Window layout
mainLayout = [[sg.FileBrowse('Open firmware file', key='openFirmware'), sg.Button('Select backend', key='backendButton')],
              [sg.Output(size=(40, 10))],
              [sg.ProgressBar(1000, orientation='h', size=(25, 20), key='progressbar')],
              [sg.Button('Read'), sg.Button('Write'), sg.Button('Erase'), sg.Button('Reboot') ]]

mainWindow = sg.Window('RTDMultiProg', mainLayout, element_justification='center')
try:
    while (True):
        event, values = mainWindow.read(timeout=10)
        if event == sg.WIN_CLOSED:
            break
        if event == "Read":
            print("Reading firmware from device...")
            isp.StartInterface(devSel)
            isp.ReadFlashFile(values["openFirmware"], lambda s, e, c: mainWindow["progressbar"].UpdateBar((c/(e-s)*1000)))
            isp.StopInterface()
        if event == "Write":
            print("Writing firmware to device...")
            isp.StartInterface(devSel)
            isp.WriteFlashFile(values["openFirmware"], lambda s, e, c: mainWindow["progressbar"].UpdateBar((c/(e-s)*1000)))
            isp.StopInterface()
        if event == "Erase":
            print("Erasing firmware on device...")
            isp.StartInterface(devSel)
            isp.EraseFlash()
            isp.StopInterface()
        if event == "Reboot":
            print("Rebooting device...")
            isp.StartInterface(devSel)
            isp.StopInterface()
        if event == "backendButton":
            ifList = isp.GetInterfaceList()
            if not ifSel:
                ifSel  = ifList[0]
            backendLayout = [[sg.Text('Interface:', size=(10,1)), sg.Combo(ifList, default_value=ifSel, size=(20,10), key="interface")],
                             [sg.Text('Device:',  size=(10,1)), sg.Combo('', size=(20,10), key="device"), sg.Button("Refresh")],
                             [sg.OK(), sg.Cancel()]]
            backendWindow = sg.Window('Backend select', backendLayout, modal=True)
            while (True):
                event, values = backendWindow.read(timeout=10)
                if event == sg.WIN_CLOSED or event == 'Cancel':
                    backendWindow.close()
                    break
                if event == 'OK':
                    devSel = devInvDict[values["device"]]
                    ifSel  = values["interface"]
                    backendWindow.close()
                    break
                if event == 'Refresh':
                    try:
                        isp.LoadInterface(values["interface"])
                        devDict = isp.GetDeviceList()
                        devInvDict = {v: k for k, v in devDict.items()} # Inverse dictonary key is value, value is key
                        devList = [kv[1] for kv in list(devDict.items())]
                        defVal  = devList[0]
                        backendWindow["device"].Update(value=defVal, values=devList)
                    except SystemError as e: # Catch system incompatible
                        print(e)
                        backendWindow.close()
                        break
                    except ModuleNotFoundError as e:
                        print(e)
                        backendWindow.close()
                        break
except Exception as e:
    tb = traceback.format_exc()
    sg.popup_error(f'AN EXCEPTION HAS OCCURRED!', e, tb)