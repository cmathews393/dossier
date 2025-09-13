<script lang="ts">
	import { api } from '$lib/api';
	let step = 1;
	let username = '';
	let email = '';
	let password = '';
	let message: string | null = null;
	let error: string | null = null;
	let busy = false;

	$: canProceed = username.trim().length >= 3 && /@/.test(email) && password.length >= 8;

	function next() {
		error = null;
		if (!canProceed) {
			error = 'Please enter a valid username, email and a password (min 8 chars).';
			return;
		}
		step = 2;
	}

	async function submit() {
		message = error = null;
		busy = true;
		try {
			await api.register(username.trim(), email.trim(), password);
			message = 'Account created. You can sign in now.';
			// keep the success state visible and reset input
			username = '';
			email = '';
			password = '';
			step = 1;
		} catch (err: any) {
			error = (err && err.message) || String(err);
		} finally {
			busy = false;
		}
	}
</script>

<div class="card setup">
	<div class="setup-head">
		<h3>Initial setup</h3>
		<p class="muted">Create the first administrator account for this Dossier instance.</p>
	</div>

	{#if message}
		<div class="notice success">{message}</div>
	{/if}
	{#if error}
		<div class="notice error">{error}</div>
	{/if}

	{#if step === 1}
		<div class="form-grid">
			<label>
				Username
				<input placeholder="username" bind:value={username} />
			</label>
			<label>
				Email
				<input placeholder="email" bind:value={email} />
			</label>
			<label>
				Password
				<input placeholder="password" type="password" bind:value={password} />
			</label>

			<div class="actions flex gap-sm justify-end mt-sm">
				<button class="btn outline" on:click={() => (location.href = '/')} disabled={busy}
					>Cancel</button
				>
				<button class="btn primary" on:click={next} disabled={!canProceed || busy}>Continue</button>
			</div>
		</div>
	{:else}
		<div class="confirm">
			<h4>Confirm details</h4>
			<dl>
				<dt>Username</dt>
				<dd>{username}</dd>
				<dt>Email</dt>
				<dd>{email}</dd>
			</dl>

			<div class="actions flex gap-sm justify-end mt-sm">
				<button class="btn outline" on:click={() => (step = 1)} disabled={busy}>Back</button>
				<button class="btn primary" on:click={submit} disabled={busy}>Create account</button>
			</div>
		</div>
	{/if}
</div>

<style>
	/* Card entry animation */
	.card.setup {
		transform-origin: top center;
		animation: card-in 420ms cubic-bezier(0.2, 0.9, 0.2, 1);
	}
	@keyframes card-in {
		from {
			opacity: 0;
			transform: translateY(-8px) scale(0.995);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}

	.setup {
		max-width: 680px;
		margin: 1rem auto;
		padding: 1.25rem;
	}
	.setup-head {
		margin-bottom: 1rem;
	}
	.muted {
		color: var(--muted);
	}
	.form-grid {
		display: grid;
		gap: 0.75rem;
	}
	label {
		display: block;
		font-size: 0.95rem;
	}

	/* Inputs styled for dark glass panels */
	input {
		width: 100%;
		padding: 0.55rem;
		border-radius: 10px;
		border: 1px solid rgba(255, 255, 255, 0.06);
		background: rgba(255, 255, 255, 0.02);
		color: inherit;
		transition:
			box-shadow 0.18s,
			transform 0.12s;
	}
	input:focus {
		outline: none;
		box-shadow: 0 6px 18px rgba(123, 97, 255, 0.12);
		transform: translateY(-1px);
	}

	.notice {
		padding: 0.5rem 0.75rem;
		border-radius: 8px;
		margin-bottom: 0.75rem;
	}
	.notice.success {
		background: rgba(40, 190, 120, 0.12);
		color: #8ff0b9;
	}
	.notice.error {
		background: rgba(185, 28, 28, 0.12);
		color: #ffb4b4;
	}

	dl {
		margin: 0 0 1rem 0;
	}
	dt {
		color: var(--muted);
		font-size: 0.9rem;
	}
	dd {
		margin: 0 0 0.75rem 0;
		font-weight: 600;
	}

	.btn {
		padding: 0.5rem 0.8rem;
		border-radius: 10px;
		font-weight: 700;
		text-decoration: none;
		transition:
			transform 0.12s,
			box-shadow 0.12s;
	}
	.btn.primary {
		background: linear-gradient(90deg, var(--accent), #a58dff);
		color: white;
		border: none;
		box-shadow: 0 10px 30px rgba(123, 97, 255, 0.12);
	}
	.btn.primary:hover {
		transform: translateY(-3px);
		box-shadow: 0 18px 44px rgba(123, 97, 255, 0.16);
	}
	.btn.outline {
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.06);
	}
</style>
