#!/usr/bin/env python

import requests
import matplotlib.pyplot as plt

api_endpoint = "https://opensense.network/beta/api/v1.0"

ref_point_lat = 52.514 # Berlin
ref_point_lon = 13.35 # Berlin
ref_point_radius = 40 # 40km
min_year_to_cover = 1950
max_year_to_cover = 2020
min_timestamp_in_year_to_use = "12-01T00:00Z" # dates/times in UTC
max_timestamp_in_year_to_use = "12-31T23:59Z" # dates/times in UTC

# ask for parameters
# no error handling here...
print("Plotting average temperatures for a given period over years based on official weather data available at opensense.network.")
input_val = input("Enter reference point latitute (default: %s): " % ref_point_lat)
if input_val != "":
    ref_point_lat = float(input_val)
input_val = input("Enter reference point longitude (default: %s): " % ref_point_lon)
if input_val != "":
    ref_point_lon = float(input_val)
input_val = input("Enter radius around reference point (in km) (default: %s): " % ref_point_radius)
if input_val != "":
    ref_point_radius = int(input_val)
input_val = input("Enter first year to cover (default: %s): " % min_year_to_cover)
if input_val != "":
    min_year_to_cover = int(input_val)
input_val = input("Enter last year to cover (default: %s): " % max_year_to_cover)
if input_val != "":
    max_year_to_cover = int(input_val)
input_val = input("Enter earliest timestamp to cover for each year (default: %s): " % min_timestamp_in_year_to_use)
if input_val != "":
    min_timestamp_in_year_to_use = input_val
input_val = input("Enter latest timestamp to cover for each year (default: %s): " % max_timestamp_in_year_to_use)
if input_val != "":
    max_timestamp_in_year_to_use = input_val


# first, get the measurand_id
measurand = "temperature"
measurand_id = None
measurand_query = api_endpoint + "/measurands?name=" + measurand
api_response = requests.get(measurand_query)
try:
    api_response = api_response.json()
except BaseException as e:
    print("Couldn't parse json from response to measurand query %s. Exception message: %s. Aborting." % (measurand_query, e))
    quit()
if len(api_response) == 1 and "id" in api_response[0]:
    measurand_id = api_response[0]["id"]
else:
    print("Invalid response length or no measurand id included in response %s. Aborting." % api_response)

print("Got measurand id for %s: %s" % (measurand, measurand_id))

# now get relevant sensors:
sensor_query = api_endpoint + "/sensors?measurandId=" + str(measurand_id) + "&refPoint=[" + str(ref_point_lat) + "," + str(ref_point_lon) + "]&maxDistance=" + str(ref_point_radius*1000)
api_response = requests.get(sensor_query)
try:
    api_response = api_response.json()
except BaseException as e:
    print("Couldn't parse json from response to sensors query %s. Exception message: %s. Aborting." % (sensor_query, e))
    quit()

sensor_ids_to_use = []
for sensor in api_response:
    if "accuracy" in sensor and sensor["accuracy"] == 10 and "id" in sensor: # only use sensors with an accuracy level of 10, thus official stations
        sensor_ids_to_use.append(sensor["id"])
print("Using %s sensors: %s" % (len(sensor_ids_to_use), sensor_ids_to_use))

years_list = []
values_list = []
for year in range(min_year_to_cover, max_year_to_cover+1):
    years_list.append(year)
    yearly_medium = None
    numValues = 0
    valueSum = 0.0
    for sensor_id in sensor_ids_to_use:
        #value_query = api_endpoint + "/sensors/" + str(sensor_id) + "/values?minTimestamp=" + str(year) + "-" + day_of_year_to_use + "T" + min_hour + ":00Z" + "&maxTimestamp="+ str(year) + "-" + day_of_year_to_use + "T" + max_hour + ":00Z"
        value_query = api_endpoint + "/sensors/" + str(sensor_id) + "/values?minTimestamp=" + str(year) + "-" +min_timestamp_in_year_to_use + "&maxTimestamp="+ str(year) + "-" + max_timestamp_in_year_to_use
        api_response = requests.get(value_query)
        try:
            api_response = api_response.json()
        except BaseException as e:
            print("Couldn't parse json from response to value query %s. Exception message: %s. Aborting." % (value_query, e))
            quit()
        if "values" in api_response:
            # yes, we consciously ignore any edge cases of sensors having values only from noon onwards in certain years or so
            for value in api_response["values"]:
                numValues +=1
                valueSum += float(value["numberValue"])
    if numValues > 0:
        average = valueSum / numValues
        values_list.append(average)
        print
        print("Average for %s (%s - %s): %s (based on %s values)" % (year, min_timestamp_in_year_to_use, max_timestamp_in_year_to_use, average, numValues))
    else:
        values_list.append(None)
        print("could not get average for %s" % year)


plt.plot(years_list, values_list)
plt.ylabel("Avg. Temp. (%s - %s)" %(min_timestamp_in_year_to_use, max_timestamp_in_year_to_use))
plt.xlabel("Year")
plt.title("Average Temp. around %s/%s (radius: %skm)" %(ref_point_lat, ref_point_lon, ref_point_radius))
plt.show()
