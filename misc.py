from math import sin, cos, sqrt, atan2, radians
from loguru import logger
# from api import get_distance

# khai báo biến (khối lượng DV Kg, Thời gian DV giờ, Vận tốc DV Km/h)
MAX_WEIGHTS = 15
DRIVER_SPEED = 30
MAX_TIME_PER_SHIFT = 2
PICKUP_TIME_PER_ORDER = 0.05  # 3 MINS per Order

TOTAL_DRIVERS = 4 # total drivers = total cluster of Kmeans

def distance(x1, y1, x2, y2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(y1)
    lon1 = radians(x1)
    lat2 = radians(y2)
    lon2 = radians(x2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


class Order:
    def __init__(self, order_code, lat, long, weight, distance, deadline_pickup, priority):
        self.order_code = order_code
        self.lat = lat
        self.long = long
        self.weight = weight
        self.distance = distance
        self.deadline_pickup = deadline_pickup
        self.priority = priority


class Driver:
    id = 0

    def __init__(self, wh_long, wh_lat):
        self.weight_capacity = 0
        self.long = wh_long
        self.lat = wh_lat
        self.wh_lat = wh_lat
        self.wh_long = wh_long
        self.current_time = 0
        self.id = Driver.id
        self.orders_list = []  # [driver_id, order_code, weight] orders of this Driver
        self.no_order = 0
        self.actioned = False
        # self.driver_left = TOTAL_DRIVERS
        Driver.id += 1

    def check_order_can_action(self, next_order):
        # check if driver can pick/deliver the next order and from that order to warehouse ontime
        if self.weight_capacity + next_order.weight > MAX_WEIGHTS:
            logger.info('Driver {} over weight capacity, move to next driver'.format(Driver.id))
            return False

        time_to_next_order = (distance(self.lat, self.long,
                                      next_order.lat, next_order.long)/1000) / DRIVER_SPEED
        time_next_order_to_warehouse = (distance(next_order.lat,next_order.long,
                                                     self.wh_lat, self.wh_long)/1000)/ DRIVER_SPEED

        if self.current_time + time_to_next_order + PICKUP_TIME_PER_ORDER + \
                time_next_order_to_warehouse > MAX_TIME_PER_SHIFT:
            logger.info('Driver {} over timing, move to next driver'.format(Driver.id))
            return False

        return True

    def next_order_to_action(self, next_order):
        # order accepted to be in action list
        time_to_next_order = (distance(self.lat, self.long,
                                           next_order.lat, next_order.long)/1000)/ DRIVER_SPEED
        time_next_order_to_warehouse = (distance(next_order.lat, next_order.long,
                                                     self.wh_lat, self.wh_long)/1000)/ DRIVER_SPEED

        # update current time
        self.current_time += time_to_next_order + PICKUP_TIME_PER_ORDER
        # update current weight
        self.weight_capacity += next_order.weight

        # update Driver location
        self.long = next_order.long
        self.lat = next_order.lat

        self.orders_list.append([self.id, next_order.order_code, next_order.lat, next_order.long, next_order.weight, next_order.distance, next_order.deadline_pickup, next_order.priority])
        self.no_order += 1

    def accept_action(self):
        self.actioned = True
        return self.orders_list[::]

    def not_accept_action(self):
        return self.actioned


class Warehouse:
    # basic warehouse
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
        # self.weight = 0

def get_priority(distance, weight, deadline_pickup):

    if weight > 5:
        weight_point = 2
    else:
        weight_point = 1

    if (distance > 15):
        distance_point = 0
    elif (distance > 5):
        distance_point = 3
    elif (distance <= 5 and distance > 2):
        distance_point = 2
    else:
        distance_point = 1

    if deadline_pickup <= 9:
        deadline_pickup_point = 3
    elif deadline_pickup <= 10:
        deadline_pickup_point = 2
    elif deadline_pickup <= 11:
        deadline_pickup_point = 1
    elif deadline_pickup <= 14:
        deadline_pickup_point = 3
    elif deadline_pickup <= 16:
        deadline_pickup_point = 2
    elif deadline_pickup <= 19:
        deadline_pickup_point = 1
    else:
        deadline_pickup_point = 3

    priority = deadline_pickup_point * 2 + distance_point + weight_point
    return priority
