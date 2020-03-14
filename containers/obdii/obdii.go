package main

import (
	"flag"
	"fmt"
	"strconv"
	"time"

	"github.com/jrcichra/karmen/karmen-go-client/karmen"
	"github.com/rzetterberg/elmobd"
)

func getEngineRPM(dev *elmobd.Device) (string, error) {
	rpm, err := dev.RunOBDCommand(elmobd.NewEngineRPM())
	if err != nil {
		fmt.Println("Failed to get rpm", err)
		return "", err
	}
	// fmt.Printf("Engine spins at %s RPMs\n", rpm.ValueAsLit())
	return rpm.ValueAsLit(), nil
}

func main() {
	serialPath := flag.String(
		"serial",
		"/dev/ttyUSB0",
		"Path to the serial device to use",
	)

	flag.Parse()

	dev, err := elmobd.NewTestDevice(*serialPath, true)

	if err != nil {
		fmt.Println("Failed to create new device", err)
		return
	}

	version, err := dev.GetVersion()

	if err != nil {
		fmt.Println("Failed to get version", err)
		return
	}

	fmt.Println("Device has version", version)

	supported, err := dev.CheckSupportedCommands()

	if err != nil {
		fmt.Println("Failed to check supported commands", err)
		return
	}

	allCommands := elmobd.GetSensorCommands()
	carCommands := supported.FilterSupported(allCommands)

	fmt.Printf("%d of %d commands supported:\n", len(carCommands), len(allCommands))

	for _, cmd := range carCommands {
		fmt.Printf("- %s supported\n", cmd.Key())
	}

	k := karmen.Karmen{}
	k.Start("controller", 8080)
	k.RegisterContainer()
	k.RegisterEvent("new_engine_rpm")
	//keep calling getEngineRPM
	lastRPM := -1

	for {
		time.Sleep(5 * time.Second)
		srpm, _ := getEngineRPM(dev)
		rpm, _ := strconv.Atoi(srpm)
		if rpm != lastRPM {
			//RPMs are different (most likely)
			//Emit an event when this happens with a map of {"rpm":val}
			params := make(map[string]int)
			params["rpm"] = rpm
			k.EmitEvent("new_engine_rpm", params)
		} else {
			//RPMs are the same (not very likely)
		}
		lastRPM = rpm
	}

}
