<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser, setupRequired } from '$lib/stores';
	import { get } from 'svelte/store';

	// local component state mirrors stores so the template updates synchronously
	let user: any = null;
	let isSetupRoute = false;
	let requiresSetup = false;

	const unsubscribeUser = currentUser.subscribe((v) => (user = v));
	const unsubscribeSetup = setupRequired.subscribe((v) => (requiresSetup = v));

	onMount(() => {
		isSetupRoute = location.pathname.startsWith('/setup');
		// If the app didn't initialize the currentUser from storage, do a best-effort
		// synchronous read so the header doesn't flash.
		if (!get(currentUser)) {
			try {
				const raw = localStorage.getItem('dossier_user');
				if (raw) currentUser.set(JSON.parse(raw));
			} catch (e) {
				// ignore
			}
		}
	});

	function logout() {
		localStorage.removeItem('dossier_token');
		localStorage.removeItem('dossier_user');
		currentUser.set(null);
		location.href = '/';
	}

	// cleanup if component is destroyed (Svelte's lifecycle is lightweight but keep tidy)
	// note: Svelte will call these when component unmounts; optional here.
	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	function onDestroy() {
		unsubscribeUser();
		unsubscribeSetup();
	}
</script>

{#if !isSetupRoute}
	<header class="card header">
		<div class="brand">
			<h2>Dossier</h2>
			<nav aria-label="primary navigation">
				<a href="/">Home</a>
				<a href="/people">People</a>
				<a href="/add">Add</a>
			</nav>
		</div>

		<div class="actions">
			{#if user}
				<span class="signed">Signed in: {user.username}</span>
				<button class="btn" on:click={logout}>Sign out</button>
			{:else}
				<!-- hide sign in if we're on a route that shouldn't show it -->
				<a class="btn" href="/login">Sign in</a>
			{/if}

			{#if !requiresSetup}
				<!-- when setup is not required, don't display the initial setup link in header -->
			{:else}
				<!-- if setup is required and user is not signed in, offer setup link -->
				{#if !user}
					<a class="btn" href="/setup">Initial setup</a>
				{/if}
			{/if}
		</div>
	</header>
{/if}

<style>
	.header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	h2 {
		margin: 0;
		font-size: 1.15rem;
	}
	nav {
		color: var(--muted);
		font-size: 1.02rem;
	}
	.dot {
		margin: 0 0.5rem;
	}
	.actions {
		display: flex;
		align-items: center;
		gap: 0.6rem;
	}
	.signed {
		margin-right: 0.4rem;
		color: var(--muted);
	}

	.btn {
		background: var(--accent);
		color: white;
		border: none;
		padding: 0.45rem 0.7rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		box-shadow: 0 4px 14px rgba(123, 97, 255, 0.18);
	}
</style>
