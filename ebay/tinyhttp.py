# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import zlib
import cookielib

from log_config import log

class NetworkError(StandardError):
    pass

#class RedirctHandler(urllib2.HTTPRedirectHandler):
    #"""docstring for RedirctHandler"""
    #def http_error_301(self, req, fp, code, msg, headers):
        #print('RedirctHandler 301')
    #def http_error_302(self, req, fp, code, msg, headers):
        #print('RedirctHandler 302')

#ua='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
user_agent=['Mozilla/5.0 (Windows NT 6.1;',
            'WOW64; rv:33.0) Gecko/20100101',
            'Firefox/33.0']
user_agent=' '.join(user_agent)

ua=user_agent

def simple_Chrome():
    cookie_jar=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)) 
    return Chrome(opener)


class Chrome(object):
    '''doc''' 
    def __init__(self, opener, c_lock=None,redirect_callback=None, timeout=0):

        if opener==None:
            raise
        self.opener=opener
        self.headers=self._user_agent()
        self.default_encoding='utf-8'
        self.lock=c_lock
        self.redirect_callback=redirect_callback
        self.abortnow=False
        self.timeout=timeout
        self.tried = 0
    
    def _check_form_encode(self, form):
        for k in form:
            v = form[k]
            if isinstance(v, unicode):
                form[k] = v.encode('utf-8', 'ignore')
        
        return form
        

    def post(self, url, form, max_try_times=1, headers={}, ok_mark=None,encode_to=''):
        #log.info('post - %s' % str([url, form, max_try_times, headers, ok_mark,encode_to]))
        print 'ok'

        #if not isinstance(url,str):
            #log.warning('Better give me str, not %r'%type(url))
            #url=str(url)
        
        if isinstance(form, dict):
            form = self._check_form_encode(form)
            self.data=urllib.urlencode(form)
            self._update_headers_post()
        elif form==None:
            self.data=None
            self._update_headers_get()
        elif form=='':
            self.data=''
        elif isinstance(form,str):
            self._update_headers_post()
            self.data=form
        else:
            log.warning('Need Dict')
            raise TypeError('Need Dict')
        
        
                

        if ok_mark and not isinstance(ok_mark,unicode):
            log.warning('ok mark not unicode.')
            raise TypeError('ok mark not unicode')
        
        self.url=url
        self.max_try_times=max_try_times
        self.ok_mark=ok_mark
        self.headers.update(headers)
        
        self.request=urllib2.Request(url=self.url, data=self.data, headers=self.headers)
        
        self.response=self._get_response()
        
        if self.abortnow:
            return ''
        
        self.response_headers=self.response.info()
        
        self.charset=self._find_charset()
        charset=self.charset
        
        gzip=self.response_headers.getheader('Content-Encoding')
        
        if ok_mark:
            return self._find_ok()
        
        while max_try_times:
            max_try_times-=1
            try:           
                response_content=self.response.read()
                if gzip and 'gzip' in gzip:
                    response_content=zlib.decompress(response_content, 16+zlib.MAX_WBITS)
                break
            except:
                log.exception('response error')
                if max_try_times==0:
                    raise NetworkError('can not open url %r' % self.url)
        
        if not response_content:
            log.warning('received empty response ""')
            

        if encode_to:
            if charset==encode_to:
                return response_content
            else:
                return self._decode(response_content,charset).encode(encode_to,'ignore')     
        else:
            '''if there is no encode_to
            this will return decoded data - unicode'''
            return self._decode(response_content, charset)
            
            
            
    def _find_ok(self):
        charset=self.charset
        
        buffer_size=1024
        
        response_content=u''
        
        max_try_times=self.max_try_times
        response=self.response
        
        while max_try_times:
            max_try_times-=1
            try:
                b=response.read(buffer_size)
                while b:
                    decoded_data=self._decode(data=b, encoding=charset)
                    response_content+=decoded_data
                    if self.ok_mark in response_content:
                        return True
                    else:
                        b=response.read(buffer_size)
                return False
            except:
                log.exception('read stream fail')
        log.warning('Max try times reached')
        raise NetworkError('can not open url %r' % self.url)
    
    def clean_get(self, url, max_try_times=1, headers={},encode_to=''):
        response_content=self.get(url=url, max_try_times=max_try_times, headers=headers, 
                                 encode_to=encode_to)
        return self._clean(response_content)
    
    def clean_post(self, url, form, max_try_times=1, headers={}, ok_mark=None,encode_to=''):
        response_content=self.post(url=url, form=form, max_try_times=max_try_times, headers=headers, 
                                  ok_mark=ok_mark, 
                                  encode_to=encode_to)
        return self._clean(response_content)
  
    def _clean(self,data):
        data=data.replace('  ','')
        data=data.replace('\r\n','')
        data=data.replace('\n','')
        data=data.replace('<br />', '\n')
        data=data.replace('<br>','\n')
        data=data.replace('</br>','')
        return data        
    
    def _get_response(self):
            
        max_try_times=self.max_try_times
        self.redirected=False
        
        
        while max_try_times:
            max_try_times-=1
            response=None
            
            timeout=30
            
            if self.timeout:
                timeout=self.timeout
                
            try:
                self.tried += 1
                if self.lock:
                    self.lock.acquire() 
                                      
                response=self.opener.open(self.request,timeout=timeout)
               
                status_code=response.getcode()
                self.status_code=status_code
                if not status_code==200:
                    log.warning('Response Code Not OK: [%r]' % status_code)     
                #if status_code==302:
                    #log.warning('Status code 302')  
                    
                self.redirected=not (self.url==response.geturl())
                
                if self.redirected:
                    log.warning('Redirected from %r to: %r'%(self.url, response.geturl()))
                
                if self.redirected and self.redirect_callback:
                    should_abort=self.redirect_callback(response.geturl())
                    if should_abort:
                        self.abort()
            
                return response
            
            except:
                
                log.exception('_get_response')
                if self.tried >= self.max_try_times:
                    log.warning('MAX: %r'%self.url)
                    if self.redirected:
                        log.warning('Redirected to: %r'%response.geturl())
                    raise NetworkError('can not open url %r' % self.url) 
   
            finally:
                
                if self.lock:
                    self.lock.release()
                    

    def get(self, url, max_try_times=1, headers={},ok_mark=None, encode_to=''):
    
        
        return self.post(url=url, form=None, max_try_times=max_try_times, headers=headers, ok_mark=ok_mark, encode_to=encode_to)
    
    def _user_agent(self):
        user_agent=['Mozilla/5.0 (Windows NT 6.1)',
                    'AppleWebKit/537.36 (KHTML, like Gecko)',
                    'Chrome/36.0.1985.125 Safari/537.36']
        user_agent=' '.join(user_agent)

        user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        
        _user_agent={'User-Agent': user_agent} 
        return _user_agent
    
    def _find_charset(self):
        log.debug('url [%s] status_code [%s]'%(self.url,self.status_code))
        
        content_type=self.response_headers.getheader('Content-Type')
        
        if content_type == None:
            return self.default_encoding
        elif not 'charset' in content_type:
            return self.default_encoding
        

        charset = re.compile('charset=(.*)').findall(content_type)[0]
        #log.debug('charset found %s' % charset)
        return charset  
    
    def _decode(self, data,encoding):
        '''
        this fuction returns original data
        when decode fails'''
        try:
            decoded_data=data.decode(encoding=encoding,errors='ignore')
            return decoded_data
        except:
            #this may never happen, 
            #errors was set to 'ignore'
            log.exception('_decode Failed, original data will be returned')
            return data   
        
    def abort(self):
        self.abortnow=True
    
    def _update_headers_get(self):
        headers={
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection':'keep-alive',
        'Cache-Control':'max-age=0'}
        self.headers.update(headers)
    
    def _update_headers_post(self):
        headers={
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.8,en;q=0.6',
        'Content-Type':'application/x-www-form-urlencoded',
        'Cache-Control':'no-cache'}
        self.headers.update(headers)

 

class Firefox(Chrome):
    def _user_agent(self):
        user_agent=['Mozilla/5.0 (Windows NT 6.1;',
                    'rv:31.0) Gecko/20100101',
                    'Firefox/31.0']
        user_agent=' '.join(user_agent)

        user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        
        _user_agent={'User-Agent': user_agent} 
        return _user_agent     

class Firefox64(Chrome):
    def _user_agent(self):
        user_agent=['Mozilla/5.0 (Windows NT 6.1;',
                    'WOW64; rv:33.0) Gecko/20100101',
                    'Firefox/33.0']
        user_agent=' '.join(user_agent)

        #user_agent='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        
        _user_agent={'User-Agent': user_agent} 
        return _user_agent
    
