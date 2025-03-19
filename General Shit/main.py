import asyncio
import websockets
import base64
import json, random, string, time, os, shutil, webbrowser, threading
from datetime import datetime
# from Bi_Directional_Connection import socket_server
from passlib.hash import sha256_crypt
from Network import local_network 
from Tracking import cursor
from vision import register, VisionDeviceSelection, recognize
import config
AppConfig = config.AppConfiguration.__dict__
from Uni_Directional_Connection import http_server
from Network import NetworkAuth

class Session:
    def __init__(self, SessionID = ''.join([random.choice(string.ascii_uppercase + string.digits) for i in range(random.randint(186, 284))])):
        self.SessionID = SessionID
    def Set(self, key, value):
        self.key = value
    def flush(self):
        _attributes = list(vars(self).keys())
        for i in _attributes:
            if i != 'SessionID':
                delattr(self, i)
    def remove(self, property):
        if hasattr(self, property):
            delattr(self, property)
        else:
            raise AttributeError(f'\'Session\' Object has no attribute \'{property}\'')

ApplicationSession = Session()


AppDirectory = 'App/'
LogDirectory = f'{AppDirectory}SystemLogs/'
ProfileDirectory = f'{AppDirectory}Profile/'
AppVersion = '1.0-D'

ProfileFingerprint = 48


def SystemLog(Log):
    with open(f'{LogDirectory}/SystemLog.txt', 'a') as file:
        file.write(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}]: {Log}\n")


NetworkAuth.initialize_network_auth(SystemLog)
network_auth = NetworkAuth.network_auth

def SetupSystemDirectory():
    os.makedirs(f"{AppDirectory}Configuration", exist_ok=True)
    os.makedirs(f"{ProfileDirectory}", exist_ok=True)
    os.makedirs(f"{ProfileDirectory}Profiles", exist_ok=True)
    os.makedirs(f"{LogDirectory}", exist_ok=True)
    if not os.path.exists(f'{ProfileDirectory}Users.json'):
        with open(f'{ProfileDirectory}Users.json', 'w') as file:
            json.dump({'User': [], 'Accounts': []}, file)
    if not os.path.exists(f'{AppDirectory}Configuration/App.json'):
        with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
            json.dump({
                'AppConfiguration': {
                    'Version': AppVersion,
                    'AppInstances': [],
                    'SystemName': local_network.currentSystem()[2],
                    'OS': local_network.currentSystem()[3],
                    'Devices': {},
                }}, file)
    if not os.path.exists(f'{LogDirectory}SystemLog.txt'):
        with open(f'{LogDirectory}SystemLog.txt', 'w') as file:
            file.write(f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}]: App Directory Initialized.\n")

def getUser()->list:
    with open(f'{ProfileDirectory}/Users.json', 'r') as file:
        return json.load(file)['User']

def SetUser(_User):
    with open(f'{ProfileDirectory}/Users.json', 'r') as file:
        UserObj = json.load(file)    
    with open(f'{ProfileDirectory}/Users.json', 'w') as file:
        UserObj['User'] = _User
        json.dump(UserObj, file)

def getAccounts()->list:
    with open(f'{ProfileDirectory}/Users.json', 'r') as file:
        return json.load(file)['Accounts']

def SetAccounts(_acc):
    with open(f'{ProfileDirectory}/Users.json', 'r') as file:
        UserObj = json.load(file)    
    with open(f'{ProfileDirectory}/Users.json', 'w') as file:
        UserObj['Accounts'] = _acc
        json.dump(UserObj, file)

def GetAppConfig():
    with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
        return json.load(file)

def SetAppConfig(config):
    with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
        json.dump(config, file)



def EditProfile(fingerprint, profile):
    UserObj = getUser()
    for user in UserObj:
        if user['Profile']['ProfileFingerprint'] == fingerprint:
            user['Profile']['ProfileName'] = profile['ProfileName']
            user['Profile']['ProfileKey'] = sha256_crypt.hash(profile['PIN'])
            if len(user['profile']['picture']) > 0:
                destination = f"{ProfileDirectory}Profiles/{fingerprint}.{(profile['ProfileImage'].split('.')[-1])}"
                shutil.copyfile(profile['ProfileImage'], destination)
                user['Profile']['ProfileImage'] = destination
    SetUser(UserObj)

def RemoveProfile(fingerprint):
    users = getUser()
    for i in range(len(users)):
        if users[i]['Profile']['ProfileFingerprint'] == fingerprint:
            users.pop(i)
            break
    SetUser(users)
    

def ConnectApp(Socket, ClientID, App):
    Config = GetAppConfig()
    InstanceIndex = Config['AppConfiguration']['AppInstances'].index((list(filter(lambda instance: instance['InstanceID'] == ApplicationSession.InstanceID, Config['AppConfiguration']['AppInstances'])))[0])
    _App = App.copy()
    del _App['Key']
    AppID = (Generator(14, True, False, ['@_=+']))
    Config['AppConfiguration']['AppInstances'][InstanceIndex]['ConnectedApps'].append({"APP_ID": AppID, 'App': _App, 'Client_ID': ClientID})
    SetAppConfig(Config)
    return AppID


