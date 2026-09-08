import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import { loadGeetestSdk } from './loadSdk'
import type { GeetestCaptcha, HumanVerificationChallenge, HumanVerificationResult } from './types'

interface Props {
  challenge: HumanVerificationChallenge
  submitting: boolean
  onComplete: (result: HumanVerificationResult) => void
  onCancel: () => void
}
function stringValue(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 ? value : null
}

function validatedResult(challenge: HumanVerificationChallenge, raw: Record<string, unknown> | false): HumanVerificationResult | null {
  if (!raw) return null
  if (challenge.version === 'gt3') {
    const geetestChallenge = stringValue(raw.geetest_challenge)
    const validate = stringValue(raw.geetest_validate)
    const seccode = stringValue(raw.geetest_seccode)
    return geetestChallenge && validate && seccode
      ? { version: 'gt3', geetest_challenge: geetestChallenge, geetest_validate: validate, geetest_seccode: seccode }
      : null
  }
  const lotNumber = stringValue(raw.lot_number)
  const output = stringValue(raw.captcha_output)
  const passToken = stringValue(raw.pass_token)
  const genTime = stringValue(raw.gen_time)
  const captchaId = stringValue(raw.captcha_id) ?? challenge.captcha_id
  if (!lotNumber || !output || !passToken || !genTime || !captchaId) return null
  const signToken = stringValue(raw.sign_token)
  return {
    version: 'gt4',
    lot_number: lotNumber,
    captcha_output: output,
    pass_token: passToken,
    gen_time: genTime,
    captcha_id: captchaId,
    ...(signToken ? { sign_token: signToken } : {}),
  }
}

export function HumanVerificationModal({ challenge, submitting, onComplete, onCancel }: Props) {
  const mountId = `geetest-${useId().replace(/:/g, '')}`
  const captcha = useRef<GeetestCaptcha | null>(null)
  const dialog = useRef<HTMLElement | null>(null)
  const completed = useRef(false)
  const expired = useRef(false)
  const cancelRef = useRef(onCancel)
  const completeRef = useRef(onComplete)
  const [status, setStatus] = useState('正在加载验证组件…')
  const [failed, setFailed] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(() => Math.max(0, Math.ceil((Date.parse(challenge.expires_at) - Date.now()) / 1000)))

  useEffect(() => { cancelRef.current = onCancel }, [onCancel])
  useEffect(() => { completeRef.current = onComplete }, [onComplete])

  useEffect(() => {
    completed.current = false
    expired.current = false
    setFailed(false)
    setStatus('正在加载验证组件…')
    let disposed = false

    const succeed = () => {
      if (disposed || completed.current || expired.current || !captcha.current) return
      const result = validatedResult(challenge, captcha.current.getValidate())
      if (!result) {
        setFailed(true)
        setStatus('验证结果不完整，请关闭后重新发起。')
        return
      }
      completed.current = true
      completeRef.current(result)
    }

    loadGeetestSdk(challenge).then(() => {
      if (disposed) return
      const callback = (instance: GeetestCaptcha) => {
        if (disposed) { instance.destroy?.(); return }
        captcha.current = instance
        instance
          .onReady(() => { setStatus('请在下方完成真人验证。'); instance.showCaptcha?.() })
          .onSuccess(succeed)
          .onClose(() => { if (!completed.current) setStatus('验证已关闭，可以重新打开或取消。') })
          .onError(() => { setFailed(true); setStatus('验证组件发生错误，请取消后重新发起。') })
        instance.appendTo(`#${mountId}`)
      }

      if (challenge.version === 'gt3' && window.initGeetest) {
        window.initGeetest({
          gt: challenge.captcha_id,
          challenge: challenge.challenge,
          offline: challenge.success === 0,
          new_captcha: challenge.new_captcha ?? true,
          product: 'custom',
          area: `#${mountId}`,
          width: '100%',
          https: true,
        }, callback)
        return
      }
      if (challenge.version === 'gt4' && window.initGeetest4) {
        window.initGeetest4({
          captchaId: challenge.captcha_id,
          riskType: challenge.risk_type ?? undefined,
          product: 'popup',
          nextWidth: '320px',
          language: 'zho',
          lang: 'zho',
          userInfo: challenge.user_info ?? undefined,
          protocol: 'https://',
          https: true,
        }, callback)
        return
      }
      throw new Error('真人验证版本不可用。')
    }).catch((reason: unknown) => {
      if (disposed) return
      setFailed(true)
      setStatus(reason instanceof Error ? reason.message : '真人验证组件加载失败。')
    })

    return () => {
      disposed = true
      captcha.current?.destroy?.()
      captcha.current = null
    }
  }, [challenge, mountId])

  useEffect(() => {
    const update = () => {
      const remaining = Math.max(0, Math.ceil((Date.parse(challenge.expires_at) - Date.now()) / 1000))
      setSecondsLeft(remaining)
      if (remaining === 0 && !expired.current) {
        expired.current = true
        captcha.current?.destroy?.()
        captcha.current = null
        setFailed(true)
        setStatus('本次真人验证已过期，请关闭后重新发起。')
      }
    }
    update()
    const timer = window.setInterval(update, 1000)
    return () => window.clearInterval(timer)
  }, [challenge.expires_at])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !submitting) cancelRef.current()
      if (event.key !== 'Tab' || !dialog.current) return
      const focusable = Array.from(dialog.current.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])'))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.body.classList.add('human-verification-open')
    window.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.classList.remove('human-verification-open')
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [submitting])

  return createPortal(<div className="human-verification-overlay" role="presentation">
    <section ref={dialog} className="human-verification-dialog" role="dialog" aria-modal="true" aria-labelledby="human-verification-title">
      <header>
        <div><span aria-hidden="true">◇</span><span><small>HUMAN VERIFICATION</small><h2 id="human-verification-title">完成真人验证</h2></span></div>
        <button autoFocus type="button" aria-label="取消真人验证" disabled={submitting} onClick={onCancel}>×</button>
      </header>
      <p className={failed ? 'verification-status is-error' : 'verification-status'}>{submitting ? '正在将验证结果交回服务端…' : status}</p>
      <div className="geetest-mount" id={mountId} aria-live="polite" />
      <footer><span>GT{challenge.version === 'gt3' ? '3' : '4'} · {secondsLeft > 0 ? `${secondsLeft} 秒后过期` : '已过期'}</span><button type="button" disabled={submitting} onClick={onCancel}>取消本次操作</button></footer>
    </section>
  </div>, document.body)
}
