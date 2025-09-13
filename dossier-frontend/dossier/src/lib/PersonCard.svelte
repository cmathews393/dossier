<script lang="ts">
	interface PersonData {
		id: string | number;
		first_name?: string;
		last_name?: string;
		email?: string;
		phone_number?: string;
		address?: any;
		socials?: Record<string, any>;
		notes?: string;
	}

	interface Props {
		person: PersonData;
		showLink?: boolean;
		class?: string;
	}

	let { person, showLink = true, class: className = '' }: Props = $props();

	function previewHandles(socials: any): string {
		if (!socials) return '';
		return Object.values(socials)
			.slice(0, 3)
			.map((v: any) => (typeof v === 'object' && v !== null ? v.handle || '' : String(v)))
			.filter(Boolean)
			.join(', ');
	}

	function getDisplayName(person: PersonData): string {
		if (person.first_name || person.last_name) {
			return `${person.first_name || ''} ${person.last_name || ''}`.trim();
		} else if (person.socials) {
			return previewHandles(person.socials);
		}
		return '(unnamed)';
	}
</script>

{#if showLink}
	<a href={`/people/${person.id}`} class="person-card card {className}">
		<div class="person-row">
			<div class="avatar"></div>
			<div class="meta">
				<div class="name">{getDisplayName(person)}</div>
				{#if person.email}
					<div class="muted">{person.email}</div>
				{/if}
			</div>
		</div>
		<div class="person-info">
			{#if person.phone_number}
				<div class="pill">📞 {person.phone_number}</div>
			{/if}
			{#if person.address}
				<div class="pill">📍 Address</div>
			{/if}
			{#if person.socials && Object.keys(person.socials).length > 0}
				<div class="pill">
					🌐 {Object.keys(person.socials).length} social{Object.keys(person.socials).length !== 1
						? 's'
						: ''}
				</div>
			{/if}
			{#if person.notes}
				<div class="pill">📝 Notes</div>
			{/if}
		</div>
	</a>
{:else}
	<div class="person-card card {className}">
		<div class="person-row">
			<div class="avatar"></div>
			<div class="meta">
				<div class="name">{getDisplayName(person)}</div>
				{#if person.email}
					<div class="muted">{person.email}</div>
				{/if}
			</div>
		</div>
		<div class="person-info">
			{#if person.phone_number}
				<div class="pill">📞 {person.phone_number}</div>
			{/if}
			{#if person.address}
				<div class="pill">📍 Address</div>
			{/if}
			{#if person.socials && Object.keys(person.socials).length > 0}
				<div class="pill">
					🌐 {Object.keys(person.socials).length} social{Object.keys(person.socials).length !== 1
						? 's'
						: ''}
				</div>
			{/if}
			{#if person.notes}
				<div class="pill">📝 Notes</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.person-card {
		padding: 1rem;
		text-decoration: none;
		color: inherit;
		transition:
			transform 0.2s ease,
			box-shadow 0.2s ease;
		cursor: pointer;
		display: block;
	}

	.person-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.person-row {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		margin-bottom: 0.75rem;
	}

	.avatar {
		width: 48px;
		height: 48px;
		border-radius: 8px;
		background: linear-gradient(135deg, var(--accent), #7b61ff);
		flex-shrink: 0;
	}

	.meta .name {
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.person-info {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.pill {
		background: rgba(0, 0, 0, 0.03);
		padding: 0.4rem 0.5rem;
		border-radius: 8px;
		font-size: 0.85rem;
		white-space: nowrap;
	}
</style>
