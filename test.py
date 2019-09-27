from datetime import datetime
from datetime import timedelta
import bcp
import pprint
import sys

n = 365*2000
date = datetime(year=1000, month=1, day=1)
pp = pprint.PrettyPrinter()

c = bcp.calendar()

for i in range(1, n):
    try:
        info = c.get_date_information(date)
    except Exception as e:
        print("ERROR on date: " + str(date))
        info = c.get_date_information(date)

    date = date + timedelta(days=1)
    
