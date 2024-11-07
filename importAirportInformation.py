from py2neo import Graph, Node, Relationship
import pandas as pd
import streamlit as st

# Connect to Neo4j Database
g = Graph(st.secrets["NEO4J_URI"], auth=(st.secrets["NEO4J_USERNAME"], st.secrets["NEO4J_PASSWORD"]))

# Fetch the document
restaurant = pd.read_csv("data/Airport Restaurants.csv")
lounge = pd.read_csv("data/Airport lounges.csv")


# Compute the number of unique Station Node we should build from two File(lounge and restaurant)
def getAirport(df1, df2):
    combined_stations = set(df1['机场名称']).union(set(df2['机场名称']))
    print(f"{len(combined_stations)} Airport Nodes should be built.")


# Compute the number of unique Restaurant Node we should build
def getRestaurant(df):
    restaurants = set(df['餐厅编码'])
    print(f"{len(restaurants)} Restaurant Nodes should be built.")


# Compute the number of unique Lounge Node we should build
def getLounge(df):
    lounges = set(df['龙腾网点编码'])
    print(f"{len(lounges)} Lounge Nodes should be built.")


# The function to import Station Node and Restaurant Node
def importAirportsAndRestaurants(df):
    for index, row in df.iterrows():
        # Create Station Node
        Airport_node = Node(
            "Airport",
            name=row['机场名称'],
            airport_id=['机场编码'],
            city=row['城市'],
            station_type=row['站点类型'],
            is_international=row['境内外'],
            province=row['省份'],
        )

        # Create Restaurant Node
        restaurant_node = Node(
            "Restaurant",
            restaurant_id=row['餐厅编码'],
            name=row['餐厅名称'],
            state=row['餐厅状态'],
            cuisine_type=row['套餐类型'],
            menu=row['套餐内容'],
            supply_time=row['套餐供应时间'],
            terminal=row['航站楼'],
            departure_type=row['出发类型'],
            security_type=row['安检类型'],
            location_guide=row['位置指引'],
        )

        # Create relationships, the station can own many restaurants
        relation = Relationship(Airport_node, "OWNS_RESTAURANT", restaurant_node)

        # Merge
        g.merge(Airport_node, "Airport", "name")
        g.merge(restaurant_node, "Restaurant", "restaurant_id")
        g.merge(relation)


# The function to import Station Node and Lounge Node
# be careful in lounge file, the station has no "境内外"，"国家","站点类型"
def importAirportsAndLounges(df):
    for index, row in df.iterrows():
        # Create Station Node
        Airport_node = Node(
            "Airport",
            name=row['机场名称'],
            airport_id=['机场编码'],
            city=row['城市'],
            province=row['省份'],
        )

        # Create Lounge Node
        lounge_node = Node(
            "Lounge",
            lounge_id=row['龙腾网点编码'],
            name=row['休息室名称'],
            service_provider=row['服务权益机构'],
            terminal=['航站楼'],
            security_type=row['安检类型'],
            vip_lounge_quality=row['品质贵宾厅（是/否）'],
            lounge_highlight=row['品质厅亮点'],
            location=row['休息室位置'],
            departure_type=['出发类型'],
            service_content=row['服务内容'],
            service_duration=row['服务时长（小时）'],
            operating_hours=row['营业时间'],
        )

        # Create relationships, the station can own many lounges
        relation = Relationship(Airport_node, "OWNS_Lounge", lounge_node)

        # Merge
        g.merge(Airport_node, "Airport", "name")
        g.merge(lounge_node, "Lounge", "lounge_id")
        g.merge(relation)


# Call two import function to build Station--
importAirportsAndRestaurants(restaurant)
importAirportsAndLounges(lounge)


# Call three number get function to confirm how many nodes separately we should build
getAirport(restaurant, lounge)
getRestaurant(restaurant)
getLounge(lounge)