#!/usr/bin/python3
import obd
connection = obd.OBD("/dev/pts/3")
cmd = obd.commands.SPEED
response = connection.query(cmd)
print(response.value)
print(response.value.to("mph"))
