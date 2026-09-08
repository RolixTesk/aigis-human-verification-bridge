import type { HumanVerificationChallenge } from './types'

const loads = new Map<'gt3' | 'gt4', Promise<void>>()
const timeoutMs = 10_000

function ready(version: 'gt3' | 'gt4'): boolean {
  return version === 'gt3' ? typeof window.initGeetest === 'function' : typeof window.initGeetest4 === 'function'
}
function source(version: 'gt3' | 'gt4'): string {
  const filename = version === 'gt3' ? 'gt.0.4.9.js' : 'gt4.js'
  const family = import.meta.env.MODE === 'mock' ? 'mock-geetest' : 'geetest'
  return `${import.meta.env.BASE_URL}vendor/${family}/${filename}`
}

export function loadGeetestSdk(challenge: HumanVerificationChallenge): Promise<void> {
  const version = challenge.version
  if (ready(version)) return Promise.resolve()
  const pending = loads.get(version)
  if (pending) return pending

  const promise = new Promise<void>((resolve, reject) => {
    const id = `aigis-bridge-geetest-${version}`
    document.getElementById(id)?.remove()
    const script = document.createElement('script')
    script.id = id
    script.src = source(version)
    script.async = true
    let settled = false
    const timer = window.setTimeout(() => finish(new Error('真人验证组件加载超时。')), timeoutMs)

    function finish(error?: Error) {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      script.onload = null
      script.onerror = null
      if (error || !ready(version)) {
        script.remove()
        loads.delete(version)
        reject(error ?? new Error('真人验证组件未正确初始化。'))
        return
      }
      resolve()
    }

    script.onload = () => finish()
    script.onerror = () => finish(new Error('无法加载真人验证组件。'))
    document.head.appendChild(script)
  })
  loads.set(version, promise)
  return promise
}
