from fastapi import *
from fastapi.responses import FileResponse,JSONResponse
from typing import Optional

app=FastAPI()

import mysql.connector.pooling
import mysql.connector
config={
    "user":"root",
    "password":"fumafaith7_",
    "host":"localhost",
    "database":"tptrip"
    }
cnxpool=mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=20, **config)

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")


# 取得景點資料列表api
@app.get("/api/attractions")
async def getAttractionName(page:int,keyword:Optional[str] = None): 
    try:
        with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:
                if (keyword!=None): 
                    attKeyword="%"+keyword+"%"
                    cursor.execute("SELECT attraction.*, mrt.mrtname, att_url.url FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id WHERE (attraction.name like %s or mrt.mrtname = %s)",[attKeyword,keyword])
                else:
                    cursor.execute("SELECT attraction.*, mrt.mrtname, att_url.url FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id")
                
                attractionList=cursor.fetchall()
                attrArray = []
                imageList = []
                currentId = 0



                for j in range(0, len(attractionList)):  
                    id = attractionList[j][0]

                    if len(attrArray) == 0 and len(imageList) == 0:
                        currentId = id
                        imageList.append(attractionList[j][10])
                    elif currentId != id:
                        # 處理上一景點的Data
                        attrData = {
                            "id": attractionList[j-1][0],
                            "name": attractionList[j-1][1],
                            "category": attractionList[j-1][2],
                            "description": attractionList[j-1][3],
                            "address": attractionList[j-1][4],
                            "transport": attractionList[j-1][5],
                            "mrt": attractionList[j-1][9],
                            "lat": attractionList[j-1][7],
                            "lng": attractionList[j-1][8],
                            "images": imageList
                        }
                        attrArray.append(attrData)
                        
                        # 重置imageList，準備下一景點的圖片
                        imageList = []
                        currentId = id

                    # 如果圖片不是重複的，才增加
                    if attractionList[j][10] not in imageList:
                        imageList.append(attractionList[j][10])

                    # 如果是最後一個景點，處理Data並增加
                    if j == (len(attractionList) - 1):
                        attrData = {
                            "id": attractionList[j][0],
                            "name": attractionList[j][1],
                            "category": attractionList[j][2],
                            "description": attractionList[j][3],
                            "address": attractionList[j][4],
                            "transport": attractionList[j][5],
                            "mrt": attractionList[j][9],
                            "lat": attractionList[j][7],
                            "lng": attractionList[j][8],
                            "images": imageList
                        }
                        attrArray.append(attrData)

                result = []
                for i in range(0, len(attrArray), 12): 
                    subArr = attrArray[i:i+12] 
                    result.append(subArr) 



                if page < (len(result)-1) : 
                    return {"nextPage":page+1,
                            "data":result[page]
                            }
                elif page == (len(result)-1):
                    return {"nextPage":None,
                            "data":result[page]
                            }                    
                else:
                    return {"nextPage":None,
                            "data":[]
                            }
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )



# 根據景點編號取得景點資料api
@app.get("/api/attraction/{attractionId}")
async def getAttById(attractionId:int):
    try:
        with cnxpool.get_connection() as cnx: 
                with cnx.cursor() as cursor:
                    cursor.execute("SELECT distinct attraction.*, mrt.mrtname, att_url.url FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id WHERE attraction.id = %s",[attractionId,])
                    attractionList=cursor.fetchall()

                    urlList=[]
                    for j in range(0,len(attractionList)):
                        urlList.append(attractionList[j][len(attractionList[j])-1])

                    if (attractionList!=[]):
                        result={
                            "data":{
                                "id":attractionList[0][0],
                                "name":attractionList[0][1],
                                "category": attractionList[0][2],
                                "description": attractionList[0][3],
                                "address": attractionList[0][4],
                                "transport": attractionList[0][5],
                                "mrt": attractionList[0][9],
                                "lat": attractionList[0][7],
                                "lng": attractionList[0][8],
                                "images": urlList
                            }                          
                        }
                        return result
                    else:
                        return JSONResponse(
                            status_code=400,
                            content={"error": True, "message": "景點編號不正確"}
                        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
        




# 取得捷運站名稱列表api
@app.get("/api/mrts")
async def getMRTName(): 
    try:
        with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:
                cursor.execute("SELECT distinct mrt.mrtname, COUNT(attraction.name) AS attraction_counts FROM attraction JOIN mrt ON mrt.id = attraction.mrt_id GROUP BY mrt.mrtname ORDER BY attraction_counts DESC")
                mrtList=cursor.fetchall()

                mrtOrderArray=[]
                for i in range(0,len(mrtList)):
                    mrtOrder=mrtList[i][0]                    
                    mrtOrderArray.append(mrtOrder)
                
                
                result={
                    "data":mrtOrderArray                          
                }
                return result
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": True, "message": "伺服器內部錯誤"}
        )