def InitiateUserAccountConnection():
    global Handler
    # host = local_network.currentSystem()[0]
    # port = '17288'
    ApplicationSession.HttpServerAddress = {'host': AppConfig['HTTPServer']['Host'], 'port': AppConfig['HTTPServer']['Port']}
    # print(f"http://accounts.encrypta.in/?ExternalLoginType=CookieLess&SUCCESS=http://{host}:{port}&AppID={ApplicationSession.InstanceID}")
    http_ServerThread = threading.Thread(target=http_server.run, args=(AppConfig['HTTPServer']['Host'], AppConfig['HTTPServer']['Port'], 'Encrypta-Auth-Server'))
    http_ServerThread.start()

def RegisterConnectedDevice(): #todo develop
    pass


def ProfileAdd(user: dict):
    def RegisterFingerprint(ProfilesFingerprint):
        global ProfileFingerprint
        fingerprint = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(ProfileFingerprint)])
        while fingerprint in ProfilesFingerprint:
            fingerprint = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(ProfileFingerprint)])
        return fingerprint
    with open(f'{ProfileDirectory}/Users.json', 'r') as user_file:
        UserObj = json.load(user_file)
        ApplicationSession.SessionKey
        User = {'Profile': {'ProfileName': user['profile']['ProfileName'], 'ProfileImage': '', 'ProfileFingerprint': RegisterFingerprint(list(map(lambda x: x['Profile']['ProfileFingerprint'], UserObj['User']))), 'ProfileKey':  sha256_crypt.hash(user['profile']['ProfilePIN'])}, 'Account': {'UserName': ApplicationSession.UserName, 'EmailID': ApplicationSession.Email, 'UserKey': ApplicationSession.UserKey, 'SessionKey': ApplicationSession.SessionKey}, 'Configuration': {'AuthenticationDirectory': user['profile']['AuthDirectory'], 'Authentication': {'PIN': True, 'Password': False, 'VisionID': False, 'Fingerprint': False}}}
        if  not user['profile']['AuthDirectory']:
            os.makedirs(f"{ProfileDirectory}/Profiles/{User['Profile']['ProfileFingerprint']}")
        if (user['profile']['ProfileImage']):
            destination = f"{ProfileDirectory}Profiles/{User['Profile']['ProfileFingerprint']}.{(user['profile']['ProfileImage'].split('.')[-1])}"
            shutil.copyfile(user['profile']['ProfileImage'], destination)
            User['Profile']['ProfileImage'] = os.path.abspath(destination)
        SystemLog(f'New Profile Created!')
        UserObj['User'].append(User)
    with open(f'{ProfileDirectory}/Users.json', 'w') as user_file:
        json.dump(UserObj, user_file)



def EstablishAppInstance():
    def Register_Instance_ID(instances):
        instanceID_len = 15
        InstanceID = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(instanceID_len)])
        while InstanceID in instances:
            InstanceID = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(instanceID_len)])
        return InstanceID
    with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
        config = json.load(file)
    Instances = list(filter(lambda x: x['SystemUsername'] == os.getlogin(), config['AppConfiguration']['AppInstances']))
    if len(Instances) != 0:
        if len(Instances[0]['Instance']) != 0:
            InstanceIndex = config['AppConfiguration']['AppInstances'].index(Instances[0])
            config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Fingerprint'] = ApplicationSession.ProfileFingerprint
            config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['SessionID'] = ApplicationSession.SessionID
            config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Activity'] = int(time.time())
        else:
            _instance = {'Fingerprint': None, 'Activity': int(time.time()), 'InputDevices': {'Biometrics': {'Vision': None, 'FingerPrint': None}}, 'Tracking': {'Vision': False, 'Cursor': False}, 'ConnectedApps': []}
            InstanceIndex = config['AppConfiguration']['AppInstances'].index(Instances[0])
            config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance'] = (_instance)
        with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
            json.dump(config, file)
    else:
        _instance = {'Fingerprint': None, 'Activity': int(time.time()), 'InputDevices': {'Biometrics': {'Vision': None, 'FingerPrint': None}}, 'Tracking': {'Vision': False, 'Cursor': False}}
        AppInstance = {'SystemUsername': os.getlogin(), 'ConnectedApps': [], 'InstanceID': Register_Instance_ID(list(map(lambda x: x['InstanceID'], config['AppConfiguration']['AppInstances']))), 'Instance': _instance}
        config['AppConfiguration']['AppInstances'].append(AppInstance)
        ApplicationSession.InstanceID = AppInstance['InstanceID']
    with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
        json.dump(config, file)




def SetSession(fingerprint):
    user = list(filter(lambda x: x['Profile']['ProfileFingerprint'] == fingerprint, getUser()))[0]
    ApplicationSession.ProfileFingerprint = user['Profile']['ProfileFingerprint']
    ApplicationSession.ProfileName = user['Profile']['ProfileName']
    ApplicationSession.ProfileKey_Auth = user['Profile']['ProfileKey']
    ApplicationSession.ProfileImage = user['Profile']['ProfileImage']
    ApplicationSession.UserName = user['Account']['UserName']
    ApplicationSession.Email = user['Account']['EmailID']
    ApplicationSession.SessionKey = user['Account']['SessionKey'] #todo: get from server
    ApplicationSession.UserKey = user['Account']['UserKey']
    with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
        config = json.load(file)
    Instance = list(filter(lambda x: x['SystemUsername'] == os.getlogin(), config['AppConfiguration']['AppInstances']))[0]
    # ApplicationSession.InstanceID = Instance['InstanceID']
    InstanceIndex = config['AppConfiguration']['AppInstances'].index(Instance)
    ApplicationSession.PreferredDevices = config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['InputDevices']['Biometrics']
    ApplicationSession.TrackingPreference = config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Tracking']
    print(ApplicationSession.__dict__)
    config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['SessionKey'] = ApplicationSession.SessionKey
    config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Fingerprint'] = ApplicationSession.ProfileFingerprint
    config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Activity'] = int(time.time())

    if ApplicationSession.TrackingPreference['Cursor']:
        CursorTrackingThread = threading.Thread(target=cursor.InitiateTracking())
        CursorTrackingThread.start()


    with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
        json.dump(config, file)
