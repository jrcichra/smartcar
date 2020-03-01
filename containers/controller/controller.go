package main

import (
	common "controller/common"
	parser "controller/parser"
	"encoding/json"
	"errors"
	"log"
	"net"
	"net/http"
	_ "net/http/pprof"
	"os"
	"strconv"
	"time"

	"github.com/jinzhu/copier"
	"github.com/op/go-logging"
)

const (
	//REGISTERCONTAINER -
	REGISTERCONTAINER = "register-container"
	//REGISTERCONTAINERRESPONSE -
	REGISTERCONTAINERRESPONSE = "register-container-response"
	//REGISTEREVENT -
	REGISTEREVENT = "register-event"
	//REGISTEREVENTRESPONSE -
	REGISTEREVENTRESPONSE = "register-event-response"
	//REGISTERACTION -
	REGISTERACTION = "register-action"
	//REGISTERACTIONRESPONSE -
	REGISTERACTIONRESPONSE = "register-action-response"
	//EMITEVENT -
	EMITEVENT = "emit-event"
	//DISPATCHEDEVENT -
	DISPATCHEDEVENT = "dispatched-event"
	//EMITEVENTRESPONSE -
	EMITEVENTRESPONSE = "emit-event-response"
	//TRIGGERACTION -
	TRIGGERACTION = "trigger-action"
	//TRIGGERACTIONRESPONSE -
	TRIGGERACTIONRESPONSE = "trigger-action-response"
	//OK -
	OK = 200
	//ERROR -
	ERROR = 503
	//ONLINE -
	ONLINE = "online"
	//OFFLINE -
	OFFLINE = "offline"
)

//Conn - local conn that handles output with a channel
type conn struct {
	name string
	conn net.Conn
	out  chan []byte
	in   chan []byte
}

func (cio *conn) HandleConnOut(c net.Conn) {
	for {
		b := <-cio.out
		b = append(b, '\n')
		c.Write(b)
	}
}

//buildResponse - takes a message that came in and turn it into a response
func (cio *conn) buildResponse(msg *common.Message, code int, dispatched bool) {
	var m common.Message
	copier.Copy(&m, msg)
	m.ResponseCode = code
	m.Timestamp = time.Now().Unix()
	//set the response code based on the message code
	switch msg.Type {
	case REGISTERCONTAINER:
		m.Type = REGISTERCONTAINERRESPONSE
	case REGISTEREVENT:
		m.Type = REGISTEREVENTRESPONSE
	case REGISTERACTION:
		m.Type = REGISTERACTIONRESPONSE
	case EMITEVENT:
		if dispatched {
			m.Type = DISPATCHEDEVENT
		} else {
			m.Type = EMITEVENTRESPONSE
		}
	default:
		panic("buildResponse does not understand how to respond to " + m.Type)
	}
	b, err := json.Marshal(&m)
	if err != nil {
		panic(err) //was unable to build a response
	}
	cio.out <- b
}

