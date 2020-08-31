<template>
  <div id="app">
    <Dashboard title="Smartcar" />
  </div>
</template>

<script>
import Dashboard from "./components/Dashboard.vue";
import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

const store = new Vuex.Store({
  state: {
    speed: 0,
    rpm: 0
  },
  mutations: {
    updateSpeed (state,speed) {
      state.speed = speed;
    },
     updateRPM (state,rpm) {
      state.rpm = rpm;
    },
  }
})

export default {
  name: "App",
  components: {
    Dashboard,
  },
  store: store
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #a00000;
  margin-top: 20px;
}
</style>
