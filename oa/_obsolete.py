def OA_REFUND_FINISHED_REFUND_QUERY_BY_ORDER(order,opener=None):
    '''This func is buggy'''
    
    PAYPAL_N_REFUNDID_PTN=r"<td\sonclick.*?paypal='(\w*?)'\srefundId='(\d*?)'\sorderId='\w*?'>"
    OTHER_INFO_PTN=r'<td.*?>\s*?(.*?)\s*?</td>'
    
    orderLen=16
    if not order.startswith('A') or not len(order)==orderLen:
            raise InvalidOrderNumber('ORDER NUMBER INCORRECT %r' % order) 
        
        
    url='http://banggood.sellercube.com/Refund/ListFinished'
    form={'orderID': order,
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
    
    
    
    response=Firefox(opener).clean_post(url, form)
    
    response=response.replace('  ','')
    response=response.replace('\r\n','')
    
    
    SEARCH_RLT_PAYPAL_N_REFUNDID=re.compile(PAYPAL_N_REFUNDID_PTN).findall(response)
    SEARCH_RLT_OTHER=map(str.strip, re.compile(OTHER_INFO_PTN).findall(response))
    
    
    if not((len(SEARCH_RLT_OTHER)%15)==0):
        raise OABaseError('OA_REFUND_QUERY_BY_ORDER:: NO OK WITH THE RESULT')
    
    if len(SEARCH_RLT_OTHER)==0:
        log.warning('%r'%response)
        return []
    
    Count=0
    Count2=0
    RLT=[]
    PART=[]
    for ech in SEARCH_RLT_OTHER:
        PART.append(ech)
        Count+=1
        if Count==15:
            Count=0
            
            d={}
            
            d['order']=PART[0]
            d['amount']=PART[1]
            d['currency']=PART[2]
            d['reason']=PART[3]
            d['created by']=PART[4]
            d['date']=PART[5]
            d['reviewed by']=PART[6]
            d['done by']=PART[8]
            d['account']=PART[14]
            d['transaction ID']=SEARCH_RLT_PAYPAL_N_REFUNDID[Count2][0]
            d['refund ID']=SEARCH_RLT_PAYPAL_N_REFUNDID[Count2][1]
            
            RLT.append(d)
            PART=[]
            Count2+=1
            
    return RLT

def OA_REFUND_UNCONFIRMED_REFUND_QUERY_BY_ORDER(order,opener=None):
    '''This func is buggy'''
    
    order=_check_order(order)    
    
    url='http://banggood.sellercube.com/Refund/ListIndex'
    
    form={'orderID': order,
          'startDate': '',
          'endDate': '',
          'ProblemType': '',
          'paymentType': '',
          'X-Requested-With': 'XMLHttpRequest',
          'CreateUser': '',
          'flytUserID': '',
          'ListPaypalNames': ''}
    
    
    response=Firefox(opener).clean_post(url, form) 
    response=re.compile(r'<tbody>.*</tbody>').findall(response)[0]
    
    AREA_RE=re.compile(r'<td.*?>\s*?(.*?)\s*?</td>')
    REFUND_ID_RE=re.compile(r'/Refund/Edit/(\d*?)\?keepThis=True')
    
    
    SEARCH_RLT_OTHER=map(str.strip, AREA_RE.findall(response))
    
    splited_list=_split_list(SEARCH_RLT_OTHER,12)
    
    #RID
    
    left=['[]','order','amount','currency','reason','issuer','create_date','[EDIT]','[DEL]','[]','label','account','RID']   
    
    RLT=[]
    
    
    for echRight in splited_list:
        right=[]
        right.extend(echRight)
        right.append(REFUND_ID_RE.findall(right[7])[0])
        
        d=dict(zip(left,right))
        
        RLT.append(d)
        
        
    return RLT
        
    
    
def OA_REFUND_CONFIRMED_REFUND_QUERY_BY_ORDER(order,opener=None):
    '''Not implemented'''
    pass
        
def OA_REFUND_DELETE_REFUND_BY_REFUND_ID(opener, refund_id):
    
    url='http://banggood.sellercube.com/Refund/Remove/%s' % refund_id
 
    response=Firefox(opener).get(url,max_try_times=6)
    
    if response is None:
        return False
    else:
        return True
    

def OA_MAIN_QUEUE_GET_BUYER_LIST(opener, store_name=''):
    '''
    这里还没弄完'''    
    data={'productManagerId': '0',
          'search': '',
          'rp': '300',
          'sortname': '',
          'orderType': '',
          '"page': '1',
          'searchField': 'Id',
          'FlytInCompany': '"',
          'countrys': '',
          'processCenterID': '',
          'sortorder': 'asc',
          'postTypeID': '',
          'query': '',
          'qtype': '',
          'productSpecialeId': '0',
          'shopName': store_name}
    

def OA_RECALL_ORDER_BY_ORDER(opener, order, reason):
    
    
    encoded_reason=_encode(reason)
    
    url='http://banggood.sellercube.com/Order/RequestBlockSet?Length=15'
    form={'state': '',
          'BlockReason': encoded_reason,
          'orderIDs': order}
    
    
    response=Firefox(opener).post(url, form)
    
    if response is None:
        return False
    else:
        return True    
    
    
def OA_MOVER_ORDER(orders, move_to,opener=None):
    '''This func is buggy'''
    
    dest={'unconfirmed':1,
          'to be examed':0,
          'contact buyer':11}
    
    if not dest.has_key(move_to):
        log.warning('Key not OK. [%r]'%move_to)
        raise OABaseError('Key not OK. [%r]'%move_to)
    
    
    move_to_code=dest[move_to]
    
    url='http://banggood.sellercube.com/order/UpdateStatus?status=1&ids=%s'
    form={}
    
    ok_mark=unicode('true')
    
    for i in orders:
        this_url=url%i
        response=Firefox(opener).post(this_url, form,max_try_times=3)
        if response is None:
            return False
        elif not ok_mark in response:
            return False
    
    return True





def OA_RETURN_CASE_QUERY_NEXT_LAYER_LINK(opener):
    url='http://banggood.sellercube.com/EBayCase/Grid'
    form={'startDate': '',
          'search': '',
          'rp': '300',
          'sortname': 'CreationDate',
          'endDate': '',
          'searchField': '',
          'site': '',
          'IsReturnRequest': 'true',
          'ManagerId': '0',
          'dispatchUserName': '',
          'sortorder': 'desc',
          'query': '',
          'eBayID': '',
          'qtype': '',
          'page': '1',
          'hasResponed': 'false'}
    
    response=Firefox(opener).post(url, form)
    
    ID_RE=re.compile(r'"id":"(\w*?)","cell":\[".*?",".*?href=\\".*?\\"')
    
    SEARCH_RLT=ID_RE.findall(response)
    

    base='http://banggood.sellercube.com/EBayCase/Detail/%s'
    
    RLT=[]
    for i in SEARCH_RLT:
        RLT.append([str(i), str(base%i)])
        
    #id
    #link    
    return RLT

def OA_RETURN_GET_EBAY_LINK(return_layer1_link, opener=None):
    response=Firefox(opener).clean_get(return_layer1_link)
    EBAY_RE=re.compile(r'href="(http://.*?returnId=.*?)"')
    
    SEARCH_RLT=EBAY_RE.findall(response)[0]
    URL=str(SEARCH_RLT)
    return URL

def OA_RETURN_SET_NO_NEED_REPLY(rid,opener=None):
    url='http://banggood.sellercube.com/EBayCase/SetReturnReply?ids=%s'%rid
    form={}
    
    response=Firefox(opener).post(url, form,max_try_times=3)
    #response='true'
    if u'true' in response:
        return True
    else:
        return False

