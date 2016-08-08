# -*- coding:UTF-8 -*-

import wx



class ButtonBox(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.addAddressText(sizer)
        self.addSayText(sizer)
        self.addSendButton(sizer)
        self.SetSizer(sizer)



    def addAddressText(self, sizer):
        self.addressInput = wx.TextCtrl(self, -1, "", size=(100, 30))
        sizer.Add(self.addressInput, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)

    def addSayText(self, sizer):
        self.sayInput = wx.TextCtrl(self, -1, "", size=(360, 30))
        sizer.Add(self.sayInput, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)

    def addSendButton(self, sizer):
        self.buttonSend = wx.Button(self, -1, u"Send", size=(-1, 30))
        sizer.Add(self.buttonSend, 0, flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=10)

    def getSayingWords(self):
        return self.sayInput.GetValue()

    def reset(self):
        self.sayInput.SetValue('')

#---------------------------------------------------------------------------
class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, u'button panel', size=(600,120))
        self.mainPanel = wx.Panel(self, -1, style=0)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.buttonBox = ButtonBox(self.mainPanel)

        self.mainSizer.Add(self.buttonBox, 1, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.mainPanel.SetSizer(self.mainSizer)

    def getNewName(self):
        return self.newName.GetValue()

    def reset(self):
        self.newName.SetValue('')

def test():
    app = wx.PySimpleApp()
    frame = TestFrame()
    frame.Show(True)
    app.MainLoop()

if __name__ == '__main__':
    test()