window.initGeetest4 = function (_config, callback) {
  let ready = function () {};
  let success = function () {};
  let mount = null;
  const instance = {
    appendTo: function (target) {
      mount = typeof target === 'string' ? document.querySelector(target) : target;
      const panel = document.createElement('div');
      panel.className = 'mock-captcha';
      panel.innerHTML = '<strong>GT4 MOCK</strong><span>这是假组件，只用于本地状态机测试。</span>';
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = '完成 GT4 模拟真人验证';
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
      return {lot_number: 'mock-lot', captcha_output: 'mock-output', pass_token: 'mock-pass', gen_time: '123', captcha_id: 'standalone-demo-gt4'};
    }
  };
  callback(instance);
};
