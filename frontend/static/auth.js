// auth.js - Clerk Authentication (Vanilla JS / CDN)
// window.Clerk from clerk.browser.js is a SINGLETON INSTANCE, not a constructor.
// The publishableKey is passed via data-clerk-publishable-key on the script tag.
// After the script loads, call window.Clerk.load({ appearance }) with no key arg.

// ── Config ──────────────────────────────────────────────────────────────────

async function getPublishableKey() {
  console.log("[auth.js] getPublishableKey called");
  const apiBase = window.API_BASE_URL || "";
  console.log("[auth.js] window.API_BASE_URL =", apiBase);
  const url = apiBase + "/config";
  console.log("[auth.js] Fetching config from:", url);
  try {
    const res = await fetch(url);
    console.log("[auth.js] /config response status:", res.status);
    if (res.ok) {
      const data = await res.json();
      console.log("[auth.js] /config response data:", data);
      if (data.CLERK_PUBLISHABLE_KEY) {
        console.log("[auth.js] Clerk key found in response:", data.CLERK_PUBLISHABLE_KEY);
        // Also set the API base URL for the frontend
        window.API_BASE_URL = data.API_BASE_URL || "";
        return data.CLERK_PUBLISHABLE_KEY;
      } else {
        console.warn("[auth.js] /config response missing CLERK_PUBLISHABLE_KEY");
      }
    } else {
      console.warn("[auth.js] /config request not ok:", res.status, res.statusText);
    }
  } catch (err) {
    console.error("[auth.js] Error fetching Clerk config from backend:", err);
  }

  if (typeof AuthConfig !== 'undefined' && AuthConfig.CLERK_PUBLISHABLE_KEY) {
    console.log("[auth.js] Falling back to AuthConfig.CLERK_PUBLISHABLE_KEY:", AuthConfig.CLERK_PUBLISHABLE_KEY);
    return AuthConfig.CLERK_PUBLISHABLE_KEY;
  }
  console.warn("[auth.js] No Clerk key found (fetch failed and AuthConfig empty)");
  return null;
}

// ── Path resolution (Live Server, FastAPI, Vercel) ──────────────────────────

function getAuthPaths() {
  const path = window.location.pathname;
  if (path.includes('/templates/')) {
    const base = path.substring(0, path.indexOf('/templates/') + '/templates/'.length);
    return { dashboard: base + 'index.html', signin: base + 'signin.html', signup: base + 'signup.html' };
  }
  return { dashboard: '/', signin: '/signin', signup: '/signup' };
}

function currentPage() {
  const path = window.location.pathname;
  if (path.includes('signin.html') || path.endsWith('/signin')) return 'signin';
  if (path.includes('signup.html') || path.endsWith('/signup')) return 'signup';
  return 'dashboard';
}

// ── Appearance (dark theme matching the dashboard) ──────────────────────────

const clerkAppearance = {
  variables: {
    colorPrimary:                 '#7C5CFC',
    colorBackground:              '#1A1D2E',
    colorText:                    '#FFFFFF',
    colorInputBackground:         '#252840',
    colorInputText:               '#FFFFFF',
    colorTextSecondary:           '#A6A8B5',
    colorTextOnPrimaryBackground: '#FFFFFF',
    colorNeutral:                 '#FFFFFF',
    borderRadius:                 '12px',
    fontFamily:                   "'Inter', sans-serif",
    fontSize:                     '14px',
  },
  elements: {
    // Card wrapper
    card: {
      backgroundColor: '#1A1D2E',
      border: '1px solid rgba(255,255,255,0.10)',
      boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
      borderRadius: '18px',
    },
    // Social (Google/GitHub etc.) buttons — light background for visibility
    socialButtonsBlockButton: {
      backgroundColor: '#FFFFFF',
      border: '1px solid rgba(255,255,255,0.15)',
      color: '#1A1D2E',
      fontWeight: '500',
      borderRadius: '10px',
      transition: 'all 200ms ease',
    },
    socialButtonsBlockButtonText: {
      color: '#1A1D2E',
      fontWeight: '500',
    },
    // Divider
    dividerText: { color: '#A6A8B5' },
    dividerLine: { backgroundColor: 'rgba(255,255,255,0.10)' },
    // Form inputs
    formFieldInput: {
      backgroundColor: '#252840',
      border: '1px solid rgba(255,255,255,0.12)',
      color: '#FFFFFF',
      borderRadius: '10px',
    },
    formFieldLabel: { color: '#A6A8B5' },
    // Primary submit button
    formButtonPrimary: {
      backgroundColor: '#7C5CFC',
      borderRadius: '10px',
      fontWeight: '600',
    },
    // Hide "Optional" hint on Last Name (First Name is marked Required in Clerk Dashboard)
    formFieldHintText__lastName:  { display: 'none' },
    formFieldHintText__firstName: { display: 'none' }, // Required asterisk is shown by Clerk automatically
    footerActionLink: { color: '#FF4F8B' },
    // Header
    headerTitle:    { color: '#FFFFFF', fontWeight: '700' },
    headerSubtitle: { color: '#A6A8B5' },
    // Internal card background
    cardBox: {
      backgroundColor: '#1A1D2E',
    },
  }
};

// ── Script loader ───────────────────────────────────────────────────────────
// Loads the Clerk browser bundle from CDN.

