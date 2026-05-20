document.addEventListener('DOMContentLoaded', function () {

  // ===== 导航滚动效果 =====
  const navbar = document.getElementById('navbar');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', function () {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    updateActiveNav();
    updateBackToTop();
  });

  // 平滑滚动到对应区块
  navLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        const offset = navbar.offsetHeight;
        const position = target.offsetTop - offset;
        window.scrollTo({ top: position, behavior: 'smooth' });
      }
      // 移动端关闭菜单
      navMenu.classList.remove('active');
      hamburger.classList.remove('active');
    });
  });

  // 高亮当前区块对应的导航链接
  function updateActiveNav() {
    const scrollY = window.scrollY;
    const sections = document.querySelectorAll('section[id]');
    sections.forEach(section => {
      const sectionTop = section.offsetTop - navbar.offsetHeight - 10;
      const sectionBottom = sectionTop + section.offsetHeight;
      if (scrollY >= sectionTop && scrollY < sectionBottom) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + section.id) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  // ===== 移动端菜单 =====
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');

  hamburger.addEventListener('click', function () {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
  });

  // ===== 案例筛选 =====
  const filterBtns = document.querySelectorAll('.filter-btn');
  const caseCards = document.querySelectorAll('.case-card');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const filter = this.dataset.filter;

      caseCards.forEach(card => {
        if (filter === 'all' || card.dataset.category === filter) {
          card.classList.remove('hidden');
        } else {
          card.classList.add('hidden');
        }
      });
    });
  });

  // ===== 数字显示动画（不修改服务端渲染的数值） =====
  const statNums = document.querySelectorAll('.stat-num');
  let statsAnimated = false;

  function animateStats() {
    if (statsAnimated) return;
    const heroStats = document.querySelector('.hero-stats');
    if (!heroStats) return;
    const rect = heroStats.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      statsAnimated = true;
      statNums.forEach((el, i) => {
        // 只加渐入动画 class，不修改文本内容
        el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        el.style.transitionDelay = (i * 0.15) + 's';
        el.classList.add('stat-animated');
      });
    }
  }

  window.addEventListener('scroll', animateStats);
  animateStats();

  // ===== 联系表单提交 =====
  const contactForm = document.getElementById('contactForm');

  contactForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const btn = contactForm.querySelector('.btn-submit');
    const originalText = btn.textContent;
    btn.textContent = '提交中...';
    btn.disabled = true;

    const data = {
      name: document.getElementById('name').value,
      phone: document.getElementById('phone').value,
      email: document.getElementById('email').value,
      service: document.getElementById('service').value,
      message: document.getElementById('message').value,
    };

    try {
      const res = await fetch('/api/submit-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await res.json();
      if (result.ok) {
        showToast(result.message || '感谢您的留言，我们会尽快与您联系！');
        contactForm.reset();
      } else {
        showToast('提交失败，请稍后重试');
      }
    } catch (err) {
      showToast('网络错误，请检查网络后重试');
    }

    btn.textContent = originalText;
    btn.disabled = false;
  });

  // ===== Toast 提示 =====
  function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  // ===== 返回顶部按钮 =====
  const backToTop = document.createElement('button');
  backToTop.className = 'back-to-top';
  backToTop.innerHTML = '&#8593;';
  backToTop.title = '返回顶部';
  document.body.appendChild(backToTop);

  function updateBackToTop() {
    if (window.scrollY > 500) {
      backToTop.classList.add('show');
    } else {
      backToTop.classList.remove('show');
    }
  }

  backToTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

});
