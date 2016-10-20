#-*-coding:utf-8-*- 
import sublime,sublime_plugin
import os,platform,re,logging,subprocess,json,sys,traceback,time
import uuid,urllib.parse,urllib.request,json,urllib.parse

curDir = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')

wifi_config_file=''
if 'windows' in platform.system().lower():
    wifi_config_file=os.path.join('c:\\','APICloud','workspace','config_info')
else:
    wifi_config_file=os.path.join(curDir,'tools','config_info')
logging.info('wifi_config_file is '+wifi_config_file)
############################################global function############################
def get_settings():
    return sublime.load_settings("wifi-sync.sublime-settings")

def is_service_start():
    if not os.path.exists(wifi_config_file):
        return False
    try:
        with open(wifi_config_file) as f:
            config=json.load(f)
            ip=config["ip"]
            websocket_port=config["websocket_port"]
    except:
        return False
    return True

def changeWorkspace(curDir,http_port):
    ''' change workspace '''
    rootDir = os.path.abspath(curDir).split(os.path.sep)[0]+os.path.sep
    if curDir == rootDir:
        return -1
    upperDir=os.path.dirname(curDir)
    workspaceEncoded='"'+urllib.parse.quote(upperDir)+'"'
    changeSpaceUrl='http://127.0.0.1:'+http_port+'?action=workspace&path='+workspaceEncoded
    logging.info('ChangeWorkspaceCommand url : '+ changeSpaceUrl)
    response = urllib.request.urlopen(changeSpaceUrl)
    html = response.read()
    time.sleep(0.2)

