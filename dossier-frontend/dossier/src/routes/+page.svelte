<script lang="ts">
	import { currentUser, setupRequired } from '$lib/stores';
	import { derived } from 'svelte/store';

	let user: any = null;
	let requiresSetup = false;

	currentUser.subscribe((v) => (user = v));
	setupRequired.subscribe((v) => (requiresSetup = v));
</script>

<main class="hero">
	<div class="hero-inner card">
		<div class="hero-content">
			<h1>Dossier</h1>
			<p class="tagline">
				Collect, centralize, and securely manage people records with confidence.
			</p>

			<div class="ctas">
				<a class="btn primary" href="/people">Explore People</a>
				<a class="btn outline" href="/add">Add a Person</a>
			</div>

			<p class="links">
				{#if !user}
					<a class="btn outline" href="/login">Sign in</a>
				{/if}

				{#if !user && requiresSetup}
					<span class="dot">•</span>
					<a class="btn primary" href="/setup">Initial setup</a>
				{/if}
			</p>
		</div>

		<div class="hero-visual" aria-hidden>
			<div class="card preview">
				<div class="person-row">
					<div class="avatar" />
					<div class="meta">
						<div class="name">Jane Doe</div>
						<div class="muted">jane@example.com</div>
					</div>
				</div>
				<div class="preview-grid">
					<div class="pill">Phone</div>
					<div class="pill">Address</div>
					<div class="pill">Aliases</div>
					<div class="pill">Notes</div>
				</div>
			</div>
		</div>
	</div>
</main>

<style>
	.hero {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 4rem 1rem;
	}
	.hero-inner {
		display: flex;
		gap: 2.5rem;
		align-items: center;
		max-width: 1100px;
		width: 100%;
		padding: 2rem;
	}
	.hero-content {
		flex: 1;
	}
	h1 {
		margin: 0 0 0.5rem 0;
		font-size: 2.5rem;
		letter-spacing: -0.02em;
	}
	.tagline {
		color: var(--muted);
		margin: 0 0 1.25rem 0;
		font-size: 1.05rem;
	}

	.ctas {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	.btn {
		display: inline-block;
		padding: 0.6rem 1rem;
		border-radius: 10px;
		text-decoration: none;
		font-weight: 600;
	}
	.btn.primary {
		background: var(--accent);
		color: white;
	}
	.btn.outline {
		background: transparent;
		border: 1px solid rgba(0, 0, 0, 0.08);
		color: inherit;
	}

	.links {
		color: var(--muted);
		font-size: 0.95rem;
	}
	.dot {
		margin: 0 0.6rem;
	}

	.hero-visual {
		width: 360px;
		flex: 0 0 360px;
	}
	.preview {
		padding: 1rem;
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.6), rgba(250, 250, 250, 0.6));
	}
	.person-row {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	.meta .name {
		font-weight: 600;
	}
	.preview-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.5rem;
	}
	.preview-grid .pill {
		text-align: center;
		font-size: 0.9rem;
	}

	@media (max-width: 900px) {
		.hero-inner {
			flex-direction: column-reverse;
			align-items: stretch;
		}
		.hero-visual {
			width: 100%;
		}
	}
</style>
