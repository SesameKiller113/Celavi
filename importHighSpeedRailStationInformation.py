from py2neo import Graph, Node, Relationship
import pandas as pd
import streamlit as st


# Connect to Neo4j Database
g = Graph(st.secrets["NEO4J_URI"], auth=(st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"]))

# Fetch the document
restaurant = pd.read_csv("data/High-speed rail restaurant.csv")
lounge = pd.read_csv("data/High-speed rail lounge.csv")


# Compute the number of unique Station Node we should build from two File(lounge and restaurant)
def getStation(df1, df2):
    combined_stations = set(df1['高铁/火车站名称']).union(set(df2['高铁/火车站名称']))
    print(f"{len(combined_stations)} Station Nodes should be built.")


# Compute the number of unique Restaurant Node we should build
def getRestaurant(df):
    restaurants = set(df['餐厅编码'])
    print(f"{len(restaurants)} Restaurant Nodes should be built.")


# Compute the number of unique Lounge Node we should build
def getLounge(df):
    lounges = set(df['网店编码'])
    print(f"{len(lounges)} Lounge Nodes should be built.")


# The function to import Station Node and Restaurant Node
def importStationAndRestaurants(df):
    for index, row in df.iterrows():
        # Create Station Node
        station_node = Node(
            "Station",
            name=row['高铁/火车站名称'],
            city=row['城市'],
            station_type=row['站点类型'],
            is_international=row['境内外'],
            country=row['国家'],
            province=row['省份'],
        )

        # Create Restaurant Node
        restaurant_node = Node(
            "Restaurant",
            restaurant_id=row['餐厅编码'],
            name=row['餐厅名称'],
            state=row['状态'],
            cuisine_type=row['套餐类型'],
            supply_time=row['套餐供应时间'],
            location_guide=row['位置指引'],
            menu=row['套餐内容'],
            security_type=row['安检类型'],
        )

        # Create relationships, the station can own many restaurants
        relation = Relationship(station_node, "OWNS_RESTAURANT", restaurant_node)

        # Merge
        g.merge(station_node, "Station", "name")
        g.merge(restaurant_node, "Restaurant", "restaurant_id")
        g.merge(relation)


# The function to import Station Node and Lounge Node
# be careful in lounge file, the station has no "境内外"，"国家","站点类型"
def importStationsAndLounges(df):
    for index, row in df.iterrows():
        # Create Station Node
        station_node = Node(
            "Station",
            name=row['高铁/火车站名称'],
            city=row['城市'],
            province=row['省份'],
        )
        # Create Lounge Node
        lounge_node = Node(
            "Lounge",
            lounge_id=row['网店编码'],
            name=row['贵宾厅名称'],
            operating_hours=row['营业时间'],
            service_duration=row['服务时长（小时）'],
            service_content=row['服务内容'],
            vip_type=row['贵宾厅性质（自营/非自营）'],
            location=row['贵宾厅位置'],
            service_provider=row['服务权益机构']
        )

        # Create relationships, the station can own many lounges
        relation = Relationship(station_node, "OWNS_Lounge", lounge_node)

        # Merge
        g.merge(station_node, "Station", "name")
        g.merge(lounge_node, "Lounge", "lounge_id")
        g.merge(relation)


# Call two import function to build Station--
importStationAndRestaurants(restaurant)
importStationsAndLounges(lounge)

# Call three number get function to confirm how many nodes separately we should build
getStation(restaurant, lounge)
getRestaurant(restaurant)
getLounge(lounge)