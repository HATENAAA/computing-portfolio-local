import { defineConfig } from 'vite';
export default defineConfig({
  base:'./',
  plugins:[{
    name:'offline-studio-script',
    transformIndexHtml:{order:'post',handler(html){
      return html.replace(/<script type="module" crossorigin src=/g,'<script defer src=');
    }}
  }],
  build:{
    modulePreload:false, outDir:'../assets/studio', emptyOutDir:true,
    rollupOptions:{input:'studio-preview.html',output:{format:'iife'}}
  }
});
