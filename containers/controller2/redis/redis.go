package redis

import (
	common "controller2/common"
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
	State         string   `json:"state"`          //online?
	ContainerName string   `json:"container_name"` //PK
	Timestamp     int64    `json:"timestamp"`      //Timestamp
	Events        []string `json:"events"`         //list of events in no particular order for this container (just the name, rest of the details can be queried out separately)
	Actions       []string `json:"actions"`        //list of actions in no particular order for this container (just the name, rest of the details can be queried out separately)
}

//Event - event type as stored in redis
type Event struct {
	State         string      `json:"state"`          //online?
	EventName     string      `json:"event_name"`     //PK
	ContainerName string      `json:"container_name"` //Relate an event to a container
	Timestamp     int64       `json:"timestamp"`      //Timestamp
	Properties    interface{} `json:"properties"`     //Properties of the event
}

//Action - action type as stored in redis
type Action struct {
	State         string      `json:"state"`          //online?
	ActionName    string      `json:"action_name"`    //PK
	ContainerName string      `json:"container_name"` //Relate an action to a container
	Timestamp     int64       `json:"timestamp"`      //Timestamp
	Properties    interface{} `json:"properties"`     //Properties of the event
}

//InstructionSet - what to reference when an event comes in (Conditionals, parallel/serial)
type InstructionSet struct {
	EventName   string        `json:"event_name"`  //Event Name (so we know what event this is for)
	Instruction []interface{} `json:"instruction"` //An instruction set is an array of Instructions (which could be actions or conditions)
}

func (r *Redis) insert(key string, obj interface{}) error {

	res, err := r.handler.JSONSet(key, ".", obj)
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

func (r *Redis) read(typ string, name string) interface{} {
	//We don't care about errors, if msg is nil we know it's not there
	msg, _ := redis.Bytes(r.handler.JSONGet(typ+"_"+name, "."))
	return msg
}

//RegisterContainer - registers the container inside of redis
func (r *Redis) RegisterContainer(msg *common.Message) error {
	existing := r.read("container", msg.ContainerName)
	if existing != nil {
		//There's something already there
		switch e := existing.(type) {
		case Container:
			tf := time.Unix(e.Timestamp, 0).Local().Format("2006-01-02T15:04:05.999999-05:00")
			return errors.New("Container already registered at" + tf)
		}

	}
	return r.insert("container_"+msg.ContainerName, msg)
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
	defer func() {
		_, err = conn.Do("FLUSHALL")
		err = conn.Close()
	}()
	r.handler.SetRedigoClient(conn)
	// fmt.Println("Executing Example_JSONSET for Redigo Client")
	// insertJSON()
	return nil
}

//GetRedis - Returns a new redis object
func GetRedis() *Redis {
	return &Redis{}
}
