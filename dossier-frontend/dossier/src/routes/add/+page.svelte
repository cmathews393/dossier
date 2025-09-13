<script lang="ts">
	import { api } from '$lib/api';
	import SocialDropdown from '$lib/SocialDropdown.svelte';
	import Map from '$lib/Map.svelte';
	import AddressSearch from '$lib/AddressSearch.svelte';
	let first_name = '';
	let last_name = '';
	let email = '';
	let phone_number = '';
	let address: any = null; // structured address object from AddressSearch
	let socials: { display: string; slug: string | null; handle: string }[] = [];
	let alt_phones = '';
	let alt_emails = '';
	let aliases = '';
	let notes = '';
	let message: string | null = null;
	let error: string | null = null;

	async function submit() {
		message = error = null;
		try {
			// build payload with flexible fields
			const slugify = (s: string) =>
				s
					.trim()
					.toLowerCase()
					.replace(/\s+/g, '_')
					.replace(/[^a-z0-9_-]/g, '');
			const socialsObj: Record<string, string> | null = socials.length
				? socials.reduce(
						(acc, s) => {
							// Always normalize to ensure backend validation passes
							let key = s.slug || s.display || '';
							if (key) key = slugify(key);
							if (key && s.handle) acc[key] = s.handle.trim();
							return acc;
						},
						{} as Record<string, string>
					)
				: null;

			const payload = {
				first_name,
				last_name,
				// send email only when non-empty to avoid EmailStr validation errors
				email: email && email.trim() ? email.trim() : undefined,
				phone_number: phone_number && phone_number.trim() ? phone_number.trim() : undefined,
				address: address || undefined,
				socials: socialsObj,
				alternate_phones: alt_phones
					? alt_phones
							.split(',')
							.map((s) => s.trim())
							.filter(Boolean)
					: undefined,
				alternate_emails: alt_emails
					? alt_emails
							.split(',')
							.map((s) => s.trim())
							.filter(Boolean)
					: undefined,
				aliases: aliases
					? aliases
							.split(',')
							.map((s) => s.trim())
							.filter(Boolean)
					: undefined,
				notes: notes || undefined
			};

			await api.create_person(payload);
			message = 'Person added. Validating socials in background…';
			first_name = last_name = email = phone_number = '';
			address = null;
			socials = [];
			alt_phones = alt_emails = aliases = notes = '';
		} catch (err: any) {
			error = err.message || String(err);
		}
	}
</script>

<div class="card">
	<h3>Add person</h3>
	{#if message}<div class="success-message">{message}</div>{/if}
	{#if error}<div class="error-message">{error}</div>{/if}
	<div class="form-grid">
		<div class="flex gap-sm">
			<input placeholder="First name" bind:value={first_name} />
			<input placeholder="Last name" bind:value={last_name} />
		</div>
		<input placeholder="Email" bind:value={email} />
		<input placeholder="Phone number" bind:value={phone_number} />
		<label class="muted">Address</label>
		<AddressSearch bind:value={address} placeholder="Search for an address…" />

		<!-- Show map preview if address is entered -->
		{#if address}
			<div class="mt-sm">
				<label class="muted" style="display:block;margin-bottom:0.25rem;">Location Preview:</label>
				{#if typeof address === 'string'}
					<Map {address} height="200px" />
				{:else if address.latitude && address.longitude}
					<Map
						latitude={address.latitude}
						longitude={address.longitude}
						address={address.display_name || ''}
						height="200px"
					/>
				{:else if address.display_name}
					<Map address={address.display_name} height="200px" />
				{/if}
			</div>
		{/if}

		<div>
			<label class="muted">Socials (platform and handle)</label>
			{#each socials as s, i}
				<div class="social-row flex gap-sm items-center mt-sm">
					<SocialDropdown
						value={s.display}
						on:change={(ev) => {
							const detail = ev.detail as { display: string; slug: string | null };
							socials[i].display = detail.display;
							socials[i].slug = detail.slug;
						}}
					/>
					<input
						placeholder="handle (e.g. @jane)"
						value={s.handle}
						on:input={(e) => (socials[i].handle = (e.target as HTMLInputElement).value)}
					/>
					<button
						class="btn outline"
						on:click={() => (socials = socials.filter((_, idx) => idx !== i))}>Remove</button
					>
				</div>
			{/each}
			<div class="mt-sm">
				<button
					class="btn"
					on:click={() => {
						// prevent adding a new social row if the last one has an empty handle
						const last = socials[socials.length - 1];
						if (last && (!last.handle || !last.handle.trim())) {
							error = 'Please fill the handle for the previous social before adding another.';
							return;
						}
						socials = [...socials, { display: '', slug: null, handle: '' }];
					}}
				>
					Add social
				</button>
			</div>
		</div>

		<input placeholder="Other phone numbers (comma separated)" bind:value={alt_phones} />
		<input placeholder="Other emails (comma separated)" bind:value={alt_emails} />
		<input placeholder="Aliases (comma separated)" bind:value={aliases} />
		<textarea placeholder="Notes" bind:value={notes} rows={4} />
		<button class="btn" on:click={submit}>Add person</button>
	</div>
</div>

<style>
	.form-grid {
		display: grid;
		gap: 0.5rem;
		max-width: 560px;
	}

	.success-message {
		color: #10b981;
		background: rgba(16, 185, 129, 0.1);
		border: 1px solid rgba(16, 185, 129, 0.2);
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}

	.error-message {
		color: #ef4444;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		padding: 0.75rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}

	.social-row input {
		flex: 1;
	}
</style>
