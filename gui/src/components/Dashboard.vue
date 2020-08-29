<template>
  <div class="dashboard">
      <Speedometer id="speedometer" value="30"/>
      <Preview id="preview"/>
  </div>
</template>

<script>
import Speedometer from "./Speedometer";
import Preview from "./Preview";
export default {
  name: "Dashboard",
  props: {
    title: String,
  },
  components: {
    Speedometer,
    Preview,
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.dashboard #speedometer {
  float: left;
}
.dashboard #preview {
  float: none;
}
</style>
