# -*- coding: utf-8 -*-

#web
default_encoding='utf-8'

'''order'''
valid_order_length=16

#order query fields
FIELD_BUYER = 'Ebayuserid'
FIELD_PAYPAL = 'PaypalTransactionId'
FIELD_TRACKING = 'TraceID'
FIELD_EMAIL = 'Email'
FIELD_ORDER = 'Id'
FIELD_RECEIVER = 'Receivename'



'''refund action'''
#refund type constances
TYPE_NOT_RECEIVED=4
TYPE_QUALITY_NOT_OK=3
TYPE_OTHER_REASONS=8
TYPE_PICTURE_MISMATCH=5
TYPE_DAMAGED=7
TYPE_REFUND_RETURN_SHIPPING=14
TYPE_CANCELED_BY_BUYER=19
TYPE_NOT_ENOUGH_STOCK=20

#currency
USD='USD'
CAD='CAD'
EUR='EUR'
GBP='GBP'
AUD='AUD'

#amount, float
min_amount=00.01
max_amount=300.00


'''move order'''
ORDER_UNCONFIRMED = '1'
ORDER_TO_BE_EXAMED = '0'
ORDER_CANCELED = '13'
ORDER_CONTACT_BUYER = '11'
ORDER_OUT_OF_STOCK = '10'



