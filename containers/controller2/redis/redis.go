package redis

import (
	common "controller2/common"
	parser "controller2/parser"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"strconv"
	"time"

	"github.com/gomodule/redigo/redis"
	"github.com/nitishm/go-rejson"
)

//Redis - Handles interaction with the Redis database
type Redis struct {
	handler *rejson.Handler
}

//Container - container type as stored in redis
type Container struct {
	State         string `json:"state"`          //online?
	ContainerName string `json:"container_name"` //PK
	Timestamp     int64  `json:"timestamp"`      //Timestamp
}

//Event - event type as stored in redis
type Event struct {
	State         string         `json:"state"`          //online?
	EventName     string         `json:"event_name"`     //PK
	ContainerName string         `json:"container_name"` //Relate an event to a container
	Timestamp     int64          `json:"timestamp"`      //Timestamp
	Blocks        *parser.Blocks `json:"blocks"`
}

//Action - action type as stored in redis
type Action struct {
	State         string `json:"state"`       //online?
	ActionName    string `json:"action_name"` //PK
	ContainerName string `json:"container_name"`
	Timestamp     int64  `json:"timestamp"` //Timestamp
}

func (r *Redis) insert(key string, name string, obj interface{}) error {

	fmt.Println("About to insert:", key+"_"+name, obj)
	res, err := r.handler.JSONSet(key+"_"+name, ".", obj)
	if err != nil {
		return err
	}

	if res.(string) == "OK" {
		fmt.Printf("Success: %s\n", res)
	} else {
		fmt.Println("Failed to Set: ")
	}

	return nil
}

func (r *Redis) read(key string, name string) []byte {
	//We don't care about errors, if msg is nil we know it's not there
	msg, _ := r.handler.JSONGet(key+"_"+name, ".")
	switch t := msg.(type) {
	case []byte:
		return t
	default:
		return nil
	}
}

//GetEvent - returns the Redis event type from what event they requested
func (r *Redis) GetEvent(eventname string) (Event, error) {
	existing := r.read("event", eventname)
	// Try to unmarshal it into what we want
	var e Event
	err := json.Unmarshal(existing, &e)
	return e, err
}

//RegisterEvent - registers the event inside of redis
func (r *Redis) RegisterEvent(msg *common.Message) error {
	existing := r.read("event", msg.Name)
	// Try to unmarshal it into what we want
	var e Event
	err := json.Unmarshal(existing, &e)
	if err == nil { //as in we didn't get an error, we need to see if it's offline or just a bad read
		if e.State == "offline" {
			//This is okay, we can make it online outside this condition
		} else {
			tf := time.Unix(e.Timestamp, 0).Local().Format("2006-01-02T15:04:05.999999-05:00")
			return errors.New("Container already registered and not offline at " + tf)
		}
	}
	//Make this stub "online"
	e.EventName = msg.Name
	e.State = "online"
	e.Timestamp = msg.Timestamp
	e.ContainerName = msg.ContainerName
	return r.insert("action", msg.Name, &e)
}

//RegisterAction - registers the action inside of redis
func (r *Redis) RegisterAction(msg *common.Message) error {
	existing := r.read("action", msg.Name)
	// Try to unmarshal it into what we want
	var a Action
	err := json.Unmarshal(existing, &a)
	if err == nil { //as in we didn't get an error, we need to see if it's offline or just a bad read
		if a.State == "offline" {
			//This is okay, we can make it online outside this condition
		} else {
			tf := time.Unix(a.Timestamp, 0).Local().Format("2006-01-02T15:04:05.999999-05:00")
			return errors.New("Container already registered and not offline at " + tf)
		}
	}
	//Make this stub "online"
	a.ActionName = msg.Name
	a.State = "online"
	a.Timestamp = msg.Timestamp
	a.ContainerName = msg.ContainerName
	return r.insert("action", msg.Name, &a)
}

//RegisterContainer - registers the container inside of redis
func (r *Redis) RegisterContainer(msg *common.Message) error {
	existing := r.read("container", msg.Name)
	// Try to unmarshal it into what we want
	var c Container
	err := json.Unmarshal(existing, &c)
	if err == nil { //as in we didn't get an error, we need to see if it's offline or just a bad read
		if c.State == "offline" {
			//This is okay, we can make it online outside this condition
		} else {
			tf := time.Unix(c.Timestamp, 0).Local().Format("2006-01-02T15:04:05.999999-05:00")
			return errors.New("Container already registered and not offline at " + tf)
		}
	}
	//Make this stub "online"
	c.ContainerName = msg.Name
	c.State = "online"
	c.Timestamp = msg.Timestamp
	return r.insert("container", c.ContainerName, &c)
}

//Prep - prep redis with things it will expect - (ex. containers, events, actions)
func (r *Redis) Prep(config *parser.Config) error {
	var err error

	//For containers and actions, we only care if they are registered or not in the system (see if we need to block), everything else is driven by event emissions
	containerSet := make(map[string]bool)
	actionSet := make(map[string]string)

	for _, event := range config.Events {
		//loop through every event building objects on the way
		var e Event
		e.ContainerName = event.ContainerName
		//No timestamp on prep
		e.State = "offline"
		e.EventName = event.EventName
		e.Blocks = event.Blocks
		//Insert event into redis
		if r.read("event", e.EventName) != nil {
			err = errors.New("Event " + e.EventName + " already pre-registered. This should only be pre-registered once")
			break
		} else {
			err = r.insert("event", e.EventName, e)
			if err != nil {
				break
			}
		}
		//Grab the Container from this event and add it to a set of containers (this pulls them out of the loop as if they were top level in the yaml)
		containerSet[e.ContainerName] = true
		//Drill down to the actions based on the config layout
		for _, block := range *event.Blocks {
			switch block.Type {
			case "parallel", "serial":
				//It's a block with actions in it
				for _, c := range block.Children {
					//Loop through each Child in the block looking for actions
					switch a := c.(type) {
					case parser.Action:
						//We should get action blocks in here
						actionSet[a.Name] = e.ContainerName
					default:
						//If we're here somethings wrong
					}
				}
			default:
				//If we're here somethings wrong
			}
		}
	}
	//Process the sets we made
	//First the containers
	for c := range containerSet {
		//Insert container into redis
		var o Container
		o.ContainerName = c
		o.State = "offline"
		if r.read("container", c) != nil {
			err = errors.New("Container " + c + " already pre-registered. This should only be pre-registered once")
			break
		} else {
			err = r.insert("container", c, o)
			if err != nil {
				break
			}
		}
	}
	//Second the actions
	for a := range actionSet {
		//Insert container into redis
		var o Action
		o.ActionName = a
		o.State = "offline"
		if r.read("action", a) != nil {
			err = errors.New("Action " + a + " already pre-registered. This should only be pre-registered once")
			break
		} else {
			err = r.insert("action", a, o)
			if err != nil {
				break
			}
		}
	}
	return err
}

//Connect - connects to redis database
func (r *Redis) Connect(hostname string, port int) error {

	addr := flag.String("Server", hostname+":"+strconv.Itoa(port), "Redis server address")

	r.handler = rejson.NewReJSONHandler()
	flag.Parse()

	conn, err := redis.Dial("tcp", *addr)
	if err != nil {
		s := fmt.Sprintf("Failed to connect to redis-server @ %s", *addr)
		return errors.New(s)
	}
	r.handler.SetRedigoClient(conn)
	//Flush the database before we start (just in case there's leftover state)
	return conn.Send("FLUSHDB")
}

//GetRedis - Returns a new redis object
func GetRedis() *Redis {
	return &Redis{}
}
