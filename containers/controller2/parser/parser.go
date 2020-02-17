package parser

// This parser uses a LOT of type switches. I apologize in advance

import (
	"controller2/common"
	"errors"
	"io/ioutil"
	"reflect"
	"strconv"
	"strings"

	"gopkg.in/yaml.v2"
)

const (
	//OFFLINE -
	OFFLINE = "offline"
	//ONLINE -
	ONLINE = "online"
)

//Container - container struct
type Container struct {
	Name  string
	State string
}

//Parameter - Single parameter with a name and value (of any type)
type Parameter struct {
	Name  string
	Type  string
	Value interface{}
}

//Parameters - an array of parameter objects
type Parameters []Parameter

//Operand - part of a conditional expression
type Operand interface{} //Could be a parameter or primitive type

//Operator - just a comparison operator
type Operator string //==,<>,<=,>=

//Condition - has one of several keywords that will conditionally execute an event's desired actions
type Condition struct {
	Type         string //when/and/else
	Operator     Operator
	LeftOperand  Operand
	RightOperand Operand
}

//Conditions - a slice of Condition objects
type Conditions []Condition

//Action - Tell a container to do something
type Action struct {
	State      string
	Container  string
	Name       string
	Parameters Parameters
}

//Actions - a slice of action objects
type Actions []Action

//Block - instruction block
type Block struct {
	Type     string        //serial,parallel, or conditional (or more later)
	Children []interface{} //Children of this block (check what type should go here and cast it at runtime)
}

//Blocks - a slice of block objects
type Blocks []Block

//Event - single event defined in a config
type Event struct {
	State         string
	ContainerName string
	EventName     string
	Blocks        *Blocks
}

//Events - a slice of event objects
type Events []Event

//Config - Config file represented in a go struct
type Config struct {
	Events     Events
	Containers map[string]*Container
	Actions    map[string]*Action
	EventsMap  map[string]*Event
}

//RegisterEvent - registers an event
func (c *Config) RegisterEvent(msg *common.Message) error {
	var err error
	err = nil
	if value, ok := c.EventsMap[msg.Name]; ok {
		value.State = ONLINE
	} else {
		err = errors.New("Could not find an event that matches one in the list")
	}
	return err
}

//RegisterAction - registers an action
func (c *Config) RegisterAction(msg *common.Message) error {
	var err error
	err = nil
	if value, ok := c.Actions[msg.Name]; ok {
		value.State = ONLINE
	} else {
		err = errors.New("Could not find an action that matches one in the list")
	}
	return err
}

//RegisterContainer - registers a container
func (c *Config) RegisterContainer(msg *common.Message) error {
	var err error
	err = nil
	if value, ok := c.Containers[msg.ContainerName]; ok {
		value.State = ONLINE
	} else {
		err = errors.New("Could not find a container that matches one in the list")
	}
	return err
}

//GetEvent - Return an event based on what we request
func (c *Config) GetEvent(name string) (*Event, error) {
	var err error
	err = nil
	var e *Event
	if value, ok := c.EventsMap[name]; ok {
		e = value
	} else {
		err = errors.New("Could not find a container that matches one in the list")
	}
	return e, err
}

//parses a yaml "parameter string" and returns a Parameter
func (c *Config) parameter(parameterName string, parameter interface{}) (*Parameter, error) {
	// Determine the type of the parameter we passed in - similar to Conditions, but with type switches (as always)
	var p Parameter

	p.Name = parameterName
	p.Value = parameter

	switch parameter.(type) {
	case string:
		//Their parameter is a string
		p.Type = "string"
	case float32, float64, int, int16, int32, int64, int8:
		//Their parameter is a number
		p.Type = "number"
	case bool:
		//Their parameter is a bool
		p.Type = "bool"
	default:
		return nil, errors.New("Unknown type in parameter")
	}

	return &p, nil
}

func (c *Config) splitter(s string) ([]string, error) {

	split := strings.Split(s, ".")
	if len(split) > 2 {
		return nil, errors.New("Action was invalid format. Expected 'container.action', got " + s)
	}

	return split, nil
}

