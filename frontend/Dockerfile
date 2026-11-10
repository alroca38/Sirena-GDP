FROM nginx:alpine

RUN cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;
    resolver 127.0.0.11 valid=5s ipv6=off;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/consult/ {
        set $consult http://ms-consult:8000;
        proxy_pass $consult;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_intercept_errors on;
        error_page 502 503 504 = @consult_off;
    }

    location @consult_off {
        default_type application/json;
        return 503 '{"status":503,"title":"Servicio no disponible","details":"El servicio de consulta se encuentra deshabilitado."}';
    }

    location /api/create/ {
        set $create http://ms-create:8000;
        proxy_pass $create;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/modify/ {
        set $modify http://ms-modify:8000;
        proxy_pass $modify;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/delete/ {
        set $delete http://ms-delete:8000;
        proxy_pass $delete;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/log/ {
        set $log http://ms-log:8000;
        proxy_pass $log;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

RUN cat <<'EOF' > /usr/share/nginx/html/index.html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sirena - Gestión de Datos Personales</title>
  <style>
    :root {
      --bg: #0b1120;
      --panel: #111827;
      --card: #1e293b;
      --border: #334155;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
      --success: #10b981;
      --danger: #ef4444;
      --warning: #f59e0b;
      --text: #f8fafc;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; }
    header { background: var(--panel); border-bottom: 1px solid var(--border); padding: 0.9rem 2rem; display: flex; justify-content: space-between; align-items: center; }
    .brand { display: flex; align-items: center; gap: 0.75rem; }
    .brand-badge { background: var(--primary); color: #fff; font-weight: 700; padding: 0.4rem 0.65rem; border-radius: 0.5rem; }
    .user-bar { display: flex; align-items: center; gap: 0.75rem; font-size: 0.875rem; }
    .badge { padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .badge-ok { background: rgba(16,185,129,0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.4); }
    .badge-err { background: rgba(239,68,68,0.15); color: var(--danger); border: 1px solid rgba(239,68,68,0.4); }
    main { max-width: 980px; width: 100%; margin: 2rem auto; padding: 0 1.25rem; flex: 1; }
    .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.75rem; }
    .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
    .menu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
    .menu-card { background: var(--card); border: 1px solid var(--border); border-radius: 0.65rem; padding: 1.25rem; cursor: pointer; transition: 0.15s; text-align: left; color: var(--text); width: 100%; }
    .menu-card:hover:not(:disabled) { border-color: var(--primary); transform: translateY(-2px); }
    .menu-card:disabled { opacity: 0.5; cursor: not-allowed; }
    .menu-card h3 { font-size: 1rem; margin-bottom: 0.35rem; display: flex; justify-content: space-between; align-items: center; }
    .menu-card p { font-size: 0.82rem; color: var(--muted); }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .full { grid-column: 1 / -1; }
    label { display: block; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; color: var(--muted); margin-bottom: 0.35rem; }
    input, select { width: 100%; padding: 0.6rem 0.75rem; border-radius: 0.45rem; border: 1px solid var(--border); background: var(--card); color: var(--text); font-size: 0.9rem; }
    .field-error { color: var(--danger); font-size: 0.76rem; margin-top: 0.25rem; min-height: 1rem; }
    .btn { padding: 0.6rem 1.1rem; border-radius: 0.45rem; border: 1px solid transparent; font-weight: 600; cursor: pointer; font-size: 0.875rem; }
    .btn-primary { background: var(--primary); color: #fff; }
    .btn-primary:hover { background: var(--primary-hover); }
    .btn-secondary { background: var(--card); color: var(--text); border-color: var(--border); }
    .btn-danger { background: var(--danger); color: #fff; }
    .actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem; }
    .alert { padding: 0.85rem 1rem; border-radius: 0.5rem; margin-bottom: 1rem; font-size: 0.88rem; }
    .alert-ok { background: rgba(16,185,129,0.15); border: 1px solid var(--success); color: #a7f3d0; }
    .alert-err { background: rgba(239,68,68,0.15); border: 1px solid var(--danger); color: #fecaca; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.82rem; }
    th, td { border-bottom: 1px solid var(--border); padding: 0.65rem 0.5rem; text-align: left; }
    th { color: var(--muted); text-transform: uppercase; font-size: 0.72rem; }
    .hidden { display: none !important; }
    .profile-box { display: grid; grid-template-columns: 180px 1fr; gap: 1.5rem; align-items: start; margin-top: 1rem; }
    .avatar-preview { width: 160px; height: 160px; border-radius: 0.75rem; border: 1px solid var(--border); background: var(--card); object-fit: cover; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 0.8rem; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <span class="brand-badge">GDP</span>
      <div>
        <div style="font-weight:700">GESTIÓN DE DATOS PERSONALES</div>
        <div style="font-size:0.75rem;color:var(--muted)">Sirena · Sistema de Microservicios</div>
      </div>
    </div>
    <div class="user-bar">
      <span id="userDisplay">ana.gomez</span>
      <span class="badge badge-ok">SSO Activo</span>
      <button class="btn btn-secondary" onclick="configureToken()">Token SSO</button>
    </div>
  </header>

  <main>
    <div id="alertBox" class="alert hidden"></div>

    <!-- VISTA MENU PRINCIPAL -->
    <section id="viewMenu" class="panel">
      <div class="panel-header">
        <h2>MENÚ PRINCIPAL</h2>
        <span id="consultBadge" class="badge badge-ok">Verificando servicios...</span>
      </div>
      <div class="menu-grid">
        <button class="menu-card" onclick="openView('create')">
          <h3>1. Crear Personas</h3>
          <p>Registrar nueva persona con datos básicos y fotografía.</p>
        </button>
        <button class="menu-card" onclick="openView('modify')">
          <h3>2. Modificar Datos Personales</h3>
          <p>Actualizar la información existente por número de documento.</p>
        </button>
        <button id="btnConsultCard" class="menu-card" onclick="openView('consult')">
          <h3>3. Consultar Datos Personales <span id="consultStatusTag" class="badge badge-ok">Disponible</span></h3>
          <p id="consultStatusDesc">Búsqueda directa de perfiles registrados por documento.</p>
        </button>
        <button class="menu-card" onclick="window.open('http://' + window.location.hostname + ':5678', '_blank')">
          <h3>4. Consultar Lenguaje Natural <span class="badge badge-ok">n8n :5678</span></h3>
          <p>Consultas con patrón RAG en la interfaz de chat de n8n.</p>
        </button>
        <button class="menu-card" onclick="openView('delete')">
          <h3>5. Borrar Personas</h3>
          <p>Eliminación permanente de registros con confirmación explícita.</p>
        </button>
        <button class="menu-card" onclick="openView('log')">
          <h3>6. Consultar Log</h3>
          <p>Auditoría de transacciones por tipo, documento y fecha.</p>
        </button>
      </div>
    </section>

    <!-- VISTA FORMULARIO CREAR / MODIFICAR -->
    <section id="viewForm" class="panel hidden">
      <div class="panel-header">
        <h2 id="formTitle">Crear Persona</h2>
        <button class="btn btn-secondary" onclick="openView('menu')">← Volver al Menú</button>
      </div>

      <div id="modifySearchBox" class="hidden" style="margin-bottom:1.25rem;padding-bottom:1rem;border-bottom:1px solid var(--border)">
        <label>Buscar por Nro. de Documento para precargar</label>
        <div style="display:flex;gap:0.75rem">
          <input id="modifySearchDoc" type="text" maxlength="10" placeholder="Ej. 1045678901" />
          <button class="btn btn-primary" type="button" onclick="preloadForModify()">Cargar Datos</button>
        </div>
      </div>

      <form id="personForm" onsubmit="submitPersonForm(event)">
        <div class="form-grid">
          <div>
            <label>Tipo de Documento *</label>
            <select id="f_documentType" required>
              <option value="CC">Cédula (CC)</option>
              <option value="TI">Tarjeta de identidad (TI)</option>
            </select>
            <div class="field-error" id="err_documentType"></div>
          </div>
          <div>
            <label>Nro. Documento *</label>
            <input id="f_documentId" type="text" maxlength="10" required />
            <div class="field-error" id="err_documentId"></div>
          </div>
          <div>
            <label>Primer Nombre *</label>
            <input id="f_firstName" type="text" maxlength="30" required />
            <div class="field-error" id="err_firstName"></div>
          </div>
          <div>
            <label>Segundo Nombre (Opcional)</label>
            <input id="f_secondName" type="text" maxlength="30" />
            <div class="field-error" id="err_secondName"></div>
          </div>
          <div class="full">
            <label>Apellidos *</label>
            <input id="f_lastNames" type="text" maxlength="60" required />
            <div class="field-error" id="err_lastNames"></div>
          </div>
          <div>
            <label>Fecha de Nacimiento *</label>
            <input id="f_birthdate" type="date" required />
            <div class="field-error" id="err_birthdate"></div>
          </div>
          <div>
            <label>Género *</label>
            <select id="f_genre" required>
              <option value="MASCULINO">Masculino</option>
              <option value="FEMENINO">Femenino</option>
              <option value="NO_BINARIO">No binario</option>
              <option value="PREFIERO_NO_REPORTAR">Prefiero no reportar</option>
            </select>
            <div class="field-error" id="err_genre"></div>
          </div>
          <div>
            <label>Correo Electrónico *</label>
            <input id="f_email" type="email" maxlength="254" required />
            <div class="field-error" id="err_email"></div>
          </div>
          <div>
            <label>Celular (10 dígitos) *</label>
            <input id="f_phoneNumber" type="text" maxlength="10" required />
            <div class="field-error" id="err_phoneNumber"></div>
          </div>
          <div class="full">
            <label>Foto de Perfil (Opcional, JPEG o PNG máx. 2 MB)</label>
            <input id="f_photo" type="file" accept="image/jpeg,image/png" />
            <div id="removePhotoWrap" class="hidden" style="margin-top:0.5rem">
              <label style="display:inline-flex;align-items:center;gap:0.5rem;text-transform:none">
                <input id="f_removePhoto" type="checkbox" style="width:auto" /> Quitar foto actual
              </label>
            </div>
            <div class="field-error" id="err_photo"></div>
          </div>
        </div>
        <div class="actions">
          <button type="button" class="btn btn-secondary" onclick="openView('menu')">Cancelar</button>
          <button type="submit" class="btn btn-primary">Guardar</button>
        </div>
      </form>
    </section>

    <!-- VISTA CONSULTAR -->
    <section id="viewConsult" class="panel hidden">
      <div class="panel-header">
        <h2>Consulta de Datos Personales</h2>
        <button class="btn btn-secondary" onclick="openView('menu')">← Volver al Menú</button>
      </div>
      <div style="display:flex;gap:0.75rem">
        <input id="consultDocInput" type="text" maxlength="10" placeholder="Ingrese número de documento (ej. 1045678901)" />
        <button class="btn btn-primary" onclick="runConsult()">Consultar</button>
      </div>
      <div id="consultResult" class="hidden profile-box">
        <img id="consultAvatar" class="avatar-preview" alt="Foto" />
        <div class="form-grid" id="consultDetails"></div>
      </div>
    </section>

    <!-- VISTA BORRAR -->
    <section id="viewDelete" class="panel hidden">
      <div class="panel-header">
        <h2>Borrar Personas</h2>
        <button class="btn btn-secondary" onclick="openView('menu')">← Volver al Menú</button>
      </div>
      <div style="display:flex;gap:0.75rem">
        <input id="deleteDocInput" type="text" maxlength="10" placeholder="Número de documento a eliminar" />
        <button class="btn btn-primary" onclick="preloadForDelete()">Buscar</button>
      </div>
      <div id="deleteConfirmBox" class="hidden" style="margin-top:1.25rem;padding:1rem;border:1px solid var(--danger);border-radius:0.5rem">
        <p id="deleteSummaryText" style="margin-bottom:1rem"></p>
        <div class="actions">
          <button class="btn btn-secondary" onclick="cancelDelete()">Cancelar</button>
          <button class="btn btn-danger" onclick="confirmDelete()">Confirmar Eliminación</button>
        </div>
      </div>
    </section>

    <!-- VISTA LOG -->
    <section id="viewLog" class="panel hidden">
      <div class="panel-header">
        <h2>Consulta del Log de Auditoría</h2>
        <button class="btn btn-secondary" onclick="openView('menu')">← Volver al Menú</button>
      </div>
      <div class="form-grid">
        <div>
          <label>Tipo de Transacción</label>
          <select id="log_type">
            <option value="">-- Todos --</option>
            <option value="CREAR">CREAR</option>
            <option value="MODIFICAR">MODIFICAR</option>
            <option value="CONSULTAR">CONSULTAR</option>
            <option value="BORRAR">BORRAR</option>
            <option value="CONSULTA_LN">CONSULTA_LN</option>
            <option value="CONSULTA_LOG">CONSULTA_LOG</option>
          </select>
        </div>
        <div>
          <label>Tipo de Documento</label>
          <select id="log_documentType">
            <option value="">-- Todos --</option>
            <option value="CC">CC</option>
            <option value="TI">TI</option>
          </select>
        </div>
        <div>
          <label>Número de Documento</label>
          <input id="log_documentId" type="text" maxlength="10" placeholder="Ej. 1045678901" />
        </div>
        <div>
          <label>Resultado</label>
          <select id="log_result">
            <option value="">-- Todos --</option>
            <option value="EXITO">EXITO</option>
            <option value="RECHAZADA">RECHAZADA</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>
        <div>
          <label>Fecha Desde (Bogotá)</label>
          <input id="log_from" type="date" />
        </div>
        <div>
          <label>Fecha Hasta (Bogotá)</label>
          <input id="log_to" type="date" />
        </div>
      </div>
      <div class="actions">
        <button class="btn btn-primary" onclick="loadLogs()">Aplicar Filtros</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>ID / Fecha UTC</th>
            <th>Tipo</th>
            <th>Usuario</th>
            <th>Documento</th>
            <th>Resultado</th>
            <th>Detalle RAG</th>
          </tr>
        </thead>
        <tbody id="logTableBody"></tbody>
      </table>
    </section>
  </main>

  <script>
    function makeDefaultJwt(username) {
      const b64 = (obj) => btoa(JSON.stringify(obj)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const header = b64({ alg: 'HS256', typ: 'JWT' });
      const payload = b64({ sub: username, preferred_username: username, name: username, exp: Math.floor(Date.now() / 1000) + 86400 });
      return `${header}.${payload}.sirena-demo-sig`;
    }

    if (!localStorage.getItem('gdp_token')) {
      localStorage.setItem('gdp_token', makeDefaultJwt('ana.gomez'));
    }

    function getToken() { return localStorage.getItem('gdp_token') || ''; }
    function authHeaders() { return { 'Authorization': 'Bearer ' + getToken() }; }

    function configureToken() {
      const current = getToken();
      const input = prompt('Ingrese el token JWT de Roble (o deje vacío para regenerar token de prueba):', current);
      if (input === null) return;
      const next = input.trim() || makeDefaultJwt('ana.gomez');
      localStorage.setItem('gdp_token', next);
      showAlert('Token actualizado correctamente.', false);
    }

    function showAlert(msg, isError = false) {
      const box = document.getElementById('alertBox');
      box.textContent = msg;
      box.className = 'alert ' + (isError ? 'alert-err' : 'alert-ok');
      box.classList.remove('hidden');
    }
    function clearAlert() { document.getElementById('alertBox').classList.add('hidden'); }
    function clearFieldErrors() {
      document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
    }

    async function checkConsultHealth() {
      const card = document.getElementById('btnConsultCard');
      const tag = document.getElementById('consultStatusTag');
      const topBadge = document.getElementById('consultBadge');
      try {
        const res = await fetch('/api/consult/health');
        if (res.ok) {
          card.disabled = false;
          tag.textContent = 'Disponible';
          tag.className = 'badge badge-ok';
          topBadge.textContent = 'ms-consult: Activo';
          topBadge.className = 'badge badge-ok';
        } else {
          throw new Error('503');
        }
      } catch (e) {
        card.disabled = true;
        tag.textContent = 'Servicio no disponible';
        tag.className = 'badge badge-err';
        topBadge.textContent = 'ms-consult: Servicio no disponible';
        topBadge.className = 'badge badge-err';
      }
    }

    let currentMode = 'create';
    let deleteTargetDoc = null;

    function openView(view) {
      clearAlert();
      clearFieldErrors();
      ['viewMenu', 'viewForm', 'viewConsult', 'viewDelete', 'viewLog'].forEach(id => {
        document.getElementById(id).classList.add('hidden');
      });
      if (view === 'menu') {
        document.getElementById('viewMenu').classList.remove('hidden');
        checkConsultHealth();
      } else if (view === 'create' || view === 'modify') {
        currentMode = view;
        document.getElementById('personForm').reset();
        document.getElementById('formTitle').textContent = view === 'create' ? 'Crear Persona' : 'Modificar Datos Personales';
        document.getElementById('modifySearchBox').classList.toggle('hidden', view !== 'modify');
        document.getElementById('removePhotoWrap').classList.toggle('hidden', view !== 'modify');
        document.getElementById('f_documentId').readOnly = (view === 'modify');
        document.getElementById('viewForm').classList.remove('hidden');
      } else if (view === 'consult') {
        document.getElementById('consultResult').classList.add('hidden');
        document.getElementById('viewConsult').classList.remove('hidden');
      } else if (view === 'delete') {
        document.getElementById('deleteConfirmBox').classList.add('hidden');
        document.getElementById('viewDelete').classList.remove('hidden');
      } else if (view === 'log') {
        document.getElementById('viewLog').classList.remove('hidden');
        loadLogs();
      }
    }

    async function preloadForModify() {
      clearAlert();
      clearFieldErrors();
      const doc = document.getElementById('modifySearchDoc').value.trim();
      const res = await fetch(`/api/modify/v1/person/${encodeURIComponent(doc)}`, { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) {
        showAlert(data.details || data.title || 'No se pudo cargar la persona.', true);
        return;
      }
      document.getElementById('f_documentType').value = data.documentType;
      document.getElementById('f_documentId').value = data.documentId;
      document.getElementById('f_firstName').value = data.firstName;
      document.getElementById('f_secondName').value = data.secondName || '';
      document.getElementById('f_lastNames').value = data.lastNames;
      document.getElementById('f_birthdate').value = data.birthdate;
      document.getElementById('f_genre').value = data.genre;
      document.getElementById('f_email').value = data.email;
      document.getElementById('f_phoneNumber').value = data.phoneNumber;
    }

    async function submitPersonForm(e) {
      e.preventDefault();
      clearAlert();
      clearFieldErrors();
      const fd = new FormData();
      fd.append('documentType', document.getElementById('f_documentType').value);
      fd.append('documentId', document.getElementById('f_documentId').value);
      fd.append('firstName', document.getElementById('f_firstName').value);
      fd.append('secondName', document.getElementById('f_secondName').value);
      fd.append('lastNames', document.getElementById('f_lastNames').value);
      fd.append('birthdate', document.getElementById('f_birthdate').value);
      fd.append('genre', document.getElementById('f_genre').value);
      fd.append('email', document.getElementById('f_email').value);
      fd.append('phoneNumber', document.getElementById('f_phoneNumber').value);
      const photoFile = document.getElementById('f_photo').files[0];
      if (photoFile) fd.append('photo', photoFile);

      let url = '/api/create/v1/person';
      let method = 'POST';
      if (currentMode === 'modify') {
        const doc = document.getElementById('f_documentId').value.trim();
        url = `/api/modify/v1/person/${encodeURIComponent(doc)}`;
        method = 'PUT';
        fd.append('removePhoto', document.getElementById('f_removePhoto').checked ? 'true' : 'false');
      }

      const res = await fetch(url, { method, headers: authHeaders(), body: fd });
      const data = await res.json();
      if (!res.ok) {
        if (data.errors) {
          Object.entries(data.errors).forEach(([k, v]) => {
            const el = document.getElementById('err_' + k);
            if (el) el.textContent = v;
          });
        }
        showAlert(data.details || data.title || 'Error en la operación.', true);
        return;
      }
      showAlert(currentMode === 'create' ? 'Persona creada exitosamente.' : 'Datos actualizados exitosamente.', false);
      if (currentMode === 'create') document.getElementById('personForm').reset();
    }

    async function runConsult() {
      clearAlert();
      const doc = document.getElementById('consultDocInput').value.trim();
      const res = await fetch(`/api/consult/v1/person/${encodeURIComponent(doc)}`, { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) {
        document.getElementById('consultResult').classList.add('hidden');
        showAlert(data.details || data.title || 'Error al consultar.', true);
        return;
      }
      const details = document.getElementById('consultDetails');
      details.innerHTML = `
        <div><label>Tipo de Documento</label><div>${data.documentType}</div></div>
        <div><label>Nro. Documento</label><div>${data.documentId}</div></div>
        <div><label>Primer Nombre</label><div>${data.firstName}</div></div>
        <div><label>Segundo Nombre</label><div>${data.secondName || '-'}</div></div>
        <div><label>Apellidos</label><div>${data.lastNames}</div></div>
        <div><label>Fecha de Nacimiento</label><div>${data.birthdate}</div></div>
        <div><label>Género</label><div>${data.genre}</div></div>
        <div><label>Celular</label><div>${data.phoneNumber}</div></div>
        <div class="full"><label>Correo Electrónico</label><div>${data.email}</div></div>
      `;
      const img = document.getElementById('consultAvatar');
      if (data.hasPhoto) {
        img.src = `/api/consult/v1/person/${encodeURIComponent(data.documentId)}/pic?token=${encodeURIComponent(getToken())}&t=${Date.now()}`;
      } else {
        img.removeAttribute('src');
      }
      document.getElementById('consultResult').classList.remove('hidden');
    }

    async function preloadForDelete() {
      clearAlert();
      const doc = document.getElementById('deleteDocInput').value.trim();
      const res = await fetch(`/api/delete/v1/person/${encodeURIComponent(doc)}`, { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) {
        document.getElementById('deleteConfirmBox').classList.add('hidden');
        showAlert(data.details || data.title || 'Persona no encontrada.', true);
        return;
      }
      deleteTargetDoc = data.documentId;
      document.getElementById('deleteSummaryText').textContent =
        `¿Confirma que desea eliminar permanentemente a ${data.firstName} ${data.secondName || ''} ${data.lastNames} (${data.documentType} ${data.documentId})?`;
      document.getElementById('deleteConfirmBox').classList.remove('hidden');
    }

    function cancelDelete() {
      deleteTargetDoc = null;
      document.getElementById('deleteConfirmBox').classList.add('hidden');
    }

    async function confirmDelete() {
      if (!deleteTargetDoc) return;
      const res = await fetch(`/api/delete/v1/person/${encodeURIComponent(deleteTargetDoc)}`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.status === 204) {
        showAlert('Persona eliminada correctamente.', false);
        cancelDelete();
      } else {
        const data = await res.json();
        showAlert(data.details || data.title || 'No se pudo eliminar.', true);
      }
    }

    async function loadLogs() {
      clearAlert();
      const params = new URLSearchParams();
      ['type', 'documentType', 'documentId', 'result', 'from', 'to'].forEach(k => {
        const val = document.getElementById('log_' + k).value.trim();
        if (val) params.set(k, val);
      });
      const res = await fetch('/api/log/v1/transactions?' + params.toString(), { headers: authHeaders() });
      const data = await res.json();
      if (!res.ok) {
        showAlert(data.details || data.title || 'Error al consultar el log.', true);
        return;
      }
      const tbody = document.getElementById('logTableBody');
      tbody.innerHTML = (data.items || []).map(row => `
        <tr>
          <td>#${row.id}<br/><span style="color:var(--muted)">${new Date(row.timestamp).toISOString().replace('T',' ').slice(0,19)}</span></td>
          <td>${row.type}</td>
          <td>${row.user || '-'}</td>
          <td>${row.documentType ? row.documentType + ' - ' : ''}${row.documentId || 'N/A'}</td>
          <td><span class="badge ${row.result === 'EXITO' ? 'badge-ok' : 'badge-err'}">${row.result}</span></td>
          <td>${row.question ? `<b>P:</b> ${row.question}<br/><b>R:</b> ${row.answer || ''}` : '-'}</td>
        </tr>
      `).join('');
    }

    checkConsultHealth();
  </script>
</body>
</html>
EOF

EXPOSE 80

