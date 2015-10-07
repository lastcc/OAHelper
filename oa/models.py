# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from log_config import logger


class Struct(object):
    """
    An object that has attributes built from the dictionary given in 
    constructor. So ss=Struct(a=1, b='b') will satisfy assert ss.a == 1
    and assert ss.b == 'b'.
    """
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
    def __getitem__(self, key):
        return self.__dict__[key]
    
    def get_items(self, keys):
        keys = keys.split('/')
        L = []
        for key in keys:
            value = self.__dict__[key]
            L.append(value)
        return L
    
    def set_items(self, keys, values):
        if isinstance(keys, (unicode, str)):
            keys = keys.split('/')
        if not isinstance(values, (list, tuple)):
            raise ZeroDivisionError('not correct type of values')
        elif not len(keys) == len(values):
            print keys
            print values
            while len(keys) > len(values):
                keys.append('ph')
            while len(values) > len(keys):
                values.append('ph')            
                
            #raise ZeroDivisionError('not the same length')
        d=dict(zip(keys,values))
        self.__dict__.update(d)
        
    def __len__(self):
        return len(self.__dict__)
    
    def __getattr__(self, attr):
        if attr.startswith('get_'):
            name = attr[4:]
            return self.__dict__[name]
        else:
            raise NameError('No such arrribute: %r' % attr)
        
    def mergeXYZ(self, *objects):
        d = {}
        for xxx in objects:
            d.update(xxx.__dict__)
            
        new = self.__class__(**d)
        return new
    
    def mergeINPLACE(self, y):
        dY = y.__dict__
        self.__dict__.update(dY)
        return self
    
    def __add__(self, other):
        if not isinstance(other, Struct):
            return NotImplemented
        d = {}
        d.update(self.__dict__)
        d.update(other.__dict__)

        return self.__class__(**d)
    
    def set_defaults(self, keys, v=''):
        if isinstance(keys, (unicode, str)):
            for k in keys.split('/'):
                self.__dict__[k] = v        


class Finder(object):
    def __init__(self, J):
        self.J = J
        self.rows = J.get('rows', [])
        self.gen = self.generator()
    
    @property
    def JSON(self, J):
        return self.J
    
    @property   
    def total(self):
        return self.J['total']

    def __iter__(self):
        return self
    
    def html_filter(self, html):
        if not html:
            return ''
        soup = BeautifulSoup(html)
        return soup.get_text()
    
    def generator(self):
        rows = self.rows
        
        for row in rows:
            xxID = row['id']
            cell = row['cell']
            cell.insert(0, xxID)
            new = map(self.html_filter, cell)
            yield new
    
    def next(self):
        return self.gen.next()
    
    
class SearchResultFinder(Finder):
    '''JSON Search Result Finder'''
    def find_all_orders(self):
        L=[]
        rows=self.rows
        for row in rows:
            order=row['id']
            L.append(order)
        return L
 
    def get_order_object(self, order):
        rows=self.rows
        ss = Struct()
        
        for rec in Finder(self.J):
            this_order = rec[0]
            if order == this_order:
                keys = 'order/ph/ph/tracking_code/order_error_text/buyer_message/comment_area/paypal_code/buyer/add_email/'\
                       'add_receiver/CN_dest/warehouse/shipping_method/online_shipping_method/store_name/order_status/'\
                       'shipped_time/intercepted_for/import_time'
                values = rec
                ss.set_items(keys, values)
                return ss

    def get_all_order_objects(self):
        L=[]
        for order in self.find_all_orders():
            L.append(self.get_order_object(order))
        return L
    
    def generator(self):
        order_objects = self.get_all_order_objects()

        for each in order_objects:
            yield each


def build_order_info_object(SoupResultSet, order):
    keys = 'order_status/warehouse/shipping_method/add_country/add_st1/add_st2/add_state/add_city/add_receiver/add_phone/add_zip/should_weight/'\
           'add_email/x_remark/comment_area/order_total/paypal_code/user_cookie/order_x_id/tracking_code/actual_weight/CN_shipping_fee/shipped_time/'\
           'store_name/order_error_text/opt_status/buyer_message/online_shipping_method/__place_holder__/ph' 
    
    values=[]
    for tag in SoupResultSet:
        print tag
    
        value=tag.get_text()
        values.append(value)
        
    ss = Struct()
    ss.set_items(keys, values)
    ss.order=order
    ss.add_country = ss.add_country.encode('ascii', 'ignore')
        
    return ss

def build_order_detail_containers(soup):
    areas=soup.find_all('tr')
    
    L=[]
    for area in areas:
        tags=area.find_all('td')
        ss = Struct()
        
        keys = 'ItemID/ProductName/SKU/POA/Position/Quantity/X_Price/ProductStatus/'\
               'Pattern/X_Weight/Y_Weight/ProductManager/TestedBy/FromOrder'
        
        values = []
        for tag in tags:
            value = tag.get_text()
            values.append(value)
            
        ss.set_items(keys, values)
        L.append(ss)

    return L

