document.addEventListener('DOMContentLoaded', function () {
  if (typeof Typed !== 'undefined') {
    new Typed('#typed', {
      strings: [
        "Welcome to <strong>Django Search Engine</strong>",
        "Find signal across every engine.",
        "Search smarter, not harder."
      ],
      backSpeed: 18,
      typeSpeed: 32,
      backDelay: 450,
      showCursor: true,
      cursorChar: "|",
      contentType: 'html'
    });
  }

  const chips = document.querySelectorAll('.recent-chip');
  const input = document.querySelector('.search-input');
  const form = document.querySelector('.search-form');
  const copyBtn = document.getElementById('copy-link-btn');
  const fusedCards = Array.from(document.querySelectorAll('.fused-card a, .provider-card .result-link'));
  const providerSections = document.querySelectorAll('.provider-card');
  let focusedIndex = -1;
  const loadingOverlay = document.getElementById('loading-overlay');

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      if (!input || !form) return;
      input.value = chip.dataset.query || chip.textContent || '';
      form.submit();
    });
  });

  document.addEventListener('keydown', function (event) {
    const isCmdOrCtrlK = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k';
    if (isCmdOrCtrlK) {
      event.preventDefault();
      if (input) {
        input.focus();
        input.select();
      }
    }
  });

  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      const url = window.location.href;
      navigator.clipboard.writeText(url).then(function () {
        copyBtn.textContent = 'Copied!';
        setTimeout(function () {
          copyBtn.textContent = 'Copy link';
        }, 1800);
      }).catch(function () {
        copyBtn.textContent = 'Failed';
      });
    });
  }

  function focusCard(index) {
    if (index < 0 || index >= fusedCards.length) return;
    focusedIndex = index;
    fusedCards[focusedIndex].focus();
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusCard(Math.min(fusedCards.length - 1, focusedIndex + 1));
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusCard(Math.max(0, focusedIndex - 1));
    }
    if (event.key === 'Enter' && focusedIndex >= 0 && document.activeElement === fusedCards[focusedIndex]) {
      fusedCards[focusedIndex].click();
    }
  });

  function findLinksByProvider(label) {
    return Array.from(document.querySelectorAll('.provider-card'))
      .filter(card => card.querySelector('.provider-tag')?.textContent.trim() === label)
      .flatMap(card => Array.from(card.querySelectorAll('.result-link')).map(a => a.href));
  }

  function copyUrls(urls, target) {
    navigator.clipboard.writeText(urls.join('\n')).then(function () {
      target.textContent = 'Copied!';
      setTimeout(() => target.textContent = 'Copy URLs', 1800);
    }).catch(function () {
      target.textContent = 'Failed';
    });
  }

  document.querySelectorAll('.copy-provider').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const provider = btn.dataset.provider;
      const urls = findLinksByProvider(provider);
      if (urls.length) {
        copyUrls(urls, btn);
      }
    });
  });

  document.querySelectorAll('.open-all').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const provider = btn.dataset.provider;
      const urls = findLinksByProvider(provider);
      urls.forEach(url => window.open(url, '_blank'));
    });
  });

  function showLoading() {
    if (loadingOverlay) {
      loadingOverlay.classList.remove('hidden');
    }
  }

  document.querySelectorAll('form.loading-trigger').forEach(function (f) {
    f.addEventListener('submit', showLoading);
  });
});
