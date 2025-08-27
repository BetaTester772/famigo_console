<script>
    import {onMount} from 'svelte';
    import {api} from './lib/api.js';

    let active = 'users'; // 'users' | 'groups' | 'members' | 'diag'
    let notice = '';
    let error = '';

    const notify = (msg) => {
        notice = msg;
        setTimeout(() => (notice = ''), 2500);
    };
    const fail = (e) => {
        console.error(e);
        error = e.message || String(e);
        setTimeout(() => (error = ''), 4000);
    };

    // Users state
    let users = [];
    let newUserName = '';
    let newUserProfile = '{\n  "bio": ""\n}';
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

    const refreshUsers = async () => {
        users = (await api.listUsers().catch(fail)) || [];
    };
    const refreshGroups = async () => {
        groups = (await api.listGroups().catch(fail)) || [];
    };

    onMount(async () => {
        try {
            health = await api.health();
        } catch (e) {
            /* server not up yet */
        }
        await Promise.all([refreshUsers(), refreshGroups()]);
    });

    async function handleCreateUser() {
        try {
            const profile = newUserProfile ? JSON.parse(newUserProfile) : {};
            const created = await api.createUser({name: newUserName.trim(), profile_json: profile});
            notify(`User #${created.user_id} created.`);
            newUserName = '';
            newUserProfile = '{\n  "bio": ""\n}';
            await refreshUsers();
        } catch (e) {
            fail(e);
        }
    }

    async function handleGetUser() {
        try {
            userDetail = await api.getUser(Number(getUserId));
        } catch (e) {
            fail(e);
            userDetail = null;
        }
    }

    async function handleCreateGroup() {
        try {
            const created = await api.createGroup({name: newGroupName.trim()});
            notify(`Group #${created.group_id} created.`);
            newGroupName = '';
            await refreshGroups();
        } catch (e) {
            fail(e);
        }
    }

    async function handleLookupGroup() {
        try {
            groupDetail = await api.getGroupByName(lookupGroupName.trim());
        } catch (e) {
            fail(e);
            groupDetail = null;
        }
    }

    async function handleListMembers() {
        try {
            members = await api.listMembers(Number(selectedGroupId));
        } catch (e) {
            fail(e);
            members = [];
        }
    }

    async function handleAddMember() {
        // 가드 + 명확한 피드백
        if (!selectedGroupId) {
            fail(new Error('Select a group first'));
            return;
        }
        if (!memberUserId || Number.isNaN(Number(memberUserId))) {
            fail(new Error('Enter a valid user_id (number)'));
            return;
        }

        const gid = Number(selectedGroupId);
        const payload = {user_id: Number(memberUserId), role: memberRole || 'member'};

        // 실행 로그 (여기까지 오면 on:click은 정상 동작)
        console.log('[AddMember] About to POST', {gid, payload});

        try {
            const res = await api.addMember(gid, payload);     // <-- 실제 fetch
            console.log('[AddMember] OK', res);
            notify(`Added user #${res.user_id} to group #${res.group_id} as ${res.role}.`);
            await handleListMembers();
        } catch (e) {
            console.error('[AddMember] FAIL', e);
            fail(e);
        }
    }

    // groups가 갱신되고 아직 아무것도 선택 안 했으면 첫 그룹 자동 선택
    $: if (groups.length > 0 && !selectedGroupId) {
        selectedGroupId = String(groups[0].group_id);
    }

    // Members 탭에 들어오면 멤버 자동 로드 (selectedGroupId가 유효할 때)
    $: if (active === 'members' && selectedGroupId) {
        // 중복 호출을 막고 싶다면 간단히 플래그를 둘 수도 있음
        handleListMembers();
    }

</script>

<style>
    :root {
        --bg: #0b1020;
        --panel: #121935;
        --muted: #9aa4c7;
        --text: #e9edff;
        --brand: #7aa2ff;
        --accent: #63e6be;
        --danger: #ff6b6b;
    }

    * {
        box-sizing: border-box;
    }

    html, body, #app {
        height: 100%;
        margin: 0;
    }

    body {
        background: radial-gradient(1200px 800px at 20% -10%, #1b2550, transparent), var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji';
    }

    .container {
        max-width: 1100px;
        margin: 24px auto;
        padding: 0 16px;
    }

    .header {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 18px;
    }

    .badge {
        background: rgba(122, 162, 255, .12);
        color: var(--brand);
        border: 1px solid rgba(122, 162, 255, .35);
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 12px;
    }

    .card {
        background: linear-gradient(180deg, rgba(255, 255, 255, .03), transparent), var(--panel);
        border: 1px solid rgba(255, 255, 255, .06);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, .25);
    }

    .toolbar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        padding: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, .06);
    }

    .content {
        padding: 14px;
    }

    .row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    input, select, button, textarea {
        font: inherit;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, .12);
        padding: 10px 12px;
        background: rgba(0, 0, 0, .25);
        color: var(--text);
    }

    button {
        cursor: pointer;
        border-color: transparent;
        background: linear-gradient(180deg, rgba(122, 162, 255, .4), rgba(122, 162, 255, .2));
    }

    button.ghost {
        background: rgba(255, 255, 255, .04);
        border: 1px solid rgba(255, 255, 255, .1);
    }

    button.success {
        background: linear-gradient(180deg, rgba(99, 230, 190, .5), rgba(99, 230, 190, .2));
    }

    .table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    .table th, .table td {
        border-bottom: 1px solid rgba(255, 255, 255, .06);
        padding: 10px;
        text-align: left;
    }

    .table th {
        color: var(--muted);
        font-weight: 600;
    }

    .kv {
        display: grid;
        grid-template-columns: 160px 1fr;
        gap: 8px 14px;
    }

    .kv div:first-child {
        color: var(--muted);
    }

    hr.soft {
        border: 0;
        border-top: 1px solid rgba(255, 255, 255, .06);
        margin: 14px 0;
    }

    .tabs {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
    }

    .tab {
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, .1);
        background: rgba(255, 255, 255, .04);
        cursor: pointer;
    }

    .tab.active {
        background: rgba(122, 162, 255, .2);
        border-color: rgba(122, 162, 255, .4);
        color: var(--text);
    }

    .alert {
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, .12);
        background: rgba(255, 255, 255, .03);
    }

    .small {
        font-size: 12px;
        color: var(--muted);
    }

    pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-word;
    }