main_event_loop = None
def network_auth_callback(source_ip, hostname):
    """
    Callback function for handling network authentications
    
    Called when a network broadcast is received with a matching user key hash
    """
    global main_event_loop
    try:
        SystemLog(f"Received valid authentication from {hostname} ({source_ip})")
        
        if not hasattr(ApplicationSession, 'pending_network_auths'):
            ApplicationSession.pending_network_auths = []
            
        ApplicationSession.pending_network_auths.append({
            'source_ip': source_ip,
            'hostname': hostname,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        if hasattr(ApplicationSession, 'ApplicationInterfaceSocket') and main_event_loop:

            asyncio.run_coroutine_threadsafe(
                deliver_network_auth_notification(ApplicationSession.ApplicationInterfaceSocket),
                main_event_loop
            )
        else:
            SystemLog("Socket not ready or event loop not available - authentication notification queued")
    except Exception as e:
        SystemLog(f"Error handling network authentication: {e}")
        
async def deliver_network_auth_notification(websocket):
    """Helper function to deliver network auth notifications via websocket"""
    try:
        if hasattr(ApplicationSession, 'pending_network_auths') and ApplicationSession.pending_network_auths:
            
            auth = ApplicationSession.pending_network_auths.pop(0)
            
            if websocket.open: 
                message = json.dumps({
                    'Action': {'Response': 'NetworkAuthentication'}, 
                    'Transfer': {
                        'Code': '25', 
                        'UserAuthentication': True,
                        'AuthType': 'Network',
                        'Source': f"Device {auth['hostname']} ({auth['source_ip']})",
                        'Message': "Network device with matching user credentials authenticated",
                        'Timestamp': auth['timestamp']
                    }
                })
                
                await websocket.send(message)
                SystemLog(f"Successfully sent network auth notification")
            else:
                SystemLog("Websocket closed - couldn't deliver notification")
    except Exception as e:
        SystemLog(f"Error delivering network auth notification: {e}")


def RestoreSession():
    with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
        config = json.load(file)
    Instance = list(filter(lambda x: x['SystemUsername'] == os.getlogin(), config['AppConfiguration']['AppInstances']))
    if len(Instance) > 0:
        Instance = Instance[0]
        if Instance['Instance']['Fingerprint'] is not None:
            SetSession(Instance['Instance']['Fingerprint'])
        else:
            ApplicationSession.ProfileFingerprint = None
            if 'SessionKey' in Instance['Instance']:
                ApplicationSession.SessionKey = Instance['Instance']['SessionKey']
            else:
                ApplicationSession.SessionKey = None
        ApplicationSession.InstanceID = Instance['InstanceID']
    else:
        ApplicationSession.ProfileFingerprint = None
        ApplicationSession.SessionKey = None
        

if not os.path.exists(f"{AppDirectory}"):
    SetupSystemDirectory()

# EditProfile('WWZfrXsW2JKgABA0OGqHuB7b41hiSZ68gEMGCX208Yjj9mMU', {'ProfileImage': './encrypta-favicon.png', 'PIN': '123456', 'ProfileName': ''})
# print(getUser())
# RemoveProfile('NIRzldgpgnzRzBM6fjW6uh77OEjia3GqDfHRc4gjgf4FTdBL')
# SetSession('NIRzldgpgnzRzBM6fjW6uh77OEjia3GqDfHRc4gjgf4FTdBL')
# ProfileAdd({'profile': {'Name': 'ankit', 'picture': r'C:\Users\mypc\Desktop\Desktop Authentication Client\Uni_Directional_Connection\static\assets\Encrypta-w-full-enl.png', 'PIN': '123456'}, 'Account': {'Username': 'Ankit_K_Nayak', 'EmailID': 'ankitnayak172@gmail.com', 'UserID': 3, 'UserKey': ''.join([random.choice(string.ascii_letters) for i in range(30)]), 'SessionKey': ''.join([random.choice(string.ascii_letters) for i in range(30)])}, 'Config': {'AuthDirectory': 'C://User/Ankit', }})
# InstanceSession()
RestoreSession()
EstablishAppInstance()

network_auth.start_listening(ApplicationSession, network_auth_callback)
InitiateUserAccountConnection()

# SetSession('WWZfrXsW2JKgABA0OGqHuB7b41hiSZ68gEMGCX208Yjj9mMU')

def SetUpAccount(User):
    accounts = getAccounts()
    account = list(filter(lambda _account: _account['UserKey'] == User['UserKey'], accounts))
    if len(account) == 1:
        Index = accounts.index(account[0])
        accounts[Index]['SessionKey'] = User['SessionKey']
        User['UserName'] = account[0]['UserName'] 
        User['EmailID'] = account[0]['EmailID'] 
    else:
        accounts.append(User)
        del User['Expiry']
    SetAccounts(accounts)
    ApplicationSession.SessionKey = User['SessionKey']
    ApplicationSession.UserKey = User['UserKey']
    ApplicationSession.UserName = User['UserName']
    ApplicationSession.Email = User['EmailID']
    if ApplicationSession.ProfileFingerprint is not None:
        UserObj = getUser()
        for user in UserObj:
            if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                user['Account'] = User
        SetUser(UserObj)



CursorTrackingThread = None
VisionTrackingInterval = None


def Authenticate():
    print(cursor.CursorActivity)


def Generator(Length: int, UpperCase = False, LowerCase = False, Symbols = []):
    return ''.join([random.choice((string.ascii_uppercase if UpperCase else '' + string.ascii_lowercase if LowerCase else '' ) + string.digits + ''.join(Symbols)) for i in range(Length)])


# Websocket server
Authentication = {}
ServerClientConnection = {}
def clientId(UpperCase=False, LowerCase = False):
    clientID = Generator(28, UpperCase, LowerCase)
    while clientID in ServerClientConnection:
        clientID = Generator(28, UpperCase, LowerCase)
    return clientID

async def Handler(websocket, path):
    print(path)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            if path == '':
                if 'App_Request' in data and data['ConnectionKey'] == AppConfig['ConnectionKey']:
                    if data['App_Request'] == 'ConnectionConfig':
                        await websocket.send(json.dumps({'Response_Header': 'ConnectionConfig', 'Response': AppConfig}))
                    elif data['App_Request'] == 'AuthenticationState':
                        await websocket.send(json.dumps({'Response_Header': 'Authentication', 'Response': ({'State': True, 'Hash': ''.join([random.choice(string.ascii_letters) for i in range(32)]), 'AuthTimeStamp': time.time(), 'Expiry': time.time() + 200}) if (random.choice([True,False])) else ({'State': False, 'Hash': ''.join([random.choice(string.ascii_letters) for i in range(32)])}) }))
                    elif data['App_Request'] == 'Authenticate':
                        pass    
            elif path == '/EncryptaAuth':
                if 'Action' in data and 'Request' in data['Action']:
                    if data['Action']['Request'] == 'Initiate':
                        _clientId = clientId()
                        ServerClientConnection[_clientId] = {'App': data['Transfer'], 'ConnectionPulse': int(time.time()), 'Socket': websocket}
                        await websocket.send(json.dumps({'Action': {'Response': 'Acknowledgement'}, 'Transfer': {'Code': '25', 'ClientId': _clientId}}))
                    else:
                        if data['Transfer']['ClientID'] in ServerClientConnection and ServerClientConnection[data['Transfer']['ClientID']]['App']['Key'] == data['Transfer']['Key']:    
                            if data['Action']['Request'] == 'Device':
                                await websocket.send(json.dumps({'Action': {'Response': 'Device'}, 'Transfer': {'Code': '25', 'DeviceName' : f'{local_network.currentSystem()[2]} - {local_network.currentSystem()[3]}', 'AppName': '(Authenticator/1.2 <EncryptaAuthDeviceFramework/1.4>)'}}))
                            elif data['Action']['Request'] == 'EncryptaAuth':
                                SetUpAccount(data['Transfer']['User'])
                                await ApplicationSession.ApplicationInterfaceSocket.send(json.dumps({'Action': {'Response': 'InitiateUserSignIn'}, 'Transfer': {'Code': '25', 'UserAuthentication': True}}))
                                ApplicationSession.remove('ApplicationInterfaceSocket')
                                # update Session
                                # SetSession(ApplicationSession.ProfileFingerprint)
                                # update app instance
                                # EstablishAppInstance()
                            elif data['Action']['Request'] == 'EncryptaAuth_CacheSession':
                                SetUpAccount(data['Transfer']['User'])
                                await ApplicationSession.ApplicationInterfaceSocket.send(json.dumps({'Action': {'Response': 'InitiateUserSignIn'}, 'Transfer': {'Code': '25', 'UserAuthentication': True}}))
                                ApplicationSession.remove('ApplicationInterfaceSocket')
                                # update Session
                                # SetSession(ApplicationSession.ProfileFingerprint)
                                # update app instance
                                # EstablishAppInstance()
                        else:
                            await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '40', 'Reason' : 'Socket Connection Unauthorized!'}}))
                else:
                    await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '33', 'Reason' : 'Invalid Message!'}}))
            elif path == '/EncryptaBrowserCompanionCommunicationInterface':
                if 'Action' in data and 'Request' in data['Action']:
                    if data['Action']['Request'] == 'Initiate':
                        if 'APP_ID' in data['Transfer']:
                            Config = GetAppConfig()
                            InstanceIndex = Config['AppConfiguration']['AppInstances'].index((list(filter(lambda instance: instance['InstanceID'] == ApplicationSession.InstanceID, Config['AppConfiguration']['AppInstances'])))[0])
                            AppID = data['Transfer']['APP_ID']
                            App = list(filter(lambda app: app['APP_ID'] == AppID, Config['AppConfiguration']['AppInstances'][InstanceIndex]['ConnectedApps']))[0]
                            AppIndex = Config['AppConfiguration']['AppInstances'][InstanceIndex]['ConnectedApps'].index(App)
                            if (App['Client_ID'] in ServerClientConnection):
                                ServerClientConnection[App['Client_ID']]['App']['Key'] = data['Transfer']['Key']
                                await websocket.send(json.dumps({'Action': {'Response': 'Acknowledgement'}, 'Transfer': {'Code': '25', 'ClientId': App['Client_ID'], 'AppID': AppID}}))
                            else:
                                _clientId = clientId(True)
                                ServerClientConnection[_clientId] = {'App': data['Transfer'], 'AppID': AppID, 'ConnectionPulse': int(time.time()), 'Socket': websocket}
                                Config['AppConfiguration']['AppInstances'][InstanceIndex]['ConnectedApps'][AppIndex]['Client_ID'] = _clientId
                                SetAppConfig(Config)
                                await websocket.send(json.dumps({'Action': {'Response': 'Acknowledgement'}, 'Transfer': {'Code': '25', 'ClientId': _clientId, 'AppID': AppID}}))
                        else:
                            _clientId = clientId(True)
                            AppID = ConnectApp(websocket, _clientId, data['Transfer'])
                            ServerClientConnection[_clientId] = {'App': data['Transfer'], 'AppID': AppID, 'ConnectionPulse': int(time.time()), 'Socket': websocket}
                            await websocket.send(json.dumps({'Action': {'Response': 'Acknowledgement'}, 'Transfer': {'Code': '25', 'ClientId': _clientId, 'AppID': AppID}}))
                    else:
                        if data['Transfer']['ClientID'] in ServerClientConnection and ServerClientConnection[data['Transfer']['ClientID']]['App']['Key'] == data['Transfer']['Key']:
                            if data['Action']['Request'] == 'Authenticator':
                                with open(ApplicationSession.ProfileImage, 'rb') as profile:
                                    Profile_bs64 = base64.b64encode(profile.read()).decode('utf-8')
                                    await websocket.send(json.dumps({'Action': {'Response': data['Action']['Request']}, 'Transfer': {'Code': '25', 'Profile': {'ProfileName': ApplicationSession.ProfileName, 'UserName': ApplicationSession.UserName, 'EmailID': ApplicationSession.Email, 'Fingerprint': ApplicationSession.ProfileFingerprint, 'ProfileImage': Profile_bs64}, 'App' : {'InstanceID': ApplicationSession.InstanceID}}}))
                            if data['Action']['Request'] == 'Authentication_State':
                                await websocket.send(json.dumps({'Action': {'Response': data['Action']['Request']}, 'Transfer': {'Code': '25', 'Authentication': {'State': random.choice([True, False]), 'Expiry': time.time() + random.randint(1, 13)*60}}}))
                            elif data['Action']['Request'] == 'Authenticate':
                                print('Authenticate')
                                await websocket.send(json.dumps({'Action': {'Response': data['Action']['Request']}, 'Transfer': {'Code': '25', 'Authenticator': {'Acknowledgement': True}}}))
                                await ApplicationSession.ApplicationInterfaceSocket.send(json.dumps({'Action': {'Response': 'Authtenticate'}, 'Transfer': {'Code': '25', 'Authenticate': 'Triggered by companion!'}}))
                                # await SessionAuthentication()
                                # await asyncio.sleep(4)

                                # print(ApplicationSession.ApplicationInterfaceSocket)
                                # await recognize.VisionDeviceSetup(ApplicationSession.PreferredDevices['Vision'], ApplicationSession.ApplicationInterfaceSocket, 'Vision_RecognitionFeedInitiate')
                                # await recognize.VisionFeed(ApplicationSession.ApplicationInterfaceSocket, 'Vision_RecognitionFeed', '')
                                await websocket.send(json.dumps({'Action': {'Request': 'SecureSession'}, 'Transfer': {'Code': '25', 'Authenticator': {'Authentication': True}}}))     
                else:
                    await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '33', 'Reason' : 'Invalid Message!'}}))
            elif path == '/AuthApp_CommunicationInterface':
                if 'Action' in data and 'Request' in data['Action']:
                    if data['Action']['Request'] == 'Initiate':
                        _clientId = clientId(True, True)
                        ServerClientConnection[_clientId] = {'App': data['Transfer'], 'ConnectionPulse': int(time.time()), 'Socket': websocket}
                        await websocket.send(json.dumps({'Action': {'Response': 'Acknowledgement'}, 'Transfer': {'Code': '25', 'ClientId': _clientId}}))
                    else:
                        if data['Transfer']['ClientID'] in ServerClientConnection and ServerClientConnection[data['Transfer']['ClientID']]['App']['Key'] == data['Transfer']['Key']:
                            ApplicationSession.ApplicationInterfaceSocket = websocket
                            if data['Action']['Request'] == 'Get_UserProfile':
                                if ApplicationSession.ProfileFingerprint is not None:
                                    await websocket.send(json.dumps({'Action': {'Response': 'Get_UserProfile'}, 'Transfer': {'Code': '25', 'Profile' : {'Fingerprint': ApplicationSession.ProfileFingerprint, 'ProfileName': ApplicationSession.ProfileName, 'Image': ApplicationSession.ProfileImage}, 'System': {'User': local_network.currentSystem()[2], 'Device': local_network.currentSystem()[3]}, 'User': {'UserName': ApplicationSession.UserName, 'EmailID': ApplicationSession.Email, 'UserKey': ApplicationSession.UserKey, 'SessionKey': ApplicationSession.SessionKey}, 'App': {'InstanceID': ApplicationSession.InstanceID, 'Version': AppConfig['Version'], 'AppName': AppConfig['Name'], 'Framework': 'EncryptaAuthenticator/1.2 <EncryptaAuthDeviceFramework/1.4>'}}}))
                                else:
                                    if ApplicationSession.SessionKey is not None:
                                        await websocket.send(json.dumps({'Action': {'Response': 'Get_UserProfile'}, 'Transfer': {'Code': '25', 'Profile' : None, 'System': {'User': local_network.currentSystem()[2], 'Device': local_network.currentSystem()[3]}, 'App': {'InstanceID': ApplicationSession.InstanceID, 'Version': AppConfig['Version'], 'AppName': AppConfig['Name'], 'Framework': 'EncryptaAuthenticator/1.2 <EncryptaAuthDeviceFramework/1.4>'}, 'User': {'UserName': ApplicationSession.UserName, 'EmailID': ApplicationSession.Email, 'UserKey': ApplicationSession.UserKey, 'SessionKey': ApplicationSession.SessionKey }, "Profiles": [{'Name': profile['Profile']['ProfileName'], 'Fingerprint': profile['Profile']['ProfileFingerprint'], 'ProfileImage': f"{profile['Profile']['ProfileImage']}"} for profile in getUser()]}}))
                                    else:
                                        await websocket.send(json.dumps({'Action': {'Response': 'Get_UserProfile'}, 'Transfer': {'Code': '25', 'Profile' : None, 'System': {'User': local_network.currentSystem()[2], 'Device': local_network.currentSystem()[3]}, 'App': {'InstanceID': ApplicationSession.InstanceID, 'Version': AppConfig['Version'], 'AppName': AppConfig['Name'], 'Framework': 'EncryptaAuthenticator/1.2 <EncryptaAuthDeviceFramework/1.4>'}, 'User': None}}))
                            elif data['Action']['Request'] == 'AddUserProfile':
                                # ProfileAdd({'profile': {'Name': 'ankit', 'picture': r'C:\Users\mypc\Desktop\Desktop Authentication Client\Uni_Directional_Connection\static\assets\Encrypta-w-full-enl.png', 'PIN': '123456'}, 'Account': {'Username': 'Ankit_K_Nayak', 'EmailID': 'ankitnayak172@gmail.com', 'UserID': 3, 'UserKey': ''.join([random.choice(string.ascii_letters) for i in range(30)]), 'SessionKey': ''.join([random.choice(string.ascii_letters) for i in range(30)])}, 'Config': {'AuthDirectory': 'C://User/Ankit', }})
                                ProfileAdd({'profile': data['Transfer']['Profile']})
                                await websocket.send(json.dumps({'Action': {'Response': 'AddUserProfile'}, 'Transfer': {'Code': '25', 'Response': True}}))
                            elif data['Action']['Request'] == 'SelectUser':
                                SetSession(data['Transfer']['fingerprint'])
                                await websocket.send(json.dumps({'Action': {'Response': 'SelectUser'}, 'Transfer': {'Code': '25', 'Response': True}}))
                            elif data['Action']['Request'] == 'InitiateUserSignIn':
                                webbrowser.open(f"http://accounts.encrypta.in/?ExternalLoginType=CookieLess&SUCCESS=http://{ApplicationSession.HttpServerAddress['host']}:{ApplicationSession.HttpServerAddress['port']}&AppID={ApplicationSession.InstanceID}")
                            elif data['Action']['Request'] == 'Auth_UserProfilePin':
                                Auth = sha256_crypt.verify(data['Transfer']['PIN'], ApplicationSession.ProfileKey_Auth)
                                await websocket.send(json.dumps({'Action': {'Response': 'Auth_UserProfilePin'}, 'Transfer': {'Code': '25', 'UserAuthentication': Auth}}))
                                if Auth and hasattr(ApplicationSession, 'UserKey'):
                                    # Broadcast authentication status in a background thread
                                    broadcast_thread = threading.Thread(
                                        target=network_auth.broadcast_auth_status,
                                        args=(ApplicationSession.UserKey,),
                                        daemon=True
                                    )
                                    broadcast_thread.start()
                                    SystemLog("Broadcasted authentication status to network")
                            elif data['Action']['Request'] == 'User_SecurityOverview':
                                user = list(filter(lambda x: x['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint , getUser()))[0]
                                await websocket.send(json.dumps({'Action': {'Response': 'User_SecurityOverview'}, 'Transfer': {'Code': '25', 'ProfileSecurityOverview': user['Configuration']['Authentication']}}))
                            elif data['Action']['Request'] == 'Update_ProfilePassword':
                                UserObj = getUser()
                                for user in UserObj:
                                    if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                                        user['Profile']['ProfileKey'] = sha256_crypt.hash(data['Transfer']['Password'])
                                        user['Configuration']['Authentication']['Password'] = True
                                        user['Configuration']['Authentication']['PIN'] = False
                                # SetUser(UserObj)
                                await websocket.send(json.dumps({'Action': {'Response': 'Update_ProfilePassword'}, 'Transfer': {'Code': '25', 'Response': True}}))
                            elif data['Action']['Request'] == 'Update_ProfilePIN':
                                UserObj = getUser()
                                for user in UserObj:
                                    if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                                        user['Profile']['ProfileKey'] = sha256_crypt.hash(data['Transfer']['PIN'])
                                        user['Configuration']['Authentication']['PIN'] = True
                                        user['Configuration']['Authentication']['Password'] = False
                                # SetUser(UserObj)
                                await websocket.send(json.dumps({'Action': {'Response': 'Update_ProfilePIN'}, 'Transfer': {'Code': '25', 'Response': True}}))
                            elif data['Action']['Request'] == 'AvailableCamera':
                                VisionDeviceSelection.PreferredCameraSetup(ApplicationSession.PreferredDevices['Vision'])
                                if ApplicationSession.PreferredDevices['Vision'] is None:
                                    VisionDeviceSelection.check_and_set_available_cameras()
                                    await VisionDeviceSelection.AvailableCameras(websocket, 'AvailableCamera')
                                else:
                                    await websocket.send(json.dumps({'Action': {'Response': 'AvailableCamera'}, 'Transfer': {'Code': '25', 'CameraPreferred': ApplicationSession.PreferredDevices['Vision']}}))
                            elif data['Action']['Request'] == 'CameraSelectionFeedInitiator':
                                    await websocket.send(json.dumps({'Action': {'Response': 'CameraSelectionFeedInitiator'}, 'Transfer': {'Code': '25', 'FeedTransferInitiation': True}}))
                                    await VisionDeviceSelection.CameraSelection(websocket, 'CameraSelectionFeed')
                            elif data['Action']['Request'] == 'VisionFeedInitiate':
                                await register.VisionDeviceSetup(ApplicationSession.PreferredDevices['Vision'], websocket, 'VisionFeedInitiate')
                                await register.VisionFeed(websocket, 'VisionFeed',  f"{ProfileDirectory}/Profiles/{ApplicationSession.ProfileFingerprint}/{'primary' if data['Transfer']['Primary'] else 'secondary' if data['Transfer']['Alternate'] else None }")
                            elif data['Action']['Request'] == 'VisionIDRegistrationCompletion':
                                UserObj = getUser()
                                for user in UserObj:
                                    if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                                        user['Configuration']['Authentication']['VisionID'] = True
                                # SetUser(UserObj)
                                await websocket.send(json.dumps({'Action': {'Response': 'VisionIDRegistrationCompletion'}, 'Transfer': {'Code': '25', 'VisionIDRegister': True}}))
                            elif data['Action']['Request'] == 'AlternateVisionIDRegistrationCompletion':
                                UserObj = getUser()
                                for user in UserObj:
                                    if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                                        user['Configuration']['Authentication']['Alternate_FacialRecognition'] = True
                                # SetUser(UserObj)
                                await websocket.send(json.dumps({'Action': {'Response': 'AlternateVisionIDRegistrationCompletion'}, 'Transfer': {'Code': '25', 'VisionIDRegister': True}}))
                            elif data['Action']['Request'] == 'VisionIDStructureRemoval':
                                UserObj = getUser()
                                for user in UserObj:
                                    if user['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint:
                                        # delete the data
                                        user['Configuration']['Authentication']['VisionID'] = not data['Transfer']['Primary']
                                        user['Configuration']['Authentication']['Alternate_FacialRecognition'] = not data['Transfer']['Alternate']
                                        print(user['Configuration']['Authentication'])
                                # SetUser(UserObj)
                                await websocket.send(json.dumps({'Action': {'Response': 'VisionIDStructureRemoval'}, 'Transfer': {'Code': '25', 'Removal': True}}))
                            elif data['Action']['Request'] == 'AvailableFPSensor':
                                await websocket.send(json.dumps({'Action': {'Response': 'AvailableFPSensor'}, 'Transfer': {'Code': '25', 'AvailableSensors': []}}))
                            elif data['Action']['Request'] == 'LocalNetworkScan':
                                Devices = (local_network.get_local_devices())
                                # print(Devices)
                                Devices[-1] = (Devices[-1][0], ApplicationSession.InstanceID, Devices[-1][2], Devices[-1][3], Devices[-1][4])
                                await websocket.send(json.dumps({'Action': {'Response': 'LocalNetworkScan'}, 'Transfer': {'Code': '25', 'Devices': Devices}}))
                            elif data['Action']['Request'] == 'ToggleTrackingPreference':
                                    ApplicationSession.TrackingPreference.Cursor = data['Transfer']['Preference']['Cursor']
                                    ApplicationSession.TrackingPreference.Vision = data['Transfer']['Preference']['Vision']
                                    with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
                                        config = json.load(file)
                                        Instance = list(filter(lambda x: x['InstanceID'] == ApplicationSession.InstanceID, config['AppConfiguration']['AppInstances']))[0]
                                        InstanceIndex = config['AppConfiguration']['AppInstances'].index(Instance)
                                    if not(ApplicationSession.TrackingPreference.Cursor) and CursorTrackingThread:
                                        cursor.CursorTracking = False
                                        CursorTrackingThread.stop()
                                        config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Tracking']['Cursor'] = data['Transfer']['Preference']['Cursor']
                                    elif ApplicationSession.TrackingPreference.Vision:
                                        VisionTrackingInterval = data['Transfer']['Preference']['VisionInterval']
                                        config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['Tracking']['Vision'] = data['Transfer']['Preference']['Vision']
                                    with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
                                        json.dump(config, file)
                                    await websocket.send(json.dumps({'Action': {'Response': 'ToggleTrackingPreference'}, 'Transfer': {'Code': '25', 'State': True}}))
                            elif data['Action']['Request'] == 'ProfileSecurityOverview':
                                user = list(filter(lambda profile: profile['Profile']['ProfileFingerprint'] == ApplicationSession.ProfileFingerprint, getUser()))[0]
                                await websocket.send(json.dumps({'Action': {'Response': 'ProfileSecurityOverview'}, 'Transfer': {'Code': '25', 'AuthenticatorAssist': bool(random.randint(0,1)), 'CursorActivity': 4, 'PIN': user['Configuration']['Authentication']['PIN'], 'Password': user['Configuration']['Authentication']['Password'], 'Vision': user['Configuration']['Authentication']['VisionID'], 'Fingerprint': user['Configuration']['Authentication']['Fingerprint']}}))
                            elif data['Action']['Request'] == 'ConnectedApplications':
                                    await websocket.send(json.dumps({'Action': {'Response': 'ConnectedApplications'}, 'Transfer': {'Code': '25', 'Apps': [{'AppID': ApplicationSession.InstanceID, 'Name': AppConfig['Name'], 'Framework': 'EncryptaAuthenticator/1.2 <EncryptaAuthDeviceFramework/1.4>','State': random.choice(['ACTIVE', 'INACTIVE', 'CONNECTED', 'IDLE'])} for i in range(4)]}}))
                            elif data['Action']['Request'] == 'CursorActivity':
                                if ApplicationSession.TrackingPreference.Cursor:
                                    # CursorTrackingThread = threading.Thread(target=cursor.InitiateTracking())
                                    # CursorTrackingThread.start()
                                    await websocket.send(json.dumps({'Action': {'Response': 'CursorActivity'}, 'Transfer': {'Code': '25', 'Activity': cursor.CursorActivity[-1], 'dt': time.time() - cursor.CursorActivity[-1]['Time']}}))
                            elif data['Action']['Request'] == 'Vision_RecognitionFeedInitiate':
                                primary = data['Transfer'].get('Primary', False) 
                                alternate = data['Transfer'].get('Alternate', False)
                                path = 'primary' if primary else 'secondary' if alternate else 'primary'

                                await recognize.set_user_key(ApplicationSession.UserKey if hasattr(ApplicationSession, 'UserKey') else None)
                                await recognize.set_system_log(SystemLog)
                                await recognize.VisionDeviceSetup(ApplicationSession.PreferredDevices['Vision'], websocket, 'Vision_RecognitionFeedInitiate')
                                await recognize.VisionFeed(websocket, 'Vision_RecognitionFeed', f"{ProfileDirectory}/Profiles/{ApplicationSession.ProfileFingerprint}/{path}")
                        else:
                            await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '40', 'Reason' : 'Socket Connection Unauthorized!'}}))
                else:
                    await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '33', 'Reason' : 'Invalid Message!'}}))
    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected")



