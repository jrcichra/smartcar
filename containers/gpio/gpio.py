import smartcarsocket

sc = smartcarsocket.smartcarsocket()
sc.registerContainer()
sc.registerEvent("key_on")
sc.registerEvent("key_off")
sc.registerAction("power_off")
