<script lang="ts">
	import { api } from '$lib/api';
	let username = '';
	let password = '';
	let error: string | null = null;

	async function submit() {
		error = null;
		try {
			const r = await api.login(username, password);
			localStorage.setItem('dossier_token', r.access_token);
			// fetch user info
			const me = await api.me_jwt();
			localStorage.setItem('dossier_user', JSON.stringify({ username: me.user }));
			location.href = '/people';
		} catch (err: any) {
			error = err.message || String(err);
		}
	}
</script>

<div class="card">
	<h3>Sign in</h3>
	{#if error}
		<div class="error-message">{error}</div>
	{/if}
	<div class="form-grid">
		<input placeholder="username" bind:value={username} />
		<input placeholder="password" type="password" bind:value={password} />
		<button class="btn primary" on:click={submit}>Sign in</button>
	</div>
</div>

<style>
	.form-grid {
		display: grid;
		gap: 0.5rem;
		max-width: 420px;
	}

	.error-message {
		color: #ef4444;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}
</style>
