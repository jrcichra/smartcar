package parser

import (
	"errors"
	"io/ioutil"
	"strconv"
	"strings"

	"github.com/davecgh/go-spew/spew"
	"gopkg.in/yaml.v2"
)

//Parameter - Single parameter with a name and value (of any type)
type Parameter struct {
	Name  string
	Value interface{}
}

//Parameters - an array of parameter objects
type Parameters *[]Parameter

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
	Name       string
	Parameters *[]Parameter
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
	Name   string
	Blocks *Blocks
}

//Config - Config file represented in a go struct
type Config struct {
	Events []Event
}

//parses a yaml "condition string" - when, and, else, etc and returns a Condition
func (c *Config) condition(conditionName string, conditionString string) (*Condition, error) {
	var condition Condition
	//separate the right side of the yaml by spaces first
	conditionSlice := strings.Split(conditionString, " ")
	condition.Type = conditionName

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
	e = nil //just making sure initalization is right

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
	case "when", "and", "else":
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
						block.Children = append(block.Children, cond)
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

		//TODO

		switch blocksArrayInterface.(type) {
		//if we have a map,
		case map[interface{}]interface{}:

		}
	default:
		return nil, errors.New("Keyword not recognized at the block level")
	}
	return &block, nil
}

func (c *Config) event(eventName interface{}, eventsInterface interface{}) (*Event, error) {
	var event Event
	var blocks Blocks

	//check if eventName is a string
	switch name := eventName.(type) {
	case string:
		//it is a string, set it
		event.Name = name
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
func (c *Config) config(generic interface{}) error {
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
							spew.Dump(event)
						}

					}

				}
			}
		}

	}
	return nil
}

//Parse - parse the yaml file
func (c *Config) Parse(filename string) error {
	//open the config file
	config, err := ioutil.ReadFile(filename)
	if err != nil {
		return err
	}
	var g interface{}
	err = yaml.Unmarshal([]byte(config), &g)
	if err != nil {
		return err
	}
	// spew.Dump(g)
	//parse it beyond interface{}
	c.config(g)
	return nil
}
