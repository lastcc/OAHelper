# -*- coding: utf-8 -*-
import re 
import urllib
import urllib2
import json
from bs4 import BeautifulSoup
from tinyhttp import Chrome as Firefox

from log_config import logger
import models
import const

logger.info('in actions')


class UnexpectedResponse(StandardError):
    pass

        
def _encode(data,encoding=None):
    if not encoding:
        encoding= const.default_encoding
    if not isinstance(data,unicode):
        raise ValueError('This is not unicode %r'%type(data))
    try:
        encoded_data = data.encode(encoding=encoding,errors='replace')
        return encoded_data
    except:
        logger.exception('ERROR. can not encode this unicode string')
        import sys
        sys.exit(1)
        
def JavaEscaper(char):
    """Some of the pairs were deleted
       This is just incomplete."""
    
    secrets = {'!': '%21', ' ': '%20', '#': '%23', '"': '%22', '%': '%25',
               '$': '%24', "'": '%27', '&': '%26', ')': '%29', '(': '%28',
               ',': '%2C', ';': '%3B', '=': '%3D', '<': '%3C', '?': '%3F',
               '>': '%3E', '[': '%5B', ']': '%5D', '\\': '%5C','^': '%5E',
               '{': '%7B', '}': '%7D', '|': '%7C', '~': '%7E'}
    
    return secrets.get(char, char)

def HackedEscape(string):
    hack_key = '\n'
    hack_val = '<br/>'
    string = string.replace(hack_key, hack_val)
    
    escaped = map(JavaEscaper, string)
    escaped = ''.join(escaped)
    return escaped
    
def _is_valid_order(order):
    valid_order_length = const.valid_order_length
    
    if not (order.startswith('A') and len(order)==valid_order_length):
        logger.debug('ORDER NUMBER INCORRECT [%r]' % order)
        raise ValueError('ORDER NUMBER INCORRECT [%r]' % order)
    else:
        return order


def LoginOA(user, password):
    import cookielib
    url='http://banggood.sellercube.com/Start/Login'
    form = {'email': user,
            'password': password,
            'rememberMe': 'true'}

    cookie_jar=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)) 

    response=Firefox(opener).post(url=url,form=form, encode_to='gbk')
    print(response)

    return opener    

def OA_INTERCEPT_ORDER(opener, order, reason):
    
    assert isinstance(reason, unicode), 'Need unicode'

    encoded_reason=_encode(reason)
    
    url='http://banggood.sellercube.com/Order/RequestBlockSet?Length=15'
    form={'state': '',
          'BlockReason': encoded_reason,
          'orderIDs': order}
    
    response=Firefox(opener).post(url, form)
    ok_mark = u'self.parent.tb_remove()'
    if ok_mark in response:
        return True
    else:
        return False
    
def OA_MAIL_INBOX_GET_FINDER(opener, who=u'', account=''):
    
    assert isinstance(who, unicode)
    if account:
        assert '@' in account
    
    who = _encode(who)
    
    url='http://banggood.sellercube.com/MailReceived/Grid?folderId='
    #XXXXX
    form={'IsOver': '',
          'Category': '',
          'search': '',
          'rp': '20',
          'sortname': 'ReceiveTime',
          'isNew': 'all',
          'productManagerId': '0',
          'searchField': '',
          'toEmail': account,
          'isIsRead': '',
          'dispatchUserName': who,
          'ProductSpeciale': '0',
          'sortorder': 'asc',
          'beginTime': '',
          'timeField': '',
          'query': '',
          'endTime': '',
          'qtype': '',
          'page': '1',
          'isReplay': '0'}
    
    
    response=Firefox(opener).post(url=url, form=form,max_try_times=7) 
    
    J=json.loads(response)
    
    Finder = models.MailInboxFinder(J)

    return Finder

