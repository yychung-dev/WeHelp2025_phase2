import json

import mysql.connector.pooling
import mysql.connector
config={
    "user":"root",
    "password":"fumafaith7_",
    "host":"localhost",
    "database":"tptrip"
    }
cnxpool=mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=20, **config)



jsonfile = open('taipei-attractions.json','r',encoding='utf-8')
jsonData=json.load(jsonfile)


rawAttrData =jsonData['result']['results']



for i in range (0,len(rawAttrData)):
    targetAttr = rawAttrData[i]
    attractionID = targetAttr["_id"]
    attractionName = targetAttr["name"]
    category = targetAttr["CAT"]
    description = targetAttr["description"]
    address = targetAttr["address"]
    transport = targetAttr["direction"]   
    mrtName = targetAttr["MRT"]
    lat = float(targetAttr["latitude"])
    lng = float(targetAttr["longitude"])

    
    if mrtName!=None: 
        with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:
                cursor.execute("SELECT id FROM mrt WHERE mrtname=%s",[mrtName,])
                mrtIdList=cursor.fetchone() 


                if mrtIdList==None:
                    with cnxpool.get_connection() as cnx:
                        with cnx.cursor() as cursor:
                            cursor.execute("INSERT INTO mrt (mrtname) VALUES (%s)",[mrtName,])
                            cnx.commit()
                            cursor.execute("SELECT id FROM mrt WHERE mrtname=%s",[mrtName,])
                            mrtId=cursor.fetchone()[0]                      
                            
                else:
                    mrtId = mrtIdList[0]                   
  
    else:
        mrtId=None


    
    with cnxpool.get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute("INSERT INTO attraction (id, name, category, description, address, transport, mrt_id, lat, lng) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",[attractionID, attractionName,category,description,address,transport,mrtId,lat,lng])
            cnx.commit()

    
    
    urlStr = targetAttr["file"]
    urlStrWithSplitter = urlStr.replace('https','-------https') 
    urlArray = urlStrWithSplitter.split('-------') 
    urlArray = list(filter(None, urlArray)) 
    for j in range (0,len(urlArray)):
        url = urlArray[j]
        fileType = url.rsplit('.', 1)[1]
        if "jpg" == fileType.lower() or "png" == fileType.lower():
            with cnxpool.get_connection() as cnx:
                with cnx.cursor() as cursor:
                    cursor.execute("INSERT INTO att_url (attraction_id,url) VALUES (%s,%s)",[attractionID, url])
                    cnx.commit()  


            

    
    
 
   

    
        