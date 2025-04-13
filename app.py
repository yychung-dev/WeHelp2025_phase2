from fastapi import *
from fastapi.responses import FileResponse,JSONResponse
from typing import Optional

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

import base64
import jwt
import datetime

app=FastAPI()

SECRET_KEY="secret" 
ALGORITHM = "HS256"

import mysql.connector.pooling
import mysql.connector
config={
    "user":"root",
    "password":"fumafaith7_",
    "host":"localhost",
    "database":"tptrip"
    }
cnxpool=mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=20, **config)

templates = Jinja2Templates(directory="static")

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
                # COUNT總資料的數量(條件：有keyword, 無keyword)
                if (keyword != None): 
                    attKeyword = "%" + keyword + "%"
                    cursor.execute("SELECT COUNT(DISTINCT attraction.id) FROM attraction "
                                   "LEFT JOIN mrt ON attraction.mrt_id = mrt.id "
                                   "LEFT JOIN att_url ON attraction.id = att_url.attraction_id "
                                   "WHERE (attraction.name LIKE %s OR mrt.mrtname = %s)", [attKeyword, keyword])
                else:
                    cursor.execute("SELECT COUNT(DISTINCT attraction.id) FROM attraction")
                
                total_count = cursor.fetchone()[0]
                totalPages = (total_count // 12) + (1 if total_count % 12 != 0 else 0)
                print('totalPages=', totalPages)

                if page <= (totalPages - 1):
                    offset = page * 12
                    print('offset=', offset)

                    # SELECT時做pagination(LIMIT and OFFSET)
                    if keyword:
                        cursor.execute(f"SELECT attraction.*, mrt.mrtname FROM attraction "
                                       f"LEFT JOIN mrt ON attraction.mrt_id = mrt.id "
                                       f"WHERE (attraction.name LIKE %s OR mrt.mrtname = %s) "
                                       f"ORDER BY attraction.id LIMIT 12 OFFSET %s", [attKeyword, keyword, offset])
                    else:
                        cursor.execute(f"SELECT attraction.*, mrt.mrtname FROM attraction "
                                       f"LEFT JOIN mrt ON attraction.mrt_id = mrt.id "
                                       f"ORDER BY attraction.id LIMIT 12 OFFSET %s", [offset])

                    attractionList = cursor.fetchall()

                    resultAttrIdList = []
                    attrArray = []
                    for j in range(0, len(attractionList)):
                        resultAttrIdList.append(attractionList[j][0])  
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
                                "images": []
                            }
                        attrArray.append(attrData)  

                    resultAttrIdStr = ', '.join(['%s'] * len(resultAttrIdList))
                    cursor.execute(f"SELECT DISTINCT attraction_id, url FROM att_url "
                                   f"WHERE attraction_id IN ({resultAttrIdStr}) "
                                   f"ORDER BY attraction_id", resultAttrIdList)
                    attrURLList = cursor.fetchall()         
                    
                    for j in range(0, len(attrURLList)):  
                        attrID = attrURLList[j][0]
                        index = resultAttrIdList.index(attrID)
                        attrArray[index]["images"].append(attrURLList[j][1])

                if page < (totalPages - 1): 
                    return {"nextPage": page + 1,
                            "data": attrArray
                            }
                elif page == (totalPages - 1):
                    return {"nextPage": None,
                            "data": attrArray
                            }                    
                else:
                    return {"nextPage": None,
                            "data": []
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
                    cursor.execute("SELECT DISTINCT attraction.*, mrt.mrtname, att_url.url FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id WHERE attraction.id = %s",[attractionId,])
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
                cursor.execute("SELECT DISTINCT mrt.mrtname, COUNT(attraction.name) AS attraction_counts FROM attraction JOIN mrt ON mrt.id = attraction.mrt_id GROUP BY mrt.mrtname ORDER BY attraction_counts DESC")
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

# 註冊一個新的會員 api

class newacctInfo(BaseModel):
    name: str
    email: str
    password: str

@app.post("/api/user")
async def signup(newacctInfo:newacctInfo,request:Request):
    with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM member WHERE email=%s" ,[newacctInfo.email,])
                data_name=cursor.fetchall()[0][0]
                try:
                    if data_name>0:  
                        return JSONResponse(
                            status_code=400,
                            content={"error": True, "message": "註冊失敗，重複的 Email 或其他原因"}
                        )

                    else:  
                        cursor.execute("INSERT INTO member(name, email, password) VALUES(%s, %s, %s) ",[newacctInfo.name, newacctInfo.email,newacctInfo.password])
                        cnx.commit()
                        return JSONResponse(
                            status_code=200,
                            content={"ok": True}
                        )
                except Exception:
                    return JSONResponse(
                        status_code=500,
                        content={"error": True, "message": "伺服器內部錯誤"}
                    )

        
                        
# 登入會員帳戶 api

def create_jwt_token(user_id,name,email):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)  
    payload = {
        "sub": "userinfo",  
        "exp": expiration,  
        "id":user_id,
        "name":name,
        "email":email,        
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

class acctInfo(BaseModel):    
    email: str
    password: str
                         
@app.put("/api/user/auth")
async def signin(acctInfo:acctInfo, request:Request): 
    # print(acctInfo)    
    with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:
                cursor.execute("SELECT id,name,email,password FROM member WHERE email=%s and password=%s",[acctInfo.email,acctInfo.password])
                data=cursor.fetchall()                
                try:
                    if data!=[]:       
                        user_id = data[0][0]
                        name = data[0][1]
                        email = data[0][2]
                        token=create_jwt_token(user_id,name,email)
                                                
                        response = JSONResponse(
                            status_code=200,
                            content={
                                "token":token
                            }
                        )
                        return response
                    else:
                        return JSONResponse(
                        status_code=400,
                        content={"error": True, "message": "登入失敗，帳號或密碼錯誤或其他原因"}
                    )

                except Exception:
                    return JSONResponse(
                        status_code=500,
                        content={"error": True, "message": "伺服器內部錯誤"}
                    )


# 取得當前登入的會員資訊 api：

def get_current_user(request:Request):  
    token = request.headers.get("Authorization")
    if token is None:
        return None  

    token = token.replace("Bearer ", "").strip()
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload   
    except:
        return None 

@app.get("/api/user/auth")
async def checkSignin(request:Request): 
    authorization= get_current_user(request)
       
    if (authorization is None):
        return None
    else:
        response={
            "data":{
                "id":authorization['id'],
                "name":authorization['name'],
                "email":authorization['email']
            }
        }
        return response


# 取得尚未確認下單的預定行程 api
@app.get("/api/booking")
async def checkIfBooking(request:Request): 
    authorization= get_current_user(request)
    if (authorization is None):
        return JSONResponse(
            status_code=403,
            content={"error": True,
              "message": "未登入系統，拒絕存取"}
            ) 
    with cnxpool.get_connection() as cnx: 
        with cnx.cursor() as cursor:
            try:
                cursor.execute("SELECT booking.member_id, booking.attraction_id,attraction.name, attraction.address, att_url_new.url, booking.date, booking.time, booking.price FROM booking JOIN attraction ON booking.attraction_id = attraction.id JOIN (SELECT att_url.attraction_id, att_url.url, ROW_NUMBER() OVER (PARTITION BY att_url.attraction_id ORDER BY att_url.id) AS rn FROM att_url) AS att_url_new ON booking.attraction_id = att_url_new.attraction_id WHERE booking.member_id = %s AND att_url_new.rn = 1",[authorization['id']])
                data=cursor.fetchall()
                # No need to SELECT booking.member_id ? 
                if data==[]:
                    return None
                else:
                    member_id=data[0][0]
                    attraction_id=data[0][1]
                    name=data[0][2]
                    address=data[0][3]
                    image=data[0][4]
                    date=data[0][5]
                    time=data[0][6]
                    price=data[0][7]

                    return {                    
                        "data":{
                            "attraction":{
                                "id":attraction_id,
                                "name":name,
                                "address":address,
                                "image":image
                        
                            },                   
                        "date":date,
                        "time":time,
                        "price":price
                        }
                    }

                
            except Exception:
                return JSONResponse(
                    status_code=500,
                    content={"error": True, "message": "伺服器內部錯誤"}
                )



# 建立新的預定行程 api
class newBooking(BaseModel):    
    attractionId: int
    date:str
    time:str
    price:int

@app.post("/api/booking")
async def startbooking(newBooking:newBooking,request:Request):
    authorization= get_current_user(request)
    if (authorization is None):
        return JSONResponse(
            status_code=403,
            content={"error": True,
              "message": "未登入系統，拒絕存取"}
            )
    if not all([newBooking.attractionId, newBooking.date, newBooking.time, newBooking.price]):
        return JSONResponse(
            status_code=400,
            content={"error": True,
              "message": "建立失敗，輸入不正確或其他原因"}
            )
    with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:                                  
                try:
                    cursor.execute("SELECT COUNT(*) FROM booking WHERE member_id=%s" ,[authorization['id']]) 
                    data=cursor.fetchall()[0][0]  
                    if data>0:
                        cursor.execute("UPDATE booking SET attraction_id=%s, `date`=%s,time=%s,price=%s WHERE member_id=%s", [newBooking.attractionId,newBooking.date,newBooking.time,newBooking.price,authorization['id']])
                        
                    else:  # data=0 
                        cursor.execute("INSERT INTO booking(attraction_id, `date`, time,price, member_id) VALUES(%s, %s, %s, %s, %s) ",[newBooking.attractionId, newBooking.date, newBooking.time, newBooking.price, authorization['id']])

                    cnx.commit()
                    return {"ok": True}    
                
                except Exception:
                    return JSONResponse(
                        status_code=500,
                        content={"error": True, "message": "伺服器內部錯誤"}
                    )


# 刪除目前的預定行程 api
@app.delete("/api/booking")
async def deletebooking(request:Request):
    authorization= get_current_user(request)
    if (authorization is None):
        return JSONResponse(
            status_code=403,
            content={"error": True,
              "message": "未登入系統，拒絕存取"}
            )
    with cnxpool.get_connection() as cnx: 
            with cnx.cursor() as cursor:                                  
                try:                
                    cursor.execute("DELETE FROM booking WHERE member_id = %s",[authorization['id'],])
                    cnx.commit()
                    return {"ok": True}  

                except Exception as e:
                    logging.error(f"Error occurred while deleting booking: {str(e)}")
                    return JSONResponse(
                        status_code=500,
                        content={"error": True, "message": "伺服器內部錯誤"}
                    )
                 



app.mount("/",StaticFiles(directory="static",html=True))
app.mount("/static", StaticFiles(directory="static"), name="static")