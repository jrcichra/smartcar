import smartcarsocket

sc = smartcarsocket.smartcarsocket()
sc.registerContainer()
sc.registerEvent("started_recording")
sc.registerAction("start_recording")