def bulid_refund_info(soup, phase):
    soup = soup.find('tbody')
    if not soup:
        return []
    areas=soup.find_all('tr')
    
    finished = 'order/amount/currency/reasons/initiator/init_time/confirmed_by/confirm_time/'\
               'completed_by/complete_time/paypal_code/final_amount/final_currency/reason_type/paypal_account'
    
    unconfirmed = 'ph/order/amount/transaction_total/currency/reasons/initiator/init_time/ph/ph/ph/reason_type/paypal_account'
    
    confirmed = 'ph/order/amount/currency/reasons/initiator/init_time/confirmed_by/confirm_time/ph/ph/ph/ph/reason_type/ph/ph'
    
    d = {'finished': finished,
         'unconfirmed': unconfirmed,
         'confirmed': confirmed}
    
    
    L=[]
    for area in areas:
        tags=area.find_all('td')
        ss = Struct()
        default = Struct()
        default.set_defaults(finished)
        default.set_defaults(unconfirmed)
        default.set_defaults(confirmed)
        
        keys = d[phase]
        
        values = []
        for tag in tags:
            value = tag.get_text(strip=True)
            values.append(value)
            
        ss.set_items(keys, values)
        ss.reason_CN, sep, ss.reason_EN = ss.reasons.rpartition('\n')
        
        color = area.get('class', None)
        ss.refund_error = color
        ss.phase = phase
        
        new = default + ss
        L.append(new)

    return L

class MailRecordsFinder(Finder):
    '''This is for Mail Records'''
    
    def find_ids(self):
        L=[]
        rows=self.rows
        for row in rows:
            this_id=row['id']
            L.append(this_id)
            
    def generator(self):
        rows = self.rows
        
        for rec in Finder(self.J):
            this_id, ph, ph, title, sender, receiver, time, sent, responder, X_ID = rec
            link = 'http://banggood.sellercube.com/MailReceived/SearchDetail/%s' % this_id
            
            yield this_id, link, title, sender, receiver, time, sent, responder
            
            
    
class MailInboxFinder(Finder):
    '''This is for Mail Inbox'''
    
    def find_buyers(self):
        L=[]
        rows=self.rows
        for row in rows:
            cell=row['cell']
            buyer=cell[8]
            if buyer in L or not buyer:
                continue
            L.append(buyer)
        return L
    
    def generator(self):
        existed = []
        for rec in Finder(self.J):
            ss = Struct()
            keys = 'MAIL_ID/PH/PH/PH/PH/MAIL_TITLE/MAIL_SENDER/MAIL_RECEIVER/MAIL_ITEM/MAIL_BUYER/MAIL_RESPONDER/'\
                   'MAIL_RECEIVE_TIME/MAIL_DOWNLOAD_TIME/MAIL_FORWARDED_BY/MAIL_FORWARD_TIME/MAIL_FORWARD_COMMENT'
            values = rec
            this_buyer = rec[9]
            if not this_buyer or this_buyer in existed:
                continue
            else:
                existed.append(this_buyer)
                ss.set_items(keys, values)
                yield ss
        

class ContactBuyerFinder(Finder):
    
    def find_buyers(self):
        L=[]
        rows=self.rows
        for row in rows:
            cell=row['cell']
            buyer=cell[10]
            L.append(buyer)
        return L
            
    def generator(self):
        L=[] 

        for rec in Finder(self.J):
            ss = Struct()
            keys = 'order/ph/ph/ph/ph/responder/assign_time/order_error_text/buyer_message/comment_area/paypal_code/buyer/add_email/'\
                   'add_receiver/CN_dest/warehouse/shipping_method/online_shipping_method/store_name/order_status/import_time'
            values = rec
            ss.set_items(keys, values)
            yield ss  
    


class TemplatesFinder(Finder):
    
    def html_filter(self, html):
        if not html:
            return ''
        html = html.replace('<br />', '\n')
        return html

class X(Struct):
    """Full Order Container"""
    
    @property
    def middle_time(self):
        history = self.history
        
        if not history:
            return '[History Not Enabled]'
        
        for x in history:
            who = x['UserId']
            what = x['OperateName']
            text = x['OperateLog']
            status_name = x['StateName']
            time = x['OperateDate']
            orderID = x['OrderId']
            
            if u'已交寄' in status_name:
                return time
        
        return '[Mid-time Not Found]'
    
    @property
    def isSentLess(self):
        def f(x):
            return x.isdigit() or x == '.'
        
        if not self.actual_weight:
            return u'Actual Weight Unknown'
        
        if not self.should_weight:
            return u'Should Weight Unknown'        
        
        actual_float = float(filter(f, self.get_actual_weight))
        should_float = float(filter(f, self.get_should_weight))

        difference = actual_float - should_float
        isless = actual_float < should_float
        percent = (difference) / should_float
        
        if isless:
            return str(percent * 100)
        else:
            return 'ok'
        
    def HasItem(self, itemID):
        for each in self.details:

            if itemID == each.ItemID:
                return True
        
        return False
    
    @property
    def status(self):
        return self.order_status
    
    @property
    def isFinished(self):
        return not self.status in u'待检查/未确认/已拦截/联系客户'
    
    @property
    def isOngoing(self):
        return not self.isFinished
    @property
    def isInterceptable(self):
        return self.status in u'处理中'
        
        
    


        
                
        
 