----has keyword
 SELECT distinct attraction.id FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id WHERE (attraction.name like %s or mrt.mrtname = %s)
 ---else:
 SELECT distinct attraction.id FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id LEFT JOIN att_url ON attraction.id = att_url.attraction_id


 targAttrIdList =[1,2,3,4,5]--符合條件的總景點ID array
 len(targAttrIdList)--符合條件的總景點數量
 (len(targAttrIdList)/12)+1 --- 總頁數



 SELECT attraction.*, mrt.mrtname FROM attraction LEFT JOIN mrt ON attraction.mrt_id = mrt.id
 WHERE attraction.id IN (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15) LIMIT 12 OFFSET (0*12);--當夜景點資料

SELECT url FROM att_url WHERE attraction_id IN ()


