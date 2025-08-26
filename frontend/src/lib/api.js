const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || 'http://localhost:8000';


async function http(path, opts = {}) {
const res = await fetch(BASE + path, {
headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
...opts
});
let data = null;
const ct = res.headers.get('content-type') || '';
if (ct.includes('application/json')) {
data = await res.json();
} else {
data = await res.text();
}
if (!res.ok) {
const msg = typeof data === 'string' ? data : data?.detail || JSON.stringify(data);
throw new Error(msg || `HTTP ${res.status}`);
}
return data;
}


export const api = {
health: () => http('/healthz'),
// Users
createUser: (payload) => http('/users', { method: 'POST', body: JSON.stringify(payload) }),
listUsers: ({ offset = 0, limit = 100 } = {}) => http(`/users?offset=${offset}&limit=${limit}`),
getUser: (id) => http(`/users/${id}`),


// Groups
createGroup: (payload) => http('/groups', { method: 'POST', body: JSON.stringify(payload) }),
listGroups: ({ offset = 0, limit = 100 } = {}) => http(`/groups?offset=${offset}&limit=${limit}`),
getGroupByName: (name) => http(`/groups/${encodeURIComponent(name)}`),


// Group members
addMember: (groupId, payload) => http(`/groups/${groupId}/members`, { method: 'POST', body: JSON.stringify(payload) }),
listMembers: (groupId, { offset = 0, limit = 200 } = {}) => http(`/groups/${groupId}/members?offset=${offset}&limit=${limit}`),


// Convenience
groupsForUser: (userId, { offset = 0, limit = 100 } = {}) => http(`/users/${userId}/groups?offset=${offset}&limit=${limit}`)
};