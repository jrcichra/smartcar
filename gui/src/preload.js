import { ipcRenderer } from 'electron'
window.ipcRenderer = ipcRenderer
//Send random numbers to the gauges
setInterval(()=>{
    console.log("doing math")
    let speed = Math.floor(Math.random() * 100); 
    let rpm = Math.floor(Math.random() * 10000);
    ipcRenderer.send("speed",speed);
    ipcRenderer.send("rpm",rpm);
},1000)