//parses a yaml "action string" - when, and, else, etc and returns an Action
func (c *Config) action(actionName string, action interface{}) (*Action, error) {
	var act Action

	act.Name = actionName
	switch a := action.(type) {
	case map[interface{}]interface{}:
		// loop through them (should be one at this level?)
		for key, a2 := range a {
			switch params := a2.(type) {
			case interface{}:
				switch k := key.(type) {
				case string:

					// We've hit the name of the action.
					// It should be formatted as "container.action"
					// Let's split on the .

					split, err := c.splitter(k)
					if err != nil {
						return nil, err
					}
					act.Container = split[0]
					act.Name = split[1]
					act.State = OFFLINE

					//add action to map of actions
					c.Actions[act.Name] = &act

					// Now that we've disected the name of the event,
					// let's check if there are any parameters
					switch p := params.(type) {
					case []interface{}:
						//This is an array, there are parameters in here
						for _, mapp := range p {
							switch m := mapp.(type) {
							case map[interface{}]interface{}:
								//Loop through all the parameters
								for k, v := range m {
									switch sk := k.(type) {
									case string:
										param, err := c.parameter(sk, v)
										if err != nil {
											return nil, err
										}
										// append param to list of parameters for this action
										act.Parameters = append(act.Parameters, *param)
									default:
										return nil, errors.New("Expected a string for the parameter name")
									}
								}
							default:
								return nil, errors.New("Expected map of parameters")
							}

						}

					default:
						return nil, errors.New("Couldn't find the name of the action? Not completely sure how we can hit this error if I'm being honest")
					}
				default:
					return nil, errors.New("Expected string key")
				}

			default:
				return nil, errors.New("Expected string condition")
			}
		}
	case string:
		// If we hit here, there are no parameters on this action, which is totally fine
		// We still want to append the action on, it just won't have parameters
		split, err := c.splitter(a)
		if err != nil {
			return nil, err
		}
		act.Container = split[0]
		act.Name = split[1]

	default:
		return nil, errors.New("Action couldn't be recognized as a string or a map of parameters")
	}

	return &act, nil
}

//EvaluateCondition - Return the result from evaluating a condition
func (c *Config) EvaluateCondition(cond Condition) bool {
	var b bool
	if reflect.TypeOf(cond.LeftOperand) == reflect.TypeOf(cond.LeftOperand) {
		//Compare strings to strings or numbers to numbers (floats)
		if reflect.TypeOf(cond.LeftOperand) == reflect.TypeOf("") {
			//Do a string compare
			switch cond.Operator {
			case "==":
				b = cond.LeftOperand.(string) == cond.RightOperand.(string)
			default:
				panic("EvaulateCondition found a conditional that cannot exist for a string compare: " + cond.Operator)
			}
		} else if reflect.TypeOf(cond.LeftOperand) == reflect.TypeOf(float64(0)) {
			//Do a numberic compare
			switch cond.Operator {
			case "==":
				b = cond.LeftOperand.(float64) == cond.RightOperand.(float64)
			case "<=":
				b = cond.LeftOperand.(float64) <= cond.RightOperand.(float64)
			case ">=":
				b = cond.LeftOperand.(float64) >= cond.RightOperand.(float64)
			case "<":
				b = cond.LeftOperand.(float64) < cond.RightOperand.(float64)
			case ">":
				b = cond.LeftOperand.(float64) > cond.RightOperand.(float64)
			default:
				panic("EvaulateCondition found a conditional that cannot exist for a numeric compare: " + cond.Operator)
			}
		} else {
			panic("EvalutateCondition does not understand the type of the left and right operand")
		}

	} else {
		panic("EvaluateCondition found that the left operand's type did not match that of the right operand")
	}
	return b
}

//parses a yaml "condition string" - when, and, else, etc and returns a Condition
func (c *Config) condition(conditionName string, conditionString string) (*Condition, error) {
	var condition Condition
	//separate the right side of the yaml by spaces first
	conditionSlice := strings.Split(conditionString, " ")
	condition.Type = "Condition"

	//We can't trust that the conditionString slice is really a string, could be a float
	lfloat, err := strconv.ParseFloat(conditionSlice[0], 64)
	if err != nil {
		//could also be a boolean
		lbool, err := strconv.ParseBool(conditionSlice[0])
		if err != nil {
			//keep it a string, it can't be a float or bool
			condition.LeftOperand = conditionSlice[0]
		} else {
			//must be a bool
			condition.LeftOperand = lbool
		}
	} else {
		//must be a float (or an int, but float is fine)
		condition.LeftOperand = lfloat
	}

	//We know the operator has to be a string, do a typecast
	condition.Operator = Operator(conditionSlice[1])

	//We can't trust that the conditionString slice is really a string, could be a float
	rfloat, err := strconv.ParseFloat(conditionSlice[2], 64)
	if err != nil {
		//could also be a boolean
		rbool, err := strconv.ParseBool(conditionSlice[2])
		if err != nil {
			//keep it a string, it can't be a float or bool
			condition.RightOperand = conditionSlice[2]
		} else {
			//must be a bool
			condition.RightOperand = rbool
		}
	} else {
		//must be a float (or an int, but float is fine)
		condition.RightOperand = rfloat
	}

	var e error
	e = nil //just making sure initialization is right

	//when we get here, the whole object should be populated
	if condition.Type == "" || condition.Operator == "" || condition.LeftOperand == "" || condition.RightOperand == "" {
		//Something is missing, error
		e = errors.New("Condition is missing one of its parameters. Something went wrong when parsing the condition string")
	}

	return &condition, e

}

