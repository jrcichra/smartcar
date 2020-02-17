package main

import (
	common "controller2/common"
	parser "controller2/parser"
	redis "controller2/redis"
	"encoding/json"
	"errors"
	"log"
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
	OK                        = 0
	ERROR                     = 1
)

//connios - array of connio structs
type connios []connio

//connio - has the channels that get input/output for a connio
type connio struct {
	name string
	// in   *chan string
	out chan []byte
}

func (cio *connio) HandleConnOut(c net.Conn) {
	for {
		b := <-cio.out
		c.Write(b)
	}
}

//buildResponse - takes a message that came in and turn it into a response
func (cio *connio) buildResponse(msg *common.Message) {
	msg.ResponseCode = OK

	//set the response code based on the message code
	switch msg.Type {
	case REGISTERCONTAINER:
		msg.Type = REGISTERCONTAINERRESPONSE
	case REGISTEREVENT:
		msg.Type = REGISTEREVENTRESPONSE
	case REGISTERACTION:
		msg.Type = REGISTERACTIONRESPONSE
	default:
		panic("buildResponse does not understand how to respond to " + msg.Type)
	}
	b, err := json.Marshal(&msg)
	if err != nil {
		panic(err) //was unable to build a response
	}
	cio.out <- b
}

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

func (c *Controller) registerContainer(msg *common.Message, cio connio) {
	err := c.redis.RegisterContainer(msg)
	if err != nil {
		panic(err)
	}
	//Send a response
	cio.buildResponse(msg)
}

func (c *Controller) registerAction(msg *common.Message, cio connio) {
	err := c.redis.RegisterAction(msg)
	if err != nil {
		panic(err)
	}
	//Send a response
	cio.buildResponse(msg)
}

func (c *Controller) registerEvent(msg *common.Message, cio connio) {
	err := c.redis.RegisterEvent(msg)
	if err != nil {
		panic(err)
	}
	//Send a response
	cio.buildResponse(msg)
}

//triggerSerialAction reaches out to a container and tells it to do something serially
func (c *Controller) triggerSerialAction(act parser.Action) *common.Message {
	//TODO - actually trigger actions by reading the event config
	var err error
	var msg common.Message
	if err != nil {
		panic(err)
	}
	return &msg
}

//triggerParallelAction reaches out to a container and tells it to do something in parallel
func (c *Controller) triggerParallelAction(act parser.Action, ret chan common.Message) {
	//TODO - actually trigger actions by reading the event config
	var err error
	if err != nil {
		panic(err)
	}
}

//handleEvent is the part of the controller responsible for goroutines that do all kinds of processes
func (c *Controller) handleEvent(msg *common.Message, cio connio) {
	//The message we were given told use to emit an event
	//Pull the information about who what containers we should contact
	//Get the event from redis
	event, err := c.redis.GetEvent(msg.Name)
	if event.State == "offline" {
		panic(errors.New("Event " + event.EventName + " emmitted before being registered"))
	} else if err != nil {
		panic(err)
	} else {
		//We have a valid event we can analyze
		blocks := *event.Blocks
		run := true //See if the conditionals warrant a run of this event
		for _, b := range blocks {
			switch b.Type {
			case "when", "and", "or":
				//Conditionals
				for i, children := range b.Children {
					switch cond := children.(type) {
					//Look for the type of each conditional
					case parser.Condition:
						//If we should still run it this condition should be true
						if i == 0 {
							if b.Type != "when" {
								//Panic, when should be the first conditional we see
								panic("when should be the first conditional for " + event.EventName)
							} else {
								//This is our first conditional, just set run to the evaluation
								run = c.config.EvaluateCondition(cond)
							}
						} else {
							//If the type is anded, we should and it with run
							if b.Type == "and" {
								run = run && c.config.EvaluateCondition(cond)
							} else if b.Type == "or" {
								run = run || c.config.EvaluateCondition(cond)
							} else {
								panic("Unrecognized conditional: " + b.Type)
							}
						}
					default:
						panic("Saw a recognized type: " + b.Type + ", but did not .(type) to a conditional")
					}
				}
			case "serial", "parallel":
				//No-op, don't error but don't process until after we get an idea of the run status
			default:
				panic("Unknown time when attempting to emit an event: " + b.Type)
			}

		}
		//Only loop through instruction blocks
		if run {
			for _, b := range blocks {
				var channels []chan common.Message
				switch b.Type {
				case "when", "and", "or":
					//no-op
				case "serial", "parallel":
					//Blocks of instructions, we'll only run this when we get out of the block loop and check the value of run
					for _, children := range b.Children {
						switch act := children.(type) {
						case parser.Action:
							log.Println("About to execute '" + act.Name + "' in " + b.Type)
							if b.Type == "serial" {
								ret := c.triggerSerialAction(act)
								log.Println("Serial job finished: " + ret.Name)
							} else if b.Type == "parallel" {
								channel := make(chan common.Message)
								//Keep track of all the channels we've made that will be returning something
								channels = append(channels, channel)
								go c.triggerParallelAction(act, channel)
							} else {
								panic("Found serial/parallel earlier but now can't find it, this must be a coder error")
							}
						default:
							panic("Expected action after entering an instruction block")
						}
					}
					//After we loop through and we are parallel, we want to block until all the parallel things are done
					if b.Type == "parallel" {
						//Handle the messages from the goroutines
						for _, channel := range channels {
							ret := <-channel
							if ret.ResponseCode == OK {
								//This is good
								log.Println("Parallel job finished: " + ret.Name)
							} else {
								log.Println("Got a bad return code from parallel response: " + ret.Name + ", " + strconv.Itoa(ret.ResponseCode))
							}
						}
					}
				default:
					panic("Unknown type when running through instruction blocks after a successful run condition")
				}
			}
		}
	}
}

func (c *Controller) handleConnection(conn net.Conn, cio connio) {
	defer conn.Close()
	c.logger.Infof("Handling %s\n", conn.RemoteAddr().String())
	//Spin up a goroutine to write out to this connection (essentially an output queue)
	go cio.HandleConnOut(conn)
	//Handle input here directly from the socket
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
			go c.registerContainer(&msg, cio)
		case REGISTERACTION:
			go c.registerAction(&msg, cio)
		case REGISTEREVENT:
			go c.registerEvent(&msg, cio)
		case EMITEVENT:
			go c.handleEvent(&msg, cio)
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
		var cio connio
		//create an input and output channel for this connection
		// in := make(chan string)
		out := make(chan []byte)
		//Assign them
		// cio.in = &in
		cio.out = out
		// For every connection that comes in, start a goroutine to handle their inputs
		go c.handleConnection(conn, cio)
	}
}

func main() {
	c := Controller{}
	c.Start(8080)
}
