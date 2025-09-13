<script lang="ts">
	import { onMount } from 'svelte';
	// Prefer loading provider templates from the backend proxy endpoint
	onMount(() => {
		if ((window as any).sherlockTemplates) return;
		// call backend endpoint which reads from installed sherlock_project resources
		api
			.get_sherlock_providers()
			.then((j) => {
				(window as any).sherlockTemplates = j;
			})
			.catch((e) => {
				console.warn('Unable to load sherlock templates from backend:', e);
			});
	});
	import { api } from '$lib/api';
	import { page } from '$app/stores';
	import Map from '$lib/Map.svelte';
	import AddressSearch from '$lib/AddressSearch.svelte';
	import SocialDropdown from '$lib/SocialDropdown.svelte';
	let person: any = null;
	let loading = true;
	let error: string | null = null;

	let editing = false;
	let firstName = '';
	let lastName = '';
	let email = '';
	let phoneNumber = '';
	let address: any = null; // Changed to object type

	let id = '';
	// reactively track the current route params via the `$page` store
	// ensure we always have a string for TypeScript
	$: id = $page.params.id || '';

	async function load() {
		loading = true;
		error = null;
		try {
			person = await api.get_person(id);
			firstName = person.first_name || '';
			lastName = person.last_name || '';
			email = person.email || '';
			phoneNumber = person.phone_number || '';
			address = person.address || null; // Handle both string and object types

			// Load recent search jobs
			loadRecentJobs();
		} catch (err: any) {
			error = err.message || String(err);
		}
		loading = false;
	}

	// reactively load when the route `id` becomes available/changes
	$: if (id) {
		load();
	}

	function accountUrl(platform: string, handle: string) {
		// prefer Sherlock templates if we've loaded them
		try {
			if ((window as any).sherlockTemplates) {
				const st: Record<string, any> = (window as any).sherlockTemplates;

				// helper to extract URL template from provider entry
				const getTemplate = (entry: any) => {
					if (!entry) return null;
					if (typeof entry.url === 'string') return entry.url;
					if (typeof entry.urlMain === 'string') return entry.urlMain;
					if (
						Array.isArray(entry.urls) &&
						entry.urls.length &&
						typeof entry.urls[0].url === 'string'
					)
						return entry.urls[0].url;
					if (typeof entry.homepage === 'string') return entry.homepage;
					return null;
				};

				// helper to build URL from template
				const buildUrl = (template: string) => {
					const s = String(template);
					// template with placeholder
					if (s.includes('{}')) return s.replace(/\{\}/g, encodeURIComponent(handle));
					// absolute URL without placeholder -> append handle
					if (/^https?:\/\//i.test(s))
						return `${s.replace(/\/+$/, '')}/${encodeURIComponent(handle)}`;
					// domain-like string -> treat as hostname
					if (s.includes('.'))
						return `https://${s.replace(/\/+$/, '')}/${encodeURIComponent(handle)}`;
					return null;
				};

				// Try multiple lookup strategies for Sherlock providers
				let entry = null;

				// 1. Direct platform name match (case-sensitive)
				entry = st[platform];
				if (entry) {
					const template = getTemplate(entry);
					if (template) {
						const url = buildUrl(template);
						if (url) return url;
					}
				}

				// 2. Case-insensitive platform name match
				if (!entry) {
					const platformLower = platform.toLowerCase();
					entry = Object.entries(st).find(([k]) => k.toLowerCase() === platformLower)?.[1];
					if (entry) {
						const template = getTemplate(entry);
						if (template) {
							const url = buildUrl(template);
							if (url) return url;
						}
					}
				}

				// 3. Try using runtimePlatformsMap to resolve display name -> slug
				const mappedSlug =
					(runtimePlatformsMap as any)[platform] || (platforms_map as any)[platform];
				if (mappedSlug && mappedSlug !== platform) {
					entry = st[mappedSlug];
					if (entry) {
						const template = getTemplate(entry);
						if (template) {
							const url = buildUrl(template);
							if (url) return url;
						}
					}
				}

				// 4. Try reverse lookup: find provider where slug matches our platform
				if (!entry) {
					const found = Object.entries(platforms_map).find(
						([, v]) => String(v).toLowerCase() === platform.toLowerCase()
					);
					if (found && st[found[0]]) {
						entry = st[found[0]];
						const template = getTemplate(entry);
						if (template) {
							const url = buildUrl(template);
							if (url) return url;
						}
					}
				}
			}
		} catch (e) {
			// ignore and fall back
		}
		// Fallback: if no Sherlock template found, use hardcoded mappings and heuristics
		const mapped =
			(runtimePlatformsMap as any)[platform] || (platforms_map as any)[platform] || platform;
		const slug = String(mapped).toLowerCase();

		// known templates for common platforms
		switch (true) {
			case slug === 'github':
				return `https://github.com/${handle}`;
			case slug === 'twitter':
				return `https://twitter.com/${handle}`;
			case slug === 'instagram':
				return `https://instagram.com/${handle}`;
			case slug === 'linkedin':
				return `https://www.linkedin.com/in/${handle}`;
			case slug === 'tiktok':
				return `https://www.tiktok.com/@${handle}`;
			case slug.includes('mastodon'):
				if (handle.includes('@')) return `https://${handle.split('@')[1]}/@${handle.split('@')[0]}`;
				// if slug looks like an instance domain use it
				if (slug.includes('.')) return `https://${slug}/@${handle}`;
				return `https://mastodon.social/@${handle}`;
			case slug === 'reddit':
				return `https://www.reddit.com/user/${handle}`;
			case slug === 'youtube' || slug === 'youtube.com':
				return `https://www.youtube.com/${handle}`;
			case slug === 'facebook':
				return `https://www.facebook.com/${handle}`;
			default:
				// best-effort fallback: try platform.com/handle
				if (/^[a-z0-9-]+$/.test(slug)) return `https://${slug}.com/${handle}`;
				return '#';
		}
	}

	async function confirmSocial(platform: string) {
		const slugify = (s: string) =>
			s
				.trim()
				.toLowerCase()
				.replace(/\s+/g, '_')
				.replace(/[^a-z0-9_-]/g, '');
		const normalizedKey = slugify(platform);
		try {
			await api.update_person(id, { socials_status: { [normalizedKey]: 'confirmed' } });
			load();
		} catch (err: any) {
			error = err.message || String(err);
		}
	}

	async function rejectSocial(platform: string) {
		const slugify = (s: string) =>
			s
				.trim()
				.toLowerCase()
				.replace(/\s+/g, '_')
				.replace(/[^a-z0-9_-]/g, '');
		const normalizedKey = slugify(platform);
		try {
			await api.update_person(id, { socials_status: { [normalizedKey]: 'rejected' } });
			load();
		} catch (err: any) {
			error = err.message || String(err);
		}
	}

	// add / edit socials UI state
	import platforms_map from '$lib/platforms_map.json';
	// runtimePlatformsMap starts with the static platforms_map as a fallback
	let runtimePlatformsMap: Record<string, string | null> = {
		...(platforms_map as Record<string, string | null>)
	};
	let newPlatformDisplay: string = '';
	let newPlatformSlug: string | null = null;
	let newHandle = '';

	// Social search state
	let searchingAccounts = false;
	let searchResults: Array<{ platform: string; url: string; handle: string; displayName: string }> =
		[];
	let searchError: string | null = null;
	let searchJobId: string | null = null;
	let searchJobStatus: string | null = null;
	let searchJobPolling = false;
	let recentJobs: any[] = [];
	let currentSearchUsername = ''; // Store the current search username for result processing

	// Check status of a recent job and load results if completed
	async function checkJobResults(jobId: string) {
		try {
			const jobStatus = await api.get_sherlock_job_status(jobId);
			if (jobStatus.status === 'completed' && jobStatus.results) {
				// Clear any existing search state
				searchError = null;
				searchResults = [];

				// Process the results
				processSearchResults(jobStatus.results);

				// Update the job ID so UI can show it's being processed
				searchJobId = jobId;
				searchJobStatus = `Loaded results from previous search`;
			} else if (jobStatus.status === 'failed') {
				searchError = jobStatus.error || 'Previous search failed';
			} else {
				// Job is still running, start polling
				searchJobId = jobId;
				searchingAccounts = true;
				searchJobStatus = `Resuming search: ${jobStatus.status}`;
				pollSearchResults();
			}
		} catch (err: any) {
			searchError = err.message || 'Failed to check job status';
		}
	}

	// Load recent Sherlock jobs for this person
	async function loadRecentJobs() {
		try {
			const jobs = await api.list_sherlock_jobs(id, undefined, 10);
			recentJobs = jobs || [];
		} catch (err: any) {
			console.warn('Failed to load recent jobs:', err);
		}
	}

	// load lightweight providers list from backend and populate runtimePlatformsMap
	onMount(() => {
		// fetch providers list and merge into runtime map
		api
			.get_sherlock_providers_list()
			.then((list: Array<{ slug: string; name: string }>) => {
				if (!Array.isArray(list)) return;
				for (const p of list) {
					// providers may have same name as slug; use display name -> slug
					runtimePlatformsMap[p.name] = p.slug;
				}
			})
			.catch(() => {
				// ignore; already have static fallback
			});
	});
	// platform is selected via SocialDropdown which provides display + slug

	async function addSocial() {
		const display = (newPlatformDisplay || '').trim();
		const handle = (newHandle || '').trim();
		const slugify = (s: string) =>
			s
				.trim()
				.toLowerCase()
				.replace(/\s+/g, '_')
				.replace(/[^a-z0-9_-]/g, '');
		// Always normalize the key to ensure backend validation passes
		let key = newPlatformSlug || display;
		if (key) key = slugify(key);
		if (!key) {
			error = 'Please choose a platform';
			return;
		}
		if (!handle) {
			error = 'Handle cannot be empty';
			return;
		}
		try {
			await api.update_person(id, { socials: { [key]: handle } });
			newPlatformDisplay = '';
			newPlatformSlug = null;
			newHandle = '';
			load();
		} catch (err: any) {
			error = err.message || String(err);
		}
	}

	// per-platform edit state
	let editingHandle: Record<string, string> = {};
	function startEditHandle(platform: string, current: string) {
		// reassign to trigger Svelte reactivity
		editingHandle = { ...editingHandle, [platform]: current || '' };
	}

	async function saveHandleEdit(platform: string) {
		const handle = (editingHandle[platform] || '').trim();
		if (!handle) {
			error = 'Handle cannot be empty';
			return;
		}

		const slugify = (s: string) =>
			s
				.trim()
				.toLowerCase()
				.replace(/\s+/g, '_')
				.replace(/[^a-z0-9_-]/g, '');

		try {
			// Always normalize platform keys to ensure backend validation passes
			// This migrates any legacy bad keys to proper format
			const currentSocials = person.socials || {};
			const normalizedSocials: Record<string, any> = {};

			// Normalize all existing social keys
			for (const [key, value] of Object.entries(currentSocials)) {
				const normalizedKey = slugify(key);
				normalizedSocials[normalizedKey] = value;
			}

			// Update the specific handle for this platform
			const normalizedPlatform = slugify(platform);
			if (typeof normalizedSocials[normalizedPlatform] === 'object') {
				normalizedSocials[normalizedPlatform] = {
					...normalizedSocials[normalizedPlatform],
					handle: handle
				};
			} else {
				normalizedSocials[normalizedPlatform] = handle;
			}

			// Send the complete normalized socials object
			await api.update_person(id, { socials: normalizedSocials });

			// remove key and reassign to trigger reactivity
			const { [platform]: _removed, ...rest } = editingHandle;
			editingHandle = rest;
			load();
		} catch (err: any) {
			error = err.message || String(err);
		}
	}

	// Social account search using Sherlock (queue-based)
	async function searchSocialAccounts() {
		if (!person) return;

		// Get a username to search with - try existing socials, first name, or prompt user
		let searchUsername = '';

		// Look for existing social handles to use as search terms
		if (person.socials) {
			const handles = Object.values(person.socials)
				.map((v) => (typeof v === 'object' ? (v as any).handle : String(v)))
				.filter(Boolean);
			if (handles.length > 0) {
				searchUsername = handles[0].replace(/^@/, ''); // Remove @ if present
			}
		}

		// If no social handles, try first name
		if (!searchUsername && person.first_name) {
			searchUsername = person.first_name.toLowerCase();
		}

		// Still no username? Ask user
		if (!searchUsername) {
			searchUsername = prompt('Enter a username to search for social accounts:') || '';
		}

		if (!searchUsername.trim()) return;

		console.log('🔍 Starting Sherlock search for username:', searchUsername.trim());
		console.log('👤 Person ID:', id);

		searchingAccounts = true;
		searchError = null;
		searchResults = [];
		searchJobId = null;
		searchJobStatus = 'Queuing search...';

		try {
			// Queue the Sherlock search
			console.log('📤 Queuing Sherlock search...');
			const queueResponse = await api.queue_sherlock_search(searchUsername.trim(), id);
			console.log('✅ Search queued successfully:', queueResponse);

			searchJobId = queueResponse.job_id;
			searchJobStatus = 'Search queued successfully';

			// Start polling for results
			pollSearchResults();
		} catch (err: any) {
			console.error('❌ Failed to queue search:', err);
			searchError = err.message || 'Failed to queue search';
			searchingAccounts = false;
		}
	}

	// Poll for search results
	async function pollSearchResults() {
		if (!searchJobId) return;

		searchJobPolling = true;
		const maxAttempts = 60; // Poll for up to 60 attempts (5 minutes at 5s intervals)
		let attempts = 0;

		const poll = async () => {
			try {
				const jobStatus = await api.get_sherlock_job_status(searchJobId!);
				searchJobStatus = `Status: ${jobStatus.status}`;

				if (jobStatus.status === 'completed') {
					// Process the results
					processSearchResults(jobStatus.results);
					searchingAccounts = false;
					searchJobPolling = false;
					// Refresh recent jobs list
					loadRecentJobs();
					return;
				} else if (jobStatus.status === 'failed') {
					searchError = jobStatus.error || 'Search failed';
					searchingAccounts = false;
					searchJobPolling = false;
					// Refresh recent jobs list
					loadRecentJobs();
					return;
				} else if (jobStatus.status === 'running') {
					searchJobStatus = 'Search in progress...';
				}

				// Continue polling if still pending or running
				attempts++;
				if (
					attempts < maxAttempts &&
					(jobStatus.status === 'pending' || jobStatus.status === 'running')
				) {
					setTimeout(poll, 5000); // Poll every 5 seconds
				} else if (attempts >= maxAttempts) {
					searchError = 'Search timed out - check results later';
					searchingAccounts = false;
					searchJobPolling = false;
				}
			} catch (err: any) {
				searchError = err.message || 'Failed to check search status';
				searchingAccounts = false;
				searchJobPolling = false;
			}
		};

		poll();
	}

	// Process search results from the queue job
	function processSearchResults(results: any) {
		if (!results || !person) return;

		const foundAccounts = [];

		// Get existing social platform slugs (normalized)
		const slugify = (s: string) =>
			s
				.trim()
				.toLowerCase()
				.replace(/\s+/g, '_')
				.replace(/[^a-z0-9_-]/g, '');

		const existingSocials = new Set();
		if (person.socials) {
			for (const key of Object.keys(person.socials)) {
				existingSocials.add(slugify(key));
			}
		}

		// Debug logging
		console.log('Existing socials (slugified):', Array.from(existingSocials));
		console.log('Sherlock results:', Object.keys(results));

		// Parse sherlock results to find confirmed accounts
		for (const [siteName, result] of Object.entries(results)) {
			if (result && typeof result === 'object') {
				const res = result as any;
				// Sherlock returns status 'Claimed' for found accounts
				if (res.status === 'Claimed' && res.url_user) {
					const platformSlug = slugify(siteName);

					console.log(
						`Checking ${siteName} -> ${platformSlug}, already exists: ${existingSocials.has(platformSlug)}`
					);

					// Skip if this platform already exists for the person
					if (existingSocials.has(platformSlug)) {
						continue;
					}

					foundAccounts.push({
						platform: platformSlug,
						url: res.url_user,
						handle: res.username || searchUsername, // Use actual found username or fallback
						displayName: siteName // Keep original site name for display
					});
				}
			}
		}

		searchResults = foundAccounts;

		if (foundAccounts.length === 0) {
			const totalClaimed = Object.values(results).filter(
				(r) => r && typeof r === 'object' && (r as any).status === 'Claimed'
			).length;
			const skippedCount = totalClaimed - foundAccounts.length;
			if (skippedCount > 0) {
				searchError = `No new social accounts found (${skippedCount} platforms already added)`;
			} else {
				searchError = `No social accounts found`;
			}
		} else {
			searchJobStatus = `Found ${foundAccounts.length} new social accounts`;
		}
	}

	// Add found social accounts to the person
	async function addFoundAccount(platform: string, handle: string) {
		try {
			await api.update_person(id, { socials: { [platform]: handle } });
			// Remove from search results
			searchResults = searchResults.filter((r) => r.platform !== platform);
			load(); // Refresh person data
		} catch (err: any) {
			error = err.message || String(err);
		}
	}
</script>

<div class="card">
	{#if loading}
		<div style="color:var(--muted)">Loading…</div>
	{:else if error}
		<div style="color:#b91c1c">{error}</div>
	{:else}
		<div style="display:flex;align-items:center;justify-content:space-between">
			<h3>{person.first_name} {person.last_name}</h3>
			<div>
				{#if editing}
					<button
						class="btn"
						on:click={async () => {
							try {
								await api.update_person(id, {
									first_name: firstName,
									last_name: lastName,
									email: email || null,
									phone_number: phoneNumber || null,
									address: address
								});
								editing = false;
								load();
							} catch (err: any) {
								error = err.message || String(err);
							}
						}}>Save</button
					>
					<button
						class="btn outline"
						on:click={() => {
							editing = false;
							firstName = person.first_name || '';
							lastName = person.last_name || '';
							email = person.email || '';
							phoneNumber = person.phone_number || '';
							address = person.address || null;
							// also cancel any in-progress social edits
							editingHandle = {};
						}}>Cancel</button
					>
				{:else}
					<button class="btn" on:click={() => (editing = true)}>Edit</button>
				{/if}
			</div>
		</div>
		{#if editing}
			<div class="flex gap-sm mt-sm">
				<input bind:value={firstName} placeholder="First name" />
				<input bind:value={lastName} placeholder="Last name" />
			</div>
			<div class="flex gap-sm mt-sm">
				<input bind:value={email} placeholder="Email" type="email" />
				<input bind:value={phoneNumber} placeholder="Phone number" type="tel" />
			</div>
			<div class="mt-sm">
				<label class="address-label">Address:</label>
				<AddressSearch bind:value={address} placeholder="Search for an address..." />

				<!-- Show map preview while editing if address is selected -->
				{#if address && address.latitude && address.longitude}
					<div class="map-preview-edit">
						<div class="map-preview-label muted">Preview:</div>
						<div class="map-container">
							<Map
								latitude={address.latitude}
								longitude={address.longitude}
								address={address.display_name || ''}
								height="200px"
							/>
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<div class="person-detail muted mt-sm">Email: {person.email || 'Not set'}</div>
			<div class="person-detail muted mt-sm">
				Phone: {person.phone_number || 'Not set'}
			</div>
			<div class="person-detail muted mt-md">
				Address: {person.address
					? typeof person.address === 'string'
						? person.address
						: person.address.display_name || 'Set'
					: 'Not set'}
			</div>

			<!-- Debug: Show address structure -->
			{#if person.address}
				<details style="margin-bottom:1rem;font-size:0.875rem;">
					<summary style="cursor:pointer;color:var(--muted);">Debug: Address Data</summary>
					<pre
						style="background:var(--bg);color:var(--fg);border:1px solid var(--muted);padding:0.5rem;border-radius:4px;overflow:auto;white-space:pre-wrap;">{JSON.stringify(
							person.address,
							null,
							2
						)}</pre>
				</details>
			{/if}

			<!-- Display map if address is available -->
			{#if person.address}
				<div class="location-section">
					<h4 class="section-header">Location</h4>
					<div class="map-container">
						{#if typeof person.address === 'string'}
							<Map address={person.address} height="300px" />
						{:else if person.address && typeof person.address === 'object'}
							<!-- Debug: let's see what we actually have -->
							<!-- Address object: {JSON.stringify(person.address)} -->
							{#if person.address.latitude && person.address.longitude}
								<Map
									latitude={person.address.latitude}
									longitude={person.address.longitude}
									address={person.address.display_name || ''}
									height="300px"
								/>
							{:else}
								<!-- Fallback: try to geocode the display_name if we have it -->
								{#if person.address.display_name}
									<Map address={person.address.display_name} height="300px" />
								{:else}
									<div class="empty-state">Address data available but coordinates missing</div>
								{/if}
							{/if}
						{/if}
					</div>
				</div>
			{/if}
		{/if}
		{#if person.socials}
			<h4>Socials</h4>
			<ul class="socials-list">
				{#each Object.entries(person.socials) as [k, v]}
					<li class="social-item flex items-center gap-sm">
						<strong>{k}</strong>:
						{#if typeof v === 'object' && v !== null}
							{#if editingHandle[k] !== undefined}
								<input bind:value={editingHandle[k]} placeholder="handle" />
							{:else if (v as any).handle}
								<a href={accountUrl(k, (v as any).handle)} target="_blank" rel="noreferrer"
									>{(v as any).handle}</a
								>
							{:else}
								<span class="muted">no handle</span>
							{/if}
							<span class="muted"> {(v as any).status}</span>
							{#if (v as any).root}
								<span class="root-badge">root</span>
							{/if}
						{:else}
							<a href={accountUrl(k, String(v))} target="_blank" rel="noreferrer">{String(v)}</a>
							<span class="muted"> unknown</span>
						{/if}
						<div class="social-actions">
							{#if editingHandle[k] !== undefined}
								<button class="btn" on:click={() => saveHandleEdit(k)}>Save</button>
								<button
									class="btn outline"
									on:click={() => {
										const { [k]: _removed, ...rest } = editingHandle;
										editingHandle = rest;
									}}>Cancel</button
								>
							{:else}
								<button class="btn" on:click={() => confirmSocial(k)}>Confirm</button>
								<button
									class="btn outline"
									on:click={() => rejectSocial(k)}
									disabled={typeof v === 'object' ? v && (v as any).root : false}
									title={typeof v === 'object' && v && (v as any).root
										? 'Cannot reject root profile'
										: ''}>Reject</button
								>
								<button
									class="btn"
									on:click={() =>
										startEditHandle(k, typeof v === 'object' ? (v as any).handle : String(v))}
									>Edit</button
								>
							{/if}
						</div>
					</li>
				{/each}
			</ul>

			<!-- add new social -->
			<div class="add-social-section flex gap-sm items-center mt-sm">
				<SocialDropdown
					value={newPlatformDisplay}
					on:change={(ev) => {
						const detail = ev.detail as { display: string; slug: string | null };
						newPlatformDisplay = detail.display;
						newPlatformSlug = detail.slug;
					}}
				/>
				<input placeholder="handle" bind:value={newHandle} />
				<button class="btn" on:click={addSocial}>Add</button>
			</div>

			<!-- search for social accounts -->
			<div class="social-search-section">
				<div class="flex gap-sm items-center mt-sm">
					<button
						class="btn outline"
						on:click={searchSocialAccounts}
						disabled={searchingAccounts || searchJobPolling}
					>
						{searchingAccounts ? 'Searching...' : 'Search for Social Accounts'}
					</button>
					{#if searchingAccounts || searchJobPolling}
						<span class="muted search-status">
							{searchJobStatus || 'Searching...'}
						</span>
					{/if}
				</div>

				{#if searchJobId && !searchError}
					<div class="job-info muted">
						Job ID: {searchJobId}
						{#if searchJobPolling}
							<span class="polling-indicator">⏳ Checking for results...</span>
						{/if}
					</div>
				{/if}

				{#if searchError}
					<div class="error-message">{searchError}</div>
				{/if}

				{#if searchResults.length > 0}
					<div class="search-results">
						<div class="results-header">
							Found {searchResults.length} account{searchResults.length === 1 ? '' : 's'}:
						</div>
						{#each searchResults as result}
							<div class="result-item">
								<div class="result-info">
									<strong>{result.displayName}</strong>:
									<a href={result.url} target="_blank" rel="noreferrer" class="result-link"
										>{result.handle}</a
									>
								</div>
								<button
									class="btn result-add-btn"
									on:click={() => addFoundAccount(result.platform, result.handle)}
								>
									Add
								</button>
							</div>
						{/each}
					</div>
				{/if}

				<!-- Recent search jobs -->
				{#if recentJobs.length > 0}
					<div class="recent-jobs">
						<div class="recent-jobs-header">Recent Searches:</div>
						{#each recentJobs.slice(0, 5) as job}
							<div class="job-item">
								<div class="job-info-compact">
									<span class="job-username">{job.username}</span>
									<span class="job-status status-{job.status}">{job.status}</span>
									<span class="job-date muted">{new Date(job.created_at).toLocaleString()}</span>
								</div>
								{#if job.status === 'completed'}
									<button class="btn job-load-btn" on:click={() => checkJobResults(job.job_id)}>
										Load Results
									</button>
								{:else if job.status === 'running' || job.status === 'pending'}
									<button class="btn job-load-btn" on:click={() => checkJobResults(job.job_id)}>
										Check Status
									</button>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
		{#if person.notes}
			<h4>Notes</h4>
			<div>{person.notes}</div>
		{/if}
	{/if}
</div>

<style>
	.address-label {
		display: block;
		margin-bottom: 0.25rem;
		font-weight: bold;
	}

	.map-preview-edit {
		margin-top: 0.75rem;
	}

	.map-preview-label {
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
	}

	.map-container {
		border: 1px solid var(--muted);
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
		background: var(--bg);
	}

	.person-detail {
		margin-bottom: 0.5rem;
	}

	.location-section {
		margin-bottom: 1.5rem;
	}

	.section-header {
		margin-bottom: 0.75rem;
		color: var(--fg);
		border-bottom: 1px solid var(--muted);
		padding-bottom: 0.25rem;
	}

	.empty-state {
		padding: 1rem;
		text-align: center;
		color: var(--muted);
	}

	.socials-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.social-item {
		margin-bottom: 0.75rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.02);
		border-radius: 8px;
	}

	.social-actions {
		display: flex;
		gap: 0.25rem;
		margin-left: auto;
	}

	.root-badge {
		background: var(--muted);
		color: var(--bg);
		padding: 0.1rem 0.4rem;
		border-radius: 4px;
		margin-left: 0.25rem;
		font-size: 0.75rem;
	}

	.social-actions .btn {
		padding: 0.25rem 0.5rem;
		font-size: 0.875rem;
	}

	.social-search-section {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid var(--muted);
	}

	.search-status {
		font-size: 0.875rem;
	}

	.job-info {
		font-size: 0.875rem;
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: rgba(255, 255, 255, 0.02);
		border-radius: 6px;
	}

	.polling-indicator {
		margin-left: 0.5rem;
		opacity: 0.7;
	}

	.error-message {
		color: #ef4444;
		font-size: 0.875rem;
		margin: 0.5rem 0;
		padding: 0.5rem;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 6px;
	}

	.search-results {
		background: var(--bg);
		border: 1px solid var(--muted);
		border-radius: 6px;
		padding: 0.75rem;
		margin: 0.5rem 0;
	}

	.results-header {
		font-weight: bold;
		margin-bottom: 0.5rem;
		color: var(--fg);
	}

	.result-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.375rem 0;
		border-bottom: 1px solid var(--muted);
	}

	.result-item:last-child {
		border-bottom: none;
	}

	.result-link {
		color: var(--accent);
	}

	.result-add-btn {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
	}

	.recent-jobs {
		margin-top: 1rem;
		padding: 0.75rem;
		background: rgba(255, 255, 255, 0.02);
		border-radius: 6px;
		border: 1px solid rgba(255, 255, 255, 0.05);
	}

	.recent-jobs-header {
		font-weight: 600;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
	}

	.job-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid rgba(255, 255, 255, 0.05);
	}

	.job-item:last-child {
		border-bottom: none;
	}

	.job-info-compact {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.job-username {
		font-weight: 600;
		font-size: 0.875rem;
	}

	.job-status {
		font-size: 0.75rem;
		padding: 0.2rem 0.4rem;
		border-radius: 4px;
		text-transform: uppercase;
		font-weight: 600;
	}

	.status-completed {
		background: rgba(34, 197, 94, 0.2);
		color: #22c55e;
	}

	.status-running {
		background: rgba(59, 130, 246, 0.2);
		color: #3b82f6;
	}

	.status-pending {
		background: rgba(245, 158, 11, 0.2);
		color: #f59e0b;
	}

	.status-failed {
		background: rgba(239, 68, 68, 0.2);
		color: #ef4444;
	}

	.job-date {
		font-size: 0.75rem;
	}

	.job-load-btn {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
	}
</style>