def OA_REFUND_QUERY_BY_ORDER(opener, order, phase=None):
    if not phase in ['confirmed', 'unconfirmed', 'finished', None]:
        raise ValueError('Phase not correct!')
    order = _is_valid_order(order)
    d = {}
    url = 'http://banggood.sellercube.com/Refund/ListFinished'
    form = {'orderID': order,
            'StandardCode': '',
            'PaypalTransactionIdIsNull': '',
            'endDate': '',
            'startDate': '',
            'ProcessCenter': '',
            'X-Requested-With': 'XMLHttpRequest',
            'ddOrderTypes': '',
            'ProblemType': '',
            'sord': 'asc',
            'paymentType': '',
            'PorductManager': '0',
            'ProductSpeciale': '',
            'sidx': 'Amount',
            'createUser': '',
            'SalePlatform': '',
            'flytUserID': '',
            'ListPaypalNames': ''}
    
    d['finished'] = (url, form)
    
    url = 'http://banggood.sellercube.com/Refund/ListIndex'
    form = {'orderID': order,
            'startDate': '',
            'endDate': '',
            'ProblemType': '',
            'paymentType': '',
            'X-Requested-With': 'XMLHttpRequest',
            'CreateUser': '',
            'flytUserID': '',
            'ListPaypalNames': ''}
    
    d['unconfirmed'] = (url, form)
    
    url = 'http://banggood.sellercube.com/Refund/ListApproved'
    form = {'orderID': order,
            'startDate': '',
            'endDate': '',
            'sidx': 'Amount',
            'sord': 'asc',
            'paymentType': '',
            'X-Requested-With': 'XMLHttpRequest',
            'CreateUser': '',
            'flytUserID': '',
            'ListPaypalNames': ''}
    d['confirmed'] = (url, form)
    
    if not phase:
        z = []
        for phase in ['confirmed', 'unconfirmed', 'finished']:
            url, form = d[phase]
            
            response = Firefox(opener).clean_post(url=url, form=form, max_try_times=7)
            soup = BeautifulSoup(response)
            
            L = models.bulid_refund_info(soup, phase)
            z.extend(L)
        return z
    
    else:
        url, form = d[phase]
        
        response = Firefox(opener).clean_post(url=url, form=form, max_try_times=7)
        soup = BeautifulSoup(response)
        
        L = models.bulid_refund_info(soup, phase)
        
        return L        
            

def OA_REFUND_CHECK_STATUS(opener, order, key=None):
    url = 'http://banggood.sellercube.com/Refund/GetOrderCurrency'
    form = {'OrderID': order}
    
    response = Firefox(opener).post(url=url, form=form, max_try_times=6)
    
    J = json.loads(response)
    
    IsRepeatedSent= J['IsRepeatSent']
    Total = J['TotalAmount']
    Currency = J['Currency']
    IsRefundedBefore = J['IsRefunded']
    PaypalName = J['PaypalName']
    
    if key:
        index = 'IsRepeatedSent, Total, Currency, IsRefundedBefore, PaypalName'.split(', ').index(key)
        return [IsRepeatedSent, Total, Currency, IsRefundedBefore, PaypalName][index]

    return IsRepeatedSent, Total, Currency, IsRefundedBefore, PaypalName
    
def OA_REDUND_SAFE(opener, order, amount, currency, reason_TYPE, reason_CN, \
                   reason_EN, existed=False, PayPalAcc=None, forceSplitted=False):
    
    IsRepeatedSent, Total, Currency, refunded, PaypalName = OA_REFUND_CHECK_STATUS(opener, order)
    
    if isinstance(amount, (str, unicode)):
        amount = float(amount)    
    
    if refunded:
        return '[Refunded Before]'
    
    if not forceSplitted:
        Finder = OA_ORDER_QUERY_ORDER_BY_ORDER(opener, order)

        pc = Finder.get_order_object(order).paypal_code
        
        x = OA_ORDER_QUERY_ORDER_BY_PAYPAL(opener, pc)
        if x.total > 1:
            return '[Splited Order]'

    if not currency:
        if Currency:
            currency = Currency
            
    if Currency and not currency == Currency:
        currency = Currency
        
    if Total > 0 and amount > Total:
        raise ValueError('Incorrect refund amount: %r'%amount)
    
    if PaypalName and '@' in PaypalName:
        PayPalAcc = PaypalName
 
    return OA_REFUND_CREATE_NEW(opener, order, amount, currency, reason_TYPE, 
                                reason_CN, reason_EN, 
                                existed, 
                                PayPalAcc)    
        
    
    
