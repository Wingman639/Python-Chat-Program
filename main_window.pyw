# -*- coding:UTF-8 -*-
import wx
import os
import button_panel
import udp

class ClientFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u'Chat', size=(600, 800))
        self.splitWindow = wx.SplitterWindow(self)
        self.mainPanel = self.newMainPanel(self.splitWindow)
        self.infoPanel = self.newInfoPanel(self.splitWindow)
        self.splitWindow.SplitHorizontally(self.mainPanel, self.infoPanel, -200)
        self.splitWindow.SetMinimumPaneSize(20)
        self.bindEvents()
        self.init_all()


    def newMainPanel(self, parent):
        mainPanel = wx.Panel(parent, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.buttonBox = button_panel.ButtonBox(mainPanel)
        mainSizer.Add(self.buttonBox, proportion=0, flag= wx.TOP, border=5)

        self.mainText = wx.TextCtrl(mainPanel, -1, style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER)
        mainSizer.Add(self.mainText, proportion= 1, flag=wx.TOP | wx.EXPAND, border=5)

        mainPanel.SetSizer(mainSizer)
        return mainPanel


    def newInfoPanel(self, parent):
        infoPanel = wx.Panel(parent)
        infoPanel.SetBackgroundColour("white")
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.infoText = wx.TextCtrl(infoPanel, -1, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.infoText, proportion=1, flag=wx.EXPAND | wx.ALL)
        infoPanel.SetSizerAndFit(vbox)
        return infoPanel


    #########################
    def init_all(self):
        self.buttonBox.addressInput.SetValue('127.0.0.1:31500')

    #########################
    def bindEvents(self):
        self.buttonBox.buttonSend.Bind(wx.EVT_BUTTON, self.onSendButton)

    #########################
    def onSendButton(self, event):
        text = 'send to [%s]: %s' % (self.buttonBox.addressInput.GetValue(), self.buttonBox.sayInput.GetValue())
        self.infoText.AppendText(text)
        parameters = self.buttonBox.addressInput.GetValue().split(':')
        host = (parameters[0], int(parameters[1]))
        udp.send(host, self.buttonBox.sayInput.GetValue())




def run_window():
    app = wx.PySimpleApp()
    frame = ClientFrame()
    frame.Show(True)
    app.MainLoop()

def main():
    run_window()

if __name__ == '__main__':
    main()
