<script lang="ts">
	interface Props {
		loading?: boolean;
		error?: string | null;
		empty?: boolean;
		emptyMessage?: string;
		loadingMessage?: string;
		class?: string;
	}

	let {
		loading = false,
		error = null,
		empty = false,
		emptyMessage = 'No data found.',
		loadingMessage = 'Loading...',
		class: className = ''
	}: Props = $props();
</script>

{#if loading}
	<div class="state-message muted {className}">{loadingMessage}</div>
{:else if error}
	<div class="state-message error {className}">{error}</div>
{:else if empty}
	<div class="state-message muted {className}">{emptyMessage}</div>
{/if}

<style>
	.state-message {
		margin-top: 1rem;
		padding: 1rem;
		text-align: center;
		border-radius: 8px;
	}

	.error {
		color: #ef4444;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
	}
</style>
