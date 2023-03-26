import pandas as pd
from src.postgres_connection import connection

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitudes and longitudes to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Earth radius in kilometers
    earth_radius = 6371
    return c * earth_radius


def query_items(search_items, selected_city, max_distance_km=10):
    city_latitude = None
    city_longitude = None

    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                latitude,
                longitude
            FROM
                public.dim_stores
            WHERE
                city = %s
            LIMIT 1;
        """, (selected_city,))

        result = cur.fetchone()
        if result:
            city_latitude, city_longitude = result

    if city_latitude is None or city_longitude is None:
        return pd.DataFrame()

    filtered_results = []

    with connection.cursor() as cur:
        search_patterns = [f"%{item}%" for item in search_items]
        search_items_count = len(search_patterns)
        cur.execute(f"""
               SELECT
                   ds.storeid,
                   ds.storename,
                   ds.city,
                   ds.address,
                   ds.latitude,
                   ds.longitude,
                   SUM(fp.itemprice) as total_price
               FROM
                   public.fact_prices AS fp
               JOIN
                   public.dim_stores AS ds
                   ON fp.storeid = ds.storeid
               WHERE
                   fp.itemname ILIKE ANY(%s)
               GROUP BY
                   ds.storeid, ds.storename, ds.city, ds.address, ds.latitude, ds.longitude
               HAVING
                   COUNT(DISTINCT fp.itemname) = {search_items_count}
               ORDER BY
                   ds.city ASC;
           """, (search_patterns,))

        results = cur.fetchall()
        columns = ["storeid", "storename", "city", "address", "latitude", "longitude", "total_price"]

        filtered_results = []

        for result in results:
            distance = haversine_distance(city_latitude, city_longitude, result[4], result[5])
            if distance <= max_distance_km:
                filtered_results.append(result)

        df = pd.DataFrame(filtered_results, columns=columns)
        return df


def get_items():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                itemname
            FROM
                public.fact_prices
            ORDER BY
                itemname ASC;
        """)

        results = cur.fetchall()
        return [{"label": item[0], "value": item[0]} for item in results]


def get_cities():
    with connection.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                city
            FROM
                public.dim_stores
            ORDER BY
                city ASC;
        """)

        results = cur.fetchall()
        return [{"label": city[0], "value": city[0]} for city in results]


# Add this function to get stores for a selected city
def get_stores(city):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                ds.storeid,
                ds.storename
            FROM
                public.dim_stores AS ds
            INNER JOIN
                public.fact_prices AS fp
                ON ds.storeid = fp.storeid
            WHERE
                ds.city = %s
            ORDER BY
                ds.storename ASC;
        """, (city,))

        results = cur.fetchall()
        return [{"label": store[1], "value": store[0]} for store in results]


# Add this function to get items for a selected store
def get_items_in_store(store_id):
    with connection.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                fp.itemname
            FROM
                public.fact_prices AS fp
            WHERE
                fp.storeid = %s
            ORDER BY
                fp.itemname ASC;
        """, (store_id,))

        results = cur.fetchall()
        return [{"label": item[0], "value": item[0]} for item in results]


