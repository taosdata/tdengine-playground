import {fileURLToPath, URL} from 'node:url'

import {defineConfig} from 'vite'
import vueJsx from '@vitejs/plugin-vue-jsx'

import monacoEditorPlugin from 'vite-plugin-monaco-editor';
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        vueJsx(),
        monacoEditorPlugin({}),
    ],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },

})
