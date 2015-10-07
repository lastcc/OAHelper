# -*- coding: utf-8 -*-
import wx
import images as images
import wx.gizmos as gizmos
import collections
import Queue
import threading
import oa
import wx.html2 as webview
import os
import win32con
import webbrowser

from tinyhttp import Firefox
from log_config import logger
from jinja2 import Template
from oa.models import Struct





class MainFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, -1, title, size=(800, 400))
        self.panel = panel = wx.Panel(self, -1)
        self.CreateControls()
        self.DoLayout()
        self.Templates = {}
        self.workerNum = 8
        self.dNum = 3
        self.Timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.Jump, self.Timer)
        self.wvs = []
        self.director = None
        self.selectedOrderObject = Struct()
        self.selectedLv = ''
        self.MagicX = False
                
        self.RegisterHotKey(1, 0, win32con.VK_F1)
        self.Bind(wx.EVT_HOTKEY, self.HKRaise, id=1)
        self.RegisterHotKey(2, 0, win32con.VK_F2)
        self.Bind(wx.EVT_HOTKEY, self.HKMagic, id=2)
        self.RegisterHotKey(3, 0, win32con.VK_F3)
        self.Bind(wx.EVT_HOTKEY, self.HKShowMeX, id=3)
        self.RegisterHotKey(7, 0, win32con.VK_F7)
        self.Bind(wx.EVT_HOTKEY, self.HKSearchIDInEbay, id=7)         
        self.RegisterHotKey(10, 0, win32con.VK_F10)
        self.Bind(wx.EVT_HOTKEY, self.HKOpenOrderInOA, id=10)
        self.RegisterHotKey(12, win32con.MOD_CONTROL, win32con.VK_F3)
        self.Bind(wx.EVT_HOTKEY, self.HKSetup, id=12)
        
        
    def ShowAsker(self, title, text, value=''):
        
        dlg = wx.TextEntryDialog(
                self, text,
                title, value)
        
        v = dlg.ShowModal()
        vv = dlg.GetValue()
        dlg.Destroy()
        
        if not vv:
            return        
        if v == wx.ID_OK:
            return vv 


    def HKShowMeX(self, evt):
        page = self.Notebook1.GetSelection()
        if page + 1 > self.Notebook1.GetPageCount() - 1:
            self.Notebook1.SetSelection(0)
        else:
            self.Notebook1.SetSelection(page+1)
    def HKSearchIDInEbay(self, evt):
        try:
            buyer = self.selectedOrderObject.MAIL_BUYER
            url=['http://k2b-bulk.ebay.com.hk/ws/eBayISAPI.dll?MfcISAPICommand=SalesRecordConsole&',
                 'currentpage=SCSold&pageNumber=1&searchField=BuyerId&searchValues=<USER_ID>&StoreCategory=',
                 '-4&Status=All&Period=Last122Days&searchSubmit=%E6%90%9C%E5%B0%8B&goToPage='] 
            url=''.join(url)
            url=url.replace('<USER_ID>',buyer)    
            webbrowser.open_new_tab(url)
        except:
            pass
        
    def HKMagic(self, evt):
        if not self.MagicX:
            self.Notebook2.Hide()
            self.panel.Layout()
            self.MagicX = True
        else:
            self.Notebook2.Show(True)
            self.panel.Layout()
            self.MagicX = False
        
    def HKRaise(self, evt):
        if self.IsIconized():
            self.Iconize(False)
            self.Raise()
        elif self.IsActive():
            self.Iconize(True)
        else:
            self.Raise()
        
    def HKOpenOrderInOA(self, evt):
      
        try:
            order = self.selectedOrderObject.order
            url = 'http://banggood.sellercube.com/BillDetail/index?id=%s' % order
            webbrowser.open_new_tab(url)
        except:
            pass


    def HKSetup(self, evt):
        frm = FrmAskPassword(self, 'Login', self.PasswordCallback)
        frm.CenterOnParent()
        frm.Show()
    def CreateControls(self):
        self.Notebook1 = wx.Notebook(self.panel, -1)
        self.Notebook2 = wx.Notebook(self.panel, -1)
        self.xNote = wx.Notebook(self.Notebook1, -1)


    def DoLayout(self):
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.Notebook1, 2, wx.EXPAND)
        sizer1.Add(self.Notebook2, 1, wx.EXPAND)
        
        self.Notebook1.AddPage(self.xNote, 'Mail Records')
        self.Notebook1.AddPage(self.CreateTreeListCtrl(), 'Order Overview')
        self.Notebook1.AddPage(self.CreateRefundRecPanel(), 'Refund Detail')
        
        self.Notebook2.AddPage(self.CreateEditorPanel(), 'Reply Editor')
        self.Notebook2.AddPage(self.CreateRefundInititorPanel(), 'Refund Initiator')
        self.Notebook2.AddPage(self.CreateShortcutsPanel(), '~ Shortcuts ~')
        
        self.panel.SetSizer(sizer1)

        
    def CreateTreeListCtrl(self):

        tree = gizmos.TreeListCtrl(self.Notebook1, -1, style =
                                wx.TR_DEFAULT_STYLE
                                | wx.TR_EDIT_LABELS
                                #| wx.TR_TWIST_BUTTONS
                                | wx.TR_ROW_LINES
                                | wx.TR_COLUMN_LINES
                                | wx.TR_HIDE_ROOT 
                                | wx.TR_FULL_ROW_HIGHLIGHT)
        tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.treeOnSelChanged)
        tree.GetMainWindow().Bind(wx.EVT_RIGHT_DOWN, self.test)
        self.tree = tree
        return tree
    
    def test(self, evt):
        pt = evt.GetPosition()
        item = self.tree.HitTest(pt)[0]
        evt.Skip()
      
        if not item:
            return
        
        self.tree.Expand(item)
        pyData = self.tree.GetItemPyData(item)
        if not pyData:
            return
        
        lv, data = pyData
        for ss in self.Orders:
            if ss.order == data:
                self.selectedOrderObject = ss
                self.selectedLv = lv
                self.selectedData = data
                self.Render()
                self.treeChangeCText()
                self.tree.SelectItem(item)
                break
        else:
            return
        
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()
            self.popupID7 = wx.NewId()
            self.popupID8 = wx.NewId()
            self.popupID9 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.mChangeComment, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.mInterceptOrder, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.mCancelOrder, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.mContactBuyer, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.mOutofStock, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.mUnconfirmed, id=self.popupID6)
            self.Bind(wx.EVT_MENU, self.mToBeExamed, id=self.popupID7)

       
        
        # make a menu
        menu = wx.Menu()

        # add some other items
        menu.Append(self.popupID1, u"修改订单备注(&O)")
        if self.selectedOrderObject.isInterceptable:
            menu.Append(self.popupID2, u"拦截订单(&I)")

        # make a submenu
        sm = wx.Menu()
        sm.Append(self.popupID3, u"取消订单")
        sm.Append(self.popupID4, u"联系客户")
        sm.Append(self.popupID5, u"缺货")
        sm.Append(self.popupID6, u"未确认")
        sm.Append(self.popupID7, u"待检查")
        
        menu.AppendMenu(-1, u"移动到", sm)


        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def mChangeComment(self, evt):
        old = self.selectedOrderObject.comment_area
        order = self.selectedOrderObject.order
        new = self.ShowAsker('Change Comment Area', 'New Comment is:', value=old)
        self.director.ChangeComment(order, new)
        
    def mInterceptOrder(self, evt):
        order = self.selectedOrderObject.order
        reason = self.ShowAsker('Intercept', 'Reason:', value=u'先不发，请拦截')
        self.director.InterceptOrder(order, reason)
        
    def mCancelOrder(self, evt):
        order = self.selectedOrderObject.order
        self.director.MoveOrder(order, to=oa.const.ORDER_CANCELED)
        
    def mContactBuyer(self, evt):
        order = self.selectedOrderObject.order
        self.director.MoveOrder(order, to=oa.const.ORDER_CONTACT_BUYER)
    def mOutofStock(self, evt):
        order = self.selectedOrderObject.order
        self.director.MoveOrder(order, to=oa.const.ORDER_OUT_OF_STOCK)
        
    def mUnconfirmed(self, evt):
        order = self.selectedOrderObject.order
        self.director.MoveOrder(order, to=oa.const.ORDER_UNCONFIRMED)
        
    def mToBeExamed(self, evt):
        order = self.selectedOrderObject.order
        self.director.MoveOrder(order, to=oa.const.ORDER_TO_BE_EXAMED)     
                 
        
    def CreateRefundRecPanel(self):
        pnl = wx.Panel(self.Notebook1)
        self.rWV = webview.WebView.New(pnl)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.rWV, 1, wx.EXPAND, 5)
        pnl.SetSizer(sizer)
        return pnl
    
    def DoSearch(self, evt):
        fltr = self.searchbox.GetValue().strip().lower()
        
        ok = []
        for key in self.Templates.keys():
            if fltr in key.lower():
                if key in ok:
                    continue
                ok.append(key)
                
        
        self.listbox.Clear()
        if not ok:
            return
        self.listbox.InsertItems(ok, 0)

        fr = self.listbox.FindString(fltr) 
        if not  fr== wx.NOT_FOUND:
            self.listbox.SetSelection(fr)
            tag = self.listbox.GetStringSelection()
            self.SelectedTemplate = self.Templates.get(tag, '')
            self.textctrl.SetValue(self.SelectedTemplate)            
  
        self.Render()
        
    def EvtListBox(self, evt):
        tag = evt.GetString()
        self.SelectedTemplate = self.Templates.get(tag, '')
        self.textctrl.SetValue(self.SelectedTemplate)        
        #for x in range(self.listbox.GetCount()):
            #text = self.listbox.GetString(x)
            #text = text.lower()
            
            #if fltr in text:
                #self.listbox.SetSelection(evt.GetSelection())
                #tag = self.listbox.GetStringSelection()
                
                
        self.Render()        
        
    def CreateShortcutsPanel(self):
        pnl = wx.Panel(self.Notebook2)
        pnl.SetBackgroundColour('LIGHT BLUE')

        
        return pnl
        
                
    
    def CreateEditorPanel(self):
        pnl = wx.Panel(self.Notebook2)
        pnl.SetBackgroundColour('LIGHT BLUE')
   
        self.listbox = wx.ListBox(pnl, -1)
        self.searchbox = wx.SearchCtrl(pnl, -1)
        self.textctrl = wx.TextCtrl(pnl, -1, style=wx.TE_MULTILINE)
        self.btnSend = wx.Button(pnl, -1, u'~ Render and Send ~')
        self.btnJump = wx.Button(pnl, -1, u'~~~ Jump ~~~')
        
        self.searchbox.Bind(wx.EVT_TEXT, self.DoSearch)
        self.listbox.Bind(wx.EVT_LISTBOX, self.EvtListBox)
         
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer1.Add(self.listbox, 1, wx.EXPAND|wx.ALL, 5)
        sizer1.Add(self.searchbox, 0, wx.EXPAND|wx.ALL, 5)
        

        sizer2.Add(self.textctrl, 1, wx.EXPAND|wx.ALL, 4)
        
        sizer2x = wx.BoxSizer(wx.HORIZONTAL)
        sizer2x.Add(self.btnJump, 0, wx.ALL, 5)
        sizer2x.Add(self.btnSend, 0, wx.ALL, 5)        
        sizer2.Add(sizer2x, 0, wx.EXPAND|wx.ALL)
        
        
        sizer.Add(sizer1, 1, wx.EXPAND)
        sizer.Add(sizer2, 3, wx.EXPAND)
        
        self.textctrl.SetBackgroundColour('light gray')

        pnl.SetSizer(sizer)
        
        return pnl
        
    def CreateRefundInititorPanel(self):
        pnl = wx.Panel(self.Notebook2)
        pnl.SetBackgroundColour('LIGHT BLUE')
        
        
        l1 = wx.StaticText(pnl, -1, u'订单编号 ')
        self.refund_orderSelector = wx.ComboBox(pnl, -1)
        l2 = wx.StaticText(pnl, -1, u'币种 ')
        self.refund_currencySelector = wx.Choice(pnl, -1, choices=["USD", "GBP", "EUR", "AUD"])
        l3 = wx.StaticText(pnl, -1, u'类型 ')
        self.refund_ReasonTypeSelector = wx.Choice(pnl, -1)
        l4 = wx.StaticText(pnl, -1, u'中文 退款原因 ')
        self.refund_ReasonSelectorCN = wx.ComboBox(pnl, -1)
        l5 = wx.StaticText(pnl, -1, u'英文 退款原因 ')
        self.refund_ReasonSelectorEN = wx.ComboBox(pnl, -1)
     
        self.rfbtnOK = wx.Button(pnl, -1, u'~ Let\'s do it ~')
        self.rfbtnJump = wx.Button(pnl, -1, u'~~~ Jump ~~~')
        
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer2.Add(self.rfbtnOK, 0, wx.EXPAND|wx.ALL, 4)
        sizer2.Add(self.rfbtnJump, 0, wx.EXPAND|wx.ALL, 4)
        
        
        sizer1.Add(l1, 0, wx.EXPAND|wx.ALL)        
        sizer1.Add(self.refund_orderSelector, 0, wx.EXPAND)
        sizer1.Add(l2, 0, wx.EXPAND|wx.ALL) 
        sizer1.Add(self.refund_currencySelector, 0, wx.EXPAND)
        sizer1.Add(l3, 0, wx.EXPAND|wx.ALL) 
        sizer1.Add(self.refund_ReasonTypeSelector, 0, wx.EXPAND)
        sizer1.Add(l4, 0, wx.EXPAND|wx.ALL) 
        sizer1.Add(self.refund_ReasonSelectorCN, 0, wx.EXPAND)
        sizer1.Add(l5, 0, wx.EXPAND|wx.ALL) 
        sizer1.Add(self.refund_ReasonSelectorEN, 0, wx.EXPAND)

        sizer.Add(sizer1, 0, wx.EXPAND)
        sizer.Add(sizer2, 0, wx.EXPAND)
        
        x = wx.BoxSizer(wx.HORIZONTAL)
        x.Add((0,0), 1)
        x.Add(sizer, 2)
        x.Add((0,0), 5)
        

        pnl.SetSizer(x)
        
        refundTypes = collections.OrderedDict()
        refundTypes[u'没收到']=oa.const.TYPE_NOT_RECEIVED
        refundTypes[u'质量投诉']=oa.const.TYPE_QUALITY_NOT_OK
        refundTypes[u'其他']=oa.const.TYPE_OTHER_REASONS
        refundTypes[u'货损']=oa.const.TYPE_DAMAGED
        refundTypes[u'与图片有出入']=oa.const.TYPE_PICTURE_MISMATCH
        refundTypes[u'客户要求取消']=oa.const.TYPE_CANCELED_BY_BUYER
        refundTypes[u'库存不足']=oa.const.TYPE_NOT_ENOUGH_STOCK
        refundTypes[u'退额外运费']=oa.const.TYPE_REFUND_RETURN_SHIPPING
        

        for k, v in refundTypes.iteritems():
            c = self.refund_ReasonTypeSelector.GetCount()
            self.refund_ReasonTypeSelector.Insert(k, c, v)
        
          
       
        return pnl
    
    def clearRefund(self, evt=None):
        self.refund_orderSelector.SetValue('')
        self.refund_ReasonSelectorCN.SetValue('')
    
    def initRefund(self, evt):
        order = self.refund_orderSelector.GetValue()
        currency = self.refund_currencySelector.GetStringSelection()
        x = self.refund_ReasonTypeSelector.GetSelection()
        if x == wx.NOT_FOUND:
            return
        reason_TYPE = self.refund_ReasonTypeSelector.GetClientData(x)
        reason_CN = self.refund_ReasonSelectorCN.GetValue()
        reason_EN = self.refund_ReasonSelectorEN.GetValue()
        
        
        try:
            value = self.selectedOrderObject.total_value
        except:
            value = '1.0'
        
        dlg = wx.TextEntryDialog(
                self, u'请输入金额',
                u'Er?? Eh??', value)
        
        v = dlg.ShowModal()
        amount = dlg.GetValue()
        dlg.Destroy()
        
        if not v == wx.ID_OK:
            return
        
        
        try:
            self.director.RefundOrder(order, amount, currency, reason_TYPE, 
                                             reason_CN, 
                                             reason_EN)
            
            for ss in self.Orders:
                ss.thisRefund = amount
        
        except:
            pass
        
        dlg = wx.MessageDialog(self, '~~ We\'ve Done!',
                               '~~ Tell you what',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        
        dlg.ShowModal()
        dlg.Destroy()
        self.clearRefund()
        
   
    
    
    def Render(self):
        try:
            rendered = Template(self.textctrl.GetValue()).render(ss=self.selectedOrderObject)
            self.textctrl.SetValue(rendered)
        except:
            pass


    def PasswordCallback(self, user, password, store, email, responder):
        self.user = user
        self.password = password
        self.store = store
        self.email = email
        self.responder = responder
        
        if not user or not password:
            return
        else:
            self.start()
            
    def start(self):

        self.Bind(wx.EVT_BUTTON, self.Jump, self.btnJump)
        self.Bind(wx.EVT_BUTTON, self.SendMail, self.btnSend)
        self.Bind(wx.EVT_BUTTON, self.initRefund, self.rfbtnOK)
        self.Bind(wx.EVT_BUTTON, self.clearRefund, self.rfbtnJump)
        
        self.openerX = OPENER_X(user=self.user, password=self.password)
        self.task_queue = Queue.Queue()
        self.pending = Queue.Queue()
        
        tf = TemplateFetcher(self.openerX, self.TemplatesCallback)
        self.task_queue.put_nowait(tf)
        
        fb = FirstBlade(self.openerX, self.FirstBladeCallback, self.responder, self.email)
        self.task_queue.put_nowait(fb)
        
        for i in range(1, self.workerNum):
            worker = Worker(self.task_queue)
            worker.start()
            
        self.dq = Queue.Queue()
        
        for i in range(1, self.dNum):
            worker = Worker(self.dq)
            worker.start()
            
        
        
    def SendMail(self, evt):
        self.Render()
        replycontent = self.textctrl.GetValue()
        try:
            self.director.ReplyMail(self.Mail.MAIL_ID, replycontent, self.Mail.MAIL_SENDER, True)
            self.dq.put_nowait(self.director)
        except:
            logger.info('There is no mail to reply!')
            
        self.Jump()
        
        
    def FirstBladeCallback(self, Finder):
        for mailInfo in Finder:
            rf = RobotFetcher(self.openerX, mailInfo, self.store, self.email, self.RobotFetcherCallback)
            self.task_queue.put_nowait(rf)
        
    def RobotFetcherCallback(self, ss):

        self.pending.put_nowait(ss)
        
        
    def TemplatesCallback(self, Finder):
        self.Templates = collections.OrderedDict()
        
        for xxid, title, content, author in Finder:
            self.Templates[title] = content
            
        keys = self.Templates.keys()
        
        self.listbox.InsertItems(keys, 0)
    
    
    def Jump(self, evt=None):
        self.director = None
        try:
            ss = self.pending.get_nowait()
            if self.Timer.IsRunning():
                self.Timer.Stop()
        except:
            if not self.Timer.IsRunning():
                self.Timer.Start(500)
            return
        
        self.Mail = ss.Mail
        
        self.MailRecords = ss.Mail.mailRecs
        self.Orders = ss.Orders
        
        self.BuildComplexObject()
        self.selectedData = self.selectedLv = self.selectedOrderObject = self.SelectedTemplate = ''
        self.refund_orderSelector.Clear()
        #self.refund_orderSelector.SetValue('')
        
        self.ShowMails()
        self.ShowOrders()
        self.ShowRefundRecs()
        self.director = Director(self.openerX)
        if evt:
            evt.Skip()
        
    
    def ShowRefundRecs(self):
        filename = 'blank.htm'
        URL = '%s%s%s' % (os.getcwd(), os.sep, filename)
        self.rWV.LoadURL(URL) 
        
        if not self.Orders:
            return
        filename = 'rt.htm'
        with open(filename, 'r') as fp:
            filecontent = fp.read()
            filecontent = filecontent.decode('utf-8', 'ignore')
        
        rendered = Template(filecontent).render(ss=self.Orders[0])
        
        newfile = 'rfn.htm'
        with open(newfile, 'w') as fp:
            fp.write(rendered.encode('utf-8', 'ignore'))
 
        URL = '%s%s%s' % (os.getcwd(), os.sep, newfile)
        
        self.rWV.LoadURL(URL)        
        
    def ShowOrders(self):
        
        self.tree.DeleteRoot()
        cCount = self.tree.GetColumnCount()
        for i in range(cCount):
            self.tree.RemoveColumn(0)
            
         
        #0   
        self.tree.AddColumn(u"交易")
        #1
        self.tree.AddColumn(u"发起日期")
        #2
        self.tree.AddColumn(u"总退款金额")
        #3
        self.tree.AddColumn(u"交易状态")
        #4
        self.tree.AddColumn(u"目的国家")
        #5
        self.tree.AddColumn(u"发货订单数")
        #6
        self.tree.AddColumn(u"交易金额")
        #7
        self.tree.AddColumn(u"其他 3")
        
        self.tree.SetMainColumn(0) 
        self.tree.SetColumnWidth(0, 175)        

        
        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        fldridx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        fileidx     = il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        smileidx    = il.Add(images.Smiles.GetBitmap())

        self.tree.SetImageList(il)
        self.il = il
        
        self.root = self.tree.AddRoot("The Root Item")
        count = 0
        #Complex Object
        for order in self.Orders:
            this_paypal = order.paypal_code
            ppnode = self.treeFindNodeByData(this_paypal)
            if not ppnode:
                count += 1
                ppnode = self.tree.AppendItem(self.root, u'交易 %s'%count)
                self.tree.SetItemPyData(ppnode, ('P', this_paypal))
                self.tree.SetItemText(ppnode, order.import_time, 1)
                self.tree.SetItemText(ppnode, u' 已完成', 3)
                self.tree.SetItemText(ppnode, order.CN_dest, 4)
                self.tree.SetItemText(ppnode, str(order.orderNum), 5)
                
                txt = '%s %s' % (order.currency, order.total_value)
                self.tree.SetItemText(ppnode, txt, 6)                
                
                self.tree.SetItemImage(ppnode, fldridx, which = wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(ppnode, fldropenidx, which = wx.TreeItemIcon_Expanded)
                
            if order.isOngoing:
                self.tree.SetItemText(ppnode, u' 进行中', 3)
                
            ssnode = self.tree.AppendItem(ppnode, order.order)
            self.tree.SetItemPyData(ssnode, ('O', order.order))
            
            if order.HasItem(self.Mail.MAIL_ITEM):
                self.tree.SetItemBackgroundColour(ssnode, 'GREEN')
                if not self.selectedOrderObject:
                    self.selectedOrderObject = order
                    csr = self.refund_currencySelector.FindString(order.currency)
                    if not csr == wx.NOT_FOUND:
                        self.refund_currencySelector.Select(csr)                    
                if not self.refund_orderSelector.GetValue():
                    self.refund_orderSelector.SetValue(order.order)
                    
            self.refund_orderSelector.Insert(order.order, self.refund_orderSelector.GetCount())
            
            self.tree.SetItemImage(ssnode, fldridx, which = wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(ssnode, fldropenidx, which = wx.TreeItemIcon_Expanded)
            
            self.tree.SetItemText(ssnode, order.order_status, 1)
            self.tree.SetItemText(ssnode, order.refund_total, 2)
            self.tree.SetItemText(ssnode, order.middle_time, 3)
            self.tree.SetItemText(ssnode, order.shipped_time, 4)
            self.tree.SetItemText(ssnode, order.tracking_code, 5)
            self.tree.SetItemText(ssnode, order.shipping_method, 6)
            self.tree.SetItemText(ssnode, order.isSentLess, 7)
            
            details = order.details
            
            for item in details:
                dnode = self.tree.AppendItem(ssnode, item.ItemID)
                self.tree.SetItemPyData(dnode, ('I', item.ItemID))
                if item.ItemID == self.Mail.MAIL_ITEM:
                    self.tree.SetItemBackgroundColour(dnode, 'YELLOW')
                
                self.tree.SetItemImage(dnode, fileidx, which = wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(dnode, smileidx, which = wx.TreeItemIcon_Selected)
                
                self.tree.SetItemText(dnode, item.ProductName, 1)
                self.tree.SetItemText(dnode, item.Quantity, 2)
                self.tree.SetItemText(dnode, item.Pattern, 3)
                self.tree.SetItemText(dnode, item.ProductManager, 4)
                self.tree.SetItemText(dnode, order.online_shipping_method, 5)
                self.tree.SetItemText(dnode, item.FromOrder, 6)
                
        self.tree.ExpandAll(self.root)
                

    
    def treeFindNodeByData(self, Data):
        v = self.tree.GetNext(self.root)
        while v:
            pyData = self.tree.GetItemPyData(v)
            
            if pyData:
                Lv, xxx = pyData
                if Data == xxx:
                    return v

            v = self.tree.GetNext(v)
            
        return None
    
    def treeChangeCText(self):
        
        if not self.selectedLv:
            return
        d = {}
          
        
        d['P'] = u'交易,发起日期,总退款金额,交易状态,目的国家,交易金额,其他 2,其他 3'.split(',')
        d['O'] = u'订单,订单状态,OA退款标识,交寄日期,发货日期,跟踪,发货方式,是否少发'.split(',')
        d['I'] = u'物品ID,名称,数量,型号,产品经理,在线邮寄方式,来源'.split(',')
        
        current = d[self.selectedLv]
        
        for p in range(len(current)):
            txt = current[p]
            self.tree.SetColumnText(p, txt)
            
    def treeOnSelChanged(self, evt=None):
        
        if evt:
            item = evt.GetItem()
            if item:
                self.tree.Expand(item)
                pyData = self.tree.GetItemPyData(item)
                if not pyData:
                    return
                
                lv, data = pyData

                for ss in self.Orders:
                    if ss.order == data:
                        self.selectedOrderObject = ss
                
                
                self.selectedLv = lv
                self.selectedData = data
                self.Render()
                self.treeChangeCText()
                
                evt.Skip()
    
                       
    def ShowMails(self):
        
        self.xNote.DeleteAllPages()

        MailRecords = self.MailRecords
        
        #for i in self.wvs:
            #i.Destroy()
            
        #The webview was destoryed since we deleted all pages
        
        self.wvs = []
        
        count = 0
        for response, flag in MailRecords:
            count += 1
            filename = 'm%s.htm' % count
            wv = webview.WebView.New(self.xNote)
            wv.Bind(webview.EVT_WEBVIEW_NAVIGATING, self.OnWebViewNavigating)
            self.wvs.append(wv)
            response = '''<meta charset="utf-8">\n''' + response
            if flag == 'R':
                self.xNote.AddPage(wv, u' Received ')
            else:
                self.xNote.AddPage(wv, u' Sent ')

            with open(filename, 'w') as fp:
                fp.write(response)
                
            URL = '%s%s%s' % (os.getcwd(), os.sep, filename)
            
            wv.LoadURL(URL)

        
    def OnWebViewNavigating(self, evt):
        URL = evt.GetURL()
        if URL.startswith('http'):
            evt.Veto()
            webbrowser.open_new_tab(URL) 
                               
        

    def BuildComplexObject(self):
        refundRecs = []
        orderNum = 0
        thisRefund = 0
    
        for ss in self.Orders:
            refundRecs.extend(ss.refundStatus)
            if len(ss.details) > 0:
                orderNum += 1
                
        for ss in self.Orders:
            ss.refundRecs = refundRecs
            ss.orderNum = orderNum
            ss.thisRefund = thisRefund
            ss.mergeINPLACE(self.Mail)
            
   

        
class TemplateFetcher(object):
    def __init__(self, XXX, callback):
        self.XXX = XXX
        self.callback = callback
    
    def run(self):
        opener = self.XXX.get()
        Finder = oa.actions.OA_MAIL_TEMPLATES_FINDER(opener)
        wx.CallAfter(self.callback, Finder)
        
class FirstBlade(object):
    def __init__(self, XXX, callback, who, account):
        self.who = who
        self.account = account
        self.XXX = XXX
        self.callback = callback
    
    def run(self):
        opener = self.XXX.get()
        Finder = oa.actions.OA_MAIL_INBOX_GET_FINDER(opener, self.who, self.account)
        wx.CallAfter(self.callback, Finder)
        
class RobotFetcher(object):
    def __init__(self, XXX, mailInfo, store, account, callback):
        self.mailInfo = mailInfo
        self.XXX = XXX
        self.store = store
        self.account = account
        self.callback = callback
        
    def run(self):
        opener = self.XXX.get()
        buyer = self.mailInfo.MAIL_BUYER
        store = self.store
        account = self.account
        
        
        mailRecs = oa.actions.OA_QUERY_MAIL_RECORDS(opener, buyer, account)
        Orders = oa.actions.OA_ORDER_GET_ALL_ORDERS_IN_FULL(opener, buyer,  store)
        
        ss = Struct()
        ss.Mail = self.mailInfo
        ss.Mail.mailRecs = mailRecs
        ss.Orders = Orders

        wx.CallAfter(self.callback, ss)
        
      
        
class LazyAction(object):
    def __init__(self, XXX):
        self.XXX = XXX
        self.chain = []
        self.opener = None
    
    def dump(self, asUnicode=True):
        #create a new list object
        chain = list(self.chain)
        if asUnicode:
            return unicode(chain)
        return chain
    
    def clean_dump(self, asUnicode=True):
        chain = self.dump(asUnicode)
        self.chain = []
        return chain
    
    def load(self, chain):
        #create a new list object
        chain = list(chain)
        self.chain = chain
    
    def pre_running(self):
        self.opener = self.XXX.get()
        
class Director(LazyAction):
    def __init__(self, XXX):
        LazyAction.__init__(self, XXX)
    
    def log(func):
        def wrapper(self, *args, **kw):
            func_name = func.__name__
            rec = func_name, args, kw
            self.chain.append(rec)
            return func(self, *args, **kw)
        return wrapper    
    

    def run(self):
        
        err_recs = []
        chain = self.clean_dump(False)
        
        for func_name, args, kw in chain:
            func = getattr(self, func_name)
            result = func(*args, **kw)()
            
            try:
                print(func_name)
                print(args, kw)
            except:
                pass
            
            if not result in [True, '[SUCCESS]', 1]:
                print(rec)
                err_recs.append(rec)

                

        if len(err_recs) == 0:
            logger.info('~No Error')
        else:
            logger.warning(err_recs)
            logger.warning(self.dump())
                
                 
    @log
    def ChangeComment(self, order, newComment):
        opener = self.opener        
        order=str(order)
        return lambda: oa.actions.OA_ORDER_CHANGE_COMMENT_AREA(opener, order, newComment)      
    
    @log
    def ReplyMail(self, mail_id,content,receiver, forceReply=False):
        opener = self.opener
        return lambda: oa.actions.OA_MAIL_REPLY_MAIL(opener, 
                                                     mail_id, 
                                                     content, 
                                                     receiver,
                                                     forceReply)
        
    @log
    def MoveOrder(self, order, to):
        opener = self.opener
        return lambda: oa.actions.OA_ORDER_MOVE_TO(opener,
                                                   order, 
                                                   to)
    @log
    def InterceptOrder(self, order, reason):
        opener = self.opener
        return lambda: oa.actions.OA_INTERCEPT_ORDER(opener,
                                                     order, 
                                                     reason)        
    @log
    def RefundOrder(self, order, amount, currency, reason_TYPE, reason_CN, \
                    reason_EN, existed=False, PayPalAcc=None, useSAFE=True, forceSplitted=False):
        
        opener = self.opener
        if useSAFE:
            return lambda:oa.actions.OA_REDUND_SAFE(opener,
                                                    order, 
                                                    amount, 
                                                    currency, 
                                                    reason_TYPE, 
                                                    reason_CN, 
                                                    reason_EN, 
                                                    existed, 
                                                    PayPalAcc, 
                                                    forceSplitted)
        else:
            return lambda:oa.actions.OA_REFUND_CREATE_NEW(opener, 
                                                          order, 
                                                          amount, 
                                                          currency, 
                                                          reason_TYPE, 
                                                          reason_CN, 
                                                          reason_EN, 
                                                          existed, 
                                                          PayPalAcc) 
        
 

 
class OPENER_X(object):
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.lock = threading.Lock()
        self.opener = None
    
    def get(self):
        self.lock.acquire()
        if self.opener:
            self.lock.release()
            return self.opener

        user = self.user
        password = self.password
        
        self.opener = oa.actions.LoginOA(user, password)
        self.lock.release()
        return self.opener
    
class Worker(threading.Thread):
    def __init__(self, task_queue):
        self.task_queue = task_queue
        threading.Thread.__init__(self)
        self.setDaemon(True)
       
        
    def run(self):
        while True:
            task = self.task_queue.get(block=True)
            pre_running = getattr(task, 'pre_running', None)
            run_func = getattr(task, 'run', None)
            after_running = getattr(task, 'after_running', None)
            try:
                if pre_running:
                    pre_running()
                if run_func:
                    run_func()
                if after_running:
                    after_running()
            except:
                logger.exception('')
                print('Caused an exception in worker')
                


class FrmAskPassword(wx.MiniFrame):
    def __init__(
        self, parent, title, callback, pos=wx.DefaultPosition, size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE 
        ):

        wx.MiniFrame.__init__(self, parent, -1, title, pos, size, style)
        self.callback = callback
        self.CreateControls()


    def OnCloseMe(self, event):
        L = self.I1.GetValue(), self.I2.GetValue(), self.I3.GetValue(), self.I4.GetValue(), self.I5.GetValue()
        
        wx.CallAfter(self.callback, *L)
                      
        self.Close(True)
        
    
    def CreateControls(self):
        panel = wx.Panel(self, -1)

        button = wx.Button(panel, -1, u"好")
        OA_L1 = wx.StaticText(panel, -1, u"OA 用户")
        OA_L2 = wx.StaticText(panel, -1, u"OA 密码")
        
        self.I1 = OA_I1 = wx.TextCtrl(panel, -1, "610591830@qq.com")
        self.I2 = OA_I2 = wx.TextCtrl(panel, -1, "topsecrett1")
        
        OA_L3 = wx.StaticText(panel, -1, u"店铺名称")
        OA_L4 = wx.StaticText(panel, -1, u"企业邮箱")
        self.I3 = OA_I3 = wx.TextCtrl(panel, -1, "homesale_estore")
        self.I4 = OA_I4 = wx.TextCtrl(panel, -1, "batterysalesonline@fivestarslike.com")
        
        OA_L5 = wx.StaticText(panel, -1, u"邮件处理人")
        self.I5 = OA_I5 = wx.TextCtrl(panel, -1, u"陈成")
       
        
        z = wx.GridBagSizer(hgap=5, vgap=5)
        
        z.Add(button, (0, 0))
        
        z.Add(OA_L1, (0, 1))
        z.Add(OA_L2, (0, 2))
        z.Add(OA_I1, (1, 1))
        z.Add(OA_I2, (1, 2))
        
        z.Add(OA_L3, (0, 4))
        z.Add(OA_L4, (0, 5))
        z.Add(OA_I3, (1, 4))
        z.Add(OA_I4, (1, 5))
        
        z.Add(OA_L5, (0, 6))
        z.Add(OA_I5, (1, 6))
        
        panel.SetSizer(z)
        self.SetClientSize(panel.GetBestSize())
        
        self.Bind(wx.EVT_BUTTON, self.OnCloseMe, button)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)        
        

    def OnCloseWindow(self, event):
        print "OnCloseWindow"
        self.Destroy()    





class App(wx.App):

    def OnInit(self):
        self.frame = MainFrame(parent=None, ID=-1, title='prototype')
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True
    
    
app = App()
#redirect = 1, filename = 'wxLog.txt'
app.MainLoop()
