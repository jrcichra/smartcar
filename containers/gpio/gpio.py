import smartcarsocket
import time

sc = smartcarsocket.smartcarsocket()
sc.registerContainer()
sc.registerEvent("key_on")
sc.registerEvent("key_off")
sc.registerAction("power_off")

time.sleep(10)
sc.emitEvent("key_on")

time.sleep(10)
sc.emitEvent("key_off")