</style>

<div class="container">
    <div class="header">
        <h1 style="margin:0">Users/Groups Console</h1>
        <span class="badge">Svelte · Vite (JS)</span>
    </div>

    {#if notice}
        <div class="alert" role="status">{notice}</div>
    {/if}
    {#if error}
        <div class="alert" style="border-color: rgba(255,107,107,.35); color:#ffd7d7">⚠ {error}</div>
    {/if}

    <div class="tabs" style="margin: 14px 0 10px;">
        <div class="tab {active==='users'?'active':''}" on:click={() => active='users'}>Users</div>
        <div class="tab {active==='groups'?'active':''}" on:click={() => active='groups'}>Groups</div>
        <div class="tab {active==='members'?'active':''}"
             on:click={async () => { active = 'members'; if (groups.length === 0) await refreshGroups(); }}>
            Group Members
        </div>
        <div class="tab {active==='diag'?'active':''}" on:click={() => active='diag'}>Diagnostics</div>
    </div>

    {#if active === 'users'}
        <section class="card">
            <div class="toolbar">
                <strong>Users</strong>
                <span class="small">Create and list users</span>
            </div>
            <div class="content">
                <div class="row" style="align-items:flex-start">
                    <div style="flex:1; min-width: 280px;">
                        <h3 style="margin:6px 0 10px">Create User</h3>
                        <div class="row">
                            <input placeholder="name" bind:value={newUserName} style="flex:1"/>
                            <button class="success" on:click={handleCreateUser} disabled={!newUserName.trim()}>Create
                            </button>
                        </div>
                        <div class="small" style="margin-top:8px">profile_json (optional)</div>
                        <textarea rows="6" spellcheck="false" bind:value={newUserProfile}
                                  style="width:100%; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;"></textarea>
                    </div>
                    <div style="flex:1; min-width: 280px;">
                        <h3 style="margin:6px 0 10px">Get User by ID</h3>
                        <div class="row">
                            <input placeholder="user_id" bind:value={getUserId}/>
                            <button class="ghost" on:click={handleGetUser} disabled={!getUserId}>Get</button>
                        </div>
                        {#if userDetail}
                            <hr class="soft"/>
                            <div class="kv">
                                <div>user_id</div>
                                <div>{userDetail.user_id}</div>
                                <div>name</div>
                                <div>{userDetail.name}</div>
                                <div>created_at</div>
                                <div>{String(userDetail.created_at)}</div>
                                <div>updated_at</div>
                                <div>{String(userDetail.updated_at)}</div>
                                <div>profile_json</div>
                                <div>
                                    <pre>{JSON.stringify(userDetail.profile_json, null, 2)}</pre>
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>

                <hr class="soft"/>
                <h3 style="margin:6px 0 10px">All Users</h3>
                <div class="row" style="margin-bottom:8px">
                    <button class="ghost" on:click={refreshUsers}>Reload</button>
                </div>
                <div style="overflow:auto">
                    <table class="table">
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Created</th>
                            <th>Updated</th>
                            <th>profile_json</th>
                        </tr>
                        </thead>
                        <tbody>
                        {#each users as u}
                            <tr>
                                <td>{u.user_id}</td>
                                <td>{u.name}</td>
                                <td>{String(u.created_at)}</td>
                                <td>{String(u.updated_at)}</td>
                                <td>
                                    <pre>{JSON.stringify(u.profile_json || {}, null, 0)}</pre>
                                </td>
                            </tr>
                        {/each}
                        {#if users.length === 0}
                            <tr>
                                <td colspan="5" class="small">No users yet.</td>
                            </tr>
                        {/if}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    {/if}

    {#if active === 'groups'}
        <section class="card">
            <div class="toolbar">
                <strong>Groups</strong>
                <span class="small">Create and list groups</span>
            </div>
            <div class="content">
                <div class="row" style="align-items:flex-start">
                    <div style="flex:1; min-width:280px;">
                        <h3 style="margin:6px 0 10px">Create Group</h3>
                        <div class="row">
                            <input placeholder="name" bind:value={newGroupName} style="flex:1"/>
                            <button class="success" on:click={handleCreateGroup} disabled={!newGroupName.trim()}>
                                Create
                            </button>
                        </div>
                    </div>
                    <div style="flex:1; min-width:280px;">
                        <h3 style="margin:6px 0 10px">Lookup Group by Name</h3>
                        <div class="row">
                            <input placeholder="name" bind:value={lookupGroupName}/>
                            <button class="ghost" on:click={handleLookupGroup} disabled={!lookupGroupName.trim()}>
                                Lookup
                            </button>
                        </div>
                        {#if groupDetail}
                            <hr class="soft"/>
                            <div class="kv">
                                <div>group_id</div>
                                <div>{groupDetail.group_id}</div>
                                <div>name</div>
                                <div>{groupDetail.name}</div>
                                <div>created_at</div>
                                <div>{String(groupDetail.created_at)}</div>
                                <div>updated_at</div>
                                <div>{String(groupDetail.updated_at)}</div>
                            </div>
                        {/if}
                    </div>
                </div>

                <hr class="soft"/>
                <h3 style="margin:6px 0 10px">All Groups</h3>
                <div class="row" style="margin-bottom:8px">
                    <button class="ghost" on:click={refreshGroups}>Reload</button>
                </div>
                <div style="overflow:auto">
                    <table class="table">
                        <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Created</th>
                            <th>Updated</th>
                        </tr>
                        </thead>
                        <tbody>
                        {#each groups as g}
                            <tr>
                                <td>{g.group_id}</td>
                                <td>{g.name}</td>
                                <td>{String(g.created_at)}</td>
                                <td>{String(g.updated_at)}</td>
                            </tr>
                        {/each}
                        {#if groups.length === 0}
                            <tr>
                                <td colspan="4" class="small">No groups yet.</td>
                            </tr>
                        {/if}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    {/if}

    {#if active === 'members'}
        <section class="card">
            <div class="toolbar">
                <strong>Group Members</strong>
                <span class="small">Add and list group members</span>
            </div>
            <div class="content">
                <div class="row" style="align-items:flex-end">
                    <div class="row" style="flex:1; min-width:260px;">
                        <select
                                bind:value={selectedGroupId}
                                on:change={handleListMembers}
                                style="flex:1"
                        >
                            <option value="" disabled>Select group…</option>
                            {#each groups as g}
                                <option value={g.group_id}>{g.group_id} · {g.name}</option>
                            {/each}
                        </select>
                        <button class="ghost" on:click={handleListMembers} disabled={!selectedGroupId}>Reload</button>
                        <button class="ghost" on:click={handleListMembers} disabled={!selectedGroupId}>Load Members
                        </button>
                    </div>
                </div>

                <hr class="soft"/>

                <h3 style="margin:6px 0 10px">Add Member</h3>
                <div class="row">
                    <input placeholder="user_id" bind:value={memberUserId}/>
                    <input placeholder="role (default: member)" bind:value={memberRole}/>
                    <!--                    <button on:click={handleAddMember} class="success" disabled={!selectedGroupId || !memberUserId}>-->
                    <!--                        Add-->
                    <!--                    </button>-->
                    <button
                            class="success"
                            on:click={() => {
    console.log('[UI] Add clicked', { selectedGroupId, memberUserId, memberRole });
    handleAddMember();
  }}
                    >
                        Add
                    </button>

                </div>

                <hr class="soft"/>

                <h3 style="margin:6px 0 10px">Members of Group #{selectedGroupId || '—'}</h3>
                <div style="overflow:auto">
                    <table class="table">
                        <thead>
                        <tr>
                            <th>group_id</th>
                            <th>user_id</th>
                            <th>role</th>
                            <th>joined_at</th>
                            <th>user.name</th>
                        </tr>
                        </thead>
                        <tbody>
                        {#each members as m}
                            <tr>
                                <td>{m.group_id}</td>
                                <td>{m.user_id}</td>
                                <td>{m.role}</td>
                                <td>{String(m.joined_at)}</td>
                                <td>{m.user?.name}</td>
                            </tr>
                        {/each}
                        {#if !members || members.length === 0}
                            <tr>
                                <td colspan="5" class="small">No members loaded.</td>
                            </tr>
                        {/if}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    {/if}

    {#if active === 'diag'}
        <section class="card">
            <div class="toolbar"><strong>Diagnostics</strong></div>
            <div class="content">
                <div class="kv">
                    <div>API Base</div>
                    <div>{import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}</div>
                    <div>Health</div>
                    <div>
                        <pre>{health ? JSON.stringify(health, null, 2) : '—'}</pre>
                    </div>
                </div>
                <div class="small" style="margin-top:10px">If CORS blocks requests, enable CORSMiddleware on FastAPI.
                </div>
            </div>
        </section>
    {/if}
</div>
