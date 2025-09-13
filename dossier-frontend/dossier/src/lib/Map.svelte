<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Map, Marker } from 'leaflet';

	export let address: string = '';
	export let height: string = '300px';
	export let width: string = '100%';
	// Optional direct coordinates support
	export let latitude: number | undefined = undefined;
	export let longitude: number | undefined = undefined;

	let mapContainer: HTMLDivElement;
	let map: Map | null = null;
	let marker: Marker | null = null;
	let loading = false;
	let error: string | null = null;
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	// Nominatim API for geocoding (free OpenStreetMap service)
	async function geocodeAddress(addr: string): Promise<{ lat: number; lng: number } | null> {
		try {
			const response = await fetch(
				`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(addr)}&limit=1`
			);
			const data = await response.json();

			if (data && data.length > 0) {
				return {
					lat: parseFloat(data[0].lat),
					lng: parseFloat(data[0].lon)
				};
			}
			return null;
		} catch (err) {
			console.error('Geocoding error:', err);
			return null;
		}
	}

	async function initializeMap() {
		if (!mapContainer) return;

		// Dynamically import Leaflet to avoid SSR issues
		const L = await import('leaflet');

		// Initialize map centered on a default location
		map = L.map(mapContainer, {
			scrollWheelZoom: false,
			doubleClickZoom: false,
			zoomControl: true
		}).setView([40.7128, -74.006], 10); // Default to NYC

		// Add OpenStreetMap tile layer
		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution:
				'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
			maxZoom: 19
		}).addTo(map);

		// If coordinates are provided, use them first; otherwise geocode the address
		if (typeof latitude === 'number' && typeof longitude === 'number') {
			const L = await import('leaflet');
			map.setView([latitude, longitude], 15);
			marker = L.marker([latitude, longitude]).addTo(map);
			if (address) marker.bindPopup(address).openPopup();
		} else if (address.trim()) {
			loading = true;
			error = null;

			const coords = await geocodeAddress(address.trim());

			if (coords) {
				// Center map on the geocoded location
				map.setView([coords.lat, coords.lng], 15);

				// Add marker
				marker = L.marker([coords.lat, coords.lng]).addTo(map).bindPopup(address).openPopup();
			} else {
				error = 'Unable to find location for this address';
			}

			loading = false;
		}
	}

	onMount(() => {
		initializeMap();
	});

	onDestroy(() => {
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}
		if (map) {
			map.remove();
			map = null;
		}
	});

	// Reactive statement to update map when address or coords change
	$: if (map) {
		updateLocationDebounced();
	}

	function updateLocationDebounced() {
		// Clear existing timer
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}

		// Set new timer to delay updates
		debounceTimer = setTimeout(() => {
			updateLocation();
		}, 1000); // Wait 1 second after user stops typing
	}

	async function updateLocation() {
		if (!map) return;

		loading = true;
		error = null;

		// Remove existing marker
		if (marker) {
			marker.remove();
			marker = null;
		}

		const L = await import('leaflet');
		if (typeof latitude === 'number' && typeof longitude === 'number') {
			map.setView([latitude, longitude], 15);
			marker = L.marker([latitude, longitude]).addTo(map);
			if (address) marker.bindPopup(address).openPopup();
		} else if (address.trim()) {
			const coords = await geocodeAddress(address.trim());
			if (coords) {
				map.setView([coords.lat, coords.lng], 15);
				marker = L.marker([coords.lat, coords.lng]).addTo(map).bindPopup(address).openPopup();
			} else {
				error = 'Unable to find location for this address';
			}
		} else {
			loading = false;
			return;
		}

		loading = false;
	}
</script>

<svelte:head>
	<link
		rel="stylesheet"
		href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
		crossorigin=""
	/>
</svelte:head>

{#if true}
	<div class="map-wrapper" style="height: {height}; width: {width};">
		{#if loading}
			<div class="map-status">Loading map...</div>
		{/if}
		{#if error}
			<div class="map-status error">{error}</div>
		{/if}
		<div bind:this={mapContainer} class="map-container" style="height: 100%; width: 100%;"></div>
	</div>
{/if}

<style>
	.map-wrapper {
		position: relative;
		border: 1px solid var(--muted);
		border-radius: 8px;
		overflow: hidden;
		background: var(--bg);
	}

	.map-container {
		z-index: 1;
	}

	.map-status {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		background: rgba(0, 0, 0, 0.7);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		z-index: 10;
		font-size: 0.9rem;
	}

	.map-status.error {
		background: rgba(185, 28, 28, 0.8);
	}

	/* Override Leaflet popup styles to match theme */
	:global(.leaflet-popup-content-wrapper) {
		background: var(--bg) !important;
		color: var(--fg) !important;
		border: 1px solid var(--muted) !important;
	}

	:global(.leaflet-popup-tip) {
		background: var(--bg) !important;
		border: 1px solid var(--muted) !important;
	}
</style>
