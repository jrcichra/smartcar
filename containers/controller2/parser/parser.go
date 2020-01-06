package parser

import (
	"errors"
	"io/ioutil"

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

//Comparator - just a comparison operator
type Comparator string //==,<>,<=,>=

//Condition - has one of several keywords that will conditionally execute an event's desired actions
type Condition struct {
	Type      string //when/and/else
	Condition string //speed > 65 - brake down into Operands and
}

//Action - Tell a container to do something
type Action struct {
	Name       string
	Parameters *[]Parameter
}

//Actions - an array of action objects
type Actions *[]Action

//Block - instruction block
type Block struct {
	Type     string         //serial,parallel, or conditional (or more later)
	Children *[]interface{} //Children of this block (check what type should go here and cast it at runtime)
}

//Blocks - an array of block objects
type Blocks *[]Block

//Event - single event defined in a config
type Event struct {
	Name   string
	Blocks *Blocks
}

//Config - Config file represented in a go struct
type Config struct {
	Events *[]Event
}

func (c *Config) block(blockType interface{}, actions interface{}) (*Blocks, error) {
	var block *Block

	//check if blockName is a string
	switch t := blockType.(type) {
	case string:
		//it is a string, set it
		block.Type = t
	default:
		//not a string, error
		return nil, errors.New("BlockType was not a string")
	}

	//decipher the string further
	switch block.Type {
	case "when":
	case "and":
	case "else":
		//conditionals
	case "serial":
		//serial
	case "parallel":
		//parallel
	}

}

func (c *Config) event(eventName interface{}, blocks interface{}) (*Event, error) {
	var event *Event

	//check if eventName is a string
	switch name := eventName.(type) {
	case string:
		//it is a string, set it
		event.Name = name
	default:
		//Not a string, error
		return nil, errors.New("EventName was not a string")
	}

	//make sure blocks is a map and loop through the blocks

	switch b := blocks.(type) {
	case map[interface{}]interface{}:
		//It's a map, loop through each block
		for key, block := range b {
			blk, err := c.block(key, block)
		}
	}

	return event, nil
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
	spew.Dump(g)
	//parse it beyond interface{}
	c.config(g)
	return nil
}