def OA_REFUND_CREATE_NEW(opener, order, amount, currency, reason_TYPE, reason_CN, reason_EN, existed=False, PayPalAcc=None):
    
    if isinstance(amount, (str, unicode)):
        amount = float(amount)
    
    min_amount= const.min_amount
    max_amount= const.max_amount
    
    if PayPalAcc == None:
        IsRepeatedSent, Total, Currency, refunded, PaypalName = OA_REFUND_CHECK_STATUS(opener, order)
        PayPalAcc = PaypalName
    
    if existed:
        exist_code=1
    else:
        exist_code=0
        
    order=_is_valid_order(order)

    if not min_amount<amount<max_amount:
        raise ValueError('Amount not ok %r' % amount)
    
    if not isinstance(reason_CN, unicode):
        raise ValueError('Encoding Not Unicode %r' % type(reason_CN))
    
    assert currency, 'Currency not ok: %r' % currency
    
    if PayPalAcc:
        assert '@' in PayPalAcc, 'Not a valid PayPal account'
    
    encoded_reason_CN = _encode(reason_CN)
    
    url='http://banggood.sellercube.com/Refund/Add?keepThis=true&'
    form={'OrderID':order,
          'Amount':amount,
          'Currency':currency,
          'OrderProblemType':reason_TYPE,
          'Reason':encoded_reason_CN,
          'ReasonEn':reason_EN,
          'isOrderExist':exist_code,
          'PaypalName':PayPalAcc}
    
    response=Firefox(opener).post(url, form,max_try_times=1)
    
    if not response:
        logger.warning('Response is None')
        
    ok_mark=u'success'
    
    if ok_mark in response:
        logger.info('success')
        return '[SUCCESS]'
    else:
        logger.debug('[Failed?] %r' % order)
        return '[FAILED]'
        

def OA_CHECK_IF_TALKED(opener, buyer, account):
    url='http://banggood.sellercube.com/MailReceived/SearchGrid'
    form={'Category': '',
          'searchStr': 'FromEbayUser',
          'search': buyer,
          'rp': '20',
          'sortname': 'ReceiveTime',
          'toEmail': account,
          'sortorder': 'DESC',
          'query': '',
          'endTime': '',
          'qtype': '',
          'page': '1',
          'beginTime': ''}
    
    
    response=Firefox(opener).post(url, form, max_try_times=3)
    
    J = json.loads(response)
    
    Finder = models.MailRecordsFinder(J)
    
    if Finder.total > 0:
        return True
    return False

    
def OA_NEED_CARE_FIND_BUYER(opener,store):
    '''This is buggy'''
    store='842'
    
    url='http://banggood.sellercube.com/eBayCaseAttempt/Grid'
    form={'ItemID': '',
          'rp': '300',
          'sortname': 'ImportTime',
          'Site': '',
          'DispatchUserID': '0',
          'sortorder': 'desc',
          'eBayName': store,
          'IsRespone': '0',
          'BuyerUserID': '',
          'query': '',
          'TurnOverUser': '',
          'qtype': '',
          'page': '1'}
    
    response=Firefox(opener).post(url, form)
    
    #id
    #item
    #buyer
    
    RE=re.compile(r'"id":"(\w*?)","cell":\["homesale_estore","(\d*?)",".*?",".*?",".*?","(.*?)"')


    RLT=RE.findall(response)
    
    logger.info(str(RLT))
    
    return RLT
    

def OA_NEED_CARE_SET_OK(opener,rid):
    '''Here is buggy'''
    url='http://banggood.sellercube.com/eBayCaseAttempt/IsResponedUser?ids=%s' % rid
    form={}
    response=Firefox(opener).post(url, form,max_try_times=3)
    ok_mark=u'设置已回复成功'
    if ok_mark in response:
        return True
    else:
        return False



def OA_QUERY_MAIL_RECORDS_GET_FINDER(opener, buyer, account):
    
    assert '@' in account,'Incorrect Mail Address'
         
    url='http://banggood.sellercube.com/MailReceived/SearchGrid'
    form={'Category': '',
          'searchStr': 'FromEbayUser',
          'search': buyer,
          'rp': '300',
          'sortname': 'ReceiveTime',
          'toEmail': account,
          'sortorder': 'DESC',
          'query': '',
          'endTime': '',
          'qtype': '',
          'page': '1',
          'beginTime': ''}
    
    response=Firefox(opener).post(url=url, form=form, max_try_times=10)
    
    J=json.loads(response)
    
    Finder = models.MailRecordsFinder(J)
    
    return Finder

