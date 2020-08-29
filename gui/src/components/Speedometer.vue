

<template>
  <div :style="speedometer_style">
    <vue-speedometer        
        :fluidWidth="true"
        :needleHeightRatio="0.7"
        :value=value
        :minValue="0"
        :maxValue="100"
        currentValueText="Speed (mph)"
        :ringWidth="47"
        :maxSegmentLabels="11"
        :segments="11"
        :customSegmentStops="[0, 10, 20, 30, 40,50,60,70,80,90,100]"
        :needleTransitionDuration="1111"
        needleColor="#a7ff83"
        textColor="#d8dee9"/>
  </div>
</template>

<script>
// import the component
import VueSpeedometer from "vue-speedometer";
// and use it in your component like
export default {
  components: { VueSpeedometer },  
  props: {
    value: String,
  },
    data() {
    return {
      speedometer_style: {
        width: "300px",
        height: "400px",
      },
    }
  },
};
</script>
<style scoped>
</style>