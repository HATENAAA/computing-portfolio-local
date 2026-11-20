<script setup>
defineProps({name:String});
const paths={courses:'M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z',studio:'M9 5l11 7-11 7z',plan:'M5 5h14v16H5z M9 3v4 M15 3v4 M8 11h8 M8 15h5',records:'M4 19h16 M7 15V9 M12 15V5 M17 15v-7',ai:'M12 3l2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8z',back:'M15 5l-7 7 7 7',arrow:'M5 12h14 M13 6l6 6-6 6'};
</script>
<template><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="paths[name]||paths.courses"/></svg></template>
