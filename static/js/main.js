// ===============================
// EAZI FINANCES - main.js
// (animaciones originales + login/registro Flask)
// ===============================
document.addEventListener('DOMContentLoaded', () => {
  // -----------------------------
  // NAVBAR BURGER
  // -----------------------------
  const burgers = Array.from(document.querySelectorAll('.navbar-burger'));
  burgers.forEach((el) => {
    el.addEventListener('click', () => {
      const target = el.dataset.target;
      const menu = document.getElementById(target);
      el.classList.toggle('is-active');
      menu?.classList.toggle('is-active');
    });
  });

  // -----------------------------
  // ELEMENTOS CLAVE
  // -----------------------------
  const startButton = document.querySelector('.start-button');
  const navLinks = document.querySelectorAll('.nav-link');
  const userIconBtn = document.getElementById('userIcon');
  const userDropdown = document.getElementById('userDropdown');

  // -----------------------------
  // GSAP - ANIMACIONES COMPLETAS
  // -----------------------------
  try {
    const navbarBrand = document.querySelector('.navbar-brand');

    // Entrada general
    gsap.set([startButton, navLinks, userIconBtn, navbarBrand], { opacity: 0, y: -20 });
    gsap.timeline()
      .to(navbarBrand, { duration: 0.6, opacity: 1, y: 0, ease: 'power3.out', delay: 0.1 })
      .to(navLinks, { duration: 0.6, opacity: 1, y: 0, ease: 'power3.out', stagger: 0.1 }, '-=0.4')
      .to(userIconBtn, { duration: 0.6, opacity: 1, y: 0, ease: 'power3.out' }, '-=0.3')
      .to(startButton, { duration: 0.6, opacity: 1, y: 0, ease: 'back.out(1.7)', delay: 0.1 }, '-=0.2');

    // Botón "Empezar" - hover/click
    if (startButton) {
      startButton.addEventListener('mouseenter', () => {
        gsap.timeline()
          .to(startButton, {
            duration: 0.3,
            scale: 1.05,
            y: -3,
            boxShadow: '0 8px 25px rgba(47, 133, 29, 0.3)',
            ease: 'power2.out'
          })
          .to(startButton, { duration: 0.2, backgroundColor: '#4CAF50', ease: 'power2.out' }, '-=0.3');
      });
      startButton.addEventListener('mouseleave', () => {
        gsap.timeline()
          .to(startButton, {
            duration: 0.3,
            scale: 1,
            y: 0,
            boxShadow: '0 2px 10px rgba(47, 133, 29, 0.1)',
            ease: 'power2.out'
          })
          .to(startButton, { duration: 0.2, backgroundColor: '#2F851D', ease: 'power2.out' }, '-=0.3');
      });
      startButton.addEventListener('click', () => {
        gsap.timeline()
          .to(startButton, { duration: 0.1, scale: 0.95, ease: 'power2.out' })
          .to(startButton, { duration: 0.2, scale: 1.05, ease: 'back.out(1.7)' });
      });
    }

    // Enlaces de navegación - entrada y hover
    navLinks.forEach((link, index) => {
      gsap.set(link, { opacity: 0, x: -30 });
      gsap.to(link, {
        duration: 0.6, opacity: 1, x: 0, ease: 'power3.out', delay: 0.3 + (index * 0.1)
      });

      link.addEventListener('mouseenter', () => {
        gsap.timeline()
          .to(link, { duration: 0.3, color: '#4CAF50', y: -2, ease: 'power2.out' })
          .to(link, { duration: 0.3, textShadow: '0 2px 8px rgba(76, 175, 80, 0.3)', ease: 'power2.out' }, '-=0.3');
      });
      link.addEventListener('mouseleave', () => {
        gsap.timeline()
          .to(link, { duration: 0.3, color: 'white', y: 0, ease: 'power2.out' })
          .to(link, { duration: 0.3, textShadow: 'none', ease: 'power2.out' }, '-=0.3');
      });
    });

    // Icono de usuario - hover
    if (userIconBtn) {
      userIconBtn.addEventListener('mouseenter', () => {
        gsap.to(userIconBtn, { duration: 0.3, scale: 1.1, backgroundColor: '#A7D28D', ease: 'power2.out' });
      });
      userIconBtn.addEventListener('mouseleave', () => {
        gsap.timeline()
          .to(userIconBtn, { duration: 0.3, scale: 1, backgroundColor: '#A7D28D', ease: 'power2.out' })
          .to(userIconBtn, { duration: 0.2, boxShadow: 'none', ease: 'power2.out' }, '-=0.3');
      });
    }

    // Logo del navbar - hover
    const navbarLogo = document.querySelector('.navbar-brand img');
    if (navbarLogo) {
      navbarLogo.addEventListener('mouseenter', () => {
        gsap.to(navbarLogo, { duration: 0.3, scale: 1.1, rotation: 10, ease: 'power2.out' });
      });
      navbarLogo.addEventListener('mouseleave', () => {
        gsap.to(navbarLogo, { duration: 0.3, scale: 1, rotation: 0, ease: 'power2.out' });
      });
    }

    // Logo principal + sombra (entrada, hover y flotación)
    const logoImage = document.querySelector('.logo-image');
    const logoShadow = document.querySelector('.logo-shadow');
    const logoGraphic = document.querySelector('.logo-graphic');

    gsap.set([logoImage, logoShadow], { opacity: 0, scale: 0.8 });
    gsap.timeline()
      .to(logoShadow, { duration: 1.2, opacity: 1, scale: 1, ease: 'back.out(1.7)', delay: 0.5 })
      .to(logoImage, { duration: 1, opacity: 1, scale: 1, ease: 'power3.out' }, '-=0.8');

    if (logoGraphic) {
      logoGraphic.addEventListener('mouseenter', () => {
        gsap.timeline()
          .to(logoImage, { duration: 0.4, scale: 1.05, rotation: 5, ease: 'power2.out' })
          .to(logoShadow, { duration: 0.4, scale: 1.1, opacity: 0.8, ease: 'power2.out' }, '-=0.4');
      });
      logoGraphic.addEventListener('mouseleave', () => {
        gsap.timeline()
          .to(logoImage, { duration: 0.4, scale: 1, rotation: 0, ease: 'power2.out' })
          .to(logoShadow, { duration: 0.4, scale: 1, opacity: 1, ease: 'power2.out' }, '-=0.4');
      });
    }

    gsap.to(logoImage, { duration: 3, y: -10, ease: 'power2.inOut', yoyo: true, repeat: -1 });
    gsap.to(logoShadow, { duration: 3, y: -5, ease: 'power2.inOut', yoyo: true, repeat: -1 });

    // Imágenes de características - entrada + hover
    const featureImages = document.querySelectorAll('.feature-image');
    featureImages.forEach((image, index) => {
      gsap.set(image, { opacity: 0, y: 30 });
      gsap.to(image, { duration: 0.8, opacity: 1, y: 0, ease: 'power3.out', delay: 0.3 + (index * 0.2) });

      image.addEventListener('mouseenter', () => {
        gsap.to(image, { duration: 0.3, y: -15, scale: 1.05, ease: 'power2.out' });
      });
      image.addEventListener('mouseleave', () => {
        gsap.timeline()
          .to(image, { duration: 0.3, y: 0, scale: 1, ease: 'power2.out' })
          .to(image, { duration: 0.2, boxShadow: 'none', ease: 'power2.out' }, '-=0.3');
      });
    });

    // Iconos de características - entrada + hover
    const featureIcons = document.querySelectorAll('.icon-image');
    featureIcons.forEach((icon, index) => {
      gsap.set(icon, { opacity: 0, scale: 0.8 });
      gsap.to(icon, { duration: 0.6, opacity: 1, scale: 1, ease: 'back.out(1.7)', delay: 0.5 + (index * 0.2) });

      icon.addEventListener('mouseenter', () => {
        gsap.to(icon, { duration: 0.3, scale: 1.1, rotation: 5, ease: 'power2.out' });
      });
      icon.addEventListener('mouseleave', () => {
        gsap.to(icon, { duration: 0.3, scale: 1, rotation: 0, ease: 'power2.out' });
      });
    });
  } catch (e) {
    console.warn('GSAP init warning:', e);
  }

  // -----------------------------
  // SWIPER (con cambio de texto)
  // -----------------------------
  try {
    const textElement = document.getElementById('carouselText');
    // eslint-disable-next-line no-undef
    const swiper = new Swiper('.mySwiper', {
      effect: 'coverflow',
      grabCursor: true,
      centeredSlides: true,
      slidesPerView: 'auto',
      loop: true,
      spaceBetween: 40,
      coverflowEffect: { rotate: 0, stretch: 0, depth: 350, modifier: 1.0, slideShadows: true },
      navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
      on: {
        slideChange: function () {
          const activeSlide = this.slides[this.activeIndex];
          const newText = activeSlide?.getAttribute('data-text') || '';
          if (textElement) {
            textElement.style.opacity = 0;
            setTimeout(() => { textElement.textContent = newText; textElement.style.opacity = 1; }, 200);
          }
        }
      }
    });
  } catch (e) { /* no-op */ }

  // -----------------------------
  // SCROLL SUAVE
  // -----------------------------
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        const navbarHeight = 80;
        const targetPosition = targetElement.offsetTop - navbarHeight;
        window.scrollTo({ top: targetPosition, behavior: 'smooth' });
      }
    });
  });

  // =====================================================
  // MODAL AUTH (Login / Registro)
  // =====================================================
  const authModal = document.getElementById('authModal');
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');
  const toRegisterBtn = document.getElementById('toRegister');
  const toLoginBtn = document.getElementById('toLogin');
  const authTitle = document.getElementById('authTitle');
  const authClose = authModal ? authModal.querySelector('.close') : null;

  function openAuth(view = 'login') {
    switchAuthView(view);
    authModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    userDropdown?.classList.remove('show');
  }
  function closeAuth() {
    authModal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
  function switchAuthView(view) {
    if (view === 'login') {
      authTitle.textContent = 'Iniciar sesión';
      loginForm.style.display = 'block';
      registerForm.style.display = 'none';
      setTimeout(() => document.getElementById('loginEmail')?.focus(), 0);
    } else {
      authTitle.textContent = 'Crear cuenta';
      loginForm.style.display = 'none';
      registerForm.style.display = 'block';
      setTimeout(() => document.getElementById('regName')?.focus(), 0);
    }
  }

  // Abrir modal desde icono y botón
  userIconBtn?.addEventListener('click', (e) => { e.stopPropagation(); openAuth('login'); });
  startButton?.addEventListener('click', () => openAuth('login'));

  // Toggle login/registro
  toRegisterBtn?.addEventListener('click', () => switchAuthView('register'));
  toLoginBtn?.addEventListener('click', () => switchAuthView('login'));

  // Cerrar modal
  authClose?.addEventListener('click', closeAuth);
  authModal?.addEventListener('click', (e) => { if (e.target === authModal) closeAuth(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && authModal?.style.display === 'block') closeAuth(); });

  // =====================================================
  // VALIDACIONES FRONT & ENVÍOS A FLASK
  // =====================================================
  const EMAIL_RE = /^\S+@\S+\.\S+$/;

  function setSubmitting(formEl, submitting) {
    const btn = formEl.querySelector('button[type="submit"]');
    if (!btn) return;
    if (!btn.dataset.defaultText) btn.dataset.defaultText = btn.textContent;
    btn.disabled = submitting;
    btn.textContent = submitting ? 'Enviando...' : btn.dataset.defaultText;
  }

  // Login
  loginForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const pass = document.getElementById('loginPassword').value;

    if (!EMAIL_RE.test(email)) return alert('Ingresa un correo válido.');
    if (!pass) return alert('Ingresa tu contraseña.');

    setSubmitting(loginForm, true);
    fetch('/login', { method: 'POST', body: new FormData(loginForm) })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          alert(`Bienvenido, ${data.user}`);
          closeAuth();
          // Redirigir al dashboard si está disponible en la respuesta
          if (data.redirect) {
            window.location.href = data.redirect;
          }
        } else {
          alert(data.message || 'Error al iniciar sesión.');
        }
      })
      .catch(() => alert('Error de conexión.'))
      .finally(() => setSubmitting(loginForm, false));
  });

  // Registro
  registerForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const pass = document.getElementById('regPassword').value;
    const phone = document.getElementById('regPhone').value.trim();

    if (!name) return alert('Escribe tu nombre.');
    if (!EMAIL_RE.test(email)) return alert('Correo inválido.');
    if (pass.length < 6) return alert('La contraseña debe tener al menos 6 caracteres.');
    if (phone && !/^\d+$/.test(phone)) return alert('El teléfono debe contener solo números.');

    setSubmitting(registerForm, true);
    fetch('/register', { method: 'POST', body: new FormData(registerForm) })
      .then(r => r.json())
      .then(data => {
        if (data.success) {
          alert('Cuenta creada correctamente. Ahora inicia sesión.');
          switchAuthView('login');
        } else {
          alert(data.message || 'No se pudo crear la cuenta.');
        }
      })
      .catch(() => alert('Error de conexión.'))
      .finally(() => setSubmitting(registerForm, false));
  });

  // =====================================================
  // MODALES DEL FOOTER (simple)
  // =====================================================
  const footerItems = document.querySelectorAll('.footer-item');
  const allModals = document.querySelectorAll('.modal');
  const closeButtons = document.querySelectorAll('.close');

  footerItems.forEach((item) => {
    item.addEventListener('click', function () {
      const modalId = this.getAttribute('data-modal');
      const modal = document.getElementById(modalId + 'Modal');
      if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
      }
    });
  });

  closeButtons.forEach((btn) => {
    btn.addEventListener('click', function () {
      const modal = this.closest('.modal');
      if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  });

  allModals.forEach((modal) => {
    modal.addEventListener('click', function (e) {
      if (e.target === this) {
        this.style.display = 'none';
        document.body.style.overflow = 'auto';
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      allModals.forEach((m) => {
        if (m.style.display === 'block') {
          m.style.display = 'none';
          document.body.style.overflow = 'auto';
        }
      });
    }
  });
});