//Parses a yaml "block" (serial/parallel/condition)
func (c *Config) block(blocksArrayInterface interface{}) (*Block, error) {
	var block Block
	blocksInterface := make(map[interface{}]interface{})

	//get the map out of this interface array
	switch m := blocksArrayInterface.(type) {
	case map[interface{}]interface{}:
		blocksInterface = m
	default:
		return nil, errors.New("Couldn't get map out of array in block")
	}

	//Get the keys for this map (there should only be one, so looping and keeping the last
	for k := range blocksInterface {
		switch s := k.(type) {
		case string:
			block.Type = s
		default:
			return nil, errors.New("Couln't find string key for block")
		}

	}

	//decipher the string further
	switch block.Type {
	case "when", "and", "or":
		//conditionals
		switch b := blocksArrayInterface.(type) {
		//make sure it's a map
		case map[interface{}]interface{}:
			//loop through them (should be one at this level?)
			for key, condition := range b {
				switch s := condition.(type) {
				case string:
					switch k := key.(type) {
					case string:
						cond, err := c.condition(k, s)
						if err != nil {
							return nil, err
						}
						//put our new condition onto the block
						block.Children = append(block.Children, *cond)
					default:
						return nil, errors.New("Expected string key")
					}

				default:
					return nil, errors.New("Expected string condition")
				}

			}
		default:
			return nil, errors.New("Map is not what we expected")
		}
	case "serial", "parallel":
		//Under serial/parallel, we have Actions, not conditions
		switch b := blocksArrayInterface.(type) {
		//make sure it's a map
		case map[interface{}]interface{}:
			//Should be one thing under this block
			for key, action := range b {
				switch k := key.(type) {
				case string:
					switch a := action.(type) {
					case []interface{}:
						//Loop through all the actions (this should be an array)
						for _, action2 := range a {
							//we've hit the actions, process each action in a function
							processedAction, err := c.action(k, action2)
							if err != nil {
								return nil, err
							}
							//put our new action onto the block
							block.Children = append(block.Children, *processedAction)
						}
					default:
						return nil, errors.New("Expected string key")
					}

				default:
					return nil, errors.New("Expected string condition")
				}

			}
		default:
			return nil, errors.New("Map is not what we expected")
		}
	}
	return &block, nil
}

func (c *Config) event(eventName interface{}, eventsInterface interface{}) (*Event, error) {
	var event Event
	var blocks Blocks

	//check if eventName is a string
	switch name := eventName.(type) {
	case string:
		//it is a string, set the container name and name
		split, err := c.splitter(name)
		if err != nil {
			return nil, err
		}

		//Add this container to the map of containers
		event.ContainerName = split[0]
		var cont Container
		cont.Name = event.ContainerName
		cont.State = OFFLINE
		c.Containers[cont.Name] = &cont

		event.EventName = split[1]
		event.State = OFFLINE
		c.EventsMap[event.EventName] = &event

	default:
		//Not a string, error
		return nil, errors.New("EventName was not a string")
	}

	//make sure blocks is an array and loop through the blocks

	switch b := eventsInterface.(type) {
	case []interface{}:
		//It's an array, loop through each block
		for _, blockArrayInterface := range b {
			b, err := c.block(blockArrayInterface)
			if err != nil {
				return nil, err
			}
			//Deference the Blocks pointer, which gives a struct
			//of []Block, appending the old blocks with the new block
			//Deferencing to get something append() understands
			blocks = append(blocks, *b)
		}
	default:
		return nil, errors.New("In event, block's type wasn't anything we expected")
	}

	//Once we built the blocks array, assign it to the event
	event.Blocks = &blocks

	return &event, nil
}

//actually do the heavy lifting
func (c *Config) config(generic interface{}) (*Config, error) {
	var mainEvents Events
	switch g := generic.(type) {
	//events:
	case map[interface{}]interface{}:
		//loop through all first level keys
		for top, events := range g {
			//If we find out it's a string type on the left
			switch t := top.(type) {
			case string:
				//check if it's "events"
				if t == "events" {
					//Dive into each event and parse it
					switch e := events.(type) {
					case map[interface{}]interface{}:
						//if it is a map, loop through each event
						for key, events := range e {
							event, err := c.event(key, events)
							if err != nil {
								panic(err)
							}
							// spew.Dump(event)
							// append event to event array
							mainEvents = append(mainEvents, *event)
						}

					}

				}
			}
		}

	}
	//Combine all the events into a Config
	var config Config
	config.Events = mainEvents
	return &config, nil
}

//Parse - parse the yaml file
func (c *Config) Parse(filename string) (*Config, error) {
	//open the config file
	config, err := ioutil.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	var g interface{}
	err = yaml.Unmarshal([]byte(config), &g)
	if err != nil {
		return nil, err
	}
	// spew.Dump(g)
	//parse it beyond interface{}
	cfg, err := c.config(g)
	if err != nil {
		return nil, err
	}

	return cfg, nil
}
