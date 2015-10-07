# -*- coding: utf-8 -*-
import re 
import urllib
from tinyhttp import Firefox64 as Firefox
from log_config import log
import threading
from bs4 import BeautifulSoup

_lock=threading.Lock()

_Global_Buyer_List=None

class _dummy_lock_cls(object):
    def __init__(self):
        pass
    def acquire(self):
        pass
    def release(self):
        pass

log.info('Enter eBay.py')
_t_lock=threading.Lock()
_dummy_lock=_dummy_lock_cls()

_c_lock=_dummy_lock


def update_lock(d):
    global _c_lock
    if d==True:
        _c_lock=_t_lock
    else:
        _c_lock=_dummy_lock


_eBay_Ctx=None
_encoding='utf-8'
_orderLen=16

class eBayError(StandardError):
    pass


    
    
def _simple_host(URL):
    URL=str(URL)
    L=URL.split('/')[2].split('.')
    if len(L)>2:
        del L[0]
            
    simple_host='.'.join(L)
            
    return simple_host   

def EBAY_SEND_MESSAGE(opener, message,buyer,item):
    '''注意这里的链接，应该传入openers自动匹配'''
    url='http://contact.ebay.com.hk/ws/eBayISAPI.dll?ContactUserNextGen'
    headers={'Referer':'http://contact.ebay.com.hk/ws/eBayISAPI.dll?ContactUserNextGen&iId=%s&recipient=%s'%(item,buyer),
             'Origin':'http://contact.ebay.com.hk'}
    
    form={'imageUrls': '',
          'msg_cnt': message, 
          'cat': '-99',
          'msg_cnt_cnt': message,
          'iId': item,
          'actn': 'submit',
          'ccSender': 'on',
          'recipient': buyer}
    
    ok_mark=u'<title>訊息已寄出</title>'
    
    response=Firefox(opener,c_lock=_c_lock).post(url, form, headers=headers, max_try_times=3)
    
    if ok_mark in response:
        return True
    else:
        return False
    
    
