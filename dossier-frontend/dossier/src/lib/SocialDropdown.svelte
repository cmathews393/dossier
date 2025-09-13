<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import platforms from './platforms.json';
	import platformsMapJson from './platforms_map.json';
	// Make the JSON map indexable by arbitrary string keys
	const platformsMap: Record<string, string | null> = platformsMapJson as Record<
		string,
		string | null
	>;

	// value can be a display name or the slug; component will keep display in input
	export let value: string | null = null;
	export let placeholder = 'platform';

	const dispatch = createEventDispatcher();
	let input = '';
	let open = false;
	let filtered: string[] = [];

	function filter(q: string) {
		const qq = q.trim().toLowerCase();
		if (!qq) return platforms.slice(0, 40);
		return platforms.filter((p) => p.toLowerCase().includes(qq));
	}

	onMount(() => {
		filtered = filter('');
		if (value) input = value;
	});

	function choose(p: string) {
		input = p;
		value = p;
		open = false;
		// map display -> slug where possible
		const slug = platformsMap[p] ?? null;
		dispatch('change', { display: p, slug });
	}

	function onInput(e: Event) {
		input = (e.target as HTMLInputElement).value;
		filtered = filter(input);
		open = true;
		dispatch('input', input);
	}
</script>

<div style="position:relative;min-width:180px">
	<input
		{placeholder}
		bind:value={input}
		on:input={onInput}
		on:focus={() => (open = true)}
		on:keydown={(e) => {
			if ((e as KeyboardEvent).key === 'Enter') {
				e.preventDefault();
				choose(input);
			}
		}}
		on:blur={() => {
			// commit current input on blur so parent always gets a value
			choose(input);
		}}
	/>
	{#if open}
		<div class="dropdown">
			{#if filtered.length === 0}
				<div class="item">No matches — press Enter to use "{input}"</div>
			{:else}
				{#each filtered as p}
					<div class="item" role="button" tabindex="0" on:mousedown={() => choose(p)}>
						{p}
						{#if platformsMap[p] === null}<span style="opacity:.5">(no slug)</span>{/if}
					</div>
				{/each}
			{/if}
		</div>
	{/if}
</div>

<style>
	.dropdown {
		position: absolute;
		z-index: 40;
		left: 0;
		right: 0;
		margin-top: 6px;
		background: var(--panel-strong, rgba(22, 18, 30, 0.9));
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 8px;
		max-height: 220px;
		overflow: auto;
		box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
	}

	.item {
		padding: 0.5rem 0.6rem;
		cursor: pointer;
		color: var(--muted);
	}

	.item:hover {
		background: rgba(255, 255, 255, 0.02);
		color: white;
	}
</style>
