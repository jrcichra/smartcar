package common

//Message - JSON structure that can handle registration, event emissions, and action distributions
type Message struct {
	Type          string      `json:"type"`           //Type of message being sent
	Timestamp     int64       `json:"timestamp"`      //What time this message was created
	ContainerName string      `json:"container_name"` //Container Name we want to address
	Name          string      `json:"name"`           //Name of the event/action/container based on type
	ResponseCode  int         `json:"response_code"`  //Response code (might be nil based on type)
	Properties    interface{} `json:"properties"`     //Properties attached to the event
}