async def _Handler(websocket, path):
    print(path)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            if path == '/AuthApp_CommunicationInterface':
                if 'Action' in data and 'Request' in data['Action']:
                    if data['Action']['Request'] == 'SelectPreferredCamera':
                        VisionDeviceSelection.PreferredCameraSetup(data['Transfer']['preference'])
                        with open(f'{AppDirectory}Configuration/App.json', 'r') as file:
                            config = json.load(file)
                        Instance = list(filter(lambda x: x['InstanceID'] == ApplicationSession.InstanceID, config['AppConfiguration']['AppInstances']))[0]
                        InstanceIndex = config['AppConfiguration']['AppInstances'].index(Instance)
                        config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['InputDevices']['Biometrics']['Vision'] = data['Transfer']['preference']
                        config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['InputDevices']['Biometrics']['Vision']['VisionID'] = ''.join([random.choice(string.ascii_uppercase + string.digits) for i in range(8)])
                        ApplicationSession.PreferredDevices = config['AppConfiguration']['AppInstances'][InstanceIndex]['Instance']['InputDevices']['Biometrics']
                        await websocket.send(json.dumps({'Action': {'Response': 'SelectPreferredCamera'}, 'Transfer': {'Code': '25', 'PreferredCamera': True}}))
                        await websocket.send(json.dumps({'Action': {'Response': 'SocketClosed'}, 'Transfer': {'Code': '25', 'Socket': False}}))
                        await websocket.close()
                        # with open(f'{AppDirectory}Configuration/App.json', 'w') as file:
                            # json.dump(config, file)
            else:
                await websocket.send(json.dumps({'Action': {'Command': 'CloseConnection'}, 'Transfer': {'Code': '33', 'Reason' : 'Invalid Message!'}}))
        
    except websockets.exceptions.ConnectionClosedOK:
            print("Client disconnected")

