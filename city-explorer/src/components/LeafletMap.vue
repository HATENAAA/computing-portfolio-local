<template><iframe class="city-atlas" :src="source" title="上海红色文化地图"></iframe></template>
<script setup>
const source = './atlas/index.html' + window.location.search;
</script>
<style>
.city-atlas{display:block;width:100%;height:100dvh;border:0}
</style>
