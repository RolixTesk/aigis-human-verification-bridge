# Protocol references

The implementation was extracted from a working HoyoPanel integration and cross-checked against these local source
snapshots. They are references, not bundled dependencies.

## TeyvatGuide

- Repository: <https://github.com/BTMuli/TeyvatGuide>
- Reviewed commit: `485fb4e451287675976159128b668399f52a81eb`
- License in reviewed repository: MIT
- Relevant reviewed files: `src/components/func/geetest.ts`, `geetest.vue`, and the Aigis retry in
  `src/components/app/t-sidebar.vue`

The reviewed code demonstrated the GT3/GT4 initialization split and the upstream retry form
`session_id + ";" + base64(JSON.stringify(validate))`. This repository contains a separate Python/React
implementation rather than vendoring the Vue/Tauri modules.

## mihoyo-api-collect

- Repository: <https://github.com/UIGF-org/mihoyo-api-collect>
- Reviewed commit: `c42b4650a2861124194303fbcbcbb91a0373f877`
- License in reviewed repository: CC BY-NC 4.0
- Relevant scope: `hoyolab/login` and `hoyolab/user` documentation used to distinguish App Aigis from Web MMT and
  other business-verification protocols

Community documentation describes observed behavior and is not an official API guarantee or permission to bypass
authentication, risk controls, rate limits, terms, or privacy obligations.
