import streamlit as st
from llm import llm
from graph import graph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain.prompts.prompt import PromptTemplate

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about airport and high-speed rail station lounges and restaurants based on graph.
Convert the user's question into Cypher based on the provided schema. 
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Do not return entire nodes or embedding properties.
If you got many nodes with information please ask user which exactly he/she wants and also you can list them out.
All query you can generate use fuzzy search(Contains, like)

Example:

一、只有高铁站的问题
1. 苏州有哪些高铁站
```
MATCH (station:Station)WHERE station.name CONTAINS "苏州" RETURN station
```
你可以通过模糊搜索找到与用户提问的某个城市的高铁站有哪些
如果提问到有关某特定火车站的餐厅或贵宾室，可以用例子二的2号查询样例和例子三的2号样例来回答

二、关于高铁/火车站和餐厅的例子
1. 查询苏州站信息
```
MATCH (station:Station)WHERE station.name CONTAINS "苏州" RETURN station
```
你可以通过上面的语句找到苏州站的node
station点有city，name, is_international, country, province, station_type这些信息，你可以使用比如n.name来获取车站的名字，n.country来获取车站所属国家
按照顺序他们分别是city：车站所在城市，name：车站的名称, is_international：车站在境内还是境外, country：车站所在国家, province：车站所在省份, station_type：车站的类型
2.苏州站有哪些餐厅以及餐厅的信息
```
MATCH (station:Station)
WHERE station.name CONTAINS "苏州"
MATCH (station)-[:OWNS_RESTAURANT]->(restaurant:Restaurant)
RETURN restaurant
```
你可以通过上面的语句查找到与苏州站有OWNS_RESTAURANT关系的餐厅点
restaurant点有cuisine_type, location_guide, menu, name, restaurant_id, security_type这些信息，你可以使用比如restaurant.menu来获取餐厅的菜单
按照顺序他们分别是cuisine_type：套餐类型, location_guide：餐厅的位置指引, menu：餐厅的菜单, name：餐厅的名称, restaurant_id：餐厅的编码, security_type：餐厅在安检前还是安检后
三、关于高铁/火车站和贵宾室的例子
1.查询北京南站信息
```
MATCH (station:Station)WHERE station.name CONTAINS "苏州" RETURN station
```
你可以通过上面的语句找到苏州站的node
station点有city，name, is_international, country, province, station_type这些信息，你可以使用比如n.name来获取车站的名字，n.country来获取车站所属国家
按照顺序他们分别是city：车站所在城市，name：车站的名称, is_international：车站在境内还是境外, country：车站所在国家, province：车站所在省份, station_type：车站的类型

2.查询北京南站有哪些贵宾室以及贵宾室信息
```
MATCH (station:Station)
WHERE station.name CONTAINS "北京南站"
MATCH (station)-[:OWNS_Lounge]->(lounge:Lounge)
RETURN lounge
```
你可以通过上面的语句找到与北京南站有OWNS_Lounge关系的贵宾室节点
lounge点有location, lounge_id, name, operating_hours, service_content, service_duration, service_provider, vip_type这些信息，你可以使用比如lounge.location来获取贵宾室位置
按照顺序他们的意思是location：贵宾室的位置指引, lounge_id：贵宾室的网点编码, name：贵宾室的名称, operating_hours：贵宾室的营业时间, service_content：贵宾室的服务内容, service_duration：贵宾室的服务时长, service_provider：贵宾室的服务权益机构可能有：移动,全球通,移动全球通,xx银行,xx银行龙腾卡), vip_type：贵宾室是否是自营


四、只有机场的问题
1.上海有哪些机场
```
MATCH (airport:Airport)WHERE airport.name CONTAINS "上海" RETURN airport
```
你可以通过模糊搜索找到与用户提问的某个城市的机场有哪些
如果提问到有关某特定机场的餐厅或贵宾室，可以用例子五的2号查询样例和例子六的2号样例来回答

五、关于机场和餐厅的例子
1.关于上海浦东机场的信息
```
MATCH (airport:Airport)WHERE airport.name CONTAINS "上海" RETURN airport
```
你可以通过上面的语句找到上海浦东机场的node（当然你可能因为模糊搜索获得很多有"上海"关键字的机场node，你可以根据问题内容再做选择）
airport点有name, airport_id, city, station_type, is_international, province
按照顺序他们分别是name： 机场名称, airport_id：机场编码, city：机场所在城市, station_type：站点类型, is_international：机场在境内还是境外, province：机场所在省份

2.上海浦东机场有哪些餐厅以及餐厅的信息
```
MATCH (airport:Airport)
WHERE airport.name CONTAINS "上海"
MATCH (airport)-[:OWNS_RESTAURANT]->(restaurant:Restaurant)
RETURN restaurant
```
你可以通过上面的语句查找到与上海浦东机场有OWNS_RESTAURANT关系的餐厅点
restaurant点有restaurant_id, name, state, cuisine_type, menu, supply_time, terminal, departure_type, security_type, location_guide
按照顺序他们分别是restaurant_id：餐厅编码, name：餐厅名称, state：餐厅状态, cuisine_type：套餐类型, menu：餐厅菜单, supply_time：套餐供应时间, terminal：餐厅所在航站楼, departure_type：餐厅所在航站楼出发类型, security_type：餐厅在安检前还是安检后, location_guide：餐厅的位置指引

六、关于机场和休息室的例子
1.关于上海浦东机场的信息
```
MATCH (airport:Airport)WHERE airport.name CONTAINS "上海" RETURN airport
```
你可以通过上面的语句找到上海浦东机场的node（当然你可能因为模糊搜索获得很多有"上海"关键字的机场node，你可以根据问题内容再做选择）
airport点有name, airport_id, city, station_type, is_international, province
按照顺序他们分别是name： 机场名称, airport_id：机场编码, city：机场所在城市, station_type：站点类型, is_international：机场在境内还是境外, province：机场所在省份

2.上海浦东机场有哪些贵宾室
```
MATCH (airport:Airport)
WHERE airport.name CONTAINS "上海浦东"
MATCH (airport)-[:OWNS_Lounge]->(lounge:Lounge)
RETURN lounge
```
你可以通过上面的语句找到与上海浦东机场有OWNS_Lounge关系的贵宾室节点
lounge点有lounge_id, name, service_provider, terminal, security_type, vip_lounge_quality, lounge_highlight, location, departure_type, service_content, service_duration, operating_hours
按照顺序他们分别是lounge_id：龙腾网点编码, name：休息室名称, service_provider：服务权益机构（可能有：移动,全球通,移动全球通,xx银行,xx银行龙腾卡), terminal：休息室所在航站楼, security_type：休息室在安检前还是安检后, vip_lounge_quality：休息室品质贵宾厅（是/否）, lounge_highlight：品质厅亮点, location：休息室位置指引, departure_type：休息室所在航站楼出发类型, service_content：休息室服务内容, service_duration：休息室服务时长（小时）, operating_hours：休息室营业时间

3.龙腾卡在上海虹桥机场的V03贵宾休息室可以使用吗？
```
MATCH (airport:Airport)
WHERE airport.name CONTAINS "上海虹桥"
MATCH (airport)-[:OWNS_Lounge]->(lounge:Lounge)
WHERE lounge.name CONTAINS "V03"
RETURN lounge.service_provider
```

Schema:
{schema}

Question:
{question}

"""


cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

# Create the Cypher QA chain
cypher_qa = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt
)