def OA_QUERY_MAIL_RECORDS_GET_RESULT(opener, Finder):
    #z=(this_id,link,title,timestamp,who)
    L=[]
    for rec in Finder:
        this_id, link, title, sender, receiver, time, sent, responder = rec
        
        response=Firefox(opener).get(url=link,max_try_times=6, encode_to='utf-8')
        
        if 'R' in this_id:
            #Received from eBay, html
            
            L.append((response, 'R'))
        else:
            #Sent from OA
            L.append((response, 'S'))
    
    return L

def OA_QUERY_MAIL_RECORDS(opener,buyer,account):
    Finder=OA_QUERY_MAIL_RECORDS_GET_FINDER(opener, buyer,account)
    
    return OA_QUERY_MAIL_RECORDS_GET_RESULT(opener, Finder)
    

def OA_MAIL_REPLY_MAIL(opener,mail_id,content,receiver, forceReply=False):
    
    if forceReply:
        replied = False
    else:
        replied = OA_MAIL_IS_MAIL_REPLIED(opener, mail_id)
        
    if replied:
        raise ZeroDivisionError('This mail had already been replied.')
    
    assert '@' in receiver, 'Incorrect Receiver %r' % receiver
    
    url='http://banggood.sellercube.com/MailSend/ReplyContent'
    
    if isinstance(content, unicode):
        content=_encode(content)
        
    content = HackedEscape(content)
    
    form={'receivedId':mail_id,
          'replyContent':content,
          'toEmail':receiver}
    
    response=Firefox(opener).post(url=url,form=form,max_try_times=4)
    
    if u'已发送成功' in response:
        return True
    
    return False
    
    
    
def OA_MAIL_IS_MAIL_REPLIED(opener,mail_id):
    url='http://banggood.sellercube.com/MailReceived/IsReplied'
    
    form={'id':mail_id}
    
    response=Firefox(opener).post(url=url, form=form, max_try_times=4)
    
    J=json.loads(response)
    
    if J==True:
        isreplied=True
    elif J==False:
        isreplied=False
    else:
        raise ValueError('Unexpected response')

    return isreplied



def OA_ORDER_QUERY_ORDER(opener, search_key, search_field='', store=''):
    if not search_field:
        if '@' in search_key:
            search_field = const.FIELD_EMAIL
        elif ' ' in search_key:
            search_field = const.FIELD_RECEIVER
        elif len(search_key) == 17:
            search_field = const.FIELD_PAYPAL
        elif len(search_key) == const.valid_order_length:
            search_field = const.FIELD_ORDER
        elif (search_key[:2].isalpha() and search_key[-2:].isalpha())\
             and (search_key[:2].isupper() and search_key[-2:].isupper()):
            search_field = const.FIELD_TRACKING
        else:
            search_field = const.FIELD_BUYER

    url='http://banggood.sellercube.com/order/ListGridMore?state=all&setting=&isIndexRequest=1'
    form={'search': search_key,
          'rp': '300',
          'sortname': '[state]',
          'isComplain': '是否投诉',
          'productManagerId': '0',
          'searchField': search_field,
          'FlytInCompany': '',
          'productSpecialeId': '0',
          'countrys': '',
          'processCenterID': '',
          'sortorder': 'asc',
          'postTypeID': '',
          'query': '',
          'qtype': '',
          'page': '1',
          'shopName': store}
    
    response=Firefox(opener).post(url=url,form=form,max_try_times=10)
    
    J=json.loads(response)
    
    Finder = models.SearchResultFinder(J)
    
    return Finder    
    
    
            
def OA_ORDER_QUERY_ORDER_BY_BUYER(opener, buyer,store=''):
    search_key = buyer
    search_field = const.FIELD_BUYER
    return OA_ORDER_QUERY_ORDER(opener, search_key, search_field, 
                               store)
    

def OA_ORDER_QUERY_ORDER_BY_PAYPAL(opener, PayPal,store=''):
    search_key = PayPal
    search_field = const.FIELD_PAYPAL
    return OA_ORDER_QUERY_ORDER(opener, search_key, search_field, 
                               store)    
    
