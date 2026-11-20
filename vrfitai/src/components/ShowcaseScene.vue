<script setup>
import FitnessScene from './FitnessScene.vue';
defineProps({program:String, difficulty:String, compact:Boolean, calibration:Object});
</script>
<template>
  <FitnessScene class="showcase-scene" preview :key="program" :program="program"
    :difficulty="difficulty" :compact="compact" :calibration="calibration" />
</template>
