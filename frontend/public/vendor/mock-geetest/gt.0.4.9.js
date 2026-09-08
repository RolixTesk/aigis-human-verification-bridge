window.initGeetest = function (_config, callback) {
  let ready = function () {};
  let success = function () {};
  let mount = null;
  const instance = {
    appendTo: function (target) {
      mount = typeof target === 'string' ? document.querySelector(target) : target;
      const panel = document.createElement('div');
      panel.className = 'mock-captcha';
      panel.innerHTML = '<strong>GT3 MOCK</strong><span>这是假组件，只用于本地状态机测试。</span>';
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = '完成 GT3 模拟真人验证';
      button.addEventListener('click', function () { success(); });
      panel.appendChild(button);
      mount.appendChild(panel);
      queueMicrotask(function () { ready(); });
      return instance;
    },
    onReady: function (fn) { ready = fn; return instance; },
    onSuccess: function (fn) { success = fn; return instance; },
    onClose: function () { return instance; },
    onError: function () { return instance; },
    showCaptcha: function () {},
    destroy: function () { if (mount) mount.replaceChildren(); },
    getValidate: function () {
      return {geetest_challenge: 'mock-challenge', geetest_validate: 'mock-validate', geetest_seccode: 'mock-seccode'};
    }
  };
  callback(instance);
};
