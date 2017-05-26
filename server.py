# coding:utf-8
import errno
import os
import signal
import socket
import json
import iptc
import time
import cloghandler
import logging, logging.config
 
SERVER_ADDRESS = (HOST, PORT) = '', 8010
REQUEST_QUEUE_SIZE = 1024
DELETE_COUNT = 3

indexPage = '''HTTP/1.1 200 OK
Content-Type: text/html

'''

file = open('files/index.html', 'r')
indexPage += file.read()
file.close()

logging.config.dictConfig({
                            'version': 1,
                            'formatters' : {
                                    'verbose' : {
                                        'format' : '%(asctime)s - %(filename)s:%(lineno)s - %(name)s : %(message)s',
                                        'datefmt' : '%Y-%m-%d %H:%M:%S',
                                    }
                                },
                            'handlers': {
                                    'file': {
                                        'level': 'DEBUG',
                                        # 如果没有使用并发的日志处理类，在多实例的情况下日志会出现缺失
                                        'class': 'cloghandler.ConcurrentRotatingFileHandler',
                                        'maxBytes': 1024 * 1024 * 3,
                                        'backupCount': 2,
                                        'filename': 'log/debug.log',
                                        'formatter': 'verbose',
                                    }
                                },
                           'loggers': {
                                    '': {
                                        'handlers': ['file'],
                                        'level': 'DEBUG',
                                    },
                                },
                           })
# 定义一个Handler打印INFO及以上级别的日志到sys.stderr  
console = logging.StreamHandler()  
console.setLevel(logging.DEBUG)
# 设置日志打印格式  
formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)s - %(name)s : %(message)s')  
console.setFormatter(formatter)  
# 将定义好的console日志handler添加到root logger  
logging.getLogger('').addHandler(console)

 
def grim_reaper(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(
                -1,          # Wait for any child process
                 os.WNOHANG  # Do not block and return EWOULDBLOCK error
            )
        except OSError:
            return
 
        if pid == 0:  # no more zombies
            return

def iptables_control(ipAddress):
    delCount = 0
    
    for index in xrange(DELETE_COUNT):        
        delCount = deleteRules(ipAddress, delCount)
        time.sleep(0.1)
        logging.debug("[Delete index {0}]".format(index))
        
    if delCount == 0:
        msg = "服务器未找到此手机的规则"
    else:
        msg = "%d条规则已清除" % delCount
    return msg

def deleteRules(ipAddress, delCount):
    table = iptc.Table(iptc.Table.MANGLE)
    chain = iptc.Chain(table, "FORWARD")
    for rule in chain.rules:
        logging.info('rule.src = {0}'.format(rule.src))
        logging.info('rule.dst = {0}'.format(rule.dst))
        if ipAddress in rule.src:
            delCount += 1
            logging.debug('[Delete {0} rule in source]'.format(ipAddress))        
        elif ipAddress in rule.dst:
            delCount += 1
            logging.debug('[Delete {0} rule in destination]'.format(ipAddress))
        else:
            continue
        try:
            chain.delete_rule(rule)
        except Exception, e:
            logging.debug('[IP not in rule then delete error]')
    return delCount

def handle_request(client_connection):
    client_connection.settimeout(30); 
    reqData = ''
    while True:
        request = client_connection.recv(1024)
        reqData += request
        EndValue = "\r\n\r\n"
        handleEnd = reqData.find(EndValue)
        if handleEnd >= 0:
            handleData = reqData[:(handleEnd+len(EndValue))]
#             logging.debug("handleData = {0}".format(handleData))
            CL = "Content-Length:"
            CLEnd = handleData.find(CL)
            if CLEnd >= 0:
                CLEndData = handleData[(CLEnd+len(CL)):]
#                 logging.debug("CLEndData = {0}".format(CLEndData))
                dataLen = int(CLEndData.split("\r\n")[0])
#                 logging.debug("dataLen = {0}".format(dataLen))
                recvLen = dataLen - len(reqData[(handleEnd+len(EndValue)):])
#                 logging.debug("recvLen = {0}".format(recvLen))
                if recvLen:
                    logging.debug("[recv again]")
                    request = client_connection.recv(recvLen)
                    reqData += request
            break
        if not len(request):
            break
        logging.debug("[buf = {0}]".format(request))
    logging.info('\n>Request = \n{data}\n'.format(data=reqData.decode()))
    request_data = reqData.split(' ')
    method = request_data[0]
    if len(request_data) > 1:
        src  = request_data[1]
    else:
        src = ''
     
    content = 'HTTP/1.1 404 NOT FOUND\r\nContent-Type: application/json\r\n\r\n'
     
    if method == 'GET':
        if src == '/':
            content = indexPage
    elif method == 'POST':
        if src == '/delete':
                entry = reqData.split('\r\n')[-1]
                logging.debug("[entry = {0}]".format(entry))
                try:
                    dataDict = json.loads(entry)
                    ipAddress = dataDict['ip']
                    
                    msg = iptables_control(ipAddress)#Delete rules
                    
                    entry = json.dumps({
                                        'status' : '1',
                                        'msg' : msg
                             })
                    logging.debug("[repMsg = {0}]".format(msg))
                except Exception, err:
                    logging.debug("[err = {0}]".format(err))
                    entry = json.dumps({
                                        'status' : '-1',
                                        'msg' : str(err),
                                        'reqData' : entry
                             })
                content = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
                content += entry

    client_connection.sendall(content)
 
def serve_forever():
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind(SERVER_ADDRESS)
    listen_socket.listen(REQUEST_QUEUE_SIZE)
    logging.info('{holder}'.format(holder='='*30))
    logging.info('Serving HTTP on port {port} ...'.format(port=PORT))
 
    signal.signal(signal.SIGCHLD, grim_reaper)
 
    while True:
        try:
            client_connection, client_address = listen_socket.accept()
            logging.info('{holder}'.format(holder='-'*30))
            logging.info('Connect by : {0}'.format(client_address, holder='-'*30))
        except IOError as e:
            code, msg = e.args
            # restart 'accept' if it was interrupted
            if code == errno.EINTR:
                continue
            else:
                logging.debug("\n[serve_forever IOError e = {0}\ncode = {1}\nmsg = {2}]".format(e, code, msg))
                raise
        except KeyboardInterrupt:
            logging.debug("[KeyboardInterrupt Close]")
            listen_socket.close()
            return
        
        pid = os.fork()
        if pid == 0:  # child
            listen_socket.close()  # close child copy
            handle_request(client_connection)
            client_connection.close()
            os._exit(0)
        else:  # parent
            client_connection.close()  # close parent copy and loop over
 
if __name__ == '__main__':
        serve_forever()