def isWidgetPath(path):
    isFound = False
    appFileList=os.listdir(path)
    if 'config.xml' in appFileList and 'index.html' in appFileList:
        with open(os.path.join(path,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)
            if len(searchResList)>0:
                isFound = True
    return isFound

def getWidgetPath(path):
    rootDir = os.path.abspath(path).split(os.path.sep)[0]+os.path.sep
    dirList = []
    for x in range(0,10):
        path = os.path.dirname(path)
        dirList.append(path)
        if path == rootDir:
            break

    syncPath=''
    for path in dirList:
        if isWidgetPath(path):
            syncPath = path
            break
    return syncPath

def getWifiInfo():
    time.sleep(4)
    if not os.path.exists(wifi_config_file):
        sublime.message_dialog(u'请先启动真机同步服务')
        return        
    try:
        with open(wifi_config_file) as f:
            config=json.load(f)
            websocket_port=config["websocket_port"]
            if 0==websocket_port:
                sublime.message_dialog(u'服务启动未完成，稍后请手动查看服务端口信息！')
                return
            ip=config["ip"]
            ip_list=ip.split(',')
            if len(ip_list)==1:
                info='端口: '+str(websocket_port)+'\nip:'+ip
            else:
                info='端口: '+str(websocket_port)
                i=0
                for ip_info in ip_list:
                    info=info+'\nip'+str(i)+': '+ip_info
                    i=i+1
    except Exception as e:
        sublime.message_dialog(u'请先启动真机同步服务')
        return
    sublime.message_dialog(info)

def getAppId(srcPath):
    appId=-1
    if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
        print('getAppId:file no exist or not a folder!')
        return appId
    appFileList=os.listdir(srcPath)
    if 'config.xml' not in appFileList:
        print('getAppId: please make sure sync the correct folder!')
        return -1
    with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
        fileContent=f.read()
        r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
        searchResList=r.findall(fileContent)  
    if len(searchResList)>0:
        appId=searchResList[0]
    return appId

############################################end global function############################

class ApicloudWifiSyncCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiSyncCommand"""
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.info('begin wifi sync')
        appId=getAppId(dirs[0])
        logging.info('appId: '+appId)
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]

        if -1==changeWorkspace(dirs[0],http_port):
            sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return
        syncUrl='http://127.0.0.1:'+http_port+'?action=sync&appid='+appId
        logging.info('syncUrl is: '+ syncUrl)
        response = urllib.request.urlopen(syncUrl)

class ApicloudWifiSyncallCommand(sublime_plugin.WindowCommand):
    '''wifi-sync all api'''
    __curDir=''
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        appId=getAppId(dirs[0])
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
            
        if -1==changeWorkspace(dirs[0],http_port):
            sublime.message_dialog(u'请确保widget文件夹未放置于根目录！')
            return            
        syncallUrl='http://127.0.0.1:'+http_port+'?action=syncall&appid='+appId
        logging.info('syncallUrl is: '+ syncallUrl)
        response = urllib.request.urlopen(syncallUrl)

class ApicloudWifiPreviewCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudWifiPreviewCommand"""
    def run(self, files):
        with open(wifi_config_file) as f:
            config=json.load(f)
            http_port=config["http_port"]
        
        fileEncoded=urllib.parse.quote(files[0])
        previewUrl='http://127.0.0.1:'+http_port+'?action=review&path='+'"'+fileEncoded+'"'
        logging.info('previewUrl is: '+ previewUrl)
        response = urllib.request.urlopen(previewUrl)

    def is_enabled(self, files):
        if len(files) > 0:
            if not is_service_start():
                return False
            else:
                return True
        else:
            return False

    def is_visible(self, files):
        return len(files) > 0 
##############################################################################################

def BeforeSystemRequests():
    '''
    the systeminfo uploads to api of ..
    '''
    def get_system_version():
        system_name = platform.system()
        if system_name == 'Windows' and os.name == 'nt':
            system_machine = platform.platform().split('-')[0] + platform.platform().split('-')[1]
        elif system_name == 'Darwin':
            system_machine = 'Mac-os'
        else:
            system_machine = system_name
        return system_machine

    def post(url,data):
        data = urllib.parse.urlencode({'info':data}).encode('utf-8')
        req = urllib.request.Request(url,data)
        urllib.request.urlopen(req)
        return
    def index():
        apiUrl = 'http://www.apicloud.com/setSublimeInfo'
        systemInfo = {
            "system": get_system_version(),
            "uuid": hex(uuid.getnode())
        }
        try:
            systemInfo = json.dumps(systemInfo) 
            post(apiUrl,systemInfo)
        except Exception as e:
            print('exception is :',e)
        finally:
            pass
    try:        
        index()
    except Exception as e:
        pass   

class InstallWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' install wifi-sync service '''
    def run(self, dirs):
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        installSyncCmd='"'+exeCmdFile+'" -install'
        os.system(installSyncCmd)
        sublime.message_dialog(u'完成安装APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower():
            return False
        else:
            return True

class StartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' start wifi-sync service '''
    def run(self, dirs):
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        startSyncCmd='"'+exeCmdFile+'" -start'
        logging.info('StartWifysyncAppCommand cmd : '+ startSyncCmd)
        os.system(startSyncCmd)
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower():
            return False
        else:
            return True

class StopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        exeCmdFile=os.path.join(curDir,'tools','APICloudWiFiSync.exe')
        stopSyncCmd='"'+exeCmdFile+'" -stop'
        logging.info('StopWifysyncAppCommand cmd : '+ stopSyncCmd)
        os.system(stopSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'darwin' in platform.system().lower():
            return False
        else:
            return True

class GetWifisyncInfoCommand(sublime_plugin.WindowCommand):
    ''' get wifi-sync ip and port '''
    def run(self, dirs):
        if not os.path.exists(wifi_config_file):
            sublime.message_dialog(u'请先启动真机同步服务')
            return        
        try:
            with open(wifi_config_file) as f:
                config=json.load(f)
                websocket_port=config["websocket_port"]
                ip=config["ip"]
                ip_list=ip.split(',')
                if len(ip_list)==1:
                    info='端口: '+str(websocket_port)+'\nip:'+ip
                else:
                    info='端口: '+str(websocket_port)
                    i=0
                    for ip_info in ip_list:
                        info=info+'\nip'+str(i)+': '+ip_info
                        i=i+1
        except Exception as e:
            sublime.message_dialog(u'请先启动真机同步服务')
            return
        sublime.message_dialog(info)

    def is_enabled(self, dirs):
        if not is_service_start():
            return False
        else:
            return True
                
    def is_visible(self, dirs):
        return len(dirs) == 1

############################ mac ####################################

class MacStartWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' mac start wifi-sync service '''
    def run(self, dirs):
        p=subprocess.Popen('java -version',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        stdoutbyte,stderrbyte=p.communicate()
        stdout=str(stdoutbyte)+str(stderrbyte)
        if 'version' not in stdout:
            sublime.error_message(u'缺少JRE环境')
            return
        jarFile=os.path.join(curDir,'tools','wifisync.jar')
        javaCmd='java'
        configPath=os.path.join(curDir,'tools')
        iosSyncCmd='nohup '+'"'+javaCmd+'" -jar "'+jarFile+'" "'+dirs[0]+'" "'+configPath+'"'+' &'
        logging.info('MacStartWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd);
        # sublime.message_dialog(u'启动APICloud真机同步服务')
        getWifiInfo()

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower():
            return False
        else:
            return True            

class MacStopWifysyncAppCommand(sublime_plugin.WindowCommand):
    ''' stop wifi-sync service '''
    def run(self, dirs):
        stopShellFile=os.path.join(curDir,'stop.sh')
        iosSyncCmd='/bin/sh'+' '+'"'+stopShellFile+'"'
        logging.info('MacStopWifysyncAppCommand cmd : '+ iosSyncCmd)
        os.system(iosSyncCmd)
        if os.path.exists(wifi_config_file):
            os.remove(wifi_config_file)
        sublime.message_dialog(u'停止APICloud真机同步服务')

    def is_visible(self, dirs):
        if 'windows' in platform.system().lower():
            return False
        else:
            return True

######################## keymap #######################################
class ApicloudWifiPreviewKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudWifiPreviewKeyCommand"""
    def run(self, edit):
        sublime.status_message(u'开始真机预览')
        file_name=self.view.file_name()
        if len(file_name) > 0:
            logging.info('preview path is '+file_name)
            try:
                preview = ApicloudWifiPreviewCommand('')
                syncPathList=[]
                syncPathList.append(file_name)
                preview.run(syncPathList)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                sublime.error_message(u'真机预览出现异常')
            sublime.status_message(u'真机预览完成')
        else:
            sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudWifiSyncKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudWifiSyncKeyCommand"""
    def run(self, edit):
        sublime.status_message(u'开始真机同步')
        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.info('sync path is '+syncPath)
            try:
                wifisync = ApicloudWifiSyncCommand('')
                syncPathList=[]
                syncPathList.append(syncPath)
                wifisync.run(syncPathList)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                sublime.error_message(u'真机同步出现异常')
            sublime.status_message(u'真机同步完成')
        else:
            sublime.error_message(u'请确保当前文件所在目录正确')
        return   
        
# BeforeSystemRequests()