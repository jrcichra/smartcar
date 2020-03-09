package main

import (
	"flag"
	"fmt"

	"github.com/rzetterberg/elmobd"
)

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

	rpm, err := dev.RunOBDCommand(elmobd.NewEngineRPM())
	if err != nil {
		fmt.Println("Failed to get rpm", err)
		return
	}

	fmt.Printf("Engine spins at %s RPMs\n", rpm.ValueAsLit())

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
}
