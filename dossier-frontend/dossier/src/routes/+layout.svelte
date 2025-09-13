<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import Header from '$lib/Header.svelte';
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { setupRequired, initCurrentUserFromStorage, appReady, markAppReady } from '$lib/stores';
	import { get } from 'svelte/store';

	let { children } = $props();

	onMount(async () => {
		// initialize the cached user from storage so Header can render synchronously
		initCurrentUserFromStorage();

		try {
			const resp = await api.setup();
			if (resp && typeof resp.setup_required !== 'undefined') {
				setupRequired.set(Boolean(resp.setup_required));
				// Preserve previous redirect behavior for first-time flow
				if (resp.setup_required && !location.pathname.startsWith('/setup')) {
					location.href = '/setup';
				}
			}
		} catch (e) {
			console.error('Setup check failed', e);
		} finally {
			// mark the app as ready to render UI; does not block.
			markAppReady();
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<!-- Use Inter for a modern UI look -->
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"
		rel="stylesheet"
	/>
	<meta name="viewport" content="width=device-width,initial-scale=1" />
	<style>
		/* Dark theme variables with purple accent and translucent surfaces */
		:root {
			--bg: #0b0b0f;
			--panel: rgba(18, 18, 22, 0.6);
			--panel-strong: rgba(22, 18, 30, 0.7);
			--muted: #9aa3b2;
			--accent: #7b61ff; /* purple */
			--glass-border: rgba(255, 255, 255, 0.06);
		}

		html,
		body {
			height: 100%;
		}
		body {
			font-family:
				Inter,
				system-ui,
				-apple-system,
				'Segoe UI',
				Roboto,
				'Helvetica Neue',
				Arial;
			margin: 0;
			color: #e6eef8;
			font-size: 16px; /* slightly larger base type */
			background: linear-gradient(180deg, #05050a 0%, #0d0812 60%);
			-webkit-font-smoothing: antialiased;
			-moz-osx-font-smoothing: grayscale;
		}

		main {
			max-width: 1100px;
			margin: 2.25rem auto;
			padding: 1rem;
		}

		header {
			border-bottom: 1px solid rgba(255, 255, 255, 0.03);
		}

		a {
			color: var(--accent);
		}

		/* Glassy card style */
		.card {
			background: var(--panel);
			border: 1px solid var(--glass-border);
			padding: 1.15rem;
			border-radius: 12px;
			box-shadow: 0 6px 24px rgba(11, 9, 20, 0.6);
			backdrop-filter: blur(6px) saturate(120%);
		}

		/* Global input styles */
		input,
		textarea,
		select {
			font-size: 1rem; /* larger controls */
			padding: 0.7rem;
			border-radius: 10px;
			border: 1px solid rgba(255, 255, 255, 0.06);
			background: rgba(255, 255, 255, 0.02);
			color: inherit;
		}

		input::placeholder,
		textarea::placeholder {
			color: rgba(255, 255, 255, 0.42);
		}

		/* Button utility classes — centralized so all pages inherit consistent styles */
		.btn {
			display: inline-block;
			padding: 0.6rem 1rem;
			border-radius: 10px;
			text-decoration: none;
			font-weight: 600;
			border: none;
			cursor: pointer;
			background: transparent;
			color: inherit;
		}

		.btn.primary {
			background: var(--accent);
			color: white;
			box-shadow: 0 8px 22px rgba(123, 97, 255, 0.12);
		}

		.btn.outline {
			background: transparent;
			border: 1px solid rgba(255, 255, 255, 0.06);
			color: inherit;
		}

		/* Utility colors that components can use */
		.muted {
			color: var(--muted);
		}

		/* Utility classes for common layouts */
		.flex {
			display: flex;
		}

		.flex-col {
			display: flex;
			flex-direction: column;
		}

		.items-center {
			align-items: center;
		}

		.justify-between {
			justify-content: space-between;
		}

		.gap-sm {
			gap: 0.5rem;
		}

		.gap-md {
			gap: 1rem;
		}

		.mt-sm {
			margin-top: 0.5rem;
		}

		.mt-md {
			margin-top: 1rem;
		}

		/* Grid utilities */
		.grid {
			display: grid;
		}

		.grid-fill {
			grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		}

		.grid-cols-1 {
			grid-template-columns: 1fr;
		}

		/* Pill component style - reusable */
		.pill {
			background: rgba(0, 0, 0, 0.03);
			padding: 0.4rem 0.5rem;
			border-radius: 8px;
			font-size: 0.85rem;
			white-space: nowrap;
		}

		/* Avatar component style - reusable */
		.avatar {
			width: 48px;
			height: 48px;
			border-radius: 8px;
			background: linear-gradient(135deg, var(--accent), #7b61ff);
			flex-shrink: 0;
		}

		/* Common transition utilities */
		.transition-hover {
			transition:
				transform 0.2s ease,
				box-shadow 0.2s ease;
		}

		.transition-hover:hover {
			transform: translateY(-2px);
			box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		}
		/* hide header immediately if HTML indicates we're on setup to avoid flash-of-header */
		[data-setup] .header {
			display: none !important;
		}

		/* header backdrop to match glass style */
		.header {
			background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
			padding: 0.6rem 0.8rem;
		}

		/* Modern nav pill styles (header nav links) */
		.header nav a {
			display: inline-block;
			padding: 0.45rem 0.7rem;
			border-radius: 999px;
			background: transparent;
			color: var(--muted);
			transition: all 0.16s ease;
			font-weight: 600;
			text-decoration: none;
		}

		.header nav a:hover {
			color: white;
			background: linear-gradient(90deg, rgba(123, 97, 255, 0.12), rgba(165, 141, 255, 0.06));
			transform: translateY(-2px);
			text-decoration: none;
		}
	</style>
</svelte:head>

{#if $appReady}
	<Header />
	<main>
		{@render children?.()}
	</main>
{:else}
	<!-- hold a minimal loading surface to avoid layout flash -->
	<div style="min-height: 100vh; display:flex; align-items:center; justify-content:center;">
		<div class="card muted">Loading…</div>
	</div>
{/if}