function loadClerkScript(publishableKey) {
  return new Promise((resolve, reject) => {
    // Already loaded?
    if (window.Clerk && typeof window.Clerk.load === 'function') {
      resolve();
      return;
    }
    const s = document.createElement('script');
    s.setAttribute('data-clerk-publishable-key', publishableKey);
    s.src = 'https://cdn.jsdelivr.net/npm/@clerk/clerk-js@5/dist/clerk.browser.js';
    s.crossOrigin = 'anonymous';
    s.type = 'text/javascript';
    s.onload  = resolve;
    s.onerror = () => reject(new Error('Failed to load Clerk SDK from CDN.'));
    document.head.appendChild(s);
  });
}

// ── Main init ───────────────────────────────────────────────────────────────

async function initAuth() {
  console.log("[auth.js] initAuth started");
  const publishableKey = await getPublishableKey();
  console.log("[auth.js] getPublishableKey returned:", publishableKey);
  if (!publishableKey) {
    showAuthError('Clerk key missing', 'Configure CLERK_PUBLISHABLE_KEY on the backend or in <code>frontend/static/auth-config.js</code>.');
    return;
  }

  try {
    console.log("[auth.js] Loading Clerk SDK");
    await loadClerkScript(publishableKey);
    console.log("[auth.js] Clerk SDK loaded");

    // Initialize window.Clerk using the official options pattern
    await window.Clerk.load({
      appearance: clerkAppearance
    });
    console.log("[auth.js] Clerk.load completed");
    route(window.Clerk);
  } catch (err) {
    console.error('[auth.js] Clerk init error:', err);
    showAuthError('Authentication failed to initialise.', err.message || 'See browser console.');
  }
}

// ── Routing ─────────────────────────────────────────────────────────────────

function route(clerk) {
  const page  = currentPage();
  const paths = getAuthPaths();

  if (page === 'signin' || page === 'signup') {
    if (clerk.user) {
      window.location.replace(paths.dashboard);
    } else {
      hideSpinner();
      if (page === 'signin') {
        clerk.mountSignIn(document.getElementById('signin-container'), {
          signUpUrl:      paths.signup,
          afterSignInUrl: paths.dashboard,
        });
      } else {
        clerk.mountSignUp(document.getElementById('signup-container'), {
          signInUrl:      paths.signin,
          afterSignUpUrl: paths.dashboard,
        });
      }
    }
  } else {
    // Dashboard
    if (!clerk.user) {
      window.location.replace(paths.signin);
    } else {
      revealDashboard(clerk.user);
    }
  }
}

// ── Dashboard ────────────────────────────────────────────────────────────────

function revealDashboard(user) {
  const loader       = document.getElementById('loadingScreen');
  const appContainer = document.getElementById('appContainer');
  const nameEl       = document.getElementById('dropdownUserName');
  const emailEl      = document.getElementById('dropdownUserEmail');
  const avatarEl     = document.getElementById('dropdownAvatar');
  const headerAvatarEl = document.getElementById('headerAvatar');
  const signOutBtn   = document.getElementById('signOutBtn');

  if (nameEl) {
    nameEl.textContent = user.fullName || 'User';
  }

  if (emailEl && user.primaryEmailAddress) {
    emailEl.textContent = user.primaryEmailAddress.emailAddress;
  }

  if (avatarEl && user.imageUrl) {
    avatarEl.innerHTML = `<img src="${user.imageUrl}" alt="avatar" class="user-avatar-img">`;
  }

  if (headerAvatarEl && user.imageUrl) {
    headerAvatarEl.innerHTML = `<img src="${user.imageUrl}" alt="avatar" class="user-avatar-img">`;
  }

  if (signOutBtn) {
    signOutBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (loader)       loader.style.display = 'flex';
      if (appContainer) appContainer.style.display = 'none';
      await window.Clerk.signOut();
    });
  }

  const manageAccountBtn = document.getElementById('manageAccountBtn');
  if (manageAccountBtn) {
    manageAccountBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      window.Clerk.openUserProfile();
    });
  }

  if (loader) {
    loader.style.transition = 'opacity 300ms ease';
    loader.style.opacity    = '0';
    setTimeout(() => { loader.style.display = 'none'; }, 320);
  }

  if (appContainer) {
    appContainer.style.display = 'grid';
    if (window.lucide) lucide.createIcons();
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function hideSpinner() {
  const el = document.getElementById('authLoader');
  if (el) el.style.display = 'none';
}

function showAuthError(title, detail) {
  hideSpinner();

  const loader = document.getElementById('loadingScreen');
  if (loader) loader.style.display = 'none';

  const container =
    document.getElementById('signin-container') ||
    document.getElementById('signup-container') ||
    document.body;

  container.innerHTML = `
    <div style="
      background:rgba(239,68,68,0.1);border:1px solid #EF4444;color:#fff;
      padding:28px 24px;border-radius:14px;max-width:420px;margin:40px auto;
      font-family:'Inter',sans-serif;text-align:center;
      box-shadow:0 10px 40px rgba(0,0,0,0.5);">
      <h3 style="margin:0 0 10px;color:#EF4444;font-size:16px;">${title}</h3>
      <p style="margin:0;font-size:13px;color:#A6A8B5;line-height:1.6;">${detail}</p>
    </div>`;
}

// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', initAuth);