//Controller - controls the whole scope of containers
type Controller struct {
	logger      *logging.Logger
	config      *parser.Config
	connections map[string]conn
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

func (c *Controller) registerContainer(msg *common.Message, cio conn) {
	err := c.config.RegisterContainer(msg)
	code := OK
	if err != nil {
		log.Println(err)
		code = ERROR
	} else {
		//Now that they've registered, take the name they registered with and add it to the list of controller connections in the map
		c.connections[msg.Name] = cio
	}
	//Send a response
	cio.buildResponse(msg, code, false)
}

func (c *Controller) registerAction(msg *common.Message, cio conn) {
	err := c.config.RegisterAction(msg)
	code := OK
	if err != nil {
		log.Println(err)
		code = ERROR
	}
	//Send a response
	cio.buildResponse(msg, code, false)
}

func (c *Controller) registerEvent(msg *common.Message, cio conn) {
	err := c.config.RegisterEvent(msg)
	code := OK
	if err != nil {
		log.Println(err)
		code = ERROR
	}
	//Send a response
	cio.buildResponse(msg, code, false)
}

//triggerSerialAction reaches out to a container and tells it to do something serially
func (c *Controller) triggerSerialAction(act *parser.Action, id string) *common.Message {
	//TODO - actually trigger actions by reading the event config
	var err error
	var msg common.Message
	if err != nil {
		panic(err)
	}

	//Send a trigger action to the container that owns this action
	msg.Type = TRIGGERACTION
	msg.Timestamp = time.Now().Unix()
	msg.ContainerName = act.Container
	msg.Properties = act.Parameters
	msg.Name = act.Name
	msg.ID = id

	b, err := json.Marshal(&msg)
	if err != nil {
		panic(err) //was unable to build a message
	}
	c.connections[act.Container].out <- b
	log.Println("Sent action to " + act.Container)

	//Wait for the response here
	retMsg := c.findYourResponse(act)
	return &retMsg
}

func (c *Controller) findYourResponse(act *parser.Action) common.Message {
	var retmsg common.Message
	//Loop through things in the input queue in case we get a different event's actionresponse (just to be safe)
	for {
		bretmsg := <-c.connections[act.Container].in
		// log.Println(bretmsg)
		err := json.Unmarshal(bretmsg, &retmsg)
		if err != nil {
			panic(err)
		}
		if retmsg.ContainerName != act.Container || retmsg.Name != act.Name {
			//We pulled something from the channel that isn't for here, put it back on the queue
			c.connections[act.Container].in <- bretmsg
		} else {
			break
		}
	}
	retmsg.ContainerName = act.Container
	retmsg.Name = act.Name
	retmsg.Type = TRIGGERACTIONRESPONSE
	return retmsg
}

//triggerParallelAction reaches out to a container and tells it to do something in parallel
func (c *Controller) triggerParallelAction(act *parser.Action, id string, ret chan common.Message) {
	//TODO - actually trigger actions by reading the event config
	var err error
	var msg common.Message
	if err != nil {
		panic(err)
	}

	//Send a trigger action to the container that owns this action
	msg.Type = TRIGGERACTION
	msg.Timestamp = time.Now().Unix()
	msg.ContainerName = act.Container
	msg.Properties = act.Parameters
	msg.ID = id
	msg.Name = act.Name

	b, err := json.Marshal(&msg)
	if err != nil {
		panic(err) //was unable to build a message
	}

	//Make sure the container & action we want to send to is online

	c.connections[act.Container].out <- b
	log.Println("Sent action to " + act.Container)

	retmsg := c.findYourResponse(act)
	ret <- retmsg
}

//handleEvent is the part of the controller responsible for goroutines that do all kinds of processes
func (c *Controller) handleEvent(msg *common.Message, cio conn) {
	//The message we were given told use to emit an event
	log.Println("We're starting event: ", msg.Name)

	//Make a unique id for this event, so everyone can keep track
	uuid := common.GenUUID()
	//Send them a dispatched message so they know we're handling their message
	msg.ID = uuid
	cio.buildResponse(msg, OK, true)

	//Pull the information about who what containers we should contact
	event, err := c.config.GetEvent(msg.Name)
	if err != nil {
		log.Println(err)
	} else if event.State == "offline" {
		log.Println(errors.New("Event " + event.EventName + " emitted before being registered"))
	} else {
		//We have a valid event we can analyze
		blocks := *event.Blocks
		run := true  //See if the conditionals warrant a run of this event
		good := true //Set to false if anything bad happens when dispatching an event
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
								good = false
								log.Println("when should be the first conditional for " + event.EventName)
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
								good = false
								log.Println("Unrecognized conditional: " + b.Type)
							}
						}
					default:
						good = false
						log.Println("Saw a recognized type: " + b.Type + ", but did not .(type) to a conditional")
					}
				}
			case "serial", "parallel":
				//No-op, don't error but don't process until after we get an idea of the run status
			default:
				good = false
				log.Println("Unknown time when attempting to emit an event: " + b.Type)
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
						case *parser.Action:
							log.Println("About to execute '" + act.Name + "' in " + b.Type)
							if b.Type == "serial" {
								ret := c.triggerSerialAction(act, uuid)
								if ret.ResponseCode != OK {
									log.Println("Got a bad return code from serial response: " + ret.Name + ", " + strconv.Itoa(ret.ResponseCode))
									good = false
								}
								log.Println("Serial job finished: " + ret.Name)
							} else if b.Type == "parallel" {
								channel := make(chan common.Message)
								//Keep track of all the channels we've made that will be returning something
								channels = append(channels, channel)
								go c.triggerParallelAction(act, uuid, channel)
							} else {
								good = false
								log.Println("Found serial/parallel earlier but now can't find it, this must be a coder error")
							}
						default:
							good = false
							log.Println("Expected action after entering an instruction block")
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
								good = false
							}
						}
					}
				default:
					panic("Unknown type when running through instruction blocks after a successful run condition")
				}
			}
			//We ran, and everything we dispatched came back, ready to respond to the caller
			if good {
				cio.buildResponse(msg, OK, false)
			} else {
				cio.buildResponse(msg, ERROR, false)
			}
		} else {
			//We did not run, but we didn't run by the conditional, not by error
			if good {
				cio.buildResponse(msg, OK, false)
			} else {
				cio.buildResponse(msg, ERROR, false)
			}
		}
		log.Println("We're finishing event: ", msg.Name)
	}
}

//handleActionResponse - sends action response to proper connection's pseduo-input channel
func (c *Controller) handleActionResponse(msg *common.Message, cio conn) {
	b, err := json.Marshal(msg)
	if err != nil {
		c.logger.Error(err)
	} else {
		c.connections[msg.ContainerName].in <- b
	}
}

func (c *Controller) handleConnection(conn net.Conn, cio conn) {
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
		// spew.Dump(msg)
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
		case TRIGGERACTIONRESPONSE:
			go c.handleActionResponse(&msg, cio)
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
func (c *Controller) readConfig() {
	c.config = c.config.NewConfig()
	config, err := c.config.Parse("/config.yml")
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
	c.readConfig()
	l := c.setupListener(port)
	defer l.Close()
	c.logger.Info("Controller is up. Listening for clients on port", port)
	for {
		con, err := l.Accept()
		if err != nil {
			c.logger.Error(err)
		}
		var cio conn
		//create an input and output channel for this connection
		in := make(chan []byte)
		out := make(chan []byte)
		//Assign them
		cio.out = out
		cio.in = in
		// For every connection that comes in, start a goroutine to handle their inputs
		go c.handleConnection(con, cio)
	}
}

func main() {
	c := Controller{}
	c.connections = make(map[string]conn)
	go func() {
		log.Println(http.ListenAndServe("localhost:6060", nil))
	}()
	c.Start(8080)

}
