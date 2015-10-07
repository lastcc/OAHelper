import logging

log = logger = logging.getLogger('C')

FH = logging.FileHandler(filename='Log.txt',encoding='utf-8',mode='a')
SH = logging.StreamHandler()
FORMATs = '%(asctime)-15s [line: %(lineno)-4d] %(filename)-8s %(levelname)-8s %(message)s'

FORMATf = '%(asctime)-15s [line: %(lineno)-4d] [func: %(funcName)-8s] %(filename)-8s %(levelname)-8s %(message)s'

logger.setLevel(logging.DEBUG)
FH.setLevel(logging.DEBUG)
SH.setLevel(logging.DEBUG)

FH.setFormatter(logging.Formatter(FORMATf))
SH.setFormatter(logging.Formatter(FORMATs))

logger.addHandler(FH)
logger.addHandler(SH)
