/* Adds a Show / Hide button (with an eye icon) to every password box on the page.
   Written in plain ES5 so it also works in older Android and desktop browsers. */
(function () {
    var dict = (window.CC_I18N && window.CC_I18N.dict) || {};
    function text(key, fallback) {
        return Object.prototype.hasOwnProperty.call(dict, key) ? dict[key] : fallback;
    }
    var SHOW = text('Show', 'Show');
    var HIDE = text('Hide', 'Hide');
    var SHOW_LONG = text('Show password', 'Show password');
    var HIDE_LONG = text('Hide password', 'Hide password');

    var SVG_OPEN = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>';
    var SVG_SHUT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 19c-7 0-11-7-11-7a18.5 18.5 0 0 1 5.06-5.94"/>' +
        '<path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 7 11 7a18.5 18.5 0 0 1-2.16 3.19"/>' +
        '<path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

    function setLabel(button, revealed) {
        button.innerHTML = (revealed ? SVG_SHUT : SVG_OPEN) + '<span></span>';
        button.getElementsByTagName('span')[0].appendChild(
            document.createTextNode(revealed ? HIDE : SHOW));
        button.setAttribute('aria-label', revealed ? HIDE_LONG : SHOW_LONG);
        button.setAttribute('aria-pressed', revealed ? 'true' : 'false');
    }

    function addToggle(input) {
        if (input.getAttribute('data-password-toggle') === 'on') { return; }
        input.setAttribute('data-password-toggle', 'on');

        var wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        input.style.paddingRight = '6.2rem';

        var button = document.createElement('button');
        button.type = 'button';
        button.style.cssText = 'position:absolute;right:8px;top:50%;margin-top:-16px;' +
            'display:inline-flex;align-items:center;gap:6px;border:0;background:#e8f5e9;color:#1B5E20;' +
            'font-weight:600;font-size:0.9rem;padding:5px 10px;border-radius:8px;cursor:pointer;line-height:1;';
        setLabel(button, false);
        button.onclick = function () {
            var reveal = input.type === 'password';
            input.type = reveal ? 'text' : 'password';
            setLabel(button, reveal);
            input.focus();
        };
        wrapper.appendChild(button);
    }

    var boxes = document.querySelectorAll('input[type="password"]');
    for (var i = 0; i < boxes.length; i++) { addToggle(boxes[i]); }
})();