def OA_ORDER_QUERY_ORDER_BY_ORDER(opener, order,store=''):
    search_key = order
    search_field = const.FIELD_ORDER
    return OA_ORDER_QUERY_ORDER(opener, search_key, search_field, 
                               store)       


def OA_ORDER_GET_ORDER_INFO(opener, order):
    order=_is_valid_order(order)
    
    def tag_filter(tag):
        if tag.name=='td' and tag.get('class')==['category'] and not tag.next_element.name in['select','input']:
            return True
        
        if tag.has_attr('selected') and tag['selected']=='selected':
            return True
       
        if tag.name=='input' and tag.get('type')=='text':
            print tag.get('value')
            tag.string=tag.get('value')
            return True    
    
    url='http://banggood.sellercube.com/BillDetail/index?id=%s' % order
    
    response=Firefox(opener).clean_get(url=url,max_try_times=6)
    
    soup=BeautifulSoup(response)
    
    resultset=soup.find_all(tag_filter)
    
    ss = models.build_order_info_object(SoupResultSet=resultset, order=order)
    
    return ss
    

def OA_ORDER_GET_ORDER_DETAIL_LIST(opener, order):
    order=_is_valid_order(order)
    
    url='http://banggood.sellercube.com/BillDetail/GetOrderDetailById'
    form={'orderId':order}
    
    response=Firefox(opener).post(url=url,form=form,max_try_times=6)
    
    soup=BeautifulSoup(response)
    
    L = models.build_order_detail_containers(soup)
        
    return L

def OA_ORDER_GET_ORDER_HISTORY(opener,order):
    url='http://banggood.sellercube.com/BillDetail/ViewOperationalHistory'
    form={'orderId':order}
    
    response=Firefox(opener).post(url=url,form=form,max_try_times=6)
    
    if 'noData' in response:
        return None
    
    J=json.loads(response)
    
    return J



def OA_OEDER_GET_ORDER_IN_FULL(opener,order,need_history=True, refundStatus=True, SearchResultFinder=None):
    
    if not SearchResultFinder:
        SearchResultFinder = OA_ORDER_QUERY_ORDER_BY_ORDER(opener, order)
        
    if not order in SearchResultFinder.find_all_orders():
        SearchResultFinder = OA_ORDER_QUERY_ORDER_BY_ORDER(opener, order)

    info_obj_X = SearchResultFinder.get_order_object(order)
    info_obj_Y = OA_ORDER_GET_ORDER_INFO(opener, order)
    
    merged_info = models.Struct().mergeXYZ(info_obj_X, info_obj_Y)
    
    details = OA_ORDER_GET_ORDER_DETAIL_LIST(opener, order)
    
    if need_history:
        history=OA_ORDER_GET_ORDER_HISTORY(opener, order)
    else:
        history=False
        
    IsRepeatedSent, Total, Currency, refunded, PaypalName = OA_REFUND_CHECK_STATUS(opener, order)
    
    merged_info.total_value = str(Total)
    merged_info.currency = Currency
    
    if refundStatus:
        X = OA_REFUND_QUERY_BY_ORDER(opener, order, None)
        amount = 0.0
        for each in X:
            try:
                amount -= float(each.amount)
                each.transaction_total = Total
            except:
                logger.exception('Err')
                amount = '[Error Occured]'
                break
            
        amount = str(amount)
            
            
        merged_info.refund_total = amount
            
        merged_info.refundStatus = X
        

    else:
        merged_info.refund_total = -1.0
            
        merged_info.refundStatus = []

    merged_info.details = details
    merged_info.history = history
    logger.debug(merged_info.__dict__)

    z = models.X().mergeINPLACE(merged_info)
    logger.debug(z.__dict__)
    
    return z

    

def OA_ORDER_GET_ALL_ORDERS_IN_FULL(opener, buyer, store='',callback=None,need_history=True):
    Finder = OA_ORDER_QUERY_ORDER_BY_BUYER(opener, buyer, store)
    
    orders = Finder.find_all_orders()
    
    if Finder.total > 120:
        if callback:
            callback()
            return None
        else:
            print('too many orders')

    L=[]
    
    for order in orders:
    
        z=OA_OEDER_GET_ORDER_IN_FULL(opener, order, need_history, SearchResultFinder=Finder)
        
        L.append(z)
    
    #Sort the result:
    
    def f(x, y):

        
        if x.paypal_code == y.paypal_code:
            if x.import_time < y.import_time:
                return -1
            elif x.import_time > y.import_time:
                return 1
            else:
                return 0
        else:
            return 0
            
    
    L = sorted(L, key=lambda x:x.paypal_code)
    L = sorted(L, cmp=f)
    print L
    logger.debug(L)
    
    #L.sort(cmp=f, key=lambda x:x.paypal_code, reverse=True)
    
    return L
        


