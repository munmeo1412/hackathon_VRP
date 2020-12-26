import pandas as pd
import csv
import numpy as np
from sklearn.cluster import KMeans
from misc import Order, Driver, Warehouse, TOTAL_DRIVERS, get_priority, distance
# from api import get_distance
from tqdm import tqdm


def kmeans_cluster(No_Driver, orders_need_clustering):
    # cluster all order in orders_need_clustering into number of cluster same as number of drivers left
    kmeans = KMeans(n_clusters=No_Driver, random_state=0)
    kmeans.fit(orders_need_clustering)
    return kmeans

def clustered(orders, kmeans, wh):

    clusters = {
        i: np.where(kmeans.labels_ == i)[0]
        for i in range(kmeans.n_clusters)
    }
    orders_list = []

    current_driver = Driver(wh.long, wh.lat)

    for key, cluster in clusters.items():
        print('*** Process for cluster {} ***'.format(key))
        orders_in_cluster = [orders[idx] for idx in cluster]

        for order in sorted(orders_in_cluster, key= lambda x: x.priority, reverse=True):
            print('*** Process for order {} ***'.format(order.order_code))
            if current_driver.check_order_can_action(order):
                current_driver.next_order_to_action(order)
            else:
                orders_list.extend(current_driver.accept_action())
                current_driver = Driver(wh.long, wh.lat)
                current_driver.next_order_to_action(order)

    if not current_driver.not_accept_action():
        orders_list.extend(current_driver.accept_action())

    return orders_list


if __name__ == '__main__':

    df_orders = pd.read_csv('data/orders_Demo_new.csv')

    wh = pd.read_csv('data/warehouse.csv')
    warehouse = Warehouse(wh['lat'][0], wh['long'][0])

    orders_to_cluster = []
    orders = []

    for _, row in tqdm(df_orders.iterrows(), total=df_orders.shape[0]):
        orders_to_cluster.append([row["lat"], row["long"]])
        dist = distance(row['lat'], row['long'], warehouse.lat, warehouse.long)/1000
        row['distance'] = dist
        row['priority'] = get_priority(dist, row['weight'],row['deadline_pickup'])
        order = Order(row["order_code"], row["lat"], row["long"], row["weight"], row['distance'],row['deadline_pickup'], row['priority'])
        orders.append(order)

    kmeans = kmeans_cluster(No_Driver=TOTAL_DRIVERS, orders_need_clustering=orders_to_cluster)

    orders_list = clustered(orders, kmeans, warehouse)

    final_no_driver = []
    driver_id = None
    for order in orders_list:
        driver_id = order[0]
        final_no_driver.append(driver_id)
    max_no_driver = max(final_no_driver)

    driver_pack = dict()

    for i in range(max_no_driver+1):
        order_pack = list()
        for order in orders_list:
            if order[0] == i:
                pack = order[1:4]
                pack.append(order[7])
                order_pack.append(pack)

        final_list = list()
        for order in sorted(order_pack, key=lambda x: str(x[3]), reverse=True):
            final_list.append(order)
        driver_pack[i] = final_list

    driver_pack_location = dict()
    for i in range(max_no_driver+1):
        pack = driver_pack[i]
        pack_combine = pd.DataFrame(pack, columns=['order_code','lat','long', 'priority'])
        pack_combine['code_priority'] = pack_combine['order_code'] + '-' + pack_combine['priority'].astype(str)
        pack_combine['code_priority'] = pack_combine.groupby(['lat','long'])['code_priority'].transform(lambda x: '_'.join(x))
        pack_combine['description'] = pack_combine['code_priority']
        pack_combine.drop(['order_code','priority'], axis=1, inplace=True)
        pack_combine.drop_duplicates(inplace=True)
        pack_combine = pack_combine[['code_priority','lat','long','description']]
        pack_list = pack_combine.values.tolist()
        pack_list.insert(0, ['WAREHOUSE',warehouse.lat, warehouse.long,"WAREHOUSE"])
        driver_pack_location[i] = pack_list

    with open("answer.csv", 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["driver_id", "order_code",'lat','long', "weight",'distance','deadline_pickup','priority'])
        for row in orders_list:
            writer.writerow(row)

    for k in driver_pack_location.keys():
        with open("driver_{}.csv".format(k), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["node",'lat','lon','description'])
            for row in driver_pack_location.get(k):
                writer.writerow(row)