def EBAY_RETURN_IS_NO_NEED_REPLY(openers,return_link):
    url=return_link
    simple=_simple_host(url)
    
    opener=openers.find(url)
    new_url=None
    def callback_f(_url):
        new_url=_url
        return True
        
    headers={
    'Host':'postorder.%s'%simple,
    'Referer':'http://banggood.sellercube.com/ebaycase',
    'Accept-Encoding':'gzip, deflate, sdch',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    
    #decoded response
    response=Firefox(opener,c_lock=_c_lock,redirect_callback=callback_f).get(url,headers=headers)
    
    if new_url:
        log.warning('Redirecting...')
        return EBAY_RETURN_IS_NO_NEED_REPLY(return_link=new_url, openers=openers)
    
    no_need_mark=u'You sent a message'
    
    if no_need_mark in response:
        log.debug('NO  NEED [%s]'%url)
        return True
    else:
        log.debug('YOU NEED[%s]'%url)
        return False
    

def EBAY_GET_FEEDBACKS_BUYER_ITEM_REPLY(opener, store, negative=False):
    headers={'Host':'feedback.ebay.com.hk',
             'Referer':'http://feedback.ebay.com.hk/'}
    if negative:
        which = 'negative'
    else:
        which = 'neutral'
    
    url=['http://feedback.ebay.com.hk/ws/eBayISAPI.dll?',
    'ViewFeedback2&userid=%s&iid=-1&de=off&',
    'items=100&which=%s&interval=30&&page=1']
    url=''.join(url)
    url = url % (store, which)
    REG = r'^(?!%s)' % store
    
    response=Firefox(opener).get(url,headers=headers)
    
    soup = BeautifulSoup(response)
    
    comments=soup('td',class_='fbOuterAddComm',nowrap=False,text=True)
    replies=soup('ul',class_='addlc')
    
    authors=[i.find_next('span',class_='mbg-nw',text=re.compile(REG)) for i in comments]
    items=[i.find_next('a',href=re.compile(r'http://.*?/itm/.*?/\d*')) for i in comments]
    
    authors=map(lambda t:str(t.text), authors)
    items=map(lambda t:re.compile(r'http://.*?/itm/.*?/(\d*)').findall(str(t['href']))[0], items)
    
    comments=map(lambda t:t.text.encode('utf-8','ignore'), comments)
    replies=map(lambda t:t.text.encode('utf-8','ignore'), replies)    

    if len(comments)<10:
        raise ValueError('Too less comments!')
    
    result=zip(comments,replies,authors,items)
    
    return result


def EBAY_CHK_IF_SENT_MSG(opener,buyer):
    _lock.acquire()

    global _Global_Buyer_List


    headers={'Origin':'http://mesgmy.ebay.com.hk',
             'Referer':'http://mesgmy.ebay.com.hk/ws/eBayISAPI.dll?ViewMyMessages&&ssPageName=STRK:MEMM:LNLK&FolderId=1&CurrentPage=MyeBayMyMessagesSent&_trksid=p3984.m2295.l3929'}
    

    url='http://mesgmy.ebay.com.hk/V4Ajax'
    
    form='svcid=MY_MSG_SERVICE&stok=351778162&pId=5039&v=0&reqttype=JSON&resptype=JSON&clientType=Safari:537:&request=%7B%22mode%22%3A12%2C%22currentView%22%3A%22%22%2C%22folderId%22%3A1%7D'
    
    if (not _Global_Buyer_List) or (len(_Global_Buyer_List)<100):
        #need to get buyer list from eBay
        #and store it.
        print('Getting list')
        response=Firefox(opener,c_lock=_c_lock).post(url=url,form=form,headers=headers,encode_to='utf-8',max_try_times=6)  
        _Global_Buyer_List=response   
        print('Getting list [OK]')

    _lock.release()


    if not buyer in _Global_Buyer_List:
        return False
    else:
        return True
    
def EBAY_ORDER_GET_ALL_ORDERS(opener,buyer):
    '''Get all orders of a buyer
    Download the CSV files, and extract the information'''
    
    url=''
    
    form={}
    
    response=Firefox.post(url=url,form=form,max_try_times=6)
    

def EBAY_LEAVE_FEEDBACK(opener, buyer):
    url=['http://k2b-bulk.ebay.com.hk/ws/eBayISAPI.dll?MfcISAPICommand=SalesRecordConsole&',
         'currentpage=SCSold&pageNumber=1&searchField=BuyerId&searchValues=<USER_ID>&StoreCategory=',
         '-4&Status=All&Period=Last122Days&searchSubmit=%E6%90%9C%E5%B0%8B&goToPage='] 
    url=''.join(url)
    url=url.replace('<USER_ID>',buyer)
    
    response = Firefox(opener).get(url=url, max_try_times=10)
    
    soup = BeautifulSoup(response)
    
    tag_a = soup.find_all('a', href=re.compile(r'http://.*?orderid=\d*'))
    
    orderids = map(lambda t:re.compile(r'http://.*?orderid=(\d*)').findall(str(t['href']))[0], tag_a)
    
    orderids = list(set(orderids))
    
    url = 'http://k2b-bulk.ebay.com.hk/ws/eBayISAPI.dll'
    
    base_form = 'MfcISAPICommand=LeaveCustomFeedback&urlstack=5508%7CPeriod_Last122Days%7CsearchField_BuyerId%'\
        '7CpageNumber_1%7Ccurrentpage_SCSold%7CsearchValues_noname%7C&orderid=<place_holder>&commenttype=0'\
        '&commentselected=0&customcomment=&LeaveFeedback=%E7%95%99%E4%B8%8B%E4%BF%A1%E7%94%A8%E8%A9%95%E5%83%B9'
    
    for i in orderids:
        form = base_form.replace('<place_holder>', str(i))
        response = Firefox(opener).post(url=url, form=form, max_try_times=3)
    
    return True
        
        
    