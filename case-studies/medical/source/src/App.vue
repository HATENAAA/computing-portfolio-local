<template>
  <div class="medical-scroll"><router-view/></div>
 </template>
 
<style>
 html,body,div,span,h1,h2,h3,h4,h5,h6,ul,ol,li,p{
    margin: 0;
    padding: 0;
 }
 html,body,#app{
    width: 100%;
    height: 100%;
    font-family: "微软雅黑";
 }
 ul,ol{
    list-style:none;
 }
 a{
    text-decoration: none;
 }
 .medical-scroll{height:100%;overflow:auto}
 :root{--medical-vw:min(1vi,4.8px)}
 @media(min-width:481px){body{background:#eaf1f6}#app{max-width:480px;margin:auto;background:white;position:relative;transform:translateZ(0);box-shadow:0 0 0 1px #cbd9e4}}
 </style>