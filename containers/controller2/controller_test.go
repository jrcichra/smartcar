package main

import (
	"controller2/common"
	"encoding/json"
	"net"
	"testing"
	"time"

	"github.com/davecgh/go-spew/spew"
)

func connect(t *testing.T) net.Conn {
	conn, err := net.Dial("tcp", "controller:8080")
	if err != nil {
		t.Error("Could not connect to server: ", err)
	}
	return conn
}

func send(containerName string, name string, typ string, t *testing.T) (common.Message, common.Message) {
	conn := connect(t)
	defer conn.Close()
	//Try to register something
	var m common.Message
	m.Name = name
	m.Timestamp = time.Now().Unix()
	m.Type = typ
	m.ContainerName = containerName

	bmsg, err := json.Marshal(m)
	if err != nil {
		t.Error("Could not convert message to bytearray: ", err)
	}
	conn.Write(bmsg)

	//Now get the response
	d := json.NewDecoder(conn)
	var m2 common.Message
	err = d.Decode(&m2)
	if err != nil {
		t.Error(err)
	}
	t.Log(spew.Sdump(m2))
	return m, m2
}

func registerContainer(name string, t *testing.T) (common.Message, common.Message) {
	return send("", name, REGISTERCONTAINER, t)
}

func registerEvent(containerName string, name string, t *testing.T) (common.Message, common.Message) {
	return send(containerName, name, REGISTEREVENT, t)
}

func registerAction(containerName string, name string, t *testing.T) (common.Message, common.Message) {
	return send(containerName, name, REGISTERACTION, t)
}

func emitEvent(containerName string, name string, t *testing.T) (common.Message, common.Message) {
	return send(containerName, name, EMITEVENT, t)
}

func TestConnection(t *testing.T) {
	conn := connect(t)
	defer conn.Close()
}

func TestRegisterContainer(t *testing.T) {
	m, m2 := registerContainer("dashcam", t)
	//And check if it is what we expect
	if m2.Timestamp >= m.Timestamp && m2.ResponseCode == OK && m2.Properties == nil && m2.Name == m.Name && m2.ContainerName == "" && m2.Type == REGISTERCONTAINERRESPONSE {
		//Valid
	} else {
		t.Error("Message received was not as expected")
	}
}

func TestRegisterEvent(t *testing.T) {
	m, m2 := registerEvent("gpio", "key_on", t)
	//And check if it is what we expect
	if m2.Timestamp >= m.Timestamp && m2.ResponseCode == OK && m2.Properties == nil && m2.Name == m.Name && m2.ContainerName == m.ContainerName && m2.Type == REGISTEREVENTRESPONSE {
		//Valid
	} else {
		t.Error("Message received was not as expected")
	}
}

func TestRegisterAction(t *testing.T) {
	m, m2 := registerAction("dashcam", "start_recording", t)
	//And check if it is what we expect
	if m2.Timestamp >= m.Timestamp && m2.ResponseCode == OK && m2.Properties == nil && m2.Name == m.Name && m2.ContainerName == m.ContainerName && m2.Type == REGISTERACTIONRESPONSE {
		//Valid
	} else {
		t.Error("Message received was not as expected")
	}
}

// func TestEmitEvent(t *testing.T) {
// 	m, m2 := emitEvent("gpio", "key_on", t)
// 	//And check if it is what we expect
// 	if m2.Timestamp >= m.Timestamp && m2.ResponseCode == OK && m2.Properties == nil && m2.Name == m.Name && m2.ContainerName == m.ContainerName && m2.Type == EMITEVENTRESPONSE {
// 		//Valid
// 	} else {
// 		t.Error("Message received was not as expected")
// 	}
// }
