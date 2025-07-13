import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	assetsInclude: ['**/*.csv'],
	server:{
	allowedHosts: ['clusterchat.ifi.uni-heidelberg.de']
	}
});