def OA_ORDER_CONTACT_BUYER(opener, order, text):
    base_url = 'http://banggood.sellercube.com/Order/ContactBuyer?orderId=<ph>'\
               '&contactProgressc=%E6%9C%AA%E8%81%94%E7%B3%BB&keepThis=true&'
    
    url = base_url.replace('<ph>', order)
    if not isinstance(text, unicode):
        raise ValueError('Need unicode')
    
    text = _encode(text)
    
    form = {'contactText': text,
            'orderId': order,
            'contactProgressc': '未联系'}
    
    response = Firefox(opener).post(url=url, form=form, max_try_times=3)
    
    ok_mark = "removeContactBuyer('%s')" % order
    
    if ok_mark in response:
        return True
    else:
        return False
    
def OA_ORDER_CHANGE_COMMENT_AREA(opener, order, newComment):
    url = 'http://banggood.sellercube.com/order/setComfirmerRemarkByCell'
    
    assert isinstance(newComment, unicode), 'need unicode'
    
    newComment = _encode(newComment)
    
    form = {'orderID': order,
            'remark': newComment}
    
    response = Firefox(opener).post(url=url, form=form, max_try_times=3)
    
    J = json.loads(response)
    
    if J['success'] == True:
        return True
    else:
        return False

def OA_ORDER_MOVE_TO(opener, order, to):
    order = _is_valid_order(order)
    url = 'http://banggood.sellercube.com/order/UpdateStatus?status=%s&ids=%s' % (to, order)
    form = {}
    
    response = Firefox(opener).post(url=url, form=form, max_try_times=3)
    
    if 'true' in response:
        return True
    else:
        return False
    
def OA_CONTACT_BUYER_QUERY_NOT_RESPONDED(opener, store):
    contactStatus='2'
    return OA_CONTACT_BUYER_QUERY(opener, store, contactStatus)

def OA_CONTACT_BUYER_QUERY_IN_CONTACTING(opener, store):
    contactStatus='0'
    return OA_CONTACT_BUYER_QUERY(opener, store, contactStatus)
    
    
def OA_CONTACT_BUYER_QUERY(opener, store, contactStatus):

    url='http://banggood.sellercube.com/order/ListGridNew?state=11&setting=&isIndexRequest=1'
    form={'productManagerId': '0',
          'ContactProgress': contactStatus,
          'rp': '300',
          'sortname': '',
          'orderType': '',
          'searchField': 'Id',
          'FlytInCompany': '',
          'HandUser': '',
          'productSpecialeId': '0',
          'countrys': '',
          'processCenterID': '',
          'search': '',
          'sortorder': 'asc',
          'postTypeID': '',
          'query': '',
          'qtype': '',
          'page': '1',
          'shopName': store}
    
    response=Firefox(opener).post(url=url, form=form,max_try_times=7) 
    
    J=json.loads(response)
    
    Finder = models.ContactBuyerFinder(J)

    return Finder
    
def OA_CONTACT_BUYER_CHECK_STOCK(opener, order):

    url = 'http://banggood.sellercube.com/order/GetOrderStock'
    form={'ids': order}
    
    response=Firefox(opener).post(url=url, form=form,max_try_times=7) 
    
    if u'不缺货' in response:
        return True
    
    return False

def OA_MAIL_TEMPLATES_FINDER(opener):
    url = 'http://banggood.sellercube.com/MailTemplate/Grid'
    form = {'rp': '300',
            'sortname': 'Title',
            'sortorder': 'asc',
            'query': '',
            'qtype': '',
            'page': '1'}
    
    response = Firefox(opener).post(url=url, form=form, max_try_times=7)
    
    J = json.loads(response)
    
    Finder = models.TemplatesFinder(J)
    
    return Finder
        
        
        
