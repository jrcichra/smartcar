

<template>
  <div :style="speedometer_style">
    <vue-speedometer        
        :fluidWidth="true"
        :needleHeightRatio="0.7"
        :value=value
        :minValue="0"
        :maxValue="10000"
        :currentValueText=title
        :ringWidth="47"
        :maxSegmentLabels="11"
        :segments="11"
        :customSegmentStops="[0, 1000, 2000, 3000, 4000,5000,6000,7000,8000,9000,10000]"
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
    value: Number,
    title: String,
  },
    data() {
    return {
      speedometer_style: {
        width: "300px",
        height: "200px",
      },
    }
  },
};
</script>
<style scoped>
</style>