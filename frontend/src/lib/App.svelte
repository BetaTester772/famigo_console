<script>
import { onMount } from 'svelte';
import { api } from './lib/api.js';


let active = 'users'; // 'users' | 'groups' | 'members' | 'diag'
let notice = '';
let error = '';


const notify = (msg) => { notice = msg; setTimeout(() => notice = '', 2500); };
const fail = (e) => { console.error(e); error = e.message || String(e); setTimeout(() => error = '', 4000); };


// Users state
let users = [];
let newUserName = '';
let newUserProfile = '{\n "bio": ""\n}';
let getUserId = '';
let userDetail = null;


// Groups state
let groups = [];
let newGroupName = '';
let lookupGroupName = '';
let groupDetail = null;


// Members state
let selectedGroupId = '';
let members = [];
let memberUserId = '';
let memberRole = 'member';


// Diag
let health = null;


const refreshUsers = async () => { users = await api.listUsers().catch(fail) || []; };
const refreshGroups = async () => { groups = await api.listGroups().catch(fail) || []; };


onMount(async () => {
try {
health = await api.health();
} catch (e) { /* ignore if server is not yet up */ }
await Promise.all([refreshUsers(), refreshGroups()]);
});


async function handleCreateUser() {
try {
const profile = newUserProfile ? JSON.parse(newUserProfile) : {};
const created = await api.createUser({ name: newUserName.trim(), profile_json: profile });
notify(`User #${created.user_id} created.`);
newUserName = '';
newUserProfile = '{\n "bio": ""\n}';
await refreshUsers();
} catch (e) { fail(e); }
}


async function handleGetUser() {
try { userDetail = await api.getUser(Number(getUserId)); }
catch (e) { fail(e); userDetail = null; }
}


async function handleCreateGroup() {
try {
const created = await api.createGroup({ name: newGroupName.trim() });
notify(`Group #${created.group_id} created.`);
newGroupName = '';
await refreshGroups();
} catch (e) { fail(e); }
}


async function handleLookupGroup() {
try { groupDetail = await api.getGroupByName(lookupGroupName.trim()); }
catch (e) { fail(e); groupDetail = null; }
}


async function handleListMembers() {
try { members = await api.listMembers(Number(selectedGroupId)); }
catch (e) { fail(e); members = []; }
}


async function handleAddMember() {
try {
const res = await api.addMember(Number(selectedGroupId), { user_id: Number(memberUserId), role: memberRole });
</div>