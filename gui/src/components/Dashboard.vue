<template>
  <div class="dashboard">
      <div class="stats">
        <h1 id="title">Smartcar</h1>
        <Speedometer id="speedometer" :value=speed title="Speed (mph)"/>
        <Tachometer id="tachometer" :value=rpm title="RPM"/>
        <input type="button" value="Button">
      </div>
    <div class="preview">
       <Preview id="preview"/> 
       </div>
  </div>
 
</template>

<script>
import Speedometer from "./Speedometer";
import Tachometer from "./Tachometer";
import Preview from "./Preview";
export default {
  name: "Dashboard",
  props: {
    title: String,
  },
  components: {
    Speedometer,
    Tachometer,
    Preview,
  },
  computed: {
    speed() {
      return this.$store.state.speed;
    },
    rpm(){
      return this.$store.state.rpm;
    }
  },
  mounted() {
    window.ipcRenderer.on("speed",(event,speed) =>{
      console.log("new speed: " + speed);
      this.$store.commit('speed',speed);
    });
    window.ipcRenderer.on("rpm",(event,rpm) =>{
      console.log("new rpm: " + rpm);
      this.$store.commit('rpm',rpm);
    });
    console.log(window.ipcRenderer);
  }
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
a {
  color: #42b983;
}
.dashboard{
  display: flex;
}
#title {
  color:#42b983;
  text-align: center;
  font-family: 'Courier New', Courier, monospace;
  font-style: italic;
}
.stats {
  display: flex;
  flex-direction: column;
}
.preview {
  margin-left: 30px;
  display: flex;
}
</style>
