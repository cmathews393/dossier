// Minimal API client for the Dossier backend

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export type LoginResult = { access_token: string; token_type: string };

async function request(path: string, opts: RequestInit = {}) {
	const headers = new Headers(opts.headers || {});
	headers.set('Content-Type', 'application/json');
	const token = localStorage.getItem('dossier_token');
	if (token) headers.set('Authorization', `Bearer ${token}`);
	const res = await fetch(`${BASE}${path}`, { ...opts, headers });
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || res.statusText);
	}
	return res.json().catch(() => null);
}

export const api = {
	login: async (username: string, password: string) => {
		const form = new URLSearchParams();
		form.set('username', username);
		form.set('password', password);
		form.set('grant_type', 'password');
		return fetch(`${BASE}/auth/login`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
			body: form.toString(),
		}).then(async (r) => {
			if (!r.ok) throw new Error(await r.text());
			return r.json() as Promise<LoginResult>;
		});
	},

	register: (username: string, email: string, password: string) =>
		request('/auth/register', {
			method: 'POST',
			body: JSON.stringify({ username, email, password }),
		}),

	me_jwt: () => request('/me-jwt'),

	get_people: (q?: string) => {
		const qs = q ? `?q=${encodeURIComponent(q)}` : '';
		return request(`/people${qs}`);
	},

	get_person: (id: string) => request(`/people/${id}`),

	update_person: (id: string, payload: any) =>
		request(`/people/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),

	// Sherlock provider helpers (backend proxies)
	get_sherlock_providers: () => request('/sherlock/providers'),
	get_sherlock_providers_list: () => request('/sherlock/providers/list'),
	run_sherlock: (username: string, sites?: string[], timeout?: number) => {
		const params = new URLSearchParams({ username });
		if (timeout) params.set('timeout', timeout.toString());
		
		// If sites are provided, send them in the body as a JSON array
		// Otherwise, send an empty body (or null)
		const body = sites ? JSON.stringify(sites) : '[]';
		
		return fetch(`${BASE}/sherlock/run?${params.toString()}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': localStorage.getItem('dossier_token') ? `Bearer ${localStorage.getItem('dossier_token')}` : ''
			},
			body
		}).then(async (res) => {
			if (!res.ok) {
				const text = await res.text();
				throw new Error(text || res.statusText);
			}
			return res.json().catch(() => null);
		});
	},

	// Sherlock queue methods
	queue_sherlock_search: (username: string, person_id?: string, sites?: string[], timeout?: number) => {
		const params = new URLSearchParams({ username });
		if (person_id) params.set('person_id', person_id);
		if (timeout) params.set('timeout', timeout.toString());
		
		const body = sites ? JSON.stringify(sites) : '[]';
		
		return fetch(`${BASE}/sherlock/queue?${params.toString()}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': localStorage.getItem('dossier_token') ? `Bearer ${localStorage.getItem('dossier_token')}` : ''
			},
			body
		}).then(async (res) => {
			if (!res.ok) {
				const text = await res.text();
				throw new Error(text || res.statusText);
			}
			return res.json().catch(() => null);
		});
	},

	get_sherlock_job_status: (job_id: string) => request(`/sherlock/queue/${job_id}`),

	list_sherlock_jobs: (person_id?: string, status?: string, limit?: number) => {
		const params = new URLSearchParams();
		if (person_id) params.set('person_id', person_id);
		if (status) params.set('status', status);
		if (limit) params.set('limit', limit.toString());
		
		const qs = params.toString() ? `?${params.toString()}` : '';
		return request(`/sherlock/queue${qs}`);
	},

	// Address search and geocoding
	search_addresses: (query: string, limit: number = 5, country_codes?: string) => {
		const params = new URLSearchParams({ q: query, limit: limit.toString() });
		if (country_codes) params.set('country_codes', country_codes);
		return request(`/addresses/search?${params.toString()}`);
	},

	reverse_geocode: (lat: number, lon: number) => {
		const params = new URLSearchParams({ lat: lat.toString(), lon: lon.toString() });
		return request(`/addresses/reverse?${params.toString()}`);
	},

	create_person: (payload: any) =>
		request('/people', { method: 'POST', body: JSON.stringify(payload) }),

	setup: () => request('/setup'),
};
