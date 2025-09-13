<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { api } from './api.js';

	const dispatch = createEventDispatcher();

	export let value: any = null; // Current address object
	export let placeholder = 'Enter address...';
	export let countryCode = ''; // Optional country restriction

	let searchInput = '';
	let searchResults: any[] = [];
	let showDropdown = false;
	let loading = false;
	let debounceTimer: ReturnType<typeof setTimeout>;

	// Initialize search input with current value
	$: if (value && value.display_name && !searchInput) {
		searchInput = value.display_name;
	}

	async function performSearch(query: string) {
		if (!query || query.length < 3) {
			searchResults = [];
			showDropdown = false;
			return;
		}

		loading = true;
		try {
			const response = await api.search_addresses(query, 5, countryCode);
			searchResults = response || [];
			showDropdown = searchResults.length > 0;
		} catch (error) {
			console.error('Address search error:', error);
			searchResults = [];
			showDropdown = false;
		} finally {
			loading = false;
		}
	}

	function handleInput(event: Event) {
		const target = event.target as HTMLInputElement;
		searchInput = target.value;

		// Clear previous timer
		if (debounceTimer) clearTimeout(debounceTimer);

		// Debounce search
		debounceTimer = setTimeout(() => {
			performSearch(searchInput);
		}, 300);
	}

	function selectAddress(address: any) {
		value = {
			display_name: address.display_name,
			latitude: parseFloat(address.lat),
			longitude: parseFloat(address.lon),
			place_id: address.place_id,
			type: address.type,
			address_components: address.address || {}
		};

		searchInput = address.display_name;
		showDropdown = false;
		searchResults = [];

		dispatch('select', value);
	}

	function clearAddress() {
		value = null;
		searchInput = '';
		showDropdown = false;
		searchResults = [];
		dispatch('select', null);
	}

	function handleFocus() {
		if (searchResults.length > 0) {
			showDropdown = true;
		}
	}

	function handleBlur() {
		// Delay hiding dropdown to allow clicks
		setTimeout(() => {
			showDropdown = false;
		}, 200);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			showDropdown = false;
		}
	}
</script>

<div class="address-search">
	<div class="input-container">
		<input
			type="text"
			bind:value={searchInput}
			on:input={handleInput}
			on:focus={handleFocus}
			on:blur={handleBlur}
			on:keydown={handleKeydown}
			{placeholder}
			class="address-input"
			autocomplete="off"
		/>

		{#if loading}
			<div class="loading-indicator">
				<span>⟳</span>
			</div>
		{/if}

		{#if value}
			<button type="button" class="clear-button" on:click={clearAddress} title="Clear address">
				×
			</button>
		{/if}
	</div>

	{#if showDropdown && searchResults.length > 0}
		<div class="dropdown">
			{#each searchResults as result}
				<button type="button" class="dropdown-item" on:click={() => selectAddress(result)}>
					<div class="address-line">
						{result.display_name}
					</div>
					<div class="address-details">
						{result.type} • {result.lat}, {result.lon}
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.address-search {
		position: relative;
		width: 100%;
	}

	.input-container {
		position: relative;
		display: flex;
		align-items: center;
	}

	.address-input {
		width: 100%;
		padding: 8px 40px 8px 12px;
		border: 1px solid var(--muted);
		border-radius: 4px;
		font-size: 14px;
		background: var(--bg);
		color: var(--fg);
		caret-color: var(--fg);
	}

	.address-input:focus {
		outline: none;
		border-color: #007acc;
		box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.25);
	}

	.address-input::placeholder {
		color: var(--muted);
	}

	.loading-indicator {
		position: absolute;
		right: 30px;
		animation: spin 1s linear infinite;
		color: var(--muted);
	}

	.clear-button {
		position: absolute;
		right: 8px;
		background: none;
		border: none;
		font-size: 18px;
		color: var(--muted);
		cursor: pointer;
		padding: 0;
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.clear-button:hover {
		color: var(--fg);
	}

	.dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		background: var(--bg);
		border: 1px solid var(--muted);
		border-top: none;
		border-radius: 0 0 4px 4px;
		max-height: 200px;
		overflow-y: auto;
		z-index: 1000;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
	}

	.dropdown-item {
		width: 100%;
		padding: 12px;
		border: none;
		background: var(--bg);
		text-align: left;
		cursor: pointer;
		border-bottom: 1px solid var(--muted);
		display: block;
		color: var(--fg);
	}

	.dropdown-item:hover {
		background: rgba(255, 255, 255, 0.06);
	}

	.dropdown-item:last-child {
		border-bottom: none;
	}

	.address-line {
		font-size: 14px;
		color: var(--fg);
		margin-bottom: 4px;
	}

	.address-details {
		font-size: 12px;
		color: var(--muted);
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>