# print(VisionDeviceSelection.check_and_set_available_cameras())

# host = 'localhost'
# host = local_network.currentSystem()[0]
# port = '17267'
start_server_2 = websockets.serve(_Handler, AppConfig['WebsocketServer']['Host'], AppConfig['WebsocketServer']['Port']+1)
start_server = websockets.serve(Handler, AppConfig['WebsocketServer']['Host'], AppConfig['WebsocketServer']['Port'])
try:
    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_until_complete(start_server_2)
        print(f'WebSocket Server Running since {datetime.now()}')
        print(f"Server Running on ws://{AppConfig['WebsocketServer']['Host']}:{AppConfig['WebsocketServer']['Port']}")
        asyncio.get_event_loop().run_forever()
    except OSError as e:
        if hasattr(e, 'errno') and e.errno == 10048:
            SystemLog(f"Required port {AppConfig['WebsocketServer']['Port']} on {AppConfig['WebsocketServer']['Host']} is not available or {AppConfig['Name']} might being used by another System User.")
        else:
            SystemLog(f"Network error: {e}")
    except RuntimeError as e:
        SystemLog(f"Runtime error: {e}")
    except Exception as e:
        
        SystemLog(f"Error starting server: {e}")
except KeyboardInterrupt:
    print("Stopping servers...")
    NetworkAuth.network_auth.stop_listening()
    http_server.Exit()
    asyncio.get_event_loop().stop()
finally:
    try:
        NetworkAuth.network_auth.stop_listening()
        http_server.Exit()
        # Only stop the event loop if it's running
        if asyncio.get_event_loop().is_running():
            asyncio.get_event_loop().stop()
    except Exception as e:
        print(f"Error during cleanup: {e}")

