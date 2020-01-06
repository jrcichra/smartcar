package main

import (
	common "controller2/common"
	parser "controller2/parser"
	redis "controller2/redis"
	"encoding/json"
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
	parser *parser.Config
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

func (c *Controller) registerContainer(msg common.Message) {
	c.logger.Debug("In registerContainer.")
}

func (c *Controller) registerAction(msg common.Message) {
	c.logger.Debug("In registerAction.")
}

func (c *Controller) registerEvent(msg common.Message) {
	c.logger.Debug("In registerEvent.")
}

func (c *Controller) triggerAction(msg common.Message) {
	c.logger.Debug("In triggerAction.")
}

func (c *Controller) emitEvent(msg common.Message) {
	c.logger.Debug("In emitEvent.")
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
			c.registerContainer(msg)
		case REGISTERACTION:
			c.registerAction(msg)
		case REGISTEREVENT:
			c.registerEvent(msg)
		case EMITEVENT:
			c.emitEvent(msg)
		case TRIGGERACTION:
			c.triggerAction(msg)
		default:
			c.logger.Error("Unknown Type:", msg.Type)
			break
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
	c.redis.Connect("justinpi", 6379)
}

func (c *Controller) readConfig() {
	c.parser.Parse("../../new_config.yml")
}

//Start - starts a controler
func (c *Controller) Start(port int) {
	c.setupLogger()
	c.setupRedis()
	c.readConfig()
	PORT := ":" + strconv.Itoa(port)
	l, err := net.Listen("tcp4", PORT)
	defer l.Close()
	if err != nil {
		c.logger.Error(err)
	} else {
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
}

func main() {
	c := Controller{}
	c.Start(8080)
}
