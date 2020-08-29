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

export default {
  name: "App",
  components: {
    Dashboard,
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #a00000;
  margin-top: 60px;
}
</style>
