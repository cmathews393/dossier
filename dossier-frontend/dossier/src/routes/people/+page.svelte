<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import PersonCard from '$lib/PersonCard.svelte';
	import SearchBar from '$lib/SearchBar.svelte';
	import LoadingState from '$lib/LoadingState.svelte';

	let q = '';
	let people: any[] = [];
	let loading = false;
	let error: string | null = null;

	async function load() {
		loading = true;
		error = null;
		try {
			people = (await api.get_people(q as any)) || [];
		} catch (err: any) {
			error = err.message || String(err);
		}
		loading = false;
	}

	onMount(load);
</script>

<div class="card">
	<h3>People</h3>
	<div class="flex items-center gap-sm">
		<SearchBar bind:value={q} placeholder="search by name or email" onSearch={load} {loading} />
		<a class="btn outline" href="/add">Add</a>
	</div>

	<LoadingState
		{loading}
		{error}
		empty={people.length === 0 && !loading}
		emptyMessage="No people found."
	/>

	{#if people.length > 0}
		<div class="people-grid grid grid-fill gap-md mt-md">
			{#each people as person}
				<PersonCard {person} />
			{/each}
		</div>
	{/if}
</div>

<style>
	@media (max-width: 768px) {
		.people-grid {
			grid-template-columns: 1fr !important;
		}
	}
</style>
