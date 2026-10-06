// Click-to-zoom for the slide images on case-study pages.
// The rest of the site works without JavaScript.
(function () {
  var shots = document.querySelectorAll('img.shot');
  if (!shots.length || typeof HTMLDialogElement === 'undefined') return;

  var dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('aria-label', 'Enlarged image');
  dialog.innerHTML =
    '<button class="lightbox__close" type="button" aria-label="Close / 閉じる">&times;</button>' +
    '<div class="lightbox__scroll"><img class="lightbox__img" alt=""></div>';
  document.body.appendChild(dialog);

  var big = dialog.querySelector('.lightbox__img');
  var opener = null;

  // Use the largest size listed in the image's srcset
  function largest(img) {
    var set = img.getAttribute('srcset');
    if (!set) return img.currentSrc || img.src;
    var best = set.split(',').map(function (s) {
      var p = s.trim().split(/\s+/);
      return { url: p[0], w: parseInt(p[1], 10) || 0 };
    }).sort(function (a, b) { return b.w - a.w; })[0];
    return best.url;
  }

  shots.forEach(function (img) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'zoom';
    img.parentNode.insertBefore(button, img);
    button.appendChild(img);
    var hint = document.createElement('span');
    hint.className = 'visually-hidden';
    hint.textContent = 'Zoom in / 拡大する';
    button.appendChild(hint);

    button.addEventListener('click', function () {
      opener = button;
      big.src = largest(img);
      big.alt = img.alt;
      dialog.showModal();
    });
  });

  dialog.addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('close', function () {
    big.removeAttribute('src');
    if (opener) opener.focus();
  });
})();
