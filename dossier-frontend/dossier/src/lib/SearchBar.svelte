<script lang="ts">
	interface Props {
		value: string;
		placeholder?: string;
		onSearch?: (query: string) => void;
		onInput?: (query: string) => void;
		loading?: boolean;
		class?: string;
	}

	let {
		value = $bindable(),
		placeholder = 'Search...',
		onSearch,
		onInput,
		loading = false,
		class: className = ''
	}: Props = $props();

	function handleInput() {
		onInput?.(value);
	}

	function handleSearch() {
		onSearch?.(value);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSearch();
		}
	}
</script>

<div class="search-bar {className}">
	<input
		bind:value
		{placeholder}
		oninput={handleInput}
		onkeydown={handleKeydown}
		disabled={loading}
	/>
	{#if onSearch}
		<button class="btn" onclick={handleSearch} disabled={loading}>
			{loading ? 'Searching...' : 'Search'}
		</button>
	{/if}
</div>

<style>
	.search-bar {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.search-bar input {
		flex: 1;
		min-width: 0;
	}
</style>
