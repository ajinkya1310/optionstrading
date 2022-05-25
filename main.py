from numpy import flipud
import pandas as pd
from distutils.log import error
import pandas as pd
from pyparsing import line
import plotly.express as px
import plotly.graph_objects as go
# import streamlit as st
import pyrebase
import time
import matplotlib.pyplot as plt
import pyrebase

firebaseConfig = {
  "apiKey": "AIzaSyC-JfGUVHdUHMYmKjt06Jhjks9rxhnU5lA",
  "authDomain": "optionskew.firebaseapp.com",
  "databaseURL": "https://optionskew-default-rtdb.firebaseio.com",
  "projectId": "optionskew",
  "storageBucket": "optionskew.appspot.com",
  "messagingSenderId": "507110709117",
  "appId": "1:507110709117:web:00f5f1201896a883c81e14"
}


firebase = pyrebase.initialize_app(firebaseConfig)
database = firebase.database()
user = 'FA20587'
pwd = 'Boss@1310'
factor2 = 'ABOPI5570L'
vc = 'FA20587_U'
app_key = '24e81cf8f74efb36bce446f8f7d6cf59'
imei = 'abc1234'

from NorenRestApiPy.NorenApi import  NorenApi
from datetime import datetime

class ShoonyaApiPy(NorenApi):
    def __init__(self):
        NorenApi.__init__(self, host='https://shoonyatrade.finvasia.com/NorenWClientTP/', websocket='wss://shoonyatrade.finvasia.com/NorenWSTP/', eodhost='https://shoonya.finvasia.com/chartApi/getdata/')



#start of our program
api = ShoonyaApiPy()


 
#make the api call
ret = api.login(userid=user, password=pwd, twoFA=factor2, vendor_code=vc, api_secret=app_key, imei=imei)

# st.set_page_config(page_title="Option Analysis",page_icon="💰",layout="wide",)
# placeholder = st.empty()


feed_opened = False
feedJson = {}
def event_handler_feed_update(tick_data):
     if 'lp' in tick_data and 'tk' in tick_data :
        timest = datetime.fromtimestamp(int(tick_data['ft'])).isoformat()
        feedJson[tick_data['tk']]  = {'ltp': float(tick_data['lp']) , 'atp': float(tick_data['ap']) }

def event_handler_order_update(tick_data):
    print(f"Order update {tick_data}")

def open_callback():
    global feed_opened
    feed_opened = True


api.start_websocket( order_update_callback=event_handler_order_update,
                     subscribe_callback=event_handler_feed_update, 
                     socket_open_callback=open_callback)

while(feed_opened==False):
    pass

while True:
    try :
        nifty = api.get_quotes('NSE','Nifty 50')
        nifltp = float(nifty['lp'])
        nfcls = float(nifty['c'])
    
    

        import math
        mod = int(nifltp)%100
        if mod < 50:
            nifstk =  int(math.floor(nifltp / 100)) * 100
        else:
            nifstk=  int(math.ceil(nifltp /100)) * 100
        
        banknifty = api.get_quotes('NSE','Nifty Bank')
        bnfltp = float(banknifty['lp'])

    
        import math
        mod = int(bnfltp)%100

        if mod < 50:
            bnfstk =  int(math.floor(bnfltp / 100)) * 100
        else:
            bnfstk=  int(math.ceil(bnfltp /100)) * 100
            

        chain = api.get_option_chain(exchange='NFO', tradingsymbol='NIFTY26MAY22F', strikeprice=nifstk, count=6)
        chain2 = api.get_option_chain(exchange='NFO', tradingsymbol='BANKNIFTY26MAY22F', strikeprice=bnfstk, count=6)
        df = pd.DataFrame(chain['values'])
        
        dfce = df.query('optt == "CE"')
        dfpe = df.query('optt == "PE"')
        res2 = pd.concat([dfce, dfpe])
        df2= dfce.sort_values("strprc", axis = 0, ascending = False,inplace = False)
        df3= dfpe.sort_values("strprc", axis = 0, ascending = False,inplace = False)
        final = pd.merge(dfce, dfpe, on="strprc", suffixes=["_CE", "_PE"])
        frames = [df2,df3]
        con = pd.concat(frames)
        df["tok"] = df['exch'] +"|"+ df["token"]
        dfce = df.query('optt == "CE"')
        dfpe = df.query('optt == "PE"')
        res2 = pd.concat([dfce, dfpe])
        df2= dfce.sort_values("strprc", axis = 0, ascending = False,inplace = False)
        df3= dfpe.sort_values("strprc", axis = 0, ascending = False,inplace = False)
        final = pd.merge(dfce, dfpe, on="strprc", suffixes=["_CE", "_PE"])
        frames = [df2,df3]
        con = pd.concat(frames)
        # con
        tokenlist = con['tok'].tolist()
        df2 = pd.DataFrame(con,columns=['tok', 'strprc', 'optt'])
        df2.sort_values(['strprc', 'optt'], ascending = (False, True))
        tokanlist = con['token'].tolist()
    except TypeError:
        print("type_error")
        break


    try:
        api.subscribe(tokenlist)
        if nifltp == None :
            print("loading data")
                    # feedJson
        df = pd.DataFrame(feedJson)
        df2 = df.transpose()
        finl = df2.rename_axis('token')
        finl['skew']=finl['ltp']-finl['atp']
        database.child('token').set(tokanlist)
        database.child('data').set(feedJson)
        df2.to_csv('sample.csv')
        
        # with placeholder.container():
        #     kpi1,kpi2 = st.columns(2)
        #     st.header("Option Chain")
        #     kpi1.metric(label= 'Strike',value = nifltp, delta = nifstk)
        #     kpi2.metric(label= 'Spot',value = nifstk )

        #     # st.([nifltp,nifstk])
        #     #st.dataframe(data=final, width=None, height=None)
        #     st.markdown("### Skew Graph NIFTY")
        #     fig = px.line(data_frame=finl, y="skew", x=df2.index ,height=550, width=1200,line_shape='spline')
        #     fig.update_layout(title_text='CE                                |                                       PE', title_x=0.5)
        #     fig.update_xaxes(title_text="Strikes")
        #     fig.update_yaxes(title_text="Buying and Selling")
        #     st.write(fig)

    except KeyError:
       print("keyerror")
    time.sleep(1)

    
