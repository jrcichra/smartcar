package main

import (
	common "controller2/common"
	parser "controller2/parser"
	redis "controller2/redis"
	"encoding/json"
	"errors"
	"net"
	"os"
	"strconv"

	"github.com/davecgh/go-spew/spew"
	"github.com/op/go-logging"
)

const (
	REGISTERCONTAINER         = "register-container"
	REGISTERCONTAINERRESPONSE = "register-container-response"
	REGISTEREVENT             = "register-event"
	REGISTEREVENTRESPONSE     = "register-event-response"
	REGISTERACTION            = "register-action"
	REGISTERACTIONRESPONSE    = "register-action-response"
	EMITEVENT                 = "emit-event"
	EMITEVENTRESPONSE         = "emit-event-response"
	TRIGGERACTION             = "trigger-action"
	TRIGGERACTIONRESPONSE     = "trigger-action-response"
)

//Controller - controls the whole scope of containers
type Controller struct {
	logger *logging.Logger
	redis  *redis.Redis
	config *parser.Config
}

/*
Example Messages:
	Register a Container:
		Type=register-container
		Timestamp=15707945
		ContainerName=gpio
		Name=gpio
		ResponseCode=nil
		Properties=nil
	Response:
		Type=register-container-response
		Timestamp=15707946
		ContainerName=gpio
		Name=gpio
		ResponseCode=200
		Properties=nil
	Emitting an Event:
		Type=emit-event
		Timestamp=15707947
		ContainerName=obdii
		Name=speed_changed
		ResponseCode=nil
		Properties={
			speed=50
			unit=mph
		}
	Trigger an Action:
		Type=trigger-action
		Timestamp=15707948
		ContainerName=espeak
		Name=speak
		ResponseCode = nil
		Properties={
			message=You're going too fast
		}
	Get an action response:
		Type=trigger-action-response
		Timestamp=15707949
		ContainerName=espeak
		Name=speak
		ResponseCode=200
		Properties = nil
*/

func (c *Controller) registerContainer(msg *common.Message) error {
	err := c.redis.RegisterContainer(msg)
	return err
}

func (c *Controller) registerAction(msg *common.Message) error {
	err := c.redis.RegisterAction(msg)
	return err
}

func (c *Controller) registerEvent(msg *common.Message) error {
	err := c.redis.RegisterEvent(msg)
	return err
}

//triggerAction reaches out to a container and tells it to do something
func (c *Controller) triggerAction(msg *common.Message) error {
	c.logger.Debug("In triggerAction.")
	return nil
}

//handleEvent is the part of the controller responsible for goroutines that do all kinds of processes
func (c *Controller) handleEvent(msg *common.Message) error {
	c.logger.Debug("In handleEvent.")

	//The message we were given told use to emit an event
	//Pull the information about who what containers we should contact

	//Get the event from redis
	event, err := c.redis.GetEvent(msg.Name)
	if event.State == "offline" {
		return errors.New("Event " + event.EventName + " emmited before being registered")
	} else if err != nil {
		return err
	} else {

	}

	return nil
}

func (c *Controller) handleConnection(conn net.Conn) {
	defer conn.Close()
	c.logger.Infof("Handling %s\n", conn.RemoteAddr().String())
	for {
		// read directly from the socket, expecting each json message to be newline separated
		d := json.NewDecoder(conn)
		var msg common.Message
		err := d.Decode(&msg)
		if err != nil {
			c.logger.Error(err)
			break
		}
		spew.Dump(msg)
		//Read the type and send it to the proper function for further processing
		switch msg.Type {
		case REGISTERCONTAINER:
			err = c.registerContainer(&msg)
		case REGISTERACTION:
			err = c.registerAction(&msg)
		case REGISTEREVENT:
			err = c.registerEvent(&msg)
		case EMITEVENT:
			err = c.handleEvent(&msg)
		// case TRIGGERACTION:
		// 	err = c.handleAction(&msg)
		default:
			c.logger.Error("Unknown Type:", msg.Type)
			break
		}
		if err != nil {
			panic(err)
		}
	}
}

func (c *Controller) setupLogger() {
	c.logger = logging.MustGetLogger("main")
	formatter := logging.MustStringFormatter(
		`%{color}%{time:15:04:05.00} %{shortfunc} ▶ %{level:.4s} %{id:03x}%{color:reset} %{message}`)

	backend := logging.NewLogBackend(os.Stdout, "", 0)
	backendFormatter := logging.NewBackendFormatter(backend, formatter)
	logging.SetBackend(backendFormatter)
	logging.SetLevel(logging.DEBUG, "main")
}

func (c *Controller) setupRedis() {
	c.redis = redis.GetRedis()
	err := c.redis.Connect("localhost", 6379)
	if err != nil {
		panic(err)
	}
}

func (c *Controller) prepRedis() {
	err := c.redis.Prep(c.config)
	if err != nil {
		panic(err)
	}
}

func (c *Controller) readConfig() {
	config, err := c.config.Parse("../../new_config.yml")
	if err != nil {
		panic(err)
	}
	c.config = config
}

func (c *Controller) setupListener(port int) net.Listener {
	PORT := ":" + strconv.Itoa(port)
	l, err := net.Listen("tcp4", PORT)
	if err != nil {
		panic(err)
	}
	return l
}

//Start - starts a controller
func (c *Controller) Start(port int) {
	c.setupLogger()
	c.setupRedis()
	c.readConfig()
	c.prepRedis()
	l := c.setupListener(port)
	defer l.Close()
	c.logger.Info("Controller is up. Listening for clients on port", port)
	for {
		conn, err := l.Accept()
		if err != nil {
			c.logger.Error(err)
		}
		// For every conection that comes in, start a goroutine to handle their inputs
		go c.handleConnection(conn)

	}
}

func main() {
	c := Controller{}
	c.Start(8080